/* SPDX-License-Identifier: GPL-3.0-only
 * Adapted from Elixir voices.c and dsp.c, based on the LXR-02 firmware
 * (Copyright 2012–2026 Erica Synths, original LXR by Julian Schmidt).
 * A JAZZY voice is one patch. State fits the shared voice pool.
 */
typedef struct {
    uint8_t note;
    int8_t fine;
    uint8_t waves, wave2, mod1, mod2, amount1, amount2;
    uint8_t attack, decay, sweep, sweep_time, cutoff, reso, filter;
    uint8_t transient, transient_wave, drive, decimation, level;
} lxr_patch_t;

#include "../jazzy/lxr_factory.h"
#define LXR_COUNT (7u * LXR_KITS)
#define LXR_PAGE 126u  /* seven voices per set; both persisted digits fit the existing wire format */
#if JAZZY_EXTERNAL_ASSETS
#include "../jazzy/lxr_assets.h"
static uint8_t lxr_assets_valid;
#else
#define lxr_assets_valid 1
#endif

enum { LX_AGE, LX_ENV, LX_SWEEP, LX_RNG, LX_LOW, LX_BAND, LX_HOLD, LX_NOISE };

static unsigned lxr_voice_id(const track_t *t)
{
    unsigned page = (unsigned)t->p[P_LN0];
    if (page > (LXR_COUNT - 1u) / LXR_PAGE) page = 0;  /* legacy default = 127 */
    return (unsigned)clamp(t->p[P_E0], 0, LXR_PAGE - 1u) + page * LXR_PAGE;
}

static unsigned preset_active(const track_t *t)
{
    return t->eng_req == ENGI_LXR ? (unsigned)clamp(lxr_voice_id(t), 0, LXR_COUNT - 1u) : t->preset;
}

static unsigned lxr_byte(unsigned off)
{
#if JAZZY_EXTERNAL_ASSETS
    unsigned start = 0;
    for (unsigned i = 0; i < sizeof LXR_ASSETS / sizeof LXR_ASSETS[0]; i++) {
        if (off < LXR_ASSETS[i].end) return *fm1_xip_ptr(LXR_ASSETS[i].at + off - start);
        start = LXR_ASSETS[i].end;
    }
    return LXR_TAIL[off - start];
#else
    return LXR_SOURCE[off];
#endif
}

static const preset_t *lxr_factory(unsigned id)
{
    static char name[12];
    static const char role[7][2] = {"D1", "D2", "D3", "SN", "CY", "CH", "OH"};
    static const preset_t preset = {.name = name, .mono = TAG(DRUM), .e = {0,0,64,64,64,64,64,64}};
    unsigned at = 0;
    if (lxr_assets_valid)
        for (unsigned k = 0; k < 8u; k++) {
            unsigned c = lxr_byte(id / 7u * 8u + k);
            if (!c) break;
            name[at++] = (char)c;
        }
    name[at++] = ' ';
    name[at++] = role[id % 7u][0];
    name[at++] = role[id % 7u][1];
    name[at] = 0;
    return &preset;
}

static unsigned lxr_bits(unsigned *bit, unsigned width)
{
    if (!width) return 0;
    unsigned at = *bit >> 3, shift = *bit & 7u;
    unsigned value = lxr_byte(at);
    if (shift + width > 8u) value |= lxr_byte(at + 1u) << 8;
    *bit += width;
    return (value >> shift) & ((1u << width) - 1u);
}

static void lxr_unpack(lxr_patch_t *patch, unsigned id)
{
    unsigned group = LXR_GROUP[id % 7u];
    unsigned row = lxr_byte(group + id / 7u);
    unsigned layout = group + LXR_KITS, table = layout;
    for (unsigned k = 0; k < sizeof *patch; k++) {
        unsigned prefix = lxr_byte(table + 1u) >> 4;
        table += 2u + ((1u << prefix) - 1u);
    }
    table += (row >> 3) * 2u;
    unsigned bit = (lxr_byte(table) | (lxr_byte(table + 1u) << 8)) * 8u;
    uint8_t *out = (uint8_t *)patch;
    for (unsigned i = 0; i <= (row & 7u); i++) {
        unsigned at = layout;
        for (unsigned k = 0; k < sizeof *patch; k++) {
            unsigned base = lxr_byte(at++), mode = lxr_byte(at++), prefix = mode >> 4;
            unsigned max = (1u << prefix) - 1u, code = lxr_bits(&bit, prefix);
            out[k] = (uint8_t)(code == max ? base + lxr_bits(&bit, mode & 15u) : lxr_byte(at + code));
            at += max;
        }
    }
}

static const lxr_patch_t *lxr_patch(const track_t *t)
{
    /* No decompression in the usual audio path. Each track owns its cache
     * and only reloads when its selected voice or voice lock changes. */
    static struct { lxr_patch_t patch; uint16_t id; } cache[NTRK];
    static const lxr_patch_t fallback = {.note=32, .decay=63, .sweep=50, .sweep_time=32,
                                         .cutoff=95, .filter=7, .decimation=127, .level=110};
    if (!lxr_assets_valid) return &fallback;
    unsigned id = preset_active(t);
    unsigned k = (unsigned)(t - trk);
    if (cache[k].id != id + 1u) {
        lxr_unpack(&cache[k].patch, id);
        cache[k].id = (uint16_t)(id + 1u);
    }
    return &cache[k].patch;
}

static int32_t lxr_wave(unsigned type, uint32_t phase, uint32_t inc, voice_t *v)
{
    switch (type) {
    case 1: return osc_tri(phase);
    case 2: return osc_saw(phase, inc);
    case 3:
    case 5: return osc_pulse(phase, inc, type == 3 ? 0x80000000u : 0x40000000u);
    case 4: return (int32_t)noise32(&v->s[LX_RNG]) >> 16;
    default: return -osc_sine(phase + 0x40000000u);
    }
}

static uint32_t lxr_inc(int32_t pitch)
{
    return pitch_inc(clamp(pitch, 0, 1968));
}

static void lxr_on(track_t *t, voice_t *v)
{
    memset(v->s, 0, sizeof v->s);
    memset(v->ph, 0, sizeof v->ph);
    v->s[LX_ENV] = 1 << 24;
    v->s[LX_SWEEP] = 1 << 24;
    v->s[LX_RNG] = (int32_t)(0x2545f491u ^ v->age);
    /* One bit per audited factory preset, in import order. AUTO uses the
     * resulting sound's role, not its slot in the original kit. */
    static const uint8_t kick_map[(LXR_COUNT + 7u) / 8u] = {
        0x81, 0x42, 0x20, 0x10, 0x08, 0x04, 0x02, 0x80, 0x40, 0x20, 0x10, 0x08,
        0x14, 0x00, 0x81, 0x40, 0x60, 0x10, 0x08, 0x04, 0x02, 0x81, 0x00, 0x20,
        0x10, 0x08, 0x0c, 0x02, 0x81, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01,
        0x40, 0x21, 0x10, 0x08, 0x04, 0x0a, 0x80, 0x40, 0x20, 0x10, 0x08, 0x14,
        0x00, 0x81, 0x40, 0x20, 0x10, 0x08, 0x00, 0x00, 0x80, 0x40, 0x20, 0x30,
        0x00, 0x04, 0x02, 0x81, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01, 0x40,
        0x20, 0x10, 0x00,
    };
    unsigned id = preset_active(t);
    if ((kick_map[id >> 3] >> (id & 7u)) & 1u)
        kick_link_strike(t, v);
}

static int lxr_done(track_t *t, voice_t *v)
{
    (void)t;
    return v->s[LX_ENV] < 2048;
}

static void lxr_render(track_t *t, voice_t *v, int32_t *out, uint32_t n, const vmod_t *m)
{
    const lxr_patch_t *p = lxr_patch(t);
    unsigned kind = preset_active(t) % 7u;
    unsigned main_wave = p->waves & 7u, mod_wave = p->waves >> 3 & 7u;
    int32_t tune = m->pitch16 - 60 * 16 + t->p[P_E1] * 16;
    int32_t sweep = mulq15(p->sweep * 8, v->s[LX_SWEEP] >> 9);
    uint32_t main_inc = lxr_inc(p->note * 16 + p->fine + tune + sweep);
    uint32_t mod_inc = kind == 3 ? (uint32_t)p->mod1 * 16871903u :
                                  lxr_inc(p->mod1 * 16 + tune + sweep);
    uint32_t mod2_inc = kind < 4 ? 0 : lxr_inc(p->mod2 * 16 + tune);
    uint32_t decay = md_decay_k(p->decay + t->p[P_E2] - 64);
    uint32_t sweep_k = md_decay_k(12 + p->sweep_time / 2);
    int32_t amount = clamp((int)p->amount1 + (t->p[P_E3] - 64) * 2, 0, 127) * 258;
    int32_t edge = clamp((int)p->transient + (t->p[P_E5] - 64) * 2, 0, 127) * 258;
    int32_t drive = 32768 + clamp((int)p->drive + (t->p[P_E6] - 64) * 2, 0, 127) * 1024;
    int32_t cut = (p->cutoff + t->p[P_E4] - 64) * 256;
    int32_t velocity = v->vel * 258;
    int32_t vol = mulq15(p->level * 258, velocity);
    unsigned attack = 1u + (unsigned)p->attack * p->attack / 24u;
    unsigned hold = 1u + (127u - (unsigned)clamp((int)p->decimation + (t->p[P_E7] - 64) * 2, 0, 127)) / 8u;
    unsigned age = (unsigned)v->s[LX_AGE], repeat = age % hold;
    dsvf_t f;
    dsvf_coef(&f, cut, p->reso);

    for (unsigned i = 0; i < n; i++, age++) {
        if (!repeat) {
            int32_t mod, x, bp = 0, hp = 0;
            uint32_t phase = v->ph[0];
            if (kind == 3) {
                if (!age || v->ph[1] < mod_inc)
                    v->s[LX_NOISE] = lxr_wave(4, 0, 0, v);
                mod = v->s[LX_NOISE];
                x = lxr_wave(main_wave, phase, main_inc, v);
            } else {
                mod = amount ? lxr_wave(mod_wave, v->ph[1], mod_inc, v) : 0;
                if (kind >= 4 && p->amount2)
                    mod = clamp(mulq15(mod, amount) +
                                mulq15(lxr_wave(p->wave2, v->ph[2], mod2_inc, v), p->amount2 * 258),
                                -32768, 32767);
                else if (!(p->waves & 64u))
                    mod = mulq15(mod, amount);
                if (!(p->waves & 64u) && mod > 0)
                    phase += (uint32_t)mod << (main_wave ? 19 : 17);
                x = lxr_wave(main_wave, phase, main_inc, v);
                if (p->waves & 64u)
                    x = mulq15(x, 32767 - amount) + mulq15(mod, amount);
            }
            /* A short synthesized exciter replaces the source's sample bank. */
            int32_t click = 0;
            unsigned length = 24u + (p->transient_wave & 7u) * 12u;
            if (edge && age < length) {
                int32_t exciter = (p->transient_wave & 1u) ? lxr_wave(4, 0, 0, v) : osc_tri(age * 0x18000000u);
                click = mulq15(exciter, edge) * (int32_t)(length - age) / (int32_t)length;
            }
            int32_t in = kind == 3 ? mod : x + (kind < 3 ? click : 0);
            int32_t lp = p->filter == 7 ? in : dsvf_tick(&f, clamp(in, -32768, 32767), &v->s[LX_BAND], &v->s[LX_LOW], &bp, &hp);
            if (p->filter == 1) lp = hp;
            else if (p->filter == 2) lp = bp;
            else if (p->filter == 3) lp = (bp * f.k) >> 12;
            else if (p->filter == 4) lp += hp;
            else if (p->filter == 5) lp -= hp;
            if (kind == 3) lp = mulq15(lp, amount) + mulq15(x, 32767 - amount);
            if (kind >= 3) lp += click;
            int32_t eg = age >= attack ? v->s[LX_ENV] >> 9 : (int32_t)(age * 32767u / attack);
            int32_t shaped = mulq15(clamp(lp, -32768, 32767), eg);
            v->s[LX_HOLD] = mulq15(softclip(mulq16(shaped, (uint32_t)drive)), vol);
        }
        if (++repeat == hold) repeat = 0;
        v->ph[0] += main_inc;
        v->ph[1] += mod_inc;
        v->ph[2] += mod2_inc;
        if (age >= attack) v->s[LX_ENV] = mulq16(v->s[LX_ENV], decay);
        out[i] += mulq15(v->s[LX_HOLD], amp_at(m, i));
    }
    /* The pitch increment is latched at the block boundary. Advance its
     * exponential once for the entire block instead of once per sample. */
    for (unsigned ticks = n; ticks; ticks >>= 1) {
        if (ticks & 1u) v->s[LX_SWEEP] = mulq16(v->s[LX_SWEEP], sweep_k);
        sweep_k = (sweep_k * sweep_k) >> 16;
    }
    v->s[LX_AGE] = (int32_t)age;
}

static const engine_t ENG_LXR = {
    .name = "LXR", .page_title = {"VOICE", "CIRCUIT"},
    .edit = {
        {"VOICE", F_INT, 0, LXR_PAGE - 1u, 0, 0, 0}, {"TUNE", F_SEMI, -24, 24, 0, 0, 0},
        {"DECAY", F_INT, 0, 127, 64, 0, 0}, {"MOD", F_INT, 0, 127, 64, 0, 0},
        {"COLOR", F_INT, 0, 127, 64, 0, 0}, {"TRANSIENT", F_INT, 0, 127, 64, 0, 0},
        {"DRIVE", F_INT, 0, 127, 64, 0, 0}, {"CRUSH", F_INT, 0, 127, 64, 0, 0},
    },
    .npresets = LXR_COUNT, .poly = 1, .oneshot = 1, .ownenv = 1,
    .note_on = lxr_on, .render = lxr_render, .done = lxr_done,
    .knob = {P_E1, P_E2, P_E3, P_E4}
};

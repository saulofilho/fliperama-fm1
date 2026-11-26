/* SPDX-License-Identifier: GPL-3.0-only
 * Copyright (C) 2026 Andrew GG. S1Vave native extensions; shared Ober DSP remains in jo_dsp.h. */
static inline __attribute__((always_inline)) int32_t js_svf_lp(const jo_svf_coef_t *c, jo_svf_state_t *s, int32_t in)   /* the plain stage (24 dB's second) */
{
    int32_t v3 = in - s->ic2;
    int32_t v1 = (c->a1 * s->ic1 + c->a2 * v3) >> 13;
    int32_t v2 = s->ic2 + ((c->a2 * s->ic1 + c->a3 * v3) >> 13);
    int32_t n1 = 2 * v1 - s->ic1;
    s->ic1 = (uint32_t)(n1 + 24576) < 49152u ? n1 : jo_softclip(n1 >> 1) << 1;
    s->ic2 = 2 * v2 - s->ic2;
    return v2;
}
/* ---- Roland S-1 Extensions: OSC DRAW, OSC CHOP, Pink Noise */

/* OSC DRAW: 16-step user wavetable lookup with Multiply (1.0x to 32.0x in Q8) and Step/Slope interpolation */
enum { js_DRAW_OFF, js_DRAW_STEP, js_DRAW_SLOPE };

static inline __attribute__((always_inline)) int32_t js_osc_draw_sample(const int16_t *draw_table, uint32_t ph, uint32_t mult_q8, uint32_t mode)
{
    uint32_t eff_ph = (uint32_t)(((uint64_t)ph * mult_q8) >> 8);
    uint32_t idx = (eff_ph >> 28) & 15u;
    if (mode == js_DRAW_STEP) {
        /* Soften the step edge to prevent wideband aliasing clicks */
        uint32_t sub = (eff_ph >> 20) & 255u; /* 0..255 within slice */
        if (sub < 32u) {
            uint32_t prev_idx = (idx + 15u) & 15u;
            int32_t v_prev = draw_table[prev_idx];
            int32_t v_curr = draw_table[idx];
            uint32_t t = sub << 3; /* 0..248 (Q8) */
            return v_prev + (int32_t)(((int64_t)(v_curr - v_prev) * t) >> 8);
        }
        return (int32_t)draw_table[idx];
    } else { /* js_DRAW_SLOPE */
        uint32_t next_idx = (idx + 1u) & 15u;
        uint32_t frac = (eff_ph >> 12) & 0xFFFFu; /* Q16 */
        /* Cubic smoothstep interpolation S(t) = 3t^2 - 2t^3 to round sharp vertex corners */
        int32_t t = (int32_t)(frac >> 1); /* Q15: 0..32767 */
        int32_t t2 = (t * t) >> 15;       /* Q15 */
        int32_t smooth_t = (int32_t)(((int64_t)t2 * (98304 - 2 * t)) >> 16); /* Q15: 0..32768 */
        int32_t v0 = draw_table[idx];
        int32_t v1 = draw_table[next_idx];
        return v0 + (int32_t)(((int64_t)(v1 - v0) * smooth_t) >> 15);
    }
}

/* OSC CHOP: Overtone gain calculation and 16-step bitmask slicing */
static inline int32_t js_chop_calc_masked_gain(uint32_t ovtn)
{
    if (ovtn == 0) return 32767;
    if (ovtn <= 100u) {
        int32_t amt = (int32_t)ovtn * 327 + ((int32_t)ovtn * 67) / 100;
        return 32767 - amt;
    } else {
        uint32_t diff = ovtn - 100u;
        int32_t amt = (int32_t)diff * 327 + ((int32_t)diff * 67) / 100;
        return -amt;
    }
}

static inline __attribute__((always_inline)) int32_t js_osc_chop_sample(int32_t sample, uint32_t ph, uint16_t mask, uint32_t comb_q8, int32_t g_masked)
{
    if (g_masked == 32767) return sample; /* Dry / passthrough */
    uint32_t chop_ph = (uint32_t)(((uint64_t)ph * comb_q8) >> 8);
    uint32_t slice = (chop_ph >> 28) & 15u;
    uint32_t next_slice = (slice + 1u) & 15u;
    int32_t g_curr = (mask & (1u << slice)) ? 32767 : g_masked;
    int32_t g_next = (mask & (1u << next_slice)) ? 32767 : g_masked;
    uint32_t pos = (chop_ph >> 20) & 255u;
    int32_t g = g_curr;
    if (g_curr != g_next && pos >= 224u) {
        /* Soft linear ramp over the final 32/256 of the slice */
        uint32_t t = (pos - 224u) << 3; /* 0..248 in Q8 */
        g = g_curr + (int32_t)(((int64_t)(g_next - g_curr) * t) >> 8);
    }
    return (int32_t)(((int64_t)sample * g) >> 15);
}

/* Pink Noise Generator: 3-pole Gardner IIR filter + 2-pole Roland analog RC warmer */
typedef struct {
    int32_t b0, b1, b2;
    int32_t lp1, lp2;
} js_pink_noise_t;

static inline __attribute__((always_inline)) int32_t js_pink_noise_step(js_pink_noise_t *pn, int32_t white)
{
    /* Clean Gardner pinking poles scaled to guarantee zero internal clipping */
    pn->b0 = (int32_t)(((int64_t)pn->b0 * 32691 + (int64_t)white * 464) >> 15);
    pn->b1 = (int32_t)(((int64_t)pn->b1 * 31555 + (int64_t)white * 1400) >> 15);
    pn->b2 = (int32_t)(((int64_t)pn->b2 * 18677 + (int64_t)white * 4400) >> 15);
    int32_t out = pn->b0 + pn->b1 + pn->b2;
    /* Gentle 2-pole lowpass matching Roland S-1 / SH-101 analog transistor RC roll-off */
    pn->lp1 += (int32_t)(((int64_t)(out - pn->lp1) * 24000) >> 15);
    pn->lp2 += (int32_t)(((int64_t)(pn->lp1 - pn->lp2) * 28000) >> 15);
    return pn->lp2;
}


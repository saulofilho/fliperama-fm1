/* SPDX-License-Identifier: GPL-3.0-only
 * JAZZY single-hit track adapter for Rhythmer's Elixir sequencer generators.
 */
#if JAZZY_EXTERNAL_ASSETS
#include "../six/drum_grids_map.h"
#define DG_MAP ((const uint8_t (*)[96])fm1_xip_ptr(JCAT_GRIDS_AT))
#endif
#include "../six/drum_generate.h"
#undef DG_MAP

static const char *const DG_NAMES[] = {"EUCLID", "MUTATE", "TURING", "CELLULAR", "GRIDS"};
static drum_gen_t dg_cfg[NTRK];
static uint8_t dg_seen;

static drum_gen_t *dg_current(track_t *t)
{
    unsigned k = trk_index(t);
    if (!(dg_seen & (1u << k))) {
        unsigned patch = preset_active(t) % 7;
        unsigned lane = trk_eng(t) == ENGI_LXR ? (patch >= 4 ? 2 : patch == 3 ? 1 : 0) : 0;
        dg_cfg[k] = (drum_gen_t){DG_GRIDS, lane, 72, 0, 64, 64, 1, 31, 0, 0, 0, 8};
        dg_seen |= (uint8_t)(1u << k);
    }
    return &dg_cfg[k];
}

static int drumgen_page(void)
{
    return !ui.home && !ui.menu && !ui.confirm && !ui.layer && !ui.ly &&
           drumgen_track(TSEL) && cur_page()->graph == GR_DGEN;
}

static void drumgen_knob(unsigned page, unsigned knob, int32_t delta)
{
    static const uint8_t max_default[3][4] = {{DG_COUNT-1,2,127,127},{127,127,1,127},{64,63,3,16}};
    drum_gen_t *g = dg_current(TSEL);
    uint8_t *fields = (uint8_t *)g;
    unsigned field = page * 4 + knob;
    int hi = max_default[page][knob], lo = field == 11 ? 2 : 0;
    if (field == 3) hi = g->type == DG_CELLULAR ? 255 : g->type == DG_EUCLID ? 63 : 127;
    int change = hi > 16 ? accel(EN_K1 + knob, delta, hi) : delta > 0 ? 1 : -1;
    fields[field] = (uint8_t)clamp(fields[field] + change, lo, hi);
    if (field == 0) g->variation = g->type == DG_CELLULAR ? 30 : g->type == DG_TURING ? 96 : 0;
    ui.force = 1;
}

static void drumgen_apply(track_t *t, int undo)
{
    if (!drumgen_track(t) || chain_busy()) {
        ui_message("STOP SONG TO EDIT");
        return;
    }
    if (undo) {
        ui_message(undo_do() ? "NOTHING TO UNDO" : "SEQ GEN UNDONE");
        ui.force = 1;
        return;
    }
    drum_gen_t g = *dg_current(t);
    if (g.type == DG_MUTATE && !g.density) return;
    if (g.type == DG_GRIDS && !jazzy_catalog_valid) {
        ui_message("GRIDS DATA MISSING");
        return;
    }
    if (g.lane == 2) g.lane = 3; /* role selector: kick / snare / hat */
    unsigned len = (unsigned)clamp(t->p[P_SLEN], 1, NSTEP);
    uint64_t before = 0, acc = 0, late, flam;
    uint8_t note = 60;
    for (unsigned i = len; i--;) {
        const step_t *s = &t->step[i];
        if (s->time != ST_NOTE || !s->n) continue;
        uint64_t bit = (uint64_t)1 << i;
        before |= bit;
        if (s->flags & SF_ACCENT) acc |= bit;
        note = s->note[0];
    }
    drum_gen_row_t r = drum_generate(&g, len, before, acc, &late, &flam);
    if (g.type == DG_MUTATE && r.hits == before && r.accents == acc) return;
    undo_mark();
    load_begin(t, LOAD_PAT);
    for (unsigned i = 0; i < len; i++) {
        step_t *s = &t->step[i];
        uint64_t bit = (uint64_t)1 << i;
        if (g.type == DG_MUTATE && !((r.hits ^ before) & bit)) {
            if (before & bit) s->flags = (uint8_t)((s->flags & ~SF_ACCENT) | (r.accents & bit ? SF_ACCENT : 0));
            else if (s->time == ST_TIE) s->time = ST_REST;
            continue;
        }
        s->time = r.hits & bit ? ST_NOTE : ST_REST;
        s->n = (uint8_t)(s->time == ST_NOTE);
        s->note[0] = note;
        s->vel = 100;
        s->flags = r.accents & bit ? SF_ACCENT : 0;
        /* A double map hit uses the existing x2 retrigger. MICRO tops out at 31/64. */
        ST_MICRO_SET(s, late & bit ? MICRO_MAX : 0);
        step_set_ratchet(s, flam & bit ? 2 : 1);
    }
    load_end(t);
    if (t == TSEL) cursor_fix();
    ui.force = 1;
    ui_say("SEQ GEN: ", DG_NAMES[g.type]);
}

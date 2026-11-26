/* SPDX-License-Identifier: GPL-3.0-only */
#define UI_TEST_NO_MAIN 1
#include "jazzy_host.h"

static void turn(unsigned control, int steps)
{
    host_enc[panel.enc[control]] = steps * panel.dir[control];
    fm1_ms += 16u;
    ui_input();
}

static void reset_duck(void)
{
    duck_env = duck_peak = duck_hit = duck_att = duck_hold = 0;
    duck_g0 = duck_g1 = 32767;
    kick_link_hold = kick_link_local = 0;
}

static int32_t midi_gain(unsigned packet)
{
    reset_duck();
    midi_in_event(packet);
    events_block(CTL);
    duck_block(CTL);
    return duck_g1;
}

static int track_hit(track_t *t, unsigned engine, unsigned preset)
{
    trk_all_off(t);
    set_engine_of(t, engine);
    apply_preset_to(t, preset);
    t->engine = t->eng_req;
    t->xf_on = 0;
    t->p[P_LEVEL] = 100;
    t->p[P_MUTE] = 0;
    reset_duck();
    trk_note_on(t, 36, 100);
    events_block(CTL);
    duck_block(CTL);
    return duck_g1 < 32767;
}

static int auto_hit(unsigned engine, unsigned preset)
{
    return track_hit(&trk[0], engine, preset);
}

int main(void)
{
    static int32_t master[2600];
    static project_t before, after;
    static project_store_t packed;
    int bad = 0;
    ui_power_on(); fm6_init(); power_on_parts();

    nav_put(SEC_FX, "MASTER");
    turn(EN_K3, 58);
    turn(EN_SELECT, 1);
    bad += check("MASTER is followed by the DUCK source page", str_eq(cur_page()->title, "DUCK"));
    turn(EN_K1, 8);
    int16_t *value;
    const param_desc_t *desc = page_desc(cur_page(), 1, &value);
    char formatted[16];
    const char *unit;
    param_format(desc, *value, formatted, &unit);
    bad += check("MIDI K2 is channel ANY, K3 is the trigger note",
        value == &song.g[G_DCH] && str_eq(formatted, "ANY") && page_desc(cur_page(), 2, &value) == &GP[G_DNOTE]);
    turn(EN_K2, 16);
    turn(EN_SELECT, 1);
    desc = page_desc(cur_page(), 2, &value);
    bad += check("DUCK ENV AMT shares the MASTER value", str_eq(cur_page()->title, "DUCK ENV") &&
        str_eq(desc->label, "AMT") && value == &song.g[G_DUCK] && *value == 58);
    turn(EN_K1, 12);
    turn(EN_K2, 17);
    turn(EN_K3, -21);
    turn(EN_SELECT, -2);
    desc = page_desc(cur_page(), 3, &value);
    param_format(desc, *value, formatted, &unit);
    bad += check("AMT updates MASTER and REL displays milliseconds",
        song.g[G_DUCK] == 37 && str_eq(formatted, "303") && str_eq(unit, "ms"));
    turn(EN_K3, 21);
    midi_gain(0x64249f09u);
    for (unsigned i = 0; i < NELEM(master); i++) {
        master[i] = duck_g1;
        duck_block(CTL);
    }
    turn(EN_SELECT, 2);
    turn(EN_K3, -21);
    turn(EN_K3, 21);
    midi_gain(0x01249f09u);
    int same = master[0] < 32767 && master[NELEM(master) - 1] == 32767;
    for (unsigned i = 0; i < NELEM(master); i++) {
        same &= master[i] == duck_g1;
        duck_block(CTL);
    }
    bad += check("MASTER and AMT give the same gain curve; MIDI velocity is timing only", same);
    bad += check("wrong channel, wrong note and Note Off leave the gain at unity",
        midi_gain(0x7f249009u) == 32767 && midi_gain(0x7f259f09u) == 32767 &&
        midi_gain(0x7f248f08u) == 32767);

    midi_gain(0x7f249f09u);
    for (unsigned i = 0; i < 500 && (duck_att || duck_hold); i++) duck_block(CTL);
    int32_t gain = duck_g1, env = duck_env;
    turn(EN_K3, -20);
    duck_block(CTL);
    bad += check("AMT changes the next block during release without restarting",
        song.g[G_DUCK] == 38 && duck_g1 > gain && duck_env > 0 && duck_env < env && !duck_att && !duck_hold);

    project_capture(&before);
    before.lfo2_mask = 1;
    bad += check("MIDI source, channel, envelope and LFO2 survive project save and import",
        proj_pack(&packed, &before) && proj_import(&after, &packed, sizeof packed) &&
        after.g[G_DSRC] == DUCK_MIDI && after.g[G_DCH] == 16 && after.g[G_DNOTE] == 36 &&
        after.g[G_DATK] == 12 && after.g[G_DREL] == 47 && after.g[G_DUCK] == 38 && after.lfo2_mask == 1);

    song.g[G_DSRC] = DUCK_USB;
    song.g[G_DTHR] = 70;
    reset_duck(); uin_on = 1; uin_l[0] = 16000;
    duck_block(CTL);
    int quiet = duck_g1 == 32767;
    uin_l[0] = 20000;
    duck_block(CTL);
    bad += check("USB audio obeys THR", quiet && duck_g1 < 32767);
    uin_on = 0;

    song.g[G_DSRC] = 1;
    song.g[G_DTHR] = 1;
    track_t *source = &trk[0];
    trk_all_off(source);
    set_engine_of(source, ENGI_ANALOG);
    apply_preset_to(source, 0);
    source->engine = source->eng_req;
    source->xf_on = 0;
    source->p[P_LEVEL] = 100;
    source->p[P_MUTE] = 0;
    reset_duck();
    source->peak = 32767; /* The UI's old meter value must not retrigger DUCK. */
    int32_t samples[2 * CTL];
    for (unsigned i = 0; i < 4; i++) mix_block(samples, CTL);
    quiet = duck_g1 == 32767;
    trk_note_on(source, 48, 112);
    for (unsigned i = 0; i < 128 && duck_g1 == 32767; i++) mix_block(samples, CTL);
    bad += check("T1 audio triggers DUCK without using the UI peak meter", quiet && duck_g1 < 32767);

    song.g[G_DSRC] = DUCK_AUTO;
    song.g[G_DTHR] = 0;
    bad += check("AUTO recognizes KW KICK, Hortator kick models, and LXR kicks across the bank",
        auto_hit(ENGI_KW_KICK, 0) && auto_hit(ENGI_KW_KICK, 6) && auto_hit(ENGI_HORT, 3) &&
        auto_hit(ENGI_HORT, 46) && auto_hit(ENGI_LXR, 0) && auto_hit(ENGI_LXR, 588));
    bad += check("AUTO ignores synth bass, snare, tom, hats and a shared-kernel FX preset",
        !auto_hit(ENGI_FMINI, 0) && !auto_hit(ENGI_HORT, 4) && !auto_hit(ENGI_HORT, 44) &&
        !auto_hit(ENGI_LXR, 589) && !auto_hit(ENGI_LXR, 591) && !auto_hit(ENGI_LXR, 594));
    unsigned lxr_kicks = 0;
    int link_matches = 1;
    trk_live = NTRK;
    mo_lvl = MO_KICK_LINK;
    usb.config = 1;
    for (unsigned id = 0; id < LXR_COUNT; id++) {
        mo_r = mo_w;
        uint32_t start = mo_w;
        int kick = track_hit(&trk[id % NTRK], ENGI_LXR, id);
        lxr_kicks += kick;
        link_matches &= kick
            ? mo_w - start == 2u && midi_out_q[start % MQ] == KICK_LINK_START &&
              midi_out_q[(start + 1u) % MQ] == (KICK_LINK_END | (100u << 16))
            : mo_w == start;
    }
    mo_lvl = MO_OFF;
    bad += check("All six tracks share the LXR AUTO classification with MIDI Kick Link", link_matches);
    bad += check("LXR AUTO follows individual presets across slots and excludes noisy D1 voices",
        lxr_kicks == 82 && !auto_hit(ENGI_LXR, 56) && !auto_hit(ENGI_LXR, 336) &&
        auto_hit(ENGI_LXR, 134) && auto_hit(ENGI_LXR, 100) &&
        !auto_hit(ENGI_LXR, 79) && !auto_hit(ENGI_LXR, 86));
    song.g[G_DTHR] = 101;
    bad += check("AUTO threshold applies to kick velocity", !auto_hit(ENGI_KW_KICK, 0));
    return !!bad;
}

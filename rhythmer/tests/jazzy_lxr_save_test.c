/* SPDX-License-Identifier: GPL-3.0-only */
#define UI_TEST_NO_MAIN 1
#include "jazzy_host.h"

static void tap(unsigned label)
{
    uint32_t bit = 1u << panel.btn[label];
    fm1_in.buttons |= bit;
    host_pressed |= bit;
    fm1_ms += 16u; ui_input();
    fm1_in.buttons &= ~bit;
    fm1_ms += 16u; ui_input();
}

static void turn(unsigned control, int direction)
{
    host_enc[panel.enc[control]] = direction * panel.dir[control];
    fm1_ms += 16u;
    ui_input();
}

static void hit(track_t *t, unsigned i, unsigned note)
{
    t->step[i].time = ST_NOTE;
    t->step[i].n = 1;
    t->step[i].note[0] = (uint8_t)note;
    t->step[i].vel = 100;
}

static int test_edit_presets(void)
{
    int bad = 0;
    song.sel = 0;
    set_engine_of(TSEL, ENGI_ANALOG);
    list_put(0);
    hit(TSEL, 0, 51);
    unsigned notes = steps_sig(TSEL);
    nav_mem_put(nav_key(SEC_EDIT), 0);
    go_home();
    tap(B_EDIT);
    turn(EN_SELECT, 2);
    bad += check("EDIT > SOUND > PRESETS via the panel", nav_sec() == SEC_EDIT &&
                 nav_ch(SEC_EDIT)->e[nav_cur()].g == 0 && cur_page()->graph == GR_BROWSE);

    unsigned total, k, cur = preset_pos(&total);
    bad += check("EDIT lists only the selected engine", cur == 0 && total == preset_shown(ENGI_ANALOG));
    turn(EN_K1, -1);
    bad += check("K1 wraps within the engine", trk_eng(TSEL) == ENGI_ANALOG && preset_active(TSEL) == total - 1u);
    turn(EN_PRESET, 1);
    bad += check("PRESETS encoder also wraps within EDIT", trk_eng(TSEL) == ENGI_ANALOG && preset_active(TSEL) == 0);
    turn(EN_K1, 1);
    bad += check("EDIT PRESETS K1 loads the next sound", trk_eng(TSEL) == ENGI_ANALOG && preset_active(TSEL) == 1);
    bad += check("Save an Analog sound", up_store(1, "ANALOG TEST") == 3);
    turn(EN_K2, 1);
    cur = preset_pos(&total);
    bad += check("EDIT PRESETS K2 switches engine and stays in SOUND",
                 trk_eng(TSEL) == ENGI_FM6 && cur == 0 && total == preset_shown(ENGI_FM6) && nav_sec() == SEC_EDIT &&
                 nav_ch(SEC_EDIT)->e[nav_cur()].g == 0 && cur_page()->graph == GR_BROWSE);
    bad += check("Save an FM6 sound", up_store(2, "FM6 TEST") == 3);
    preset_pos(&total);
    unsigned e = preset_at(total - 1u, &k);
    bad += check("Only this engine's saved sound is appended",
                 total == preset_shown(ENGI_FM6) + 1u && e == NENGINES && k == 2u);
    turn(EN_K4, 1);
    preset_pos(&total);
    bad += check("FAV with no stars returns no matches", list_get() == 1u && total == 0);
    turn(EN_K3, 1);
    cur = preset_pos(&total);
    bad += check("EDIT PRESETS K3 stars the sound and K4 filters favorites",
                 preset_favorite() && cur == 0 && total == 1u && preset_at(0, &k) == ENGI_FM6 && k == 0);
    turn(EN_K3, -1);
    turn(EN_K4, 1);
    turn(EN_K1, 1);
    bad += check("EDIT PRESETS K3 clears the star and K4 filters BASS",
                 !favorite_has(ENGI_FM6, 0) && list_get() == PT_BASS + 1u &&
                 preset_in(trk_eng(TSEL), preset_active(TSEL)));
    bad += check("EDIT sound browsing keeps the sequence", steps_sig(TSEL) == notes);

    unsigned first, first_e = preset_all_at(0, &first);
    midi_pc_req[song.sel] = 1;
    midi_pc_poll();
    bad += check("MIDI Program Change still uses the full catalog from EDIT",
                 trk_eng(TSEL) == first_e && preset_active(TSEL) == first && steps_sig(TSEL) == notes);
    set_engine_of(TSEL, ENGI_ANALOG);
    apply_preset(preset_shown(ENGI_ANALOG) - 1u);
    go_home();
    cur = preset_all_pos(&total);
    e = preset_all_at(cur + 1u, &k);
    turn(EN_PRESET, 1);
    bad += check("HOME ignores the type filter and crosses the engine boundary",
                 !list_get() && e != ENGI_ANALOG && trk_eng(TSEL) == e && preset_active(TSEL) == k);
    nav_put(SEC_EDIT, "PRESETS");
    bad += check("EDIT retains the BASS filter on return", list_get() == PT_BASS + 1u);
    nav_put(SEC_EDIT, "EDIT 1");
    set_engine_of(TSEL, ENGI_ANALOG);
    apply_preset(preset_shown(ENGI_ANALOG) - 1u);
    turn(EN_PRESET, 1);
    bad += check("EDIT outside PRESETS ignores BASS and crosses the engine boundary",
                 !list_get() && trk_eng(TSEL) == e && preset_active(TSEL) == k);
    nav_put(SEC_EDIT, "PRESETS");
    bad += check("EDIT PRESETS restores the saved BASS filter", list_get() == PT_BASS + 1u);

    set_engine_of(TSEL, ENGI_FM6);
    list_put(0);
    cv_begin(240, 146, T_BG);
    six_graph_surface(TSEL, cur_page());
    bad += check("Selected preset spans the list width", cv_px[20 + 2 * 240] != cv_px[20]);
    nav_go(SEC_SAVE, 6, 0);
    preset_pos(&total);
    bad += check("SAVE SOUND PRESETS keeps the whole catalog",
                 cur_page()->fam == FAM_SAVE && total > LXR_COUNT && preset_at(0, &k) == first_e);

    set_engine_of(TSEL, ENGI_EMPTY);
    nav_put(SEC_EDIT, "PRESETS");
    turn(EN_K2, 1);
    bad += check("An empty track can pick an engine from EDIT PRESETS",
                 trk_eng(TSEL) == ENGI_LXR && cur_page()->graph == GR_BROWSE);
    turn(EN_K1, -1);
    bad += check("LXR wraps to its own saved sound", user_of(TSEL) == 0 && preset_active(TSEL) == LXR_COUNT - 1u);
    turn(EN_K1, -1);
    cur = preset_pos(&total);
    bad += check("LXR retains all 595 sounds and the full preset index", cur == LXR_COUNT - 1u &&
                 total == LXR_COUNT + 1u && user_of(TSEL) == UP_SLOTS && preset_active(TSEL) == LXR_COUNT - 1u);
    list_put(PT_DRUM + 1u);
    cur = preset_pos(&total);
    bad += check("DRUM lists all factory LXR voices", total == LXR_COUNT && cur == LXR_COUNT - 1u);
    turn(EN_PRESET, 1);
    bad += check("Last LXR factory voice wraps to the first", trk_eng(TSEL) == ENGI_LXR && preset_active(TSEL) == 0);
    list_put(0);
    song.playing = 1;
    ui_message("ENGINE LXR");
    ui.force = 1;
    draw_graph();
    unsigned rows = host_blit_rows;
    ui.force = 0;
    fm1_ms += 220u;
    ui.frame += 12;
    draw_graph();
    bad += check("Playback alone does not redraw the preset list", host_blit_rows == rows);
    ui.msg_t = 0;
    fm1_ms += 220u;
    draw_graph();
    bad += check("The preset list clears expired messages", host_blit_rows > rows);
    song.playing = 0;
    return bad;
}

static int test_section_buttons(void)
{
    static const uint8_t buttons[SEC_N] = {B_HOME, B_EDIT, B_SEQ, B_FX, B_GLO, B_ENV, B_LFO, B_SCL, B_ARP, B_SAVE};
    int bad = 0;
    unsigned cycles = 0, loads[] = {LOAD_ECO, LOAD_LITE, LOAD_FULL};
    song.sel = 0;
    int owner = six_break_track();
    if (owner > 0) set_engine_of(&trk[owner], ENGI_ANALOG);
    for (unsigned i = 0; i <= NENG_SHOWN; i++) {
        /* BYTE also exposes RETRIG in place of LOFI's normal MORPH page. */
        unsigned engine = i == NENG_SHOWN ? ENGI_LOFI : ENGINE_ORDER[i];
        set_engine_of(TSEL, engine);
        if (i == NENG_SHOWN) TSEL->p[P_E1] = RW_BYTE;
        for (unsigned l = 0; l < NELEM(loads); l++) {
            sys_load = loads[l];
            for (unsigned sec = 0; sec < SEC_N; sec++) {
                uint8_t visible[NAV_PAGE_MAX];
                unsigned n = nav_list(sec, visible), start = 0;
                nav_go(SEC_HOME, 0, 0);
                if (sec != SEC_HOME) {
                    tap(buttons[sec]);
                    while (start < n && visible[start] != nav_cur()) start++;
                }
                int ok = start < n && nav_sec() == sec;
                for (unsigned j = 1; ok && j <= n; j++) {
                    tap(buttons[sec]);
                    unsigned want = visible[(start + j) % n];
                    ok = nav_sec() == sec && nav_cur() == want &&
                         (sec == SEC_HOME || cur_page() == &PAGES[nv_page(sec, want)]);
                }
                if (!ok) {
                    printf("button cycle: %s / %s / load %u\n", SEC_NAME[sec], ENGINES[engine]->name, sys_load);
                    bad++;
                }
                cycles++;
            }
            for (unsigned p = 0; p < NPAGES; p++) {
                if (!page_visible(p) || PAGES[p].graph == GR_PATS || PAGES[p].graph == GR_CHANCE) continue;
                unsigned sec = sec_of_fam(PAGES[p].fam), j = 0;
                const ch_t *chain_pages = nav_ch(sec);
                while (j < chain_pages->n && nv_page(sec, j) != p) j++;
                if (j == chain_pages->n) {
                    printf("page missing from chain: %s / %s / load %u\n", PAGES[p].title, ENGINES[engine]->name, sys_load);
                    bad++;
                }
            }
        }
    }
    printf("physical section button cycles checked: %u\n", cycles);
    bad += check("Every visible section page is reachable by button", !bad);

    nav_go(SEC_HOME, 3, 0);
    chain.armed = 1;
    tap(B_HOME);
    bad += check("HOME wraps when song playback blocks GEN", nav_cur() == 0 && !gen_on());
    chain.armed = 0;
    nav_go(SEC_HOME, 4, 0);
    tap(B_EDIT);
    chain.armed = 1;
    tap(B_HOME);
    bad += check("HOME re-enters safely when remembered GEN is blocked", nav_sec() == SEC_HOME && nav_cur() == 0);
    chain.armed = 0;
    return bad;
}

int main(void)
{
    ui_power_on(); fm6_init(); power_on_parts(); song_index_load();
    song.playing = 0; transport_req = 0;
    int bad = 0;
    nav_go(SEC_SAVE, nav_mem(SEC_SAVE), 1);
    bad += check("SAVE opens PROJECTS with LOAD selected", nav_cur() == 1 && save_level() == SV_LIB && ui.act == 3);
    bad += check("SAVE navigation groups order", !strcmp(CG_SAVE[0].nm, "SONG") &&
                 !strcmp(CG_SAVE[1].nm, "PROJECT") && !strcmp(CG_SAVE[2].nm, "SOUND"));

    for (unsigned s = 0; s < 4; s++) {
        hit(&trk[1], 0, 60 + s);
        section_store(s);
    }
    project_store_t originals[4];
    memcpy(originals, proj_slot, sizeof originals);
    chain_config.count = 5;
    unsigned rows[] = {0,1,2,1,3};
    for (unsigned i = 0; i < 5; i++) {
        chain_config.row[i].slot = (uint8_t)rows[i];
        chain_config.row[i].bars = 1;
        song_idx.scene[0][i].on = 1;
    }
    song_idx.rows[1].count = 1;
    chain_config_t other = song_idx.rows[1];
    live.cur = 1;
    nav_go(SEC_SAVE, 3, 0);
    bad += check("CLEAR opens disarmed", cur_page()->graph == GR_LIBCLEAR && ui.act == 0);
    edit_param(0, 1);
    bad += check("K1 selects the project", song_cur == 1);
    edit_param(0, -1);
    /* The no-flash host's project switch reloads empty flash; restore the
     * four fake slots to continue testing the stored erase flow. */
    memcpy(proj_slot, originals, sizeof originals);
    live.cur = 1;
    song.g[G_SLOT] = 1;
    edit_param(1, 1); edit_param(2, 1);
    tap(B_OCTUP);
    bad += check("K2/K3 plus OCT+ reviews B without erasing it",
                 ui.confirm == CF_ERASE_SECTION && ui.confirm_trk == 1 && project_used(1));
    char a[24], b[24];
    confirm_text(a,b);
    bad += check("confirmation identifies section B", strstr(a, "SECTION B") && strstr(b, "NO UNDO"));
    tap(B_OCTDN);
    bad += check("cancel preserves each stored section", !memcmp(originals, proj_slot, sizeof originals));
    edit_param(2, 1); tap(B_OCTUP); tap(B_OCTUP);
    bad += check("second OCT+ clears section B only", project_used(0) && !project_used(1) && project_used(2) && project_used(3));
    bad += check("other section payloads are byte-identical",
                 !memcmp(&originals[0], &proj_slot[0], sizeof originals[0]) &&
                 !memcmp(&originals[2], &proj_slot[2], 2 * sizeof originals[0]));
    bad += check("song retains rows for A, C and D", chain_config.count == 3 && chain_config.row[0].slot == 0 &&
                 chain_config.row[1].slot == 2 && chain_config.row[2].slot == 3);
    bad += check("erasing the loaded section clears the audition", live.cur < 0 && seq_is_empty(&trk[1]));
    bad += check("other project arrangement preserved", !memcmp(&other, &song_idx.rows[1], sizeof other));
    song.playing = 1;
    edit_param(3, 1); tap(B_OCTUP);
    bad += check("transport blocks clear", !ui.confirm && project_used(0));
    song.playing = 0;
    edit_param(3, 1); tap(B_OCTUP);
    bad += check("K4 reviews whole project", ui.confirm == CF_ERASE_PROJECT && project_used(0));
    tap(B_OCTUP);
    bad += check("whole project clear empties A-D and song order", !project_used(0) && !project_used(1) &&
                 !project_used(2) && !project_used(3) && !chain_config.count);
 
    song.sel = 0;
    set_engine_of(&trk[0], ENGI_LXR); apply_preset_to(&trk[0], 6);
    set_engine_of(&trk[1], ENGI_HORT); hit(&trk[1], 3, 60);
    track_t *t = &trk[0];
    t->p[P_SLEN] = 16;
    step_t other_steps[NSTEP];
    memcpy(other_steps, trk[1].step, sizeof other_steps);
    nav_go(SEC_SEQ, 14, 0);
    bad += check("SEQ GEN is available on LXR and remembers hat role", drumgen_page() && dg_current(TSEL)->lane == 2);
    for (unsigned i = 0; i < DG_COUNT; i++) {
        dg_current(TSEL)->type = (uint8_t)i;
        dg_current(TSEL)->density = 110;
        dg_current(TSEL)->variation = i == DG_CELLULAR ? 30 : 0;
        if (i == DG_MUTATE) hit(t, 1, 60);
        tap(B_OCTUP);
        unsigned n = 0, multi = 0;
        for (unsigned s = 0; s < 16; s++) {
            n += t->step[s].time == ST_NOTE;
            multi += t->step[s].n > 1;
        }
        bad += check(DG_NAMES[i], n && !multi && !memcmp(other_steps, trk[1].step, sizeof other_steps));
    }
    tap(B_OCTDN);
    bad += check("generator undo and patch stay on the one drum sound", t->eng_req == ENGI_LXR && t->p[P_E0] == 6);
    bad += check("LXR patch and generated notes save", project_save(0) == 0);
    unsigned saved = steps_sig(t);
    set_engine_of(t, ENGI_ANALOG); project_load(0);
    bad += check("LXR patch and pattern reload", t->eng_req == ENGI_LXR && t->p[P_E0] == 6 && steps_sig(t) == saved);
    unsigned last = LXR_COUNT - 1u;
    apply_preset_to(t, last);
    bad += check("last LXR preset is in the normal browser", preset_active(t) == last &&
                 !strcmp(factory_preset(&ENG_LXR, last)->name, "KRAFTWOK OH"));
    bad += check("high preset saves without a new project format", project_save(0) == 0);
    set_engine_of(t, ENGI_ANALOG); project_load(0);
    bad += check("high LXR sound survives reloading", preset_active(t) == last);
    bad += check("high LXR user sound saves", up_store(0,"LXR HAT") == 3);
    set_engine_of(t, ENGI_ANALOG); up_load(0);
    bad += check("high LXR voice survives as a user sound", preset_active(t) == last);
    persist_t settings_copy = {0};
    favorite_set(ENGI_LXR, last, 1);
    settings_export(&settings_copy);
    memset(lxr_stars, 0, sizeof lxr_stars);
    bad += check("extended favorite round-trip", settings_import(&settings_copy, sizeof settings_copy) &&
                 favorite_has(ENGI_LXR, last));
    bad += check("older settings keep legacy stars without inventing extended ones",
                 settings_import(&settings_copy, PERSIST_V4_BASE) && !favorite_has(ENGI_LXR, last));
    set_engine_of(t, ENGI_ANALOG);
    bad += check("drum generator is hidden on a synth", !nv_ok(SEC_SEQ, 14));
    bad += test_edit_presets();
    bad += test_section_buttons();
    printf("LXR, drum generator, SAVE and EDIT PRESETS failures=%d\n", bad);
    return bad != 0;
}

/* SPDX-License-Identifier: GPL-3.0-only */
/* Offline website auditions using the JAZZY mixer, factory voices and native FX. */
#define UI_TEST_NO_MAIN 1
#include "jazzy_host.h"

typedef struct {
    unsigned start, length, velocity;
    uint8_t notes[4];
} phrase_note_t;

static const phrase_note_t bass[] = {
    {0, 2, 112, {36}}, {3, 1, 91, {36}}, {6, 1, 105, {43}}, {8, 2, 108, {34}},
    {11, 1, 95, {46}}, {13, 1, 103, {43}}, {15, 1, 89, {35}}, {16, 3, 114, {36}},
    {20, 1, 104, {48}}, {22, 1, 98, {43}}, {24, 2, 110, {39}}, {27, 1, 93, {41}},
    {29, 1, 101, {43}}, {31, 1, 92, {35}},
};
static const phrase_note_t clavi[] = {
    {0, 2, 99, {53, 57, 60, 64}}, {3, 1, 88, {57, 60, 64}}, {6, 2, 104, {55, 59, 62, 65}},
    {9, 1, 87, {59, 62, 65}}, {12, 2, 98, {55, 59, 65, 69}}, {15, 1, 80, {71}},
    {16, 2, 103, {52, 55, 59, 62}}, {19, 1, 90, {55, 59, 62}}, {22, 1, 95, {59, 62, 67}},
    {24, 2, 104, {55, 61, 65, 69}}, {27, 1, 91, {61, 65, 69}}, {30, 2, 100, {53, 57, 60, 64}},
};
static const phrase_note_t pad[] = {
    {0, 8, 101, {48, 55, 60, 63}}, {8, 8, 100, {44, 55, 60, 67}},
    {16, 8, 104, {51, 58, 62, 67}}, {24, 8, 97, {46, 53, 60, 65}},
};

typedef struct { unsigned step, track, velocity; } drum_hit_t;
static const drum_hit_t drums[] = {
    {0,0,118},{0,5,73},{0,2,72},{2,2,93},{3,0,103},{3,2,63},{4,1,110},{4,2,79},
    {6,2,94},{7,0,110},{8,0,114},{8,2,74},{10,3,84},{11,2,62},{12,1,117},
    {12,2,85},{13,4,79},{14,0,104},{14,2,98},{15,1,57},
    {16,0,120},{16,2,78},{18,2,93},{19,0,102},{19,2,63},{20,1,112},{20,2,78},
    {21,5,72},
    {22,3,86},{23,0,108},{24,0,112},{24,2,75},{25,1,56},{26,2,93},{27,4,90},
    {28,1,118},{28,2,79},{29,4,99},{30,0,111},{30,3,85},{31,1,80},{31,4,108},
};

typedef struct {
    const char *slug;
    unsigned engine, program, bpm, level, delay, reverb, phaser;
    const phrase_note_t *phrase;
    unsigned notes;
} audition_t;

static const audition_t auditions[] = {
    {"fmini", ENGI_FMINI, 137, 116, 104, 0, 0, 0, bass, NELEM(bass)},
    {"cz", ENGI_CZ, 10, 116, 99, 16, 24, 0, clavi, NELEM(clavi)},
    {"hydra", ENGI_HYDRA, 3, 100, 83, 26, 37, 15, pad, NELEM(pad)},
    {"lxr", ENGI_LXR, 0, 116, 0, 0, 0, 0, NULL, 0},
};

static void track_sound(unsigned i, unsigned engine, unsigned patch, int level, int pan, int reverb)
{
    track_t *t = &trk[i];
    set_engine_of(t, engine);
    apply_preset_to(t, patch);
    t->engine = t->eng_req;
    t->p[P_LEVEL] = level;
    t->p[P_PAN] = pan;
    t->p[P_MUTE] = 0;
    t->p[P_AMODE] = 0;
    t->p[P_DIST] = 0;
    t->p[P_CHOR] = 0;
    t->p[P_DLY] = 0;
    t->p[P_REV] = reverb;
}

static void rhythm_step(unsigned step, int note_on)
{
    for (unsigned i = 0; i < NELEM(drums); i++) {
        const drum_hit_t *hit = &drums[i];
        if (hit->step != step) continue;
        if (note_on) trk_note_on(&trk[hit->track], 60, hit->velocity);
        else trk_note_off(&trk[hit->track], 60);
    }
}

static void phrase_step(const audition_t *a, unsigned step)
{
    for (unsigned i = 0; i < a->notes; i++) {
        const phrase_note_t *n = &a->phrase[i];
        if (step != n->start + n->length) continue;
        for (unsigned j = 0; j < 4 && n->notes[j]; j++)
            trk_note_off(&trk[0], n->notes[j]);
    }
    for (unsigned i = 0; i < a->notes; i++) {
        const phrase_note_t *n = &a->phrase[i];
        if (step != n->start) continue;
        for (unsigned j = 0; j < 4 && n->notes[j]; j++)
            trk_note_on(&trk[0], n->notes[j], n->velocity - j * 4u);
    }
}

int main(int argc, char **argv)
{
    if (argc != 3) return 2;
    const audition_t *a = NULL;
    for (unsigned i = 0; i < NELEM(auditions); i++)
        if (!strcmp(auditions[i].slug, argv[1])) a = &auditions[i];
    if (!a) return 2;

    ui_power_on();
    fm6_init();
    power_on_parts();
    six_native_init();
    song.master_q12 = 4096;
    song.g[G_BPM] = a->bpm;
    song.g[G_RSIZE] = 77;
    song.g[G_DFDBK] = 48;
    song.g[G_DTIME] = 6;
    song.g[G_DPING] = 1;
    int is_drums = a->engine == ENGI_LXR;

    if (is_drums) {
        enum { METROID = 3, NUYORK = 20, WARMTUBE = 21, ZUBAT = 43 };
        static const unsigned kits[] = {WARMTUBE, NUYORK, METROID, METROID, NUYORK, ZUBAT};
        static const unsigned roles[] = {0, 3, 5, 6, 1, 4};
        static const int level[] = {105, 116, 50, 56, 64, 82};
        static const int pan[] = {0, 0, -18, 21, -12, 28};
        trks_put(1);
        for (unsigned i = 0; i < NELEM(kits); i++) {
            track_sound(i, ENGI_LXR, kits[i] * 7u + roles[i], level[i], pan[i], i ? 15 : 0);
            printf("%s\n", lxr_factory(preset_active(&trk[i]))->name);
        }
        trk[0].p[P_E2] = 28; /* Shorten the kick's factory tail to leave room for the next hit. */
        trk[0].p[P_E3] = 43;
        trk[0].p[P_E5] = 49;
        trk[1].p[P_E1] = 6;
        trk[1].p[P_E3] = 86;
        trk[1].p[P_E5] = 79;
        trk[4].p[P_E2] = 49;
        fx_stems = 1;
    } else {
        for (unsigned i = 1; i < NTRK; i++) trk[i].p[P_MUTE] = 1;
        track_sound(0, a->engine, a->program, a->level, 0, a->reverb);
        trk[0].p[P_DLY] = a->delay;
        trk[0].p[P_CHOR] = a->phaser;
        printf("%s\n", factory_preset(ENGINES[a->engine], a->program)->name);
    }

    FILE *out = fopen(argv[2], "wb");
    if (!out) return 3;
    const unsigned pulse = (FS * 15u + a->bpm * CTL / 2u) / (a->bpm * CTL);
    const unsigned swing = a->engine == ENGI_HYDRA ? 0 : pulse / 10u;
    int32_t pcm[2 * CTL];
    uint64_t energy[NTRK] = {0};
    for (unsigned step = 0; step < 40; step++) {
        if (is_drums) rhythm_step(step, 1);
        else phrase_step(a, step);
        unsigned blocks = (step & 1u) ? pulse - swing : pulse + swing;
        for (unsigned block = 0; block < blocks; block++) {
            if (is_drums && block == 3u) rhythm_step(step, 0);
            mix_block(pcm, CTL);
            if (is_drums)
                for (unsigned i = 0; i < NTRK; i++)
                    for (unsigned j = 0; j < CTL; j++) {
                        int64_t sample = stem_buf[i][j];
                        energy[i] += sample * sample;
                    }
            if (fwrite(pcm, sizeof pcm, 1, out) != 1) return 4;
        }
    }
    if (fclose(out)) return 5;
    if (is_drums)
        for (unsigned i = 0; i < NTRK; i++) {
            printf("LXR track %u energy %llu\n", i + 1, (unsigned long long)energy[i]);
            if (!energy[i]) return 6;
        }
    return 0;
}

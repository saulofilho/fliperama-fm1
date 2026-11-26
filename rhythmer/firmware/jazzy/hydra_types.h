/* SPDX-License-Identifier: MPL-2.0
 * Copyright (C) 2026 Kerem Kilic (Ellic Studio)
 * Portions Copyright (C) 2026 john (@johnskiller)
 * Portions Copyright (C) 2026 Leo Kuroshita (@kurogedelic), Hügelton Instruments */
/* HYDRA: a wave-scanning synth after the ASM Hydrasynth (engine 25; it grew from Melodee's WT engine).
 *
 * A voice: OSC 1 and OSC 2 play one wave (SINGLE) or scan a list of eight (SCAN crossfades neighbouring slots, an
 * EMPTY slot is silence), each through two MUTANTs in series (FM-LIN, STACK, SYNC, PW, SQUEEZE, WARP, HARMONIC, each
 * with its dry/wet); OSC 3 plays one wave. RING (two oscillators multiplied) and NOISE (white, pink, brown) join them
 * in the MIXER, where each source has a level and a share sent to FILTER 2 instead of FILTER 1 (ladders, MS-20, LPG,
 * three-pole, vowel). FILTER 2 is a state variable morphing through band or notch, after FILTER 1 (SERIES) or beside
 * it (PARALLEL). ENV 1 (delay, attack, hold, decay, sustain, release) moves both filters. The track's ADSR is the
 * amplitude; its LFO, ENV DEST and MOD slots modulate as for any engine (SHP moves the scans of OSC 1 and 2).
 *
 * The patch: HY_BYTES native bytes a part (hy_patch[]; hydra_patch.h lays them out, hydra_edit.h describes them to the pages).
 * Its eight macros, after the Hydrasynth's: the patch names them and routes each to destinations of its own with depths
 * (hy_macros); E0..E7 are their values, -64..63 (0: the sound as stored), which the knobs, CC 74/71 and the matrix's
 * E1..E8 move. The part state holds the voices and a RAM copy of the waves the patch uses (XIP reads stall the audio
 * loop); the block hook refreshes both when the patch or a macro changes. A voice is costed with every macro wherever
 * it costs most (hy_worst), so no turn of a macro can make the block late.
 */
typedef struct {
    uint8_t mode, src, sh;
    float wet, fm, fb, win, hfr, det;
    uint32_t ratio, knee, k1, k2, h;                   /* SYNC Q16 / WARP sections; PW knee and slopes (Q16) */
    int32_t sq;                                        /* SQUEEZE: the stretch (Q16) */
} hy_mut_t;
typedef struct {                                       /* the patch, made ready (per part, at a change) */
    hy_mut_t mut[4];
    float lvl[HYS_N], bal[HYS_N], amp;
    float f1cut, f1res, f1drive, f1env, f1key, f1vel, f2cut, f2res, f2morph, f2env, f2key;
    float e1atk[1], e1sus, e1dec, e1rel, e1sc[2], e1mu;
    int32_t scan[2], semi16[3], cent[3], key[3];
    uint8_t m1[HM_N];                                  /* MUTANT 1 as the macros leave it (ENV 1 moves it a voice) */
    uint16_t e1dly, e1hld;                             /* control ticks */
    uint8_t scanning[2], on[3], src_used[HYS_N], stack[2], ring_a, ring_b, noise, route, f1type, f1post, f2notch;
    uint8_t row0[2], row3;                             /* OSC 1's and OSC 2's first wave copy, OSC 3's */
    uint8_t fallback;                                  /* the arena had no room for the patch's scans: first waves */
    uint8_t mix[HYS_N], nmix, bus2, noise_on;          /* the sources heard (their order), FILTER 2's bus fed alone */
    uint8_t f2open;                                    /* FILTER 2 wide open, unmoved: passed by (no filter) */
} hy_base_t;
typedef struct {
    uint32_t sp[2][4];                                 /* STACK: the four detuned copies of OSC 1 and 2 */
    uint32_t ph[3];                                    /* OSC 1, 2, 3 */
    float z[6], f2[2];                                 /* FILTER 1 (ladder stages, SVF, VOWEL's three), FILTER 2 */
    float dodd[2][16], deven[2][8];                    /* the two buses' half-band decimators (2x voices) */
    float out[HYS_N];                                  /* the sources' last samples (FM, ring, feedback) */
    float pink[3], brown, e1, dc;                      /* (dc: this voice's capacitor, so a voice that ends takes its own) */
    int32_t noise;
    uint16_t e1wait;
    uint8_t e1stage, os, dp;                           /* os: oversampled; dp: the decimators' ring position */
    uint8_t thin;                                      /* a tail hy_tails_fit fades: its last 23 ms without mutants */
    hy_mut_t mu1;                                      /* MUTANT 1 moved by ENV 1 (CPU0 writes it, then the kernel) */
} hy_voice_t;

/* SPDX-License-Identifier: GPL-3.0-only
 * Copyright (C) 2026 Leo Kuroshita (@kurogedelic), Hügelton Instruments */
#define FELUCCA_FAVORITES 1
/* Stable engine/preset references; fixed capacity independent of optional engines. */
typedef struct {
    uint8_t factory[16][32]; /* engine 0..15, preset 0..255 */
    uint32_t user, filter;
} favorites_t;
static favorites_t favorites;
/* Preserve the original 48 LXR slots; new IDs get their own settings tail. */
#define LXR_LEGACY_STARS 48u
static uint8_t lxr_stars[(LXR_COUNT - LXR_LEGACY_STARS + 7u) / 8u];
/* Stable capacities, independent of curated quota. Legacy first 128 stars stay put;
 * DIGITAL/MIDI learn (row 1), crash (13), settings (15) remain entirely reserved. */
static uint8_t *jazzy_favorite_byte(uint32_t engine,uint32_t preset){
 static const uint16_t base[21]={0,1,33,41,57,65,73,81,89,97,105,113,121,129,137,145,153,161,193,201,203};
 static const uint16_t cap[21]={8,256,64,128,64,64,64,64,64,64,64,64,64,64,64,64,64,256,64,16,48};
 static const uint8_t rows[]={0,2,3,4,5,6,7,8,9,11,12};
 if(engine<ENGI_MELO_TRIO||engine>ENGI_LXR||preset>=ENGINES[engine]->npresets)return 0;
 if(engine==ENGI_LXR&&preset>=LXR_LEGACY_STARS)return &lxr_stars[(preset-LXR_LEGACY_STARS)/8u];
 unsigned i=engine-ENGI_MELO_TRIO;if(preset>=cap[i])return 0;
 unsigned off=base[i]+preset/8u;
 if(off<64u)return &favorites.factory[off<32u?10:14][off&31u];
 off-=64u;return &favorites.factory[rows[off/16u]][16u+(off&15u)];
}
/* Preserve Acid/Break favorites; new engines use retired rows. */
static uint32_t favorite_row(uint32_t e) { return e == ENGI_EMPTY ? 14u : e == ENGI_ACID ? 3u : e == ENGI_BREAK ? 4u : e == ENGI_SERUM ? 5u : e == ENGI_LOFI ? 6u : e == ENGI_M2STAT ? 8u : e == ENGI_M2SAW ? 9u : e == ENGI_M2SID ? 11u : e; }
static int favorite_has(uint32_t engine, uint32_t preset)
{
    if(engine>=ENGI_MELO_TRIO&&engine<=ENGI_LXR){uint8_t *b=jazzy_favorite_byte(engine,preset);return b&&((*b>>(preset&7u))&1u);}
    if(engine==ENGI_EMPTY)return 0;
    if (engine == NENGINES)
        return preset < UP_SLOTS && ((favorites.user >> preset) & 1u);
    return engine < NENGINES && favorite_row(engine) < 16u && preset < ENGINES[engine]->npresets && preset < 128u &&
        ((favorites.factory[favorite_row(engine)][preset / 8u] >> (preset % 8u)) & 1u);
}
static int favorite_set(uint32_t engine, uint32_t preset, int on)
{
    if(engine>=ENGI_MELO_TRIO&&engine<=ENGI_LXR){uint8_t *b=jazzy_favorite_byte(engine,preset);if(!b||favorite_has(engine,preset)==!!on)return 0;if(on)*b|=(uint8_t)(1u<<(preset&7u));else *b&=(uint8_t)~(1u<<(preset&7u));return 1;}
    if(engine==ENGI_EMPTY)return 0;
    if (engine > NENGINES || (engine == NENGINES ? preset >= UP_SLOTS : favorite_row(engine) >= 16u || preset >= ENGINES[engine]->npresets || preset >= 128u))
        return 0;
    if (favorite_has(engine, preset) == !!on) return 0;
    if (engine == NENGINES) {
        if (on) favorites.user |= 1u << preset;
        else favorites.user &= ~(1u << preset);
    } else {
        uint8_t *b = &favorites.factory[favorite_row(engine)][preset / 8u];
        if (on) *b |= (uint8_t)(1u << (preset % 8u));
        else *b &= (uint8_t)~(1u << (preset % 8u));
    }
    return 1;
}

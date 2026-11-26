/* GPL-3.0-only. Mutually exclusive per-track DSP storage. */
#include "../jazzy/mel_fastmath.h"
#include "../jazzy/mel_prophet.h"
#include "../jazzy/jo_dsp.h"
#include "../jazzy/s1_dsp.h"
#include "../jazzy/hydra_patch.h"
#include "../jazzy/hydra_types.h"
#include "../jazzy/jc_dsp.h"
#include "../jazzy/fm106_osc.h"
#include "../jazzy/fm106_vcf.h"
#include "../jazzy/kwasub.h"
typedef struct {jo_osc_t osc[3];jo_svf_state_t filter[2];js_pink_noise_t pink;uint32_t rng;int32_t noise_lp;} js_voice_t;
typedef union {
 js_voice_t s1;
 struct {jo_osc_t osc[2];jo_svf_state_t f[2];} ob;
 struct {uint32_t ph[2];int32_t h[2][2],l[2][2];} cs;
 struct {fm106_dco_t osc;fm106_vcf_t f;fm106_hpf_t hp;} juno;
 jk_osc_t kw;
} jazzy_voice_t;
typedef struct {hy_base_t b;int16_t key_e[8];uint8_t tag[17],key,valid;} hy_part_t;
typedef union {jazzy_voice_t model[4];p5_voice_t prophet[3];hy_voice_t hydra;} jazzy_voices_t;
/* A track runs one model: native FM6 and all imported model state share storage. */
static union {fm6_note_t fm6[4];struct {jazzy_voices_t voice;hy_part_t part;} jazzy;} jazzy_host_state[NTRK];
static uint8_t jazzy_state_owner[NTRK];
static void jazzy_prepare(track_t *t){unsigned i=(unsigned)(t-trk);if(jazzy_state_owner[i]!=t->engine+1u){memset(&jazzy_host_state[i],0,sizeof jazzy_host_state[i]);jazzy_state_owner[i]=(uint8_t)(t->engine+1u);}}
_Static_assert(sizeof(jazzy_voices_t)<=400,"native states fit original model voice budget");

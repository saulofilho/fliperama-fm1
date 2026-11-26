/* GPL-3.0-only. Hortator individual-hit adapter; no JIANT kit. */
#include "md_states.h"
typedef struct {md_state_t ms;uint32_t t;int32_t rng,last;uint8_t active,vel,kind;} md_voice_t;
typedef struct {int16_t p[8];int8_t nt;} md_track_t;
static md_voice_t hort_hit[NTRK];
static uint32_t pow2_q16(int32_t d16) {
 uint32_t u=(uint32_t)(d16+192*16),oct=u/192u;
 uint32_t r=pitch_inc(1600+u%192u)/(pitch_inc(1600)>>16);
 return oct>=16u?r<<(oct-16u):r>>(16u-oct);
}
static uint32_t inc_tune(uint32_t inc,int32_t semis) {return (uint32_t)(((uint64_t)inc*pow2_q16(clamp(semis,-48,48)*16))>>16);}
static int32_t dm_tune(const md_track_t *t) {return t->p[0]+clamp(t->nt,-24,24);}
static int32_t vel_gain(const md_voice_t *v) {return v->vel*258;}
static void dm_end(md_voice_t *v) {v->active=0;v->last=0;}
/* Q24 filter coefficient helpers: Hortator / Mutable Instruments (MIT).
 * Only called on a new cymbal strike, never per sample. */
#define QONE (1<<24)
#define Q24(x) ((int32_t)((x)*16777216.0+((x)<0?-0.5:0.5)))
static inline int32_t qm(int32_t a,int32_t b) {return (int32_t)(((int64_t)a*b+(1<<23))>>24);}
static inline int32_t qtan_acc(int32_t f)
{
    int32_t x = qm(f, Q24(3.14159265358979)), x2 = qm(x, x), p;
    p = Q24(9.5168091e-03);
    p = Q24(2.900525e-03) + qm(p, x2);
    p = Q24(5.33740603e-02) + qm(p, x2);
    p = Q24(1.333923995e-01) + qm(p, x2);
    p = Q24(3.333314036e-01) + qm(p, x2);
    return qm(x, QONE + qm(p, x2));
}

#define ENV1 (1<<24)
#define ENV_END (1<<10)
static inline uint32_t md_decay_k(int32_t i){return DECAY_K[clamp(i,0,127)];}
static inline int32_t env_q15(int32_t e){return e>>9;}
static inline int32_t dnoise(md_voice_t *v){return (int32_t)noise32(&v->rng)>>16;}
static inline void env_step(md_voice_t *v,uint32_t i){v->ms.kt.env[i]=mulq16(v->ms.kt.env[i],v->ms.kt.k[i]);}
static void dsvf_coef(dsvf_t *c, int32_t cut, int32_t reso)       /* cut 0..127 << 8, reso 0..127 */
{
    tsvf_t t;
    tsvf_coef(&t, cut, reso);
    c->a1 = t.a1;
    c->a2 = t.a2;
    c->a3 = t.a3;
    c->k = 8192 - reso * 7600 / 127;          /* damping, Q12, as tsvf_coef */
}

static inline int32_t dsvf_tick(const dsvf_t *c, int32_t in, int32_t *ic1, int32_t *ic2, int32_t *bp, int32_t *hp)
{
    int32_t v3 = in - *ic2;
    int32_t v1 = (c->a1 * *ic1 + c->a2 * v3) >> 13;
    int32_t v2 = *ic2 + ((c->a2 * *ic1 + c->a3 * v3) >> 13);
    *ic1 = clamp(2 * v1 - *ic1, -150000, 150000);
    *ic2 = clamp(2 * v2 - *ic2, -150000, 150000);
    *bp = v1;
    *hp = in - ((c->k * v1) >> 12) - v2;
    return v2;
}


static inline void dm_put(md_voice_t *v,int32_t *out,uint32_t i,int32_t x){x=mulq15(mulq15(x,vel_gain(v)),VOICE_FS);out[i]+=x;v->last=x;}
#define HZ(f) ((uint32_t)((f)*97391.548))
#define LIFE_A ((uint32_t)FS*11u/2u)
#define dk md_decay_k
#define track_t md_track_t
#define dvoice_t md_voice_t
#define P_E0 0
#include "md_ktrx_kernels.h"
#include "md_sdtrx_kernels.h"
#include "md_xttrx_kernels.h"
#include "md_trxn_kernels.h"
#include "md_rstrx_kernels.h"
#include "md_trxm_kernels.h"
#include "md_trxcb_kernels.h"
#include "md_cltrx_kernels.h"
#include "md_b2trx_kernels.h"
#include "md_bdefm_kernels.h"
#include "md_efmn_kernels.h"
#include "md_efmm_kernels.h"
#undef dk
#undef P_E0
#undef dvoice_t
#undef track_t
#undef LIFE_A
#undef HZ
#include "md_models.h"


static void hort_reset(void){memset(hort_hit,0,sizeof hort_hit);}
static void hort_on(track_t *t,voice_t *v){
 md_voice_t *h=&hort_hit[t-trk];memset(h,0,sizeof *h);h->active=1;h->vel=v->vel;h->rng=0x2545f491u+(unsigned)(t-trk)*977u+v->age;
 unsigned kind=(unsigned)t->p[P_E0]%MD_NMODEL;h->kind=kind;
 const md_model_t *model=&MD_MODELS[kind];md_track_t ctx;memcpy(ctx.p,model->def,sizeof ctx.p);ctx.nt=0;
 ctx.p[0]=clamp(t->p[P_E1],-24,24);ctx.p[1]=t->p[P_E2];
 for(unsigned k=0;k<3;k++)ctx.p[model->ctl[k]]=t->p[P_E3+k];
 /* Use the selected SOUND, including on edited/user presets. NOISEZA shares
  * the BDEFM kernel but is an FX voice, so it does not trigger AUTO. */
 static const uint32_t kicks[]={
  (1u<<3)|(1u<<15)|(1u<<16)|(1u<<29), /* BDTRX, B2TRX, BDEFM, SUBDIRT */
  (1u<<(42-32))|(1u<<(43-32))|(1u<<(45-32))|(1u<<(46-32)) /* ZAPKICK, TICKKIC, FMBOOM, RISEKIC */
 };
 if((kicks[kind>>5]>>(kind&31u))&1u)kick_link_strike(t,v);
 model->trigger(&ctx,h);
}
static void hort_render(track_t *t,voice_t *v,int32_t *out,uint32_t n,const vmod_t *m){
 (void)v;md_voice_t *h=&hort_hit[t-trk];int32_t tmp[CTL]={0};if(n>CTL)n=CTL;
 if(h->active)MD_MODELS[h->kind].render(0,h,tmp,n);
 for(unsigned i=0;i<n;i++)out[i]+=mulq15(tmp[i],amp_at(m,i));
}
static int hort_done(track_t *t,voice_t *v){(void)v;return !hort_hit[t-trk].active;}
static const preset_t HORT_PRESETS[]={
{.name="HHEFM",.e={0,-2,52,3,12,26,0,0}},
{.name="CBEFM",.e={1,-2,61,17,112,56,0,0}},
{.name="CYEFM",.e={2,-2,93,76,88,22,0,0}},
{.name="BDTRX",.e={3,-4,68,35,14,14,0,0}},
{.name="SDTRX",.e={4,0,7,127,0,0,0,0}},
{.name="TMTRX",.e={5,0,48,48,64,0,0,0}},
{.name="CGTRX",.e={6,11,15,30,105,127,0,0}},
{.name="CPTRX",.e={7,10,127,56,7,43,0,0}},
{.name="RSTRX",.e={8,-4,0,0,0,0,0,0}},
{.name="CBTRX",.e={9,0,48,127,127,0,0,0}},
{.name="CHTRX",.e={10,0,8,0,0,127,0,0}},
{.name="OHTRX",.e={11,0,61,57,8,127,0,0}},
{.name="CYTRX",.e={12,0,35,127,93,107,0,0}},
{.name="SHTRX",.e={13,0,64,0,0,0,0,0}},
{.name="CLTRX",.e={14,0,64,0,64,0,0,0}},
{.name="B2TRX",.e={15,-1,74,33,22,7,0,0}},
{.name="BDEFM",.e={16,-13,68,29,5,10,0,0}},
{.name="SDEFM",.e={17,-9,60,0,5,14,0,0}},
{.name="TMEFM",.e={18,12,85,64,4,62,0,0}},
{.name="CPEFM",.e={19,24,45,75,36,91,0,0}},
{.name="RSEFM",.e={20,1,10,8,15,38,0,0}},
{.name="METALHA",.e={21,0,71,112,0,127,0,0}},
{.name="TINHAT",.e={22,0,0,0,0,127,0,0}},
{.name="TRASHHA",.e={23,3,69,99,81,94,0,0}},
{.name="TREMHAT",.e={24,-14,76,76,48,24,0,0}},
{.name="SPITHAT",.e={25,-8,20,85,29,106,0,0}},
{.name="WIDECLA",.e={26,15,106,0,22,77,0,0}},
{.name="PINGBEL",.e={27,0,0,127,0,126,0,0}},
{.name="LONGRID",.e={28,0,106,127,64,64,0,0}},
{.name="SUBDIRT",.e={29,-24,64,32,0,0,0,0}},
{.name="LOWCHIM",.e={30,-15,77,0,0,57,0,0}},
{.name="DARKOPE",.e={31,0,86,120,0,84,0,0}},
{.name="POPSNAR",.e={32,0,12,127,29,36,0,0}},
{.name="FUZZTOM",.e={33,-12,27,42,98,98,0,0}},
{.name="SHORTTO",.e={34,1,24,48,0,0,0,0}},
{.name="BUZZLOW",.e={35,-12,30,0,98,127,0,0}},
{.name="GRITRIM",.e={36,-1,0,50,0,0,0,0}},
{.name="LONGBEL",.e={37,0,79,13,21,127,0,0}},
{.name="THINHAT",.e={38,0,0,23,127,127,0,0}},
{.name="SIZZLE",.e={39,0,20,0,112,127,0,0}},
{.name="HALFOPE",.e={40,0,29,0,29,127,0,0}},
{.name="THINCRS",.e={41,0,0,0,100,35,0,0}},
{.name="ZAPKICK",.e={42,13,64,127,0,0,0,0}},
{.name="TICKKIC",.e={43,-3,49,12,55,92,0,0}},
{.name="NOISEZA",.e={44,24,49,0,0,35,0,0}},
{.name="FMBOOM",.e={45,-9,80,95,35,117,0,0}},
{.name="RISEKIC",.e={46,4,54,37,32,0,0,0}},
{.name="DROPTOM",.e={47,1,31,5,4,127,0,0}},
{.name="RISETOM",.e={48,7,73,8,4,0,0,0}},
{.name="GRITTOM",.e={49,-12,70,76,16,12,0,0}},
{.name="FMZAP",.e={50,-13,14,127,127,0,0,0}},
{.name="DEEPBLI",.e={51,-24,64,12,33,0,0,0}},
{.name="RATTLE",.e={52,-8,0,115,127,127,0,0}},
{.name="RIMSNAR",.e={53,3,23,0,4,100,0,0}},
{.name="GONG",.e={54,-11,92,126,24,0,0,0}},
{.name="FMSPLAS",.e={55,0,25,127,127,64,0,0}},
{.name="SIZZRID",.e={56,5,81,8,40,126,0,0}},
};
static const engine_t ENG_HORT={.name="HORTATOR",.page_title={"SINGLE HIT","TIMBRE"},
.edit={{"SOUND",F_INT,0,MD_NMODEL-1,3,0,0},{"TUNE",F_SEMI,-24,24,0,0,0},{"DECAY",F_INT,0,127,64,0,0},{"COLOR",F_INT,0,127,64,0,0},{"BODY",F_INT,0,127,64,0,0},{"EDGE",F_INT,0,127,64,0,0},{"-",F_INT,0,0,0,0,0},{"-",F_INT,0,0,0,0,0}},
.presets=HORT_PRESETS,.npresets=sizeof HORT_PRESETS/sizeof HORT_PRESETS[0],.poly=1,.oneshot=1,.ownenv=1,.note_on=hort_on,.render=hort_render,.done=hort_done,.knob={P_E1,P_E2,P_E3,P_E4}};

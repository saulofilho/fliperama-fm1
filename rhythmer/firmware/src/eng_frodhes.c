/* GPL-3.0-only. Frodhes native physical tine / magnetic pickup voice.
 * Common host envelope/modulation and FX. No duplicate 256-frame mixer or FX. */
#include "../jazzy/frodhes.h"
static jf_rh_voice_t jazzy_tine[NTRK][3];
static jf_rh_voice_t *tine_of(track_t *t,voice_t *v){return &jazzy_tine[t-trk][(unsigned)(v-t->v)%3u];}
static void tine_on(track_t *t,voice_t *v){
 jf_rh_type=(uint8_t)clamp(t->p[P_E0],0,3);
 jf_rh_bark_s=32768+t->p[P_E1]*512;jf_rh_bark_g=(int32_t)(0x100000000ull/(unsigned)jf_rh_bark_s);
 jf_rh_bell=32768+t->p[P_E2]*512;jf_rh_k_decay=32768+(127-t->p[P_E3])*768;jf_rh_k_rel=32768+(127-t->p[P_E4])*768;
 jf_rh_voice_t *r=tine_of(t,v);memset(r,0,sizeof *r);jf_rh_init(r,v->note,v->vel);
}
static int tine_done(track_t *t,voice_t *v){return !tine_of(t,v)->alive;}
static void tine_render(track_t *t,voice_t *v,int32_t *out,uint32_t n,const vmod_t *m){
 jf_rh_voice_t *r=tine_of(t,v);int32_t y[CTL]={0},side[CTL]={0};if(n>CTL)n=CTL;
 if(!v->gate&&r->held){r->held=0;jf_rh_set_damper(r,32768);}
 if(r->alive)jf_rh_voice_sub(r,y,side);
 for(unsigned i=0;i<n;i++)out[i]+=mulq15(clamp(y[i]/16,-32767,32767),amp_at(m,i));
}
static const preset_t TINE_PRE[]={
 {"STAGE 77",{0,64,64,72,45,0,0,0},{0,64,127,0},0,TAG(KEYS)},
 {"SUITCASE",{1,64,64,72,45,0,0,0},{0,64,127,0},0,TAG(KEYS)},
 {"FELT",{2,45,45,60,35,0,0,0},{0,64,127,0},0,TAG(KEYS)},
 {"DYNO",{3,80,90,80,55,0,0,0},{0,64,127,0},0,TAG(KEYS)}
};
#define TP(n,d) {n,F_INT,0,127,d,0,0}
static const engine_t ENG_FRODHES={.name="FRODHES",.page_title={"TINE / PICKUP","DAMPER"},.edit={{"TYPE",F_INT,0,3,0,0,0},TP("BARK",64),TP("BELL",64),TP("DECAY",72),TP("RELEASE",45),TP("-",0),TP("-",0),TP("-",0)},.presets=TINE_PRE,.npresets=4,.knob={P_E0,P_E1,P_E2,P_E3},.poly=3,.ownenv=1,.note_on=tine_on,.render=tine_render,.done=tine_done};
#undef TP

/* SPDX-License-Identifier: GPL-3.0-only
 * JAZZY host adapters. DSP provenance: firmware/jazzy/UPSTREAM.json.
 * All models use the host scheduler, per-track modulation, envelopes and FX.
 * No upstream firmware scheduler, audio interrupt, sequencer or FX buffers. */
#include "../jazzy/factory_meta.h"
#include "../jazzy/melodee_trio.c"
#include "../jazzy/fmini.c"
static jazzy_voice_t *jazzy_state(track_t *t,voice_t *v){return &jazzy_host_state[t-trk].jazzy.voice.model[(unsigned)(v-t->v)%4u];}
static void jazzy_on(track_t *t,voice_t *v){
 jazzy_prepare(t);jazzy_voice_t *s=jazzy_state(t,v);memset(s,0,sizeof *s);
 if(t->engine==ENGI_S1)s->s1.rng=0x2f6e2b1u+(unsigned)(t-trk)*177u+(unsigned)(v-t->v)*71u;
 if(t->engine==ENGI_JUNO){fm106_dco_init(&s->juno.osc,(unsigned)(t-trk)*4u+(unsigned)(v-t->v));fm106_vcf_init(&s->juno.f);fm106_hpf_init(&s->juno.hp);}
 if(t->engine==ENGI_KW_KICK){s->kw.f[1]=0x7fffffffu;s->kw.f[2]=32767;kick_link_strike(t,v);}
}
static void jazzy_render(track_t *t,voice_t *v,int32_t *out,uint32_t n,const vmod_t *m){
 jazzy_voice_t *s=jazzy_state(t,v);const int16_t *p=t->p+P_E0;
 if(n>CTL)n=CTL;
 int32_t cut=clamp(p[0]*256+m->cutoff,0,127*256),res=clamp(p[1],0,120),tmp[CTL];
 if(t->engine>=ENGI_KW_FIRST&&t->engine<=ENGI_KW_LAST){
  static const uint8_t ids[]={jk_E_ANALOG,jk_E_CS,jk_E_WAVE,jk_E_FM,jk_E_PHASE,jk_E_SYNC,jk_E_KICK,jk_E_GROWL,jk_E_ADD};
  jk_oscp_t q={0};q.eng=ids[t->engine-ENGI_KW_FIRST];q.inc=m->inc;
  q.p1=clamp(p[2]*258+m->shape-16384,0,32767);q.p2=p[3]*258;q.p3=p[4]*258;q.p4=p[5]*258;
  jk_osc_render(&s->kw,&q,tmp,0,n);
  tsvf_t f;tsvf_coef(&f,cut,res);
  for(unsigned i=0;i<n;i++){int32_t y=tsvf_lp(&f,tmp[i]/2,&v->s[0],&v->s[1]);out[i]+=voice_amp(y,m,i);}
 }else if(t->engine==ENGI_OBER){
  jo_svf_coef_t f;jo_svf_coef(&f,25*256+cut*100/127,8192-res*7600/127);
  uint32_t inc2=cents_inc(clamp(m->pitch16+p[7]*16,0,2047),p[3],m->fine);
  uint32_t pw=0x10000000u+(uint32_t)clamp(p[4]+(m->shape-16384)/258,0,127)*0x1a00000u;
  for(unsigned i=0;i<n;i++){
   int32_t a=jo_osc_step(&s->ob.osc[0],m->inc,(m->inc>>15)|1u,pw,p[2]<43?jo_OSC_SAW:p[2]<86?(jo_OSC_SAW|jo_OSC_PLS):jo_OSC_PLS,0,-1);
   int32_t b=jo_osc_step(&s->ob.osc[1],inc2,(inc2>>15)|1u,0x80000000u,jo_OSC_SAW,0,-1),lp,bp,hp;
   jo_svf_step(&f,&s->ob.f[0],(a+b)/6,&lp,&bp,&hp);
   int32_t y=p[5]<43?lp:p[5]<86?bp:hp;
   if(p[6]>63)y=jo_svf_lp(&f,&s->ob.f[1],y);
   out[i]+=voice_amp(y,m,i);
  }
 }else if(t->engine==ENGI_CS){
  jc_svf_t lo,hi;jc_svf_coef(&lo,clamp(cut/16+256,0,2047),jc_SVF_K(res));jc_svf_coef(&hi,clamp(p[5]*16,0,2047),jc_SVF_K(16));
  for(unsigned i=0;i<n;i++){
   int32_t sum=0;
   for(unsigned c=0;c<2;c++){
    uint32_t inc=c?cents_inc(m->pitch16,p[3],m->fine):m->inc;
    uint32_t ph=s->cs.ph[c];s->cs.ph[c]+=inc;
    int32_t x=(jc_osc_saw(ph,inc)*(127-p[2])+jc_osc_pulse(ph,inc,0x10000000u+(uint32_t)clamp(p[4]+(m->shape-16384)/258,0,127)*0x1a00000u)*p[2])/127;
    int32_t lp,hp;jc_svf_step(&hi,x/2,&s->cs.h[c][0],&s->cs.h[c][1],&lp,&hp);
    jc_svf_step(&lo,hp,&s->cs.l[c][0],&s->cs.l[c][1],&lp,&hp);sum+=lp;
   }
   if(p[6]){int32_t ring=sine_i(v->ph[2]);v->ph[2]+=pitch_inc(p[7]*16);sum=mulq15(sum,32767-p[6]*258+mulq15(ring,p[6]*258));}
   out[i]+=voice_amp(sum/2,m,i);
  }
 }else if(t->engine==ENGI_JUNO){
  s->juno.osc.saw_on=p[2]>=32&&p[2]<96;s->juno.osc.pulse_on=p[2]>=64;s->juno.osc.sub_on=p[3]>0;s->juno.osc.sub_level=p[3];s->juno.osc.noise_level=p[5];
  uint16_t dac=fm106_calc_vcf_freq(cut/2,0,0,(p[6]<0?-p[6]:p[6])*4,128,0,0,p[6]>=0,v->env_out/2,m->pitch16*16);
  s->juno.hp.mode=(uint8_t)clamp(p[7],0,3);
  float inv=1.0f/(float)(m->inc?m->inc:1);
  for(unsigned i=0;i<n;i++){
   int32_t x=fm106_dco_process_fast(&s->juno.osc,m->inc,m->inc,inv,clamp(p[4]+(m->shape-16384)/258,0,127),1,0,v->env_out);
   out[i]+=voice_amp(fm106_hpf_process(&s->juno.hp,fm106_vcf_process(&s->juno.f,x,dac,(uint8_t)res)),m,i);
  }
 }
}
#define JP(n,d) {n,F_INT,0,127,d,0,0}
#define JR(n,l,h,d) {n,F_INT,l,h,d,0,0}
#define JMODEL(symbol,title,fid,num,...) static const engine_t symbol={.name=title,.page_title={"FILTER / OSC","VOICE"},.edit={__VA_ARGS__},.factory_id=fid,.npresets=num,.knob={P_E0,P_E1,P_E2,P_E3},.poly=4,.note_on=jazzy_on,.render=jazzy_render}
JMODEL(ENG_OBER,"OBERVAVE",FP_ID_24,FP_COUNT_24,JP("CUTOFF",80),JP("RESO",20),JP("SAW/PULSE",48),JR("FINE B",-64,63,6),JP("WIDTH",64),JP("LP/BP/HP",0),JP("4-POLE",0),JR("SEMI B",-24,24,0));
JMODEL(ENG_CS,"CS-1",FP_ID_26,FP_COUNT_26,JP("LOWPASS",80),JP("RESO",20),JP("SAW/PULSE",48),JP("DETUNE",12),JP("WIDTH",64),JP("HIGHPASS",0),JP("RING",0),JP("RING NOTE",48));
JMODEL(ENG_JUNO,"FM-106",FP_ID_25,FP_COUNT_25,JP("CUTOFF",80),JP("RESO",20),JP("SAW/PULSE",48),JP("SUB",60),JP("WIDTH",64),JP("NOISE",0),JR("FILTER EG",-64,63,20),JR("HPF",0,3,1));
static const preset_t KW_DERIVED[]={{"INIT",{90,20,48,32,32,0,0,0},{0,65,100,40},0,TAG(LEAD)}};
#define KENGINE(symbol,title,fid,num,a,b,c,d) static const engine_t symbol={.name=title,.page_title={"FILTER / COLOR","TIMBRE"},.edit={JP("CUTOFF",90),JP("RESO",20),JP(a,48),JR(b,0,(fid==FP_ID_29?0:127),(fid==FP_ID_29?0:32)),JP(c,32),JP(d,0),JR("-",0,0,0),JR("-",0,0,0)},.factory_id=fid,.presets=KW_DERIVED,.npresets=num,.knob={P_E0,P_E2,P_E3,P_E4},.poly=2,.note_on=jazzy_on,.render=jazzy_render}
KENGINE(ENG_KW_ANALOG,"KW ANALOG",FP_ID_27,FP_COUNT_27,"WAVE","WIDTH","DRIVE","FOLD");KENGINE(ENG_KW_CS,"KW CS",FP_ID_28,FP_COUNT_28,"WAVE","DETUNE","MOTION","RING");KENGINE(ENG_KW_WAVE,"KW WAVE",FP_ID_29,FP_COUNT_29,"SCAN","-","WARP","FOLD");KENGINE(ENG_KW_FM,"KW FM",FP_ID_30,FP_COUNT_30,"INDEX","RATIO","FEEDBACK","ALGO");KENGINE(ENG_KW_PHASE,"KW PHASE",0,1,"AMOUNT","TYPE","BODY","FOLD");KENGINE(ENG_KW_SYNC,"KW SYNC",0,1,"SYNC","WAVE","SOFT","FOLD");KENGINE(ENG_KW_KICK,"KW KICK",FP_ID_33,FP_COUNT_33,"PUNCH","DROP","DRIVE","CLICK");KENGINE(ENG_KW_GROWL,"KW GROWL",FP_ID_34,FP_COUNT_34,"GROWL","VOWEL","BITE","TYPE");KENGINE(ENG_KW_ADD,"KW ADD",FP_ID_35,FP_COUNT_35,"TILT","HARMONICS","ODD/EVEN","REGISTER");
static const param_desc_t FMINI_LAST={"PATCH",F_INT,0,71,0,0,0};
static const param_desc_t *fmini_desc(const track_t *t,uint32_t k){return k==7u&&t->p[P_E6]?&FMINI_LAST:0;}
static void jazzy_bound(track_t *t){if(t->eng_req==ENGI_FMINI)t->p[P_E7]=(int16_t)clamp(t->p[P_E7],0,t->p[P_E6]?71:127);}
static const engine_t ENG_FMINI={.name="FMINI-1",.page_title={"LADDER","CONTOUR"},.edit={JP("CUTOFF",64),JP("EMPH",40),JP("CONTOUR",64),JP("F.ATK",0),JP("F.DEC",64),JP("F.SUS",40),{"BANK",F_INT,0,1,0,0,0},{"PATCH",F_INT,0,127,0,0,0}},.factory_id=1,.npresets=200,.desc=fmini_desc,.knob={P_E0,P_E1,P_E2,P_E4},.poly=3,.keep=0x13,.note_on=fmini_note_on,.render=fmini_render,.block=fmini_block};
#undef JP
#undef JMODEL
#undef JR
#undef KENGINE

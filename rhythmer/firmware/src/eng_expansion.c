/* SPDX-License-Identifier: GPL-3.0-only
 * JAZZY S1Vave adapter. Native DSP Copyright (C) 2026 Andrew GG.
 * Original host glue: common envelope/LFO/FX, no imported sequencer or kit state. */
#include "../jazzy/s1_curve.h"
#if JAZZY_EXTERNAL_ASSETS
#define JS_CFG (jazzy_asset_at(JA_JS_CFG))
#define JS_WAVE (jazzy_asset_at(JA_JS_WAVE))
#define JS_DRAW ((const int16_t*)jazzy_asset_at(JA_JS_DRAW))
#define JS_CHOP ((const uint16_t*)jazzy_asset_at(JA_JS_CHOP))
#else
#include "../jazzy/s1_factory.h"
#endif
static void js_render(track_t *t,voice_t *v,int32_t *out,uint32_t n,const vmod_t *m){
 if(!jazzy_assets_valid)return;
 const int16_t *p=t->p+P_E0;unsigned program=(unsigned)clamp(t->p[P_LN0],0,63);
 const uint8_t *q=JS_CFG+program*9u;js_voice_t *s=&jazzy_state(t,v)->s1;
 const int16_t *draw=JS_DRAW+JS_WAVE[program*2u]*16u;const uint16_t *chop=JS_CHOP+JS_WAVE[program*2u+1]*4u;
 int32_t fa=q[8],cv=clamp(p[0],0,127);if(cv<32)fa=fa*(75+52*cv/32)/127;if(fa>80)fa=80+(fa-80)*6/8;
 int32_t cut=JS_CUTOFF[cv]+m->cutoff+(int32_t)(((int64_t)m->envq15*fa*244)>>15)+(m->pitch16/16-60)*q[7]*256/127;
 jo_svf_coef_t f1,f2;jo_svf_coef(&f1,cut,clamp(8192-p[1]*8400/127,0,8192));jo_svf_coef(&f2,cut,8192);
 int32_t depth=clamp(p[5]+(m->shape-16384)/258,0,127);uint32_t pw=0x80000000u-(uint32_t)depth*0x00e80000u;
 if(q[4]==0)pw=0x80000000u-(uint32_t)(((int64_t)m->envq15*depth)*464);
 int32_t level[4]={clamp(q[0]+p[2],0,127),clamp(q[1]-p[2],0,127),clamp(p[3],0,127)*7/4,clamp(p[4],0,127)*6};
 int32_t gain=js_chop_calc_masked_gain((unsigned)clamp(p[7],0,100)*2u);
 uint32_t sub=q[2]==2?m->inc>>1:m->inc>>2;
 if(n>CTL)n=CTL;
 for(unsigned i=0;i<n;i++){
  int32_t x[4];
  if(q[5]){s->osc[0].ph+=m->inc;x[0]=js_osc_draw_sample(draw,s->osc[0].ph,(unsigned)(clamp(p[6],0,31)+1)*256u,q[5]);}
  else x[0]=jo_osc_step(&s->osc[0],m->inc,m->inc>>15,pw,jo_OSC_PLS,-65536,-1);
  x[1]=jo_osc_step(&s->osc[1],m->inc,m->inc>>15,0,jo_OSC_SAW,-65536,-1);
  x[2]=jo_osc_step(&s->osc[2],sub,sub>>15,q[2]?0x80000000u:0x40000000u,jo_OSC_PLS,-65536,-1);
  int32_t w=(int32_t)(jo_xorshift(&s->rng)>>16)-32768;
  if(q[3])x[3]=js_pink_noise_step(&s->pink,w);else{s->noise_lp+=(w-s->noise_lp)>>1;x[3]=s->noise_lp*180>>8;}
  int32_t sum=0;for(unsigned k=0;k<4;k++){if(gain!=32767)x[k]=js_osc_chop_sample(x[k],s->osc[k?1:0].ph,chop[k],(q[6]+1u)*256u,gain)*21294>>15;sum+=x[k]*level[k];}
  int32_t lp,bp,hp;jo_svf_step(&f1,&s->filter[0],clamp(sum>>7,-65535,65535),&lp,&bp,&hp);
  out[i]+=voice_amp(js_svf_lp(&f2,&s->filter[1],lp)/4,m,i);
 }
}
#define XP(n,l,h,d) {n,F_INT,l,h,d,0,0}
static const engine_t ENG_S1={.name="S1VAVE",.page_title={"S1 / FILTER","DRAW / CHOP"},.edit={XP("CUTOFF",0,127,70),XP("RESO",0,127,20),XP("PULSE/SAW",-64,63,0),XP("SUB",0,127,60),XP("NOISE",0,127,0),XP("WIDTH",0,127,32),XP("DRAW MULT",0,31,0),XP("CHOP",0,100,0)},.factory_id=FP_ID_40,.npresets=FP_COUNT_40,.poly=4,.note_on=jazzy_on,.render=js_render,.knob={P_E0,P_E1,P_E2,P_E3}};
#undef XP

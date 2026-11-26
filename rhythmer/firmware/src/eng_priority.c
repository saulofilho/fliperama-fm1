/* SPDX-License-Identifier: GPL-3.0-only
 * JAZZY adapters for Melodee DSP by Kerem Kilic (Ellic Studio).
 * CZ waveform core retains Devin Acker BSD-3-Clause notices in mel_cz_wave.h.
 * Eight controls, common envelopes, no second worker/FX/sequencer/patch editor.
 */
#include "../jazzy/mel_cz_wave.h"
static void priority_on(track_t *t,voice_t *v){
 jazzy_prepare(t);
 if(t->engine==ENGI_CZ){memset(v->ph,0,sizeof v->ph);memset(v->s,0,sizeof v->s);return;}
 if(t->engine==ENGI_PROPHET){p5_voice_t *s=&jazzy_host_state[t-trk].jazzy.voice.prophet[(unsigned)(v-t->v)%3u];memset(s,0,sizeof *s);s->noise=0x13579bdu+(unsigned)(t-trk)*177u+(unsigned)(v-t->v)*77u;}
}
static void jcz_render(track_t *t,voice_t *v,int32_t *out,uint32_t n,const vmod_t *m){
 static const uint8_t waves[7]={0,1,2,4,5,6,7};const int16_t *p=t->p+P_E0;cz_hw_pd_t shape[2];
 float dcw=fm_clampf((float)p[2]*8.0f+(float)(m->shape-16384)/32.0f+(float)m->cutoff/32.0f+(float)m->envq15*p[7]/4096.0f,0,1023);
 for(unsigned l=0;l<(p[1]?2u:1u);l++){unsigned w=waves[(unsigned)(l?(p[1]?p[1]-1:0):p[0])%7u];cz_native_pd(&shape[l],(w<<13)|((unsigned)p[6]<<6),dcw);}
 uint32_t inc[2]={m->inc,cents_inc(clamp(m->pitch16+p[3]*16,0,2047),0,m->fine)};
 for(unsigned i=0;i<n;i++){
  int32_t pcm[2]={0,0};for(unsigned l=0;l<(p[1]?2u:1u);l++){
   uint32_t old=v->ph[l];float raw=cz_native_wave(&shape[l],old,(unsigned)v->s[l]);v->ph[l]+=inc[l];if(v->ph[l]<old)v->s[l]^=1;
   int32_t x=(int32_t)(raw*16384.0f),y=x-v->s[l+2]+mulq15(v->s[l+4],32693);v->s[l+2]=x;v->s[l+4]=y;pcm[l]=clamp(y,-32767,32767);
  }
  int32_t b=p[5]?mulq15(pcm[0],pcm[1])*2:pcm[1];int32_t y=p[1]?(pcm[0]*(127-p[4])+b*p[4])/127:pcm[0];out[i]+=voice_amp(y,m,i);
 }
}
static void jp_render(track_t *t,voice_t *v,int32_t *out,uint32_t n,const vmod_t *m){
 const int16_t *p=t->p+P_E0;p5_voice_t *s=&jazzy_host_state[t-trk].jazzy.voice.prophet[(unsigned)(v-t->v)%3u];uint8_t patch[56]={0};
 patch[P5_SAW_A]=p[3]==0||p[3]==3||p[3]==5||p[3]==7;patch[P5_SAW_B]=p[3]==0||p[3]==3;
 patch[P5_PULSE_A]=p[3]==1||p[3]==3||p[3]==6;patch[P5_PULSE_B]=p[3]==1||p[3]==3;patch[P5_TRI_B]=p[3]==2||p[3]==7;
 patch[P5_FILTER_REV]=(uint8_t)p[2];patch[P5_SYNC]=(uint8_t)p[7];patch[P5_POLY_FILTER]=p[6]>0;patch[P5_POLY_PW]=p[6]>0;patch[P5_POLY_FREQ]=p[6]>0;
 static const float zero[CTL]={0};
 float env=(float)m->envq15/32768.0f;
 p5_render_params_t c={0};c.f0=c.f1=env;c.a0=c.a1=1;c.cut=(float)p[0]+(float)m->cutoff/256.0f;c.k=p[1]*(p[2]?19200.0f:18800.0f)/(127.0f*4096.0f);c.filter_gain=1-p[1]*(p[2]?100.0f:45.0f)/32768.0f;
 c.filter_velocity=c.amp_velocity=1;c.env_amount=p[5]*.3f;c.pf_b=p[6]*.35f;c.pa_b=p[6]/512.0f;c.pa_env=p[5]/512.0f;c.pw_b=p[6]/256.0f;c.pwm_a=c.pwm_b=.5f+(m->shape-16384)/65536.0f;c.la=c.lb=.5f;c.ln=p[3]==4?1.0f:0;
 c.ia=m->inc;c.ib=cents_inc(clamp(m->pitch16+p[4]*16,0,2047),6,m->fine);c.wheel=zero;c.wheel_pitch=zero;
 p5_samples(s,patch,out,n,m,&c);
}
#define PC(n,l,h,d) {n,F_INT,l,h,d,0,0}
static const engine_t ENG_JCZ={.name="MELO CZ",.page_title={"PHASE / LINE","WINDOW / ENV"},.edit={PC("WAVE1",0,6,0),PC("WAVE2",0,7,0),PC("DCW",0,127,64),PC("INTERVAL",-24,24,0),PC("MIX",0,127,64),PC("RING",0,1,0),PC("WINDOW",0,5,0),PC("ENV",0,127,40)},.factory_id=FP_ID_38,.npresets=FP_COUNT_38,.poly=3,.note_on=priority_on,.render=jcz_render,.knob={P_E0,P_E1,P_E2,P_E4}};
static const engine_t ENG_JPROPHET={.name="PROPHET",.page_title={"FILTER / OSC","POLY-MOD"},.edit={PC("CUTOFF",0,127,70),PC("RESO",0,127,25),PC("REV",0,1,1),PC("OSC",0,7,0),PC("SEMI B",-48,48,0),PC("ENV",0,127,50),PC("POLYMOD",0,127,0),PC("SYNC",0,1,0)},.factory_id=FP_ID_39,.npresets=FP_COUNT_39,.poly=3,.note_on=priority_on,.render=jp_render,.knob={P_E0,P_E1,P_E5,P_E6}};
#undef PC

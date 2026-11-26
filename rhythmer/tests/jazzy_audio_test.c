#define UI_TEST_NO_MAIN 1
#include "jazzy_host.h"
int main(void){
 ui_power_on();fm6_init();power_on_parts();song.playing=0;unsigned bad=0;
 for(unsigned j=0;j<NENG_SHOWN;j++){
  unsigned e=ENGINE_ORDER[j];if(e==ENGI_EMPTY||e==ENGI_BREAK)continue;
  for(unsigned pi=0;pi<ENGINES[e]->npresets;pi++){
   track_t *t=&trk[0];set_engine_of(t,e);apply_preset_to(t,pi);t->engine=t->eng_req;memset(t->v,0,sizeof t->v);
   const engine_t *en=ENGINES[e];voice_t *v=&t->v[0];v->active=v->gate=1;v->note=60;v->vel=112;v->env_out=32767;v->env=0x7fffffffu;
   if(en->block)en->block(t);if(en->note_on)en->note_on(t,v);
   vmod_t m={0};m.inc=pitch_inc(60*16);m.pitch16=60*16;m.amp0=m.amp1=24576;m.shape=16384;m.envq15=32767;
   long long energy=0;unsigned peak=0;
   for(unsigned b=0;b<180;b++){int32_t out[CTL]={0};if(en->block)en->block(t);en->render(t,v,out,CTL,&m);for(unsigned k=0;k<CTL;k++){unsigned a=out[k]<0?-(int64_t)out[k]:out[k];energy+=a;if(a>peak)peak=a;}}
   if(!energy||peak>1000000){printf("FAIL engine=%u preset=%u %s energy=%lld peak=%u\n",e,pi,factory_preset(en,pi)->name,energy,peak);bad++;}
   if(e==ENGI_FMINI&&t->p[P_E6]*128+t->p[P_E7]!=(int)pi){printf("FAIL patch slot %u = %d\n",pi,t->p[P_E7]);bad++;}
   if(pi==0)printf("AUDIO %u %s peak=%u energy=%lld\n",e,en->name,peak,energy);
  }
 }
 printf("audio failures=%u\n",bad);return bad?1:0;
}

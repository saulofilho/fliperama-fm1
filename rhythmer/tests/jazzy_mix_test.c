#define UI_TEST_NO_MAIN 1
#include "jazzy_host.h"
int main(void){
 ui_power_on();fm6_init();power_on_parts();six_native_init();song.playing=0;transport_req=0;chain.armed=0;song.master_q12=4096;
 const unsigned models[]={ENGI_FMINI,ENGI_JUNO,ENGI_CZ,ENGI_PROPHET,ENGI_OBER,ENGI_CS,ENGI_KW_WAVE,ENGI_KW_FM,ENGI_KW_CS,ENGI_KW_PHASE,ENGI_KW_SYNC,ENGI_KW_GROWL,ENGI_S1,ENGI_HYDRA,ENGI_FM6,ENGI_PROPHET,ENGI_LXR,ENGI_HORT,ENGI_ACID,ENGI_FMINI};
 unsigned bad=0;long long energy[4]={0};int32_t out[CTL*2];
 for(unsigned run=0;run<sizeof models/sizeof models[0]/4;run++){
  for(unsigned k=0;k<4;k++){track_t *t=&trk[k];set_engine_of(t,models[run*4+k]);apply_preset_to(t,ENGINES[t->eng_req]->npresets-1);t->p[P_VOICE]=V_POLY;t->p[P_MUTE]=0;t->p[P_LEVEL]=95;t->p[P_AMODE]=0;t->p[P_DIST]=12;t->p[P_CHOR]=30;t->p[P_DLY]=22;t->p[P_REV]=25;t->p[P_LD_FLT]=12;}
  for(unsigned b=0;b<80;b++)mix_block(out,CTL);
  for(unsigned k=0;k<4;k++){trk_note_on(&trk[k],48+k*3,110);trk_note_on(&trk[k],55+k*3,100);trk_note_on(&trk[k],60+k*3,95);}
  for(unsigned b=0;b<600;b++){
   mix_block(out,CTL);for(unsigned i=0;i<CTL*2;i++){long long a=out[i]<0?-(long long)out[i]:out[i];if(a>4000000){bad++;break;}}
   if(b==300)for(unsigned k=0;k<4;k++){trk_note_off(&trk[k],48+k*3);trk_note_off(&trk[k],55+k*3);trk_note_off(&trk[k],60+k*3);}
   for(unsigned k=0;k<4;k++){int32_t one[CTL]={0};track_render(&trk[k],one,CTL);for(unsigned i=0;i<CTL;i++)energy[k]+=one[i]<0?-(long long)one[i]:one[i];}
  }
  for(unsigned k=0;k<4;k++){if(!energy[k])bad++;printf("mixed voice e=%u energy=%lld\n",trk[k].engine,energy[k]);energy[k]=0;}
 }
 printf("four-track mixed-model/FX/switch failures=%u\n",bad);return !!bad;
}

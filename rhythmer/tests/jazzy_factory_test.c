#define UI_TEST_NO_MAIN 1
#include "jazzy_host.h"
#include "jazzy_factory_expect.h"
static unsigned failures;
#define REQ(s,x) do{if(!(x)){printf("FAIL %s e=%u p=%u\n",s,e,k);failures++;}}while(0)
static unsigned hashbyte(unsigned h,unsigned x){return (h^(x&255u))*16777619u;}
int main(void){
 ui_power_on();fm6_init();power_on_parts();
 uint8_t settings_before[32],crash_before[32],learn_before[32];
 memset(&favorites,0,sizeof favorites);memset(favorites.factory[15],0x53,32);memset(favorites.factory[13],0x26,32);memset(favorites.factory[1],0x37,32);
 memcpy(settings_before,favorites.factory[15],32);memcpy(crash_before,favorites.factory[13],32);memcpy(learn_before,favorites.factory[1],32);
 unsigned checked=0,starred=0;
 for(unsigned j=0;j<NENG_SHOWN;j++){
  unsigned e=ENGINE_ORDER[j],k=0;if(e==ENGI_EMPTY)continue;const engine_t *en=ENGINES[e];
  REQ("legacy stars fit protected prefix",e>=22||en->npresets<=128);
  for(k=0;k<en->npresets;k++){REQ("star starts clear",!favorite_has(e,k));REQ("star set",favorite_set(e,k,1));REQ("star stays set",favorite_has(e,k));starred++;}
 }
 for(unsigned j=0;j<NENG_SHOWN;j++){unsigned e=ENGINE_ORDER[j];if(e==ENGI_EMPTY)continue;for(unsigned k=0;k<ENGINES[e]->npresets;k++){REQ("star survives other engines",favorite_has(e,k));favorite_set(e,k,0);}}
 {unsigned e=0,k=0;REQ("settings preserved",!memcmp(settings_before,favorites.factory[15],32));REQ("crash preserved",!memcmp(crash_before,favorites.factory[13],32));REQ("MIDI learn preserved",!memcmp(learn_before,favorites.factory[1],32));}
 memset(&favorites,0,sizeof favorites);
 for(unsigned q=0;q<NELEM(FP_EXPECT);q++){
  unsigned e=FP_EXPECT[q][0],k=FP_EXPECT[q][1];const engine_t *en=ENGINES[e];track_t *t=&trk[0];set_engine_of(t,e);unsigned sig=steps_sig(t);apply_preset_to(t,k);const preset_t *p=factory_preset(en,k);
  unsigned h=2166136261u;for(unsigned i=0;i<16;i++)h=hashbyte(h,i<strlen(p->name)?p->name[i]:0);
  for(unsigned i=0;i<8;i++){h=hashbyte(h,p->e[i]);REQ("macro loaded within declared range",t->p[P_E0+i]>=en->edit[i].min&&t->p[P_E0+i]<=en->edit[i].max);REQ("macro value applied",t->p[P_E0+i]==p->e[i]);}
  for(unsigned i=0;i<4;i++)h=hashbyte(h,p->env[i]);h=hashbyte(h,p->fenv);h=hashbyte(h,p->mono);for(unsigned i=0;i<4;i++)h=hashbyte(h,p->fx[i]);
  unsigned ids[7]={P_LRATE,P_LWAVE,P_LD_PIT,P_LD_FLT,P_LD_SHP,P_LD_AMP,P_GLIDE};for(unsigned i=0;i<7;i++)h=hashbyte(h,t->p[ids[i]]);
  REQ("decoded preset matches source projection",h==FP_EXPECT[q][2]);REQ("preset keeps pattern",sig==steps_sig(t));checked++;
  // Rotate through >8 cache entries and revisit signed values/program boundaries.
  for(unsigned i=0;i<12;i++)factory_preset(en,(k+i+1)%en->npresets);
  REQ("cache eviction preserves macro",factory_preset(en,k)->e[0]==t->p[P_E0]);
 }
 printf("factory validation: %u projections, %u stars, failures=%u\n",checked,starred,failures);return !!failures;
}

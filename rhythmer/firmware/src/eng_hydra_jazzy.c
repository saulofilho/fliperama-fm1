/* SPDX-License-Identifier: MPL-2.0
 * JAZZY adapter for Saadet HYDRA. Native engine Copyright (C) 2026 Kerem Kilic (Ellic Studio).
 * Extracted native DSP notices remain in hydra_types.h / hydra_core.h.
 * One voice per track; shared immutable native waves; host scheduler / ENV / LFO / FX. */
#if JAZZY_EXTERNAL_ASSETS
#define JH_FACTORY ((const hy_patch_t*)jazzy_asset_at(JA_JH_FACTORY))
#else
#include "../jazzy/hydra_factory.h"
#endif
#include "../jazzy/hydra_waves.h"
static int16_t jh_waves[24][256] __attribute__((section(".pool")));
static const int16_t jh_zero[256]={0};
static void jh_wave_put(unsigned i,uint8_t x){((uint8_t*)jh_waves)[(i%6144u)*2u+i/6144u]=x;}
static uint8_t jh_wave_get(unsigned i){return ((uint8_t*)jh_waves)[(i%6144u)*2u+i/6144u];}
static unsigned jh_pack_get(unsigned i){
#if JAZZY_EXTERNAL_ASSETS
 return *jazzy_asset_at(JA_JH_WAVE_PACK+i);
#else
 return JH_WAVE_PACK[i];
#endif
}
static void jh_init(void){
 if(!jazzy_assets_valid)return;
 unsigned p=0,n=0;
 while(p<sizeof JH_WAVE_PACK){unsigned tok=jh_pack_get(p++),len=tok>>4;if(len==15){unsigned a;do{a=jh_pack_get(p++);len+=a;}while(a==255);}
  while(len--)jh_wave_put(n++,jh_pack_get(p++));if(p==sizeof JH_WAVE_PACK)break;
  unsigned off=jh_pack_get(p)|jh_pack_get(p+1)<<8;p+=2;len=(tok&15)+4;if((tok&15)==15){unsigned a;do{a=jh_pack_get(p++);len+=a;}while(a==255);}
  while(len--){uint8_t x=jh_wave_get(n-off);jh_wave_put(n++,x);}
 }
 for(unsigned w=0;w<24;w++){uint16_t prev=0;for(unsigned i=0;i<256;i++){prev+=(uint16_t)jh_waves[w][i];jh_waves[w][i]=(int16_t)prev;}}
 memset(jazzy_state_owner,0,sizeof jazzy_state_owner);
}
static const hy_patch_t *jh_patch(const track_t *t){return &JH_FACTORY[(unsigned)clamp(t->p[P_LN0],0,15)];}
static hy_part_t *hy_part(unsigned k){return &jazzy_host_state[k%NTRK].jazzy.part;}
static hy_voice_t *jh_voice(const track_t *t){return &jazzy_host_state[t-trk].jazzy.voice.hydra;}
static const int16_t *jh_wave(unsigned k){return k<24?jh_waves[k]:jh_zero;}
static uint8_t jh_wave_index(unsigned id){for(unsigned i=0;i<24;i++)if(JH_WAVE_IDS[i]+1u==id)return (uint8_t)i;return 255;}
static unsigned hy_rows(const uint8_t *r){return (r[HY_O1+HO_MODE]?8u:1u)+(r[HY_O2+HO_MODE]?8u:1u)+1u;}
static void hy_block(track_t *t);
#define HY_COUPLE (2.0f * 3.14159265f * 5.0f / (float)FS)
#include "../jazzy/hydra_core.h"
static void hy_block(track_t *t){
 if(!jazzy_assets_valid)return;
 jazzy_prepare(t);
 hy_part_t *P=hy_part((unsigned)(t-trk));unsigned pi=(unsigned)clamp(t->p[P_LN0],0,15);
 if(P->valid&&P->key==pi&&!memcmp(P->key_e,t->p+P_E0,sizeof P->key_e))return;
 const uint8_t *r=JH_FACTORY[pi].raw;hy_base(P,t,r);unsigned row=0;
 for(unsigned o=0;o<2;o++){const uint8_t *q=r+(o?HY_O2:HY_O1);P->b.row0[o]=(uint8_t)row;
  if(q[HO_MODE])for(unsigned j=0;j<8;j++)P->tag[row++]=jh_wave_index(q[HO_L0+j]);
  else P->tag[row++]=jh_wave_index(q[HO_WAVE]+1u);
 }
 P->b.row3=(uint8_t)row;P->tag[row]=jh_wave_index(r[HY_O3_WAVE]+1u);P->key=(uint8_t)pi;memcpy(P->key_e,t->p+P_E0,sizeof P->key_e);P->valid=1;
}
static void jh_on(track_t *t,voice_t *v){
 if(!jazzy_assets_valid)return;
 hy_block(t);hy_voice_t *s=jh_voice(t);memset(s,0,sizeof *s);
 s->ph[0]=0x9e3779b9u;s->ph[1]=s->ph[0]+0x2aaaaaaau;s->ph[2]=s->ph[0]+0x55555555u;
 for(unsigned j=0;j<4;j++){s->sp[0][j]=s->ph[0]+(j+1u)*0x33333333u;s->sp[1][j]=s->ph[1]+(j+1u)*0x33333333u;}
 s->noise=(int32_t)(0x5a1793u+v->age*17u);const hy_base_t *b=&hy_part((unsigned)(t-trk))->b;
 int top=-(1<<20),low=65*16;for(unsigned j=0;j<3;j++)if(b->on[j]){int q=960+(v->pitch16-960)*b->key[j]/100+b->semi16[j];if(q>top)top=q;}
 for(unsigned j=0;j<4;j++)if(b->mut[j].mode==MU_SYNC||b->mut[j].mode==MU_HARM)low=53*16;
 s->os=top>=low;s->e1stage=b->e1dly?1:2;s->e1wait=b->e1dly;
}
static const param_desc_t *jh_desc(const track_t *t,unsigned k){
 static param_desc_t desc[8];param_desc_t *d=&desc[k&7u];*d=(param_desc_t){"M",F_BIPCT,-64,63,0,0,0};const uint8_t *r=jh_patch(t)->raw;unsigned name=r[HY_MNAME+(k&7u)];
 if(!name)for(unsigned j=0;j<HY_MSLOTS;j++){unsigned a=r[HY_MA+j*2u];if(HY_SLOT_MACRO(a)==k&&HY_SLOT_TGT(a)){d->label=HY_MACRO_NAMES[HN_AUTO];switch(HY_SLOT_TGT(a)){case HT_SCAN1:case HT_SCAN2:name=HN_SCAN;break;case HT_CUT:name=HN_FILTER;break;case HT_RES:name=HN_RES;break;case HT_DRIVE:name=HN_GRIT;break;default:name=HN_MORPH;break;}break;}}
 d->label=HY_MACRO_NAMES[name<HY_NNAME?name:0];return d;
}
#define HM(n) {n,F_BIPCT,-64,63,0,0,0}
static const engine_t ENG_JHYDRA={.name="HYDRA",.page_title={"MACROS 1-4","MACROS 5-8"},.edit={HM("M1"),HM("M2"),HM("M3"),HM("M4"),HM("M5"),HM("M6"),HM("M7"),HM("M8")},.factory_id=FP_ID_41,.npresets=FP_COUNT_41,.desc=jh_desc,.poly=1,.note_on=jh_on,.render=hy_render,.block=hy_block,.knob={P_E0,P_E1,P_E2,P_E3}};
#undef HM

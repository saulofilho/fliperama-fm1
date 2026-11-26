/* GPL-3.0-only. UI/control-only factory bank decoder; never called by an engine render callback.
 * Bounded immutable LZ4 blocks, static scratch/cache, no allocation or flash writes.
 */
#include "../jazzy/factory_projection.h"
#include "../jazzy/catalog_assets.h"
static uint8_t fp_block[FP_BLOCK_ROWS*41];
static uint16_t fp_loaded=65535;
static struct {preset_t preset;char name[16];int8_t extra[7];uint16_t key;} fp_cache[8];
static unsigned fp_hand;
static int fp_unpack(unsigned block){
 unsigned p=FP_AT[block],end=FP_AT[block+1],n=0;
 const uint8_t *src;
#if JAZZY_EXTERNAL_ASSETS
 if(!jazzy_catalog_valid)return 0;
 if(p<JCAT_FP_SPLIT1)src=fm1_xip_ptr(0xda000u+p);
 else if(p<JCAT_FP_SPLIT2)src=fm1_xip_ptr(0x94000u+p-JCAT_FP_SPLIT1);
 else src=fm1_xip_ptr(0x95000u+p-JCAT_FP_SPLIT2);
#else
 src=FP_DATA+p;
#endif
 end-=p;p=0;
 while(p<end){unsigned tok=src[p++],len=tok>>4;if(len==15){unsigned a;do{if(p>=end)return 0;a=src[p++];len+=a;}while(a==255);}
  if(p+len>end||n+len>sizeof fp_block)return 0;while(len--)fp_block[n++]=src[p++];if(p==end)break;
  if(p+2>end)return 0;unsigned off=src[p]|src[p+1]<<8;p+=2;if(!off||off>n)return 0;len=(tok&15)+4;
  if((tok&15)==15){unsigned a;do{if(p>=end)return 0;a=src[p++];len+=a;}while(a==255);}
  if(n+len>sizeof fp_block)return 0;while(len--){fp_block[n]=fp_block[n-off];n++;}
 }return 1;
}
static const preset_t *factory_preset(const engine_t *e,unsigned k){
 if(e==&ENG_LXR)return lxr_factory(k%LXR_COUNT);
 if(!e->factory_id)return &e->presets[k%e->npresets];
 unsigned id=e->factory_id;k%=e->npresets;unsigned key=id*256+k;
 for(unsigned i=0;i<8;i++)if(fp_cache[i].key==key)return &fp_cache[i].preset;
 unsigned record=FP_BANK[id][0]+k,block=record/FP_BLOCK_ROWS;
 if(fp_loaded!=block){if(!fp_unpack(block)){static const preset_t init={.name="INIT"};return &init;}fp_loaded=(uint16_t)block;}
 unsigned i=fp_hand++&7u;uint8_t b[41];for(unsigned j=0;j<41;j++)b[j]=fp_block[j*FP_BLOCK_ROWS+record%FP_BLOCK_ROWS];memset(&fp_cache[i],0,sizeof fp_cache[i]);
 memcpy(fp_cache[i].name,b,15);fp_cache[i].preset.name=fp_cache[i].name;
 memcpy(fp_cache[i].preset.e,b+16,8);memcpy(fp_cache[i].preset.env,b+24,4);fp_cache[i].preset.fenv=(int8_t)b[28];fp_cache[i].preset.mono=b[29];memcpy(fp_cache[i].preset.fx,b+30,4);memcpy(fp_cache[i].extra,b+34,7);fp_cache[i].key=(uint16_t)key;
 return &fp_cache[i].preset;
}
static void factory_performance(track_t *t,const engine_t *e,unsigned k){
 if(e==&ENG_LXR){t->p[P_E0]=(int16_t)(k%LXR_PAGE);t->p[P_LN0]=(int16_t)(k/LXR_PAGE);return;}
 if(e==&ENG_S1||e==&ENG_JHYDRA)t->p[P_LN0]=(int16_t)(k%e->npresets);
 if(!e->factory_id)return;const preset_t *p=factory_preset(e,k);
 for(unsigned i=0;i<8;i++)if(p==&fp_cache[i].preset){
  static const uint8_t ids[7]={P_LRATE,P_LWAVE,P_LD_PIT,P_LD_FLT,P_LD_SHP,P_LD_AMP,P_GLIDE};for(unsigned j=0;j<7;j++)t->p[ids[j]]=fp_cache[i].extra[j];return;
 }
}

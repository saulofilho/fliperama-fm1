/* Real external-asset path and original integer-table/program parity. */
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define JAZZY_EXTERNAL_ASSETS 1
#define UI_TEST_NO_MAIN 1
static uint8_t asset_flash[1<<20];
static const uint8_t *fm1_xip_ptr(uint32_t off){return asset_flash+off;}
#include "jazzy_host.h"
#include "../firmware/jazzy/hydra_expect.h"
static int st_read(uint32_t off,void *dst,uint32_t n){memcpy(dst,asset_flash+off,n);return 0;}
static int st_erase(uint32_t off){memset(asset_flash+off,255,4096);return 0;}
static int st_prog(uint32_t off,const void *p,uint32_t n){memcpy(asset_flash+off,p,n);return 0;}
#include "../firmware/src/storage.c"
#include "../firmware/src/synth_assets.c"
static uint32_t hash(const void *p,unsigned n){const uint8_t *b=p;uint32_t h=2166136261u;while(n--)h=(h^*b++)*16777619u;return h;}
static uint32_t play(unsigned e,unsigned pi,unsigned macro,int value){
 track_t *t=&trk[0];set_engine_of(t,e);apply_preset_to(t,pi);t->engine=t->eng_req;t->p[P_E0+macro]=(int16_t)value;
 memset(t->v,0,sizeof t->v);voice_t *v=&t->v[0];v->active=v->gate=1;v->note=60;v->pitch16=960;v->vel=110;v->env_out=32767;
 const engine_t *en=ENGINES[e];if(en->block)en->block(t);en->note_on(t,v);
 vmod_t m={0};m.inc=pitch_inc(960);m.pitch16=960;m.amp0=m.amp1=24576;m.envq15=32767;m.shape=16384;
 uint32_t h=2166136261u;for(unsigned j=0;j<120;j++){int32_t o[CTL]={0};if(en->block)en->block(t);en->render(t,v,o,CTL,&m);h=(h^hash(o,sizeof o))*16777619u;}return h;
}
int main(int argc,char **argv){
 unsigned bad=0;uint8_t p[32];if(argc!=8&&argc!=9)return 2;
 for(unsigned i=0;i<2;i++){FILE *f=fopen(argv[i+1],"rb");if(!f||fread(asset_flash+0xA0000+i*0x14000,1,81920,f)!=81920)return 2;fclose(f);}
 for(unsigned i=0;i<3;i++){
  FILE *f=fopen(argv[i+3],"rb");
  if(!f||fread(asset_flash+JCAT_PARTS[i].at,1,JCAT_PARTS[i].size,f)!=JCAT_PARTS[i].size)return 2;
  fclose(f);
 }
 FILE *font=fopen(argv[6],"rb");
 if(!font||fread(asset_flash+JAZZY_FONT_AT,1,AF_M_XIP_BYTES,font)!=AF_M_XIP_BYTES)return 2;
 fclose(font);
 FILE *marker=fopen(argv[7],"rb");
 if(!marker||fread(asset_flash+0x93020u,1,LXR_MARKER_BYTES,marker)!=LXR_MARKER_BYTES)return 2;
 fclose(marker);
 FILE *lxr=argc==9?fopen(argv[8],"rb"):NULL;
 if(argc==9&&!lxr)return 2;
 bad+=check("external factory catalog and font checksums valid",jazzy_catalog_check()&&jazzy_font_valid);
 asset_flash[JAZZY_FONT_AT]^=1;
 bad+=check("bad font triggers fallback with catalog still available",jazzy_catalog_check()&&!jazzy_font_valid);
 cv_begin(240, 60, 0);
 cv_text(10, 5, &AF_M, "azimuth", 65535);
 asset_flash[JAZZY_FONT_AT]^=1;
 bad+=check("restored font validates",jazzy_catalog_check()&&jazzy_font_valid);
 bad+=check("factory rows decode on both sides of both boundaries",fp_unpack(15)&&fp_unpack(16)&&fp_unpack(23)&&fp_unpack(24));
 for(unsigned i=0;i<3;i++){
  asset_flash[JCAT_PARTS[i].at]^=1;
  bad+=check("bad factory resource is detected before decoding",!jazzy_catalog_check()&&!fp_unpack(0));
  asset_flash[JCAT_PARTS[i].at]^=1;
  bad+=check("restored catalog validates",jazzy_catalog_check());
 }
 bad+=check("LXR marker and catalog assets validate",lxr_assets_valid);
 asset_flash[0x93020u]^=1;
 bad+=check("bad LXR marker is isolated from synth catalog and font",jazzy_catalog_check()&&!lxr_assets_valid&&jazzy_font_valid);
 asset_flash[0x93020u]^=1;
 bad+=check("restored LXR bank validates",jazzy_catalog_check()&&lxr_assets_valid);
 unsigned lxr_differences=0;
 uint32_t lxr_hash=2166136261u;
 for(unsigned i=0;i<LXR_COUNT;i++){
  lxr_patch_t got,expected;
  lxr_unpack(&got,i);
  if(lxr){
   if(fread(&expected,1,sizeof expected,lxr)!=sizeof expected)return 2;
   lxr_differences+=memcmp(&got,&expected,sizeof got)!=0;
  }
  for(unsigned k=0;k<sizeof got;k++)lxr_hash=(lxr_hash^((const uint8_t*)&got)[k])*16777619u;
  lxr_differences+=!lxr_factory(i)->name[0];
 }
 if(lxr)fclose(lxr);
 bad+=check("595 LXR voices round-trip from the upstream projection",LXR_COUNT==595u&&!lxr_differences&&lxr_hash==0x18a8b620u);
 bad+=check("bank-tail checksums valid",jazzy_assets_check());ui_power_on();fm6_init();power_on_parts();song.playing=0;transport_req=0;chain.armed=0;
 unsigned mismatch=0;
 for(unsigned i=0;i<4096;i++)mismatch+=jv_lookup(i)!=FM106_VCF_G1[i];
 for(unsigned i=0;i<1025;i++)mismatch+=jt_lookup(&JT_EXP,i)!=FM6_EXP2[i];
 for(unsigned i=0;i<769;i++)mismatch+=jt_lookup(&JT_M2,i)!=m2_T_INC_TOP[i];
 for(unsigned i=0;i<768;i++)mismatch+=jt_lookup(&JT_KW,i)!=jk_KS_PITCH[i];
 bad+=check("6658 original table values match exactly",mismatch==0);
 mismatch=0;for(unsigned i=0;i<200;i++){jf_load(p,i);mismatch+=memcmp(p,FMINI_FACTORY[i],32)!=0;}
 bad+=check("all 6400 FMini native bytes match",mismatch==0);
 /* The off-chip compressed stream must decode identically to the independently
  * generated inline source, across the physical slot boundary. */
 for(unsigned i=0;i<sizeof JH_WAVE_PACK;i++)mismatch+=jh_pack_get(i)!=JH_WAVE_PACK[i];
 bad+=check("split physical HYDRA stream matches",mismatch==0);
 uint32_t wavehash=hash(jh_waves,sizeof jh_waves);printf("HYDRA wave FNV=%u\n",wavehash);bad+=check("all 12288 native wave bytes match",wavehash==JH_WAVE_EXPECT);
 static const unsigned models[]={ENGI_S1,ENGI_HYDRA};
 for(unsigned j=0;j<2;j++){
  unsigned e=models[j],pi=j?15:47;track_t *t=&trk[0];set_engine_of(t,e);apply_preset_to(t,pi);t->engine=e;t->p[P_E2]=31;t->p[P_E6]=12;
  int16_t saved[P_COUNT];memcpy(saved,t->p,sizeof saved);song.sel=0;
  bad+=check("new model user preset stores",up_store(j,"EXPANSION")==3);set_engine_of(t,ENGI_ANALOG);up_load(j);
  bad+=check("native program and macros survive user preset",t->eng_req==e&&t->p[P_LN0]==(int)pi&&t->p[P_E2]==31&&t->p[P_E6]==12);
  bad+=check("expansion project saves",project_save(j)==0);set_engine_of(t,ENGI_ANALOG);project_load(j);
  bad+=check("native program survives project",t->eng_req==e&&t->p[P_LN0]==(int)pi&&t->p[P_E2]==31&&t->p[P_E6]==12);
 }
 bad+=check("S1 DRAW multiplier reaches native DSP",play(ENGI_S1,42,6,0)!=play(ENGI_S1,42,6,20));
 bad+=check("S1 CHOP reaches native DSP",play(ENGI_S1,3,7,0)!=play(ENGI_S1,3,7,100));
 unsigned changes=0;for(unsigned pi=0;pi<16;pi++)for(unsigned k=0;k<8;k++)changes+=play(ENGI_HYDRA,pi,k,-64)!=play(ENGI_HYDRA,pi,k,63);
 bad+=check("HYDRA factory macro routes affect sound",changes>=80);printf("HYDRA audible macro comparisons=%u/128\n",changes);
 /* Exercise union reuse at high preset IDs; a previous model's bytes must not
  * be mistaken for a valid prepared HYDRA part. */
 uint32_t expected=play(ENGI_HYDRA,0,0,0);
 for(unsigned i=0;i<24;i++){play(i&1?ENGI_FM6:ENGI_PROPHET,0,0,60);bad+=check("FM6 / Prophet / HYDRA storage switching stable",play(ENGI_HYDRA,0,0,0)==expected);}
 unsigned flips[]={0,8175,8176,16089};for(unsigned i=0;i<4;i++){uint8_t *b=(uint8_t*)jazzy_asset_at(flips[i]);*b^=1;bad+=check("asset corruption detected",!jazzy_assets_check());bad+=check("bad asset bank prevents new model selection",!eng_ok(ENGI_S1)&&!eng_ok(ENGI_HYDRA));*b^=1;bad+=check("restored asset bank validates",jazzy_assets_check());}
 printf("expansion failures=%u\n",bad);return !!bad;
}

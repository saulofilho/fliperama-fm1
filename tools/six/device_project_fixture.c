/* SPDX-License-Identifier: GPL-3.0-only */
/* Turn a read-only CDC track/global snapshot into a local emulator fixture.
 * Only persistent parameters and sequence events are copied, never live
 * pointers, voice/filter state, locks or physical-device transport state. */
#define UI_TEST_NO_MAIN 1
#include "../../rhythmer/tests/ui_test.c"
int main(int argc,char **argv){
 if(argc!=4&&argc!=5)return 1;
 static unsigned char raw[6*2772],global[164];
 FILE *f=fopen(argv[1],"rb");if(!f||fread(raw,1,sizeof raw,f)!=sizeof raw)return 2;fclose(f);
 f=fopen(argv[2],"rb");if(!f||fread(global,1,sizeof global,f)!=sizeof global)return 3;fclose(f);
 if(sizeof(track_t)!=2772||offsetof(track_t,step)!=1036||P_COUNT!=127||sizeof(step_t)!=20||G_COUNT!=71)return 4;
 ui_power_on();fm6_init();power_on_parts();six_native_init();trks_put(1);
 memcpy(song.g,global,sizeof song.g);song.sel=4;
 for(unsigned k=0;k<6;k++){
  track_t *t=&trk[k];unsigned char *s=raw+k*2772;unsigned e=s[254];if(!six_engine_available(k,e))return 5;
  set_engine_of(t,e);t->engine=t->eng_req=e;
  apply_preset_to(t,s[255]<ENGINES[e]->npresets?s[255]:0);
  memcpy(t->p,s,sizeof t->p);memcpy(t->step,s+1036,sizeof t->step);
  if(argc==5)t->p[P_MUTE]=(strtoul(argv[4],0,0)>>k)&1u; /* local A/B test only */
  t->xf=t->xf_on=0;
 }
 project_capture(&proj_scratch);if(!proj_pack(&proj_wire,&proj_scratch))return 6;
 f=fopen(argv[3],"wb");if(!f||fwrite(&proj_wire,1,sizeof proj_wire,f)!=sizeof proj_wire)return 7;fclose(f);
 printf("Read-only device fixture: %u BPM, engines",song.g[G_BPM]);for(unsigned k=0;k<6;k++)printf(" %u",trk[k].engine);puts("");
 return 0;
}

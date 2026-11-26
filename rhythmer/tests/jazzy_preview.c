#define UI_TEST_NO_MAIN 1
#include "jazzy_host.h"
static void save_screen(const char *root,unsigned e,unsigned f){
 char path[1024];if(e==99)snprintf(path,sizeof path,"%s/startup-%02u.ppm",root,f);else snprintf(path,sizeof path,"%s/engine-%02u-%02u.ppm",root,e,f);FILE *o=fopen(path,"wb");if(!o)exit(2);fprintf(o,"P6\n240 240\n255\n");
 for(unsigned i=0;i<240*240;i++){unsigned p=swap16(host_screen[i]);unsigned char rgb[3]={(p>>11)*255/31,((p>>5)&63)*255/63,(p&31)*255/31};fwrite(rgb,1,3,o);}fclose(o);
}
int main(int argc,char **argv){
 if(argc<2||argc>3)return 2;ui_power_on();fm6_init();power_on_parts();palette_set(0);ux.skin=1;ux.style=1;ui.home=0;ui.confirm=0;
 if (argc == 3 && !strcmp(argv[2], "--startup")) {
  for (unsigned ms = 0; ms < SPL_WRITE + SPL_HOLD; ms += 80u) {
   splash_sig(0, ms);
   save_screen(argv[1], 99, ms / 80u);
  }
  return 0;
 }
 for(unsigned p=0;p<NPAGES;p++)if(PAGES[p].scope==SC_ENGINE&&PAGES[p].id[0]==P_E0){ui.page=p;break;}
 for(unsigned j=0;j<NENG_SHOWN;j++){unsigned e=ENGINE_ORDER[j];if(e==ENGI_EMPTY||(argc==3&&e!=(unsigned)atoi(argv[2])))continue;set_engine_of(&trk[0],e);apply_preset_to(&trk[0],0);trk[0].engine=trk[0].eng_req;
 for(unsigned f=0;f<24;f++){fm1_ms=2000+f*50;six_vis_note_at[0]=2001+(f/6)*300;memset(trk[0].v,0,sizeof trk[0].v);for(unsigned z=0;z<1+(f/6)%4;z++){trk[0].v[z].active=trk[0].v[z].gate=1;trk[0].v[z].note=60+z*4;}trk[0].seq_idx=f; six_vis_note_vel[0]=112;trk[0].m_env=f<6?24000-f*3000:0;trk[0].lfo_ph=f*0x10000000u;ui.force=1;ui_draw();save_screen(argv[1],e,f);}}
 for(unsigned f=0;f<3;f++){splash_sig(0,f*500);save_screen(argv[1],99,f);}
 return 0;
}

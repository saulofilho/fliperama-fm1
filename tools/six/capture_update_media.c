/* SPDX-License-Identifier: GPL-3.0-only
 * Real current firmware UI rendered on the host. Presentation capture only. */
#define UI_TEST_NO_MAIN 1
#include "../../rhythmer/tests/ui_test.c"
static void pixels(FILE *f){for(unsigned i=0;i<57600;i++){unsigned p=swap16(host_screen[i]);unsigned char c[3]={(p>>11)*255/31,((p>>5)&63)*255/63,(p&31)*255/31};fwrite(c,1,3,f);}}
static FILE *out(const char *dir,const char *name){char p[1024];snprintf(p,sizeof p,"%s/%s.rgb",dir,name);FILE *f=fopen(p,"wb");if(!f)exit(2);return f;}
int main(int argc,char **argv){if(argc!=2)return 1;ui_power_on();load_depth++;fm6_init();power_on_parts();load_depth--;six_native_init();trks_put(1);menu_put(MI_COLOR,0);menu_put(MI_SKIN,1);menu_put(MI_STYLE,1);fm1_ms+=8000;
 song.sel=0;dx_kit_load(0);dx_ui_seen=last_note;dx_ui_lane=3;dx_voice_bank=0;go_title("DRUM VOICE");
 FILE *f=out(argv[1],"drum-sound");
 for(unsigned n=0;n<48;n++){unsigned ids[]={3,72+10,72+11,72+12};dx_ui_lane=3;dx_voice_pick(ids[n/12]);fm1_ms+=80;ui.force=1;frame();pixels(f);}fclose(f);
 ui.page=(uint8_t)page_first(FAM_EDIT);
 const char *names[]={"gen-target","gen-break","gen-styles"};
 for(unsigned k=0;k<3;k++){f=out(argv[1],names[k]);gp.target=k==1?7:k==0?2:0;gp.form=0;gp.genre=k==1?47:59;gp.seed=31;gp.energy=55;gp.complex=65;gp.human=70;gp.swing=GA_AUTO;for(unsigned j=0;j<GP_N;j++)gp.amt[j]=GA_AUTO;
 for(unsigned n=0;n<48;n++){if(n%12==0){if(k==2){static unsigned gs[]={59,58,57,55};gp.genre=gs[n/12];}ui.home=1;ui.confirm=CF_DICE_ALL;gp.page=0;gp.seed=31+n*17;gen_fresh=1;gen_go();}fm1_ms+=80;gen_fresh=1;ui.force=1;frame();pixels(f);}fclose(f);}
 return 0;
}

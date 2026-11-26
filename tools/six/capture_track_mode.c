/* SPDX-License-Identifier: GPL-3.0-only */
#define UI_TEST_NO_MAIN 1
#include "../../rhythmer/tests/ui_test.c"
static void save(const char *dir,const char *name){char path[1024];snprintf(path,sizeof path,"%s/%s.ppm",dir,name);ui.force=1;frame();FILE *f=fopen(path,"wb");if(!f)exit(2);fprintf(f,"P6\n240 240\n255\n");for(unsigned i=0;i<57600;i++){unsigned p=swap16(host_screen[i]);unsigned char c[3]={(p>>11)*255/31,((p>>5)&63)*255/63,(p&31)*255/31};fwrite(c,1,3,f);}fclose(f);}
int main(int argc,char **argv){if(argc!=2)return 1;ui_power_on();fm6_init();power_on_parts();six_native_init();trks_put(0);ui.home=1;save(argv[1],"four-track-home");go_title("SYSTEM");frame();if(cur_page()->fam!=FAM_GLO)return 3;save(argv[1],"track-system");turn(EN_K1,1);if(ui.confirm!=CF_TRACKS6||trk_live!=4)return 4;save(argv[1],"cpu-notice");press(B_OCTUP);if(trk_live!=6)return 5;ui.home=1;save(argv[1],"six-track-home");return 0;}

/* SPDX-License-Identifier: GPL-3.0-only
 * Presentation capture of the real held-SEQ layer; no hardware access. */
#define UI_TEST_NO_MAIN 1
#include "../../rhythmer/tests/ui_test.c"
int main(int argc,char **argv){
 if(argc!=2)return 1;
 ui_power_on();fm6_init();load_depth++;power_on_parts();load_depth--;six_native_init();trks_put(1);
 menu_put(MI_COLOR,0);menu_put(MI_SKIN,1);menu_put(MI_STYLE,1);
 song.sel=5;ui.home=1;fm1_ms+=8000;
 fm1_in.buttons|=1u<<panel.btn[B_SEQ];host_pressed|=1u<<panel.btn[B_SEQ];frames(850);
 if(layer_open()!=LAYER_SEQ||strcmp(layer_head(),"[SEQ] BREAK"))return 2;
 ui.force=1;frame();
 FILE *f=fopen(argv[1],"wb");if(!f)return 3;fprintf(f,"P6\n240 240\n255\n");
 for(unsigned i=0;i<57600;i++){unsigned p=swap16(host_screen[i]);unsigned char c[3]={(p>>11)*255/31,((p>>5)&63)*255/63,(p&31)*255/31};fwrite(c,1,3,f);}fclose(f);
 return 0;
}

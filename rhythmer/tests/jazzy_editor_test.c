#include "jazzy_editor_host.h"
int main(void){unsigned bad=0;uint8_t a[4]={0};reset();
 for(unsigned k=0;k<ED_MENU_N;k++)bad+=check("legacy skin and style not advertised",ED_MENU[k][1]!=1&&ED_MENU[k][1]!=21);
 a[0]=ENGI_FMINI;unsigned total=0;
 for(unsigned start=0;start<200;start+=32){a[1]=start&127;a[2]=start>>7;a[3]=32;unsigned n=request(ED_NAMES,a,4);unsigned count=host_wire[6];bad+=check("catalog page framing",n<sizeof ed_out&&n>11&&host_wire[0]==0xf0&&host_wire[n-1]==0xf7&&count<=32);unsigned p=7;for(unsigned i=0;i<count;i++){bad+=check("catalog name matches",!strncmp((char*)host_wire+p,factory_preset(ENGINES[ENGI_FMINI],start+i)->name,strlen((char*)host_wire+p)));while(host_wire[p++]);}for(unsigned i=0;i<2;i++)while(host_wire[p++]);bad+=check("catalog complete 14-bit extent",host_wire[p]+128u*host_wire[p+1]==start&&host_wire[p+2]+128u*host_wire[p+3]==200);total+=count;}
 bad+=check("all 200 names retrieved",total==200);request(ED_NAMES,a,1);bad+=check("legacy name request safely bounded",host_wire[6]==32&&host_wire_n<600);
 a[0]=ENGI_FMINI;a[1]=71;a[2]=1;request(ED_PRESET,a,3);bad+=check("extended preset selects slot 199",TSEL->preset==199&&TSEL->p[P_E6]==1&&TSEL->p[P_E7]==71&&host_wire[6]==71&&host_wire[7]==1);
 request(ED_DUMP,a,0);bad+=check("dump retains high preset bit",host_wire[host_wire_n-2]==1);a[0]=song.sel;request(ED_TRACK_DUMP,a,1);bad+=check("track dump retains high preset bit",host_wire[host_wire_n-2]==1);a[0]=ENGI_FMINI;a[1]=5;request(ED_PRESET,a,2);bad+=check("legacy preset remains compatible",TSEL->preset==5&&host_wire_n==8);
 a[0]=ENGI_FMINI;a[1]=(8192+199)&127;a[2]=(8192+199)>>7;a[3]=1;request(ED_FAV_SET,a,4);bad+=check("favorite slot 199 via USB protocol",favorite_has(ENGI_FMINI,199));
 for(unsigned e=ENGI_S1;e<=ENGI_HYDRA;e++){a[0]=e;a[1]=ENGINES[e]->npresets-1;a[2]=0;request(ED_PRESET,a,3);bad+=check("new engine last native program selected via USB",TSEL->eng_req==e&&TSEL->p[P_LN0]==a[1]);a[1]=0;a[2]=0;a[3]=32;request(ED_NAMES,a,4);bad+=check("new engine catalog page fits protocol",host_wire_n<600&&host_wire[6]==(e==ENGI_S1?32:16));}
 printf("JAZZY editor failures=%u\n",bad);return !!bad;}

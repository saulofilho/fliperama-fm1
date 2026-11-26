#define UI_TEST_NO_MAIN 1
#include "jazzy_host.h"
static uint32_t sound_hash(unsigned e,unsigned param,int value){
 track_t *t=&trk[0];set_engine_of(t,e);apply_preset_to(t,0);t->engine=t->eng_req;t->p[P_E0+param]=(int16_t)value;memset(t->v,0,sizeof t->v);
 voice_t *v=&t->v[0];v->active=v->gate=1;v->note=60;v->vel=110;v->env_out=32767;
 const engine_t *en=ENGINES[e];en->note_on(t,v);vmod_t m={0};m.inc=pitch_inc(60*16);m.pitch16=60*16;m.amp0=m.amp1=24000;m.envq15=24000;m.shape=16384;
 uint32_t h=2166136261u;for(unsigned b=0;b<80;b++){int32_t o[CTL]={0};en->render(t,v,o,CTL,&m);for(unsigned i=0;i<CTL;i++)h=(h^(unsigned)o[i])*16777619u;}return h;
}
int main(void){unsigned bad=0;ui_power_on();fm6_init();power_on_parts();
 bad+=check("priority models selectable",eng_ok(ENGI_CZ)&&eng_ok(ENGI_PROPHET)&&eng_ok(ENGI_FMINI)&&eng_ok(ENGI_JUNO)&&eng_ok(ENGI_M2SID));
 const int connection[][4]={{ENGI_OBER,2,0,127},{ENGI_OBER,3,-64,63},{ENGI_OBER,7,-24,24},{ENGI_CS,5,0,110},{ENGI_CS,6,0,127},{ENGI_JUNO,7,0,3},{ENGI_JUNO,6,-64,63},{ENGI_JUNO,4,0,105},{ENGI_KW_WAVE,2,0,127},{ENGI_KW_WAVE,4,0,127},{ENGI_KW_WAVE,5,0,127},{ENGI_KW_FM,5,0,127},{ENGI_KW_ADD,5,0,127},{ENGI_KW_SYNC,2,0,127}};
 for(unsigned j=0;j<NELEM(connection);j++){const int *c=connection[j];uint32_t lo=sound_hash(c[0],c[1],c[2]),hi=sound_hash(c[0],c[1],c[3]);if(lo==hi)printf("CONNECTION e=%d macro=%d\n",c[0],c[1]);bad+=check("imported macro reaches DSP",lo!=hi);}
 bad+=check("CZ DCW changes audio",sound_hash(ENGI_CZ,2,10)!=sound_hash(ENGI_CZ,2,110));
 bad+=check("Prophet filter revisions differ",sound_hash(ENGI_PROPHET,2,0)!=sound_hash(ENGI_PROPHET,2,1));
 bad+=check("Prophet sync changes audio",sound_hash(ENGI_PROPHET,7,0)!=sound_hash(ENGI_PROPHET,7,1));
 bad+=check("Prophet poly-mod changes audio",sound_hash(ENGI_PROPHET,6,0)!=sound_hash(ENGI_PROPHET,6,100));
 set_engine_of(&trk[0],ENGI_FMINI);trk[0].p[P_E6]=1;trk[0].p[P_E7]=127;knob_cap(&trk[0],P_E6);bad+=check("FMini last bank limited to valid programs",trk[0].p[P_E7]==71&&track_desc(&trk[0],P_E7)->max==71);
 set_engine_of(&trk[0],ENGI_CZ);set_engine_of(&trk[1],ENGI_PROPHET);trk[0].p[P_E2]=99;trk[1].p[P_E6]=101;
 song.playing=0;transport_req=0;chain.armed=0;bad+=check("new priority project saves",!project_save(0));set_engine_of(&trk[0],ENGI_ANALOG);set_engine_of(&trk[1],ENGI_ANALOG);project_load(0);
 bad+=check("CZ and Prophet project roundtrip",trk[0].eng_req==ENGI_CZ&&trk[1].eng_req==ENGI_PROPHET&&trk[0].p[P_E2]==99&&trk[1].p[P_E6]==101);
 printf("priority failures=%u\n",bad);return !!bad;
}

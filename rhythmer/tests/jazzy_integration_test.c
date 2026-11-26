#define UI_TEST_NO_MAIN 1
#include <stdint.h>
static unsigned watch_tabs, tab_clears;
#define UI_FILL_HOOK(x, y, w, h) do { if (watch_tabs && (w) && (h) && (y) < 39 && (y) + (h) > 26) tab_clears++; } while(0)
#include "jazzy_host.h"
static unsigned errors;
#define REQUIRE(s,x) do{if(!(x)){printf("FAIL %s\n",s);errors++;}}while(0)
int main(void){
 ui_power_on();fm6_init();power_on_parts();six_native_init();
 REQUIRE("retired kit not selectable",!eng_ok(ENGI_DRUM));
 set_engine_of(&trk[0],ENGI_DRUM);REQUIRE("retired kit request becomes EMPTY",trk[0].eng_req==ENGI_EMPTY);project_capture(&proj_scratch);proj_scratch.t[0].engine=ENGI_DRUM;proj_phys_gone(&proj_scratch);REQUIRE("legacy kit project becomes EMPTY",proj_scratch.t[0].engine==ENGI_EMPTY);
 REQUIRE("single Hort voice",ENG_HORT.poly==1&&ENG_HORT.oneshot);
 unsigned char reserved[32];memcpy(reserved,favorites.factory[15],32);
 for(unsigned i=0;i<NENG_SHOWN;i++){unsigned e=eng_vis(i);if(e==ENGI_EMPTY)continue;unsigned last=ENGINES[e]->npresets-1;REQUIRE("factory star set",favorite_set(e,last,1));REQUIRE("factory star read",favorite_has(e,last));}
 REQUIRE("settings untouched by stars",!memcmp(reserved,favorites.factory[15],32));
 for(unsigned seed=1;seed<=24;seed++){
  for(unsigned k=0;k<4;k++)set_engine_of(&trk[k],ENGI_ANALOG);
  unsigned tail[2]={steps_sig(&trk[4]),steps_sig(&trk[5])};gp.target=0;gp.form=0;gp.genre=GEN_EXPLORE;gp.seed=seed*139;gen_go();
  for(unsigned k=0;k<4;k++){unsigned notes=0;for(unsigned j=0;j<NSTEP;j++)notes+=trk[k].step[j].time==ST_NOTE&&trk[k].step[j].n;if(!notes)printf("EMPTY seed=%u trk=%u role=%u active=%u amount=%u\n",seed,k,gs.role[k],gs.act[gs.role[k]],gs.amt[GP_BASS+k]);REQUIRE("four populated melodic tracks",notes>0);REQUIRE("no kit or Hort assignment",trk[k].eng_req!=ENGI_DRUM&&trk[k].eng_req!=ENGI_HORT&&trk[k].eng_req!=ENGI_KW_KICK);unsigned tag=PR_TAG(factory_preset(ENGINES[trk[k].eng_req],trk[k].preset));REQUIRE("GEN excludes drum and FX synth presets",tag!=PT_DRUM&&tag!=PT_FX);}
  REQUIRE("unused tracks preserved",tail[0]==steps_sig(&trk[4])&&tail[1]==steps_sig(&trk[5]));
 }
 unsigned mini=0,total=0,regular_mini=0,regular_total=0,miss=0,used[NENGINES]={0},heavy_violations=0,empty=0;
 static const unsigned roles[]={RL_BASS,RL_PAD,RL_ARP,RL_LEAD};
 static const unsigned accepted[]={1u<<PT_BASS,(1u<<PT_PAD)|(1u<<PT_KEYS)|(1u<<PT_VOX),
  (1u<<PT_PLUCK)|(1u<<PT_BELL)|(1u<<PT_KEYS)|(1u<<PT_LEAD),
  (1u<<PT_LEAD)|(1u<<PT_KEYS)|(1u<<PT_PLUCK)|(1u<<PT_BELL)|(1u<<PT_VOX)};
 for(unsigned genre=0;genre<=NGENRE;genre++)for(unsigned seed=0;seed<12;seed++){
  gp.genre=genre==NGENRE?GEN_EXPLORE:genre+1;gp.seed=(seed*619+genre*103)%10000;gen_make();
  unsigned heavy=0;
  for(unsigned i=0;i<4;i++){
   track_t *t=&trk[i];unsigned e=t->eng_req,preset=preset_active(t),tag=PR_TAG(factory_preset(ENGINES[e],preset));
   miss+=(gs.role[i]!=roles[i])||(i==0?!gen_bass_ok(e,preset):!((accepted[i]>>tag)&1u));
   used[e]++;heavy+=gen_heavy(e);
   unsigned notes=0;for(unsigned j=0;j<dlen(t);j++)notes+=t->step[j].time==ST_NOTE&&t->step[j].n;
   if(!notes)printf("empty genre=%u %s seed=%u role=%u len=%u\n",genre,gs.g->name,gp.seed,roles[i],dlen(t));
   empty+=!notes;
   if(!i){
    mini+=e==ENGI_FMINI;total++;
    if(!gen_techno_bass()){regular_mini+=e==ENGI_FMINI;regular_total++;}
   }
  }
  heavy_violations+=heavy>1;
 }
 printf("GEN arrangements=%u FMini bass=%u empty=%u role mismatches=%u\n",total,mini,empty,miss);
 REQUIRE("Other genres retain their FMini bass bias",regular_mini*100u>=35u*regular_total&&regular_mini*100u<=48u*regular_total);
 static const char *const techno[]={"TECH HOUSE","TECHNO","DETROIT","DUB TECHNO","HARD TECHNO","HYPNOTIC"};
 unsigned techno_presets=0,techno_draws=0;
 for(unsigned i=0;i<NELEM(techno);i++){
  gs.gi=0;
  while(gs.gi<NGENRE&&strcmp(techno[i],GENRE[gs.gi].name))gs.gi++;
  REQUIRE("Named techno family excludes the FMini boost",gs.gi<NGENRE&&gen_techno_bass());
  unsigned count=0;
  for(unsigned seed=0;seed<256;seed++){
   gp.seed=seed*37u;
   gseed(GS_SOUND+RL_BASS*17u);
   gen_sound(&trk[0],RL_BASS,0);
   count+=trk[0].eng_req==ENGI_FMINI;
  }
  REQUIRE("FMini is still an occasional techno bass",count>0u&&count<31u);
  techno_presets+=count;techno_draws+=256;
 }
 printf("FMini bass regular=%u/%u techno=%u/%u\n",regular_mini,regular_total,techno_presets,techno_draws);
 REQUIRE("all generated presets fit their role",!miss);
 REQUIRE("AUTO generates four populated roles",!empty);
 REQUIRE("one expensive model maximum per generated arrangement",!heavy_violations);
 REQUIRE("mandatory additions reachable by GEN",used[ENGI_FMINI]&&used[ENGI_CZ]&&used[ENGI_PROPHET]&&used[ENGI_FM6]&&used[ENGI_S1]&&used[ENGI_HYDRA]);
 gp.amt[GP_ARP]=0;gen_make();
 REQUIRE("explicit ARP OFF remains silent",seq_is_empty(&trk[2]));
 gp.amt[GP_ARP]=GA_AUTO;
 set_engine_of(&trk[2],ENGI_LXR);apply_preset_to(&trk[2],LXR_COUNT-1u);
 unsigned drum_steps=steps_sig(&trk[2]);gen_make();
 REQUIRE("song GEN preserves an existing LXR slot",trk[2].eng_req==ENGI_LXR&&preset_active(&trk[2])==LXR_COUNT-1u&&steps_sig(&trk[2])==drum_steps);
 set_engine_of(&trk[2],ENGI_ANALOG);
 nav_go(SEC_HOME,4,0);ui_draw();
 watch_tabs=1;
 for(unsigned i=0;i<12;i++){
  fm1_ms+=30;gen_knob(2,1);ui_draw();
  gen_page_put(i%3);ui_draw();
 }
 gen_press();ui_draw();
 watch_tabs=0;
 REQUIRE("GEN tab names stay painted through knob, page and generate redraws",gen_on()&&!tab_clears);
 ui.confirm=0;
 song.sel=0;set_engine_of(TSEL,ENGI_LXR);apply_preset_to(TSEL,320u);
 unsigned kept=steps_sig(TSEL);
 nav_go(SEC_SAVE,6,0);
 REQUIRE("SAVE > SOUND > PRESETS opens the preset browser",cur_page()->graph==GR_BROWSE);
 edit_param(1,1);
 REQUIRE("K2 jumps from the middle of LXR straight to next engine",trk_eng(TSEL)==ENGI_SERUM&&preset_active(TSEL)==0);
 edit_param(1,-1);
 REQUIRE("K2 jumps back to LXR without stepping the catalog",trk_eng(TSEL)==ENGI_LXR&&preset_active(TSEL)==0&&steps_sig(TSEL)==kept);
 song.playing=0;transport_req=0;chain.armed=0;set_engine_of(&trk[0],ENGI_KW_ADD);set_engine_of(&trk[1],ENGI_FMINI);apply_preset_to(&trk[1],199);
 printf("save result=%d msg=%s\n",project_save(0),ui.msg);REQUIRE("project stored",project_used(0));set_engine_of(&trk[0],ENGI_ANALOG);set_engine_of(&trk[1],ENGI_ANALOG);project_load(0);
 REQUIRE("engine above 31 survives project",trk[0].eng_req==ENGI_KW_ADD);REQUIRE("FMini slot 199 survives project",trk[1].eng_req==ENGI_FMINI&&trk[1].p[P_E6]*128+trk[1].p[P_E7]==199);
 song.master_q12=4096;trk[0].p[P_AMODE]=0;trk[0].p[P_MUTE]=0;trk[0].p[P_LEVEL]=100;
 int32_t audio[CTL*2];long long energy=0;for(unsigned k=0;k<40;k++)mix_block(audio,CTL);
 song.sel=0;kb_note[0]=60;key_on(0,&trk[0]);for(unsigned k=0;k<100;k++){mix_block(audio,CTL);for(unsigned j=0;j<CTL*2;j++)energy+=audio[j]<0?-audio[j]:audio[j];}REQUIRE("keyboard reaches audio mixer",energy>100);key_off(0,&trk[0]);
 static uint16_t a[CV_MAX];track_t *t=&trk[0];t->engine=t->eng_req=ENGI_CS;
 memset(t->v,0,sizeof t->v);t->nheld=1;t->held[0]=60;
 palette_set(0);ui_prefs&=~PREF_ANIM_OFF;
 cv_begin(240,146,T_BG);jw_draw(t,ENGI_CS,100,0x12345678,16,16,208,94,T_TEXT);memcpy(a,cv_px,sizeof a);
 t->held[1]=84;t->nheld=2;
 cv_begin(240,146,T_BG);jw_draw(t,ENGI_CS,100,0x12345678,16,16,208,94,T_TEXT);
 REQUIRE("held chord changes the fencers' guard",memcmp(a,cv_px,240*146*2));
 static const unsigned scenes[]={ENGI_CS,ENGI_HYDRA,ENGI_ACID};
 for(unsigned k=0;k<NELEM(scenes);k++){
  t->engine=t->eng_req=scenes[k];t->m_env=20000;
  cv_begin(240,146,T_BG);six_instrument(t);
  unsigned marks=0;
  for(unsigned x=16;x<224;x++)marks+=cv_px[113*240+x]!=swap16(T_BG);
  REQUIRE("engine scene has no shared row of lights",!marks);
 }
 t->eng_req=ENGI_CS;
 t->engine=ENGI_FMINI;t->m_env=0;six_vis_note_at[0]=0;song.playing=1;
 cv_begin(240,146,T_BG);six_machine_mark(t,16,16,208,94);
 memcpy(a,cv_px,sizeof a);
 fm1_ms+=80u;
 cv_begin(240,146,T_BG);six_machine_mark(t,16,16,208,94);
 REQUIRE("skate pavement scrolls during rests",memcmp(a+106*240,cv_px+106*240,4*240*2));
 song.playing=0;t->engine=ENGI_CS;
 ui_prefs|=PREF_ANIM_OFF;
 cv_begin(240,146,T_BG);jw_draw(t,ENGI_CS,100,0x12345678,16,16,208,94,T_TEXT);memcpy(a,cv_px,sizeof a);
 t->seq_idx=7;t->nheld=1;
 cv_begin(240,146,T_BG);jw_draw(t,ENGI_CS,20,0x87654321,16,16,208,94,T_TEXT);
 REQUIRE("ANIM OFF freezes scene",!memcmp(a,cv_px,240*146*2));
 palette_set(0);REQUIRE("DARK background matches Rhythmer RGB565 black",T_BG==0u);
 REQUIRE("themes only DARK and LIGHT",NPALETTES==2&&!strcmp(menu_vname(MI_THEME,0),"DARK")&&!strcmp(menu_vname(MI_THEME,1),"LIGHT"));
 REQUIRE("known light theme persists, retired ones resolve to dark",palette_from_stored(75)==1&&palette_from_stored(76)==0&&palette_from_stored(77)==0);
 ui_prefs&=~PREF_ANIM_OFF;t->nheld=4;t->held[2]=76;t->held[3]=82;
 for(unsigned theme=0;theme<2;theme++){
  menu_put(MI_THEME,theme);
  for(unsigned k=0;k<NENG_SHOWN;k++){
   unsigned e=ENGINE_ORDER[k];if(e==ENGI_EMPTY)continue;
   for(unsigned j=0;j<8;j++)t->p[P_E0+j]=ENGINES[e]->edit[j].max;
   for(unsigned f=0;f<8;f++){
    fm1_ms=500+f*39;six_vis_note_at[0]=501;six_vis_note_vel[0]=127;
    cv_begin(240,146,T_BG);jw_draw(t,e,127,f*0x20000000u,16,16,208,94,T_TEXT);
    REQUIRE("scene completes inside primitive budget",jw.ops<480u);
    REQUIRE("scene never leaks to top or bottom of the canvas",cv_px[240*12+120]==swap16(T_BG)&&cv_px[240*115+120]==swap16(T_BG));
   }
  }
 }
 printf("JAZZY integration failures=%u\n",errors);return !!errors;
}

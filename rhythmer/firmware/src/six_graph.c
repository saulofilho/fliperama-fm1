/* SPDX-License-Identifier: GPL-3.0-only
 * SIX monochrome instrument surface. Integer geometry only, UI thread only.
 * Motion comes from sequencer position and parameter values, never a free-running creature.
 */
#include "jazzy_world.c"
#define six_machine_glyph jw_draw
static int six_visual_level(const track_t *t);
static void six_mixer(void){
 int h=graph_h(),base=h-27,top=23;
 for(unsigned k=0;k<NTRK;k++){
  const track_t *t=&trk[k];int x=6+(int)k*38,sel=k==song.sel;
  int on=six_track_enabled(k),mute=t->p[P_MUTE],lv=six_visual_level(t),span=base-top-14;
  uint16_t ink=on&&!mute?(sel?T_THEME:T_TEXT):T_DIM;
  char n[3]={'T',(char)('1'+k),0};
  cv_rect(x,1,34,h-5,sel?T_TINT:T_RAISE);
  cv_text_in(x,5,34,&AF_X,n,ink,sel?T_TINT:T_RAISE);
  cv_rect(x+8,top,2,span,T_LINE);
  cv_rect(x+19,top,8,span,T_BG);
  int meter=lv*span/127;
  if(meter)cv_rect(x+20,top+span-meter,6,meter,lv>109?T_ACCENT:T_K(0));
  for(int j=1;j<5;j++)cv_rect(x+20,top+j*span/5,6,1,T_BG);
  int y=top+span-3-clamp(t->p[P_LEVEL],0,127)*(span-4)/127;
  cv_rect(x+3,y,12,4,ink);cv_rect(x+5,y+1,8,1,sel?T_BG:T_RAISE);
  cv_rect(x+6,base-6,22,1,T_LINE);
  cv_rect(x+15+clamp(t->p[P_PAN],-64,63)*9/64,base-8,4,5,ink);
  cv_text_in(x,base,34,&AF_X,!on?"OFF":mute?"MUTE":six_kind_label(t->eng_req),ink,sel?T_TINT:T_RAISE);
  for(int j=0;j<4;j++)cv_rect(x+5+j*7,h-11,4,3,on&&t->p[P_DIST+j]>0?T_K(j):T_LINE);
 }
}
static void six_graph_vectors(const track_t *t){
 const page_t *pg=cur_page();int base=graph_h()-25;
 /* A compact readout for the four current parameters. No synthetic motion. */
 for(unsigned k=0;k<4;k++){
  int16_t *value=0;const param_desc_t *d=page_desc(pg,k,&value);int x=10+58*(int)k;
  if(!d||!value||d->max<=d->min)continue;
  int q=clamp(*value,d->min,d->max)-d->min,span=(base-18)*q/(d->max-d->min);
  cv_rect(x,12,46,base-12,T_RAISE);
  cv_rect(x+16,18,13,base-18,T_BG);
  if(span)cv_rect(x+16,base-span,13,span,T_K(k));
  for(int j=1;j<=3;j++)cv_rect(x+14,18+j*(base-18)/4,17,1,T_LINE);
  cv_text_in(x,base+5,46,&AF_X,d->label,T_TEXT,T_BG);
 }
 (void)t;
}
static void six_graph_matrix(const track_t *t){
 cv_text_in(8,0,224,&AF_X,"MODULATION / 4 SLOTS",T_TEXT,T_BG);
 for(unsigned k=0;k<4;k++){
  int y=22+(int)k*28;unsigned src=t->p[P_M1SRC+3*k],dst=t->p[P_M1DST+3*k];
  char n[2]={(char)('1'+k),0},a[12];fmt_int(a,t->p[P_M1AMT+3*k]);
  cv_text_in(8,y,12,&AF_X,n,T_TEXT,T_BG);cv_text_in(24,y,55,&AF_X,N_MSRC[src<MS_N?src:0],T_TEXT,T_BG);
  cv_line_t(81,y+5,108,y+5,T_DIM,1);
  int value=src==MS_LFO?mulq15(t->lfo_val,t->lfo_fade):src==MS_LFO2?mulq15(t->lfo2_val,t->lfo2_fade):0;
  cv_rect(94+value/4096,y+3,3,5,T_TEXT);
  cv_text_in(114,y,68,&AF_X,N_MDST[dst<MD_N?dst:0],T_TEXT,T_BG);cv_text_r(232,y,&AF_X,a,T_TEXT,T_BG);
  if(k==mod_ui_slot)cv_frame(3,y-4,234,20,T_TEXT);
 }
}
/* JIANT's animation sites, with original geometric machine marks in place of organisms. */
static int six_note_punch(const track_t *t){
 unsigned k=(unsigned)(t-trk),at=six_vis_note_at[k];
 if(!at||(ui_prefs&PREF_ANIM_OFF))return 0;
 unsigned age=fm1_ms-(at-1u);if(age>=280u)return 0;
 return (int)((280u-age)*(48u+six_vis_note_vel[k]*79u/127u)/280u);
}
static int six_visual_level(const track_t *t){
 unsigned ti=(unsigned)(t-trk);if(!six_track_enabled(ti)||t->p[P_MUTE])return 0;
 int en=clamp(t->m_env/258,0,127);
 for(unsigned v=0;v<NVOICE;v++)if(t->v[v].active){int e=clamp(t->v[v].env>>17,0,127);if(e>en)en=e;}
 if(t->engine==ENGI_BREAK&&jungle_playing())en=64+((jungle_current_step()&1)?0:63);
 ;
 int punch=six_note_punch(t);if(punch>en)en=punch;
 return en;
}
static void six_dot_background(int h){
 for(int y=8;y<h-4;y+=12)for(int x=8;x<236;x+=12)cv_rect(x,y,1,1,T_DIM);
}
/* Shared geometry for the live instrument and startup. A NULL track uses a
 * bounded visual preview: startup precedes track/kit/sample initialization. */

static void six_machine_mark(const track_t *t,int x,int y,int w,int h){
 int en=(ui_prefs&PREF_ANIM_OFF)?0:six_visual_level(t);
 /* No additional redraws: use the existing graph governor and idle cache. */
 unsigned ph=(en||(song.playing&&(t->engine==ENGI_FMINI||t->engine==ENGI_ANALOG)))?fm1_ms*0x002e0000u:0u;
 if(t->engine==ENGI_BREAK&&en){
  unsigned warp=(unsigned)clamp(t->p[P_E2],0,127);
  ph=fm1_ms*0x00180000u+((six_break_ticks&191u)<<24)+(warp<<19);
 }
 six_machine_glyph(t,t->engine,en,ph,x,y,w,h,T_TEXT);
}
/* Main workstation: machine identity + six channels + the selected track's 16-step rail. */
static void six_home_cards(void){
 const track_t *t=TSEL;char n[5]={'0',(char)('1'+song.sel),0},name[40],line[40]="P0";
 cv_rect(6,3,27,27,T_TEXT);cv_text_in(6,8,27,&AF_S,n,T_BG,T_TEXT);
 cv_text_in(40,2,104,&AF_S,trk_engp(t)->name,T_TEXT,T_BG);
 sound_name(t,name);cv_clip_text(40,21,&AF_X,name,T_TEXT,T_BG,104);
 line[1]=(char)('1'+song_cur);line[2]=' ';line[3]='/';line[4]=' ';line[5]=live.cur>=0?(char)('A'+live.cur):'-';line[6]=' ';line[7]='/';line[8]=' ';line[9]=0;
 fmt_int(line+9,t->p[P_SLEN]);str_cpy(line+str_len(line)," STEPS",sizeof line-str_len(line));
 char pg[5]={' ',(char)('1'+t->seq_idx/16),'/',(char)('0'+((unsigned)clamp(t->p[P_SLEN],1,64)+15u)/16u),0};str_cpy(line+str_len(line),pg,sizeof line-str_len(line));
 cv_text_in(8,43,140,&AF_X,line,T_DIM,T_BG);
 if(six_track_enabled(song.sel))six_machine_mark(t,158,4,70,38);
 else cv_text_in(158,18,70,&AF_S,"OFF",T_DIM,T_BG);
 cv_line_t(6,58,234,58,T_TEXT,1);
 for(unsigned k=0;k<6;k++){
  int x=6+(int)k*38,selected=k==song.sel,en=six_visual_level(&trk[k]);char num[3]={'0',(char)('1'+k),0};
  if(selected)cv_rect(x,64,34,12,T_TEXT);
  cv_text_in(x,66,34,&AF_X,num,selected?T_BG:T_TEXT,selected?T_TEXT:T_BG);
  cv_text_in(x,81,34,&AF_X,!six_track_enabled(k)?"OFF":trk[k].p[P_MUTE]?"MUT":six_kind_label(trk[k].eng_req),T_TEXT,T_BG);
  if(six_track_enabled(k)&&!trk[k].p[P_MUTE])six_machine_mark(&trk[k],x+2,93,30,24);
  else six_machine_glyph(0,trk[k].engine,0,0,x+2,93,30,24,T_DIM);
  /* Sound level remains a small rail below the shared machine symbol. */
  cv_rect(x+3,121,28,1,T_DIM);
  if(en)cv_rect(x+3,121,1+en*27/127,1,T_TEXT);
  if(k<5)cv_line_t(x+36,65,x+36,122,T_DIM,1);
 }
 unsigned base=(t->seq_idx/16)*16;
 for(unsigned j=0;j<16;j++){
  const step_t *st=&seq_steps(t)[base+j];int x=8+(int)j*14,on=st->time!=ST_REST&&(st->n||st->hit||st->time==ST_TIE);
  if(on)cv_rect(x+2,129,7,5,T_TEXT);else cv_rect(x+5,131,1,1,T_DIM);
  if((j&3u)==0)cv_rect(x,139,1,1,T_TEXT);
  if(song.playing&&six_track_enabled(song.sel)&&!t->p[P_MUTE]&&j==(t->seq_idx&15u))cv_frame(x,126,11,11,T_TEXT);
 }
}
static void six_home_routes(void){
 for(unsigned m=0;m<4;m++){
  int y=6+(int)m*32;char n[3]={'M',(char)('1'+m),0},v[12];fmt_int(v,macro_v[m]);
  cv_text_in(8,y,22,&AF_X,n,T_TEXT,T_BG);cv_frame(34,y,62,9,T_DIM);cv_rect(35,y+1,macro_v[m]*60/127,7,T_TEXT);cv_text_in(102,y,26,&AF_X,v,T_TEXT,T_BG);
  unsigned count=0;for(unsigned k=0;k<6;k++)for(unsigned z=0;z<4;z++)if(trk[k].p[P_M1SRC+z*3]==(int)(MS_M1+m)&&trk[k].p[P_M1DST+z*3]&&trk[k].p[P_M1AMT+z*3]){
   char t[3]={'T',(char)('1'+k),0};int xx=136+(int)(count++%5)*19;cv_line_t(96,y+4,xx,y+4,T_DIM,1);cv_text_in(xx,y+11,18,&AF_X,t,T_TEXT,T_BG);
  }
  if(!count)cv_text_in(136,y,94,&AF_X,"NO ROUTE",T_DIM,T_BG);
 }
}
static void six_instrument(const track_t *t){
 char name[40];sound_name(t,name);
 cv_text_in(8,0,224,&AF_X,trk_engp(t)->name,T_TEXT,T_BG);
 six_machine_mark(t,16,16,208,94);
 cv_text_in(8,124,224,&AF_X,name,T_TEXT,T_BG);
}
static const char *six_break_event_name(unsigned n){
 static const char *const name[19]={"1/4 REPEAT","BUILD","STRETCH","ECHO","1/8 REPEAT","1/8 DOWN","1/8 UP","1/8 SHRINK","1/16 REPEAT","1/16 DOWN","1/16 UP","1/16 SHRINK","1/32 REPEAT","1/32 DOWN","1/32 UP","1/32 SHRINK","SOURCE A / AMEN","SOURCE B / THINK","STRAIGHT RETURN"};
 return n<16?"SLICE TRIGGER":name[n<35?n-16:18];
}
static void six_graph_break_step(void){
 const track_t *t=TSEL;unsigned len=(unsigned)clamp(t->p[P_SLEN],1,64),base=(ui.cursor/16)*16;
 six_dot_background(graph_h());
 cv_text_in(8,7,224,&AF_X,t->p[P_LN0]?"CHOP / STEP EVENTS":"LOOP + PERFORMANCE EVENTS",T_TEXT,T_BG);
 for(unsigned j=0;j<16&&base+j<len;j++){
  const step_t *s=&t->step[base+j];int x=8+(j%8)*28,y=32+(j/8)*34;char b[8];
  if(s->time==ST_TIE)str_cpy(b,"=",8);else if(s->time==ST_REST||!s->n)str_cpy(b,".",8);else note_name(b,s->note[0]);
  uint16_t bg=(j&1)?T_BG:T_RAISE;cv_rect(x,y,25,25,bg);cv_frame(x,y,25,25,base+j==ui.cursor?T_TEXT:T_LINE);cv_text_in(x,y+7,25,&AF_X,b,s->n?T_THEME:T_DIM,bg);
  if(song.playing&&base+j==t->seq_idx)cv_rect(x,y+27,25,2,T_ACCENT);
 }
 const step_t *s=&t->step[ui.cursor%len];
 cv_text_in(8,108,224,&AF_X,s->time==ST_REST?"REST":s->time==ST_TIE?"TIE / KEEP HELD EFFECT":six_break_event_name(s->note[0]),T_TEXT,T_BG);
 cv_text_in(8,128,224,&AF_X,"HOLD SEQ: STRAIGHT / MUT / RND",T_DIM,T_BG);
}

static void six_graph_surface(const track_t *t,const page_t *pg){
 if(!ui.home&&pg->graph==GR_BROWSE){graph_lz_presets();return;}
 if(!ui.home&&pg->fam==FAM_EDIT&&!ui.confirm&&trk_eng(TSEL)==ENGI_EMPTY){
  cv_text_in(8,24,224,&AF_S,"EMPTY TRACK",T_TEXT,T_BG);
  cv_text_in(8,50,224,&AF_X,"SELECT AN ENGINE",T_TEXT,T_BG);
  cv_text_in(8,72,224,&AF_X,"PRESETS / ENG",T_DIM,T_BG);return;
 }

 cv_oy=0;cv_bg=T_BG;
 if(ui.confirm==CF_DICE_ALL){gen_panel();return;}
 if(ui.home){if(home_set())six_home_routes();else if(home_level())six_instrument(t);else six_home_cards();return;}
 
 if(pg->graph==GR_TRK){six_mixer();return;}
 if(pg->graph==GR_SIXSTEP){six_graph_break_step();return;}
 if(pg->graph==GR_SIXBRK||pg->graph==GR_SIXBRKSEQ){six_graph_break();return;}
 if(pg->graph==GR_LIBCLEAR){
  cv_text_in(8,20,224,&AF_M,"CLEAR LIBRARY",T_TEXT,T_BG);
  cv_text_in(8,51,224,&AF_X,"K3: SELECTED STORED SECTION",T_TEXT,T_BG);
  cv_text_in(8,69,224,&AF_X,"K4: PROJECT SECTIONS A-D",T_TEXT,T_BG);
  cv_text_in(8,91,224,&AF_X,"RELATED SONG ROWS ALSO CLEAR",T_DIM,T_BG);
  cv_text_in(8,118,224,&AF_X,"OCT+ REVIEW / OCT- CANCEL",T_TEXT,T_BG);return;
 }
 if (pg->graph == GR_DGEN) {
  unsigned len = (unsigned)clamp(t->p[P_SLEN], 1, NSTEP);
  for (unsigned i = 0; i < len; i++) {
   const step_t *step = &t->step[i];
   unsigned x = 9 + i % 16 * 14, y = 32 + i / 16 * 19;
   int lit = step->time == ST_NOTE && step->n;
   cv_rect(x + 2, y + 4, lit ? 8 : 2, lit ? 6 : 2, lit ? (step->flags & SF_ACCENT ? VAL(2) : T_TEXT) : T_DIM);
   if (song.playing && i == t->seq_idx) cv_frame(x, y, 12, 14, VAL(1));
  }
  cv_text_in(8,118,224,&AF_X,"OCT+ GENERATE  /  OCT- UNDO",T_TEXT,T_BG);
  return;
 }
 if(six_gen_page()){six_graph_gen();return;}
 if(six_return_page()){
  cv_text_in(8,18,224,&AF_S,"STRAIGHT BREAK",T_TEXT,T_BG);
  cv_text_in(8,48,224,&AF_X,"VAR / WARP -> 0",T_TEXT,T_BG);
  cv_text_in(8,72,224,&AF_X,"SOURCE / CHOPS / FX KEPT",T_TEXT,T_BG);
  cv_text_in(8,104,224,&AF_X,"OCT+ APPLY / OCT- BACK",T_TEXT,T_BG);return;
 }
 if(seq_roll_view(pg)){graph_roll(t,T_THEME);seq_overlay(t,pg);return;}
 if(lz_on()&&lz_fam()==LZ_FX){graph_fx_lz(t,pg);return;}
 if(pg->fam==FAM_FX){
  if(pg->scope==SC_TRACK)fxg_sends(t,8,11,224,graph_h()-19);
  else fxg_mod(fx_mod_of(ui.page),8,12,224,graph_h()-23);
  return;
 }
 if(pg->fam==FAM_ENV&&graph_env_lz(t,pg))return;
 if(pg->graph==GR_MSEQ||pg->id[0]==P_MSDIV){graph_mseq(t,T_TEXT);return;}
 if(pg->scope==SC_ENGINE){six_instrument(t);return;}
 if(pg->fam==FAM_EDIT){
  if(pg->id[0]==P_FTYPE){graph_filter_lz(t,pg);return;}
  if(pg->id[0]==P_VOICE||pg->id[0]==P_ALLOC){graph_voice_lz(t,pg);return;}
  if(pg->graph==GR_FOCUS){graph_focus_lz(t);return;}
  if(pg->graph==GR_MORPH){graph_morph(t);return;}
  if(pg->graph==GR_FMOP||pg->graph==GR_FMOP2||pg->graph==GR_FMENV){six_instrument(t);return;}
 }
 switch(pg->graph){
 case GR_ADSR:graph_adsr(t,T_THEME);return;
 case GR_PATS:graph_pats();return;
 case GR_LIVE:graph_live();return;
 default:break;
 }
 /* Keep operational library/FX/key/automation diagrams; organic engine art is unreachable. */
 if(lz_on()&&lz_fam()==LZ_SAVE){graph_save_lz(pg);return;}
 if(lz_on()&&lz_fam()==LZ_KEY&&graph_key_lz(t,pg))return;
 if(pg->graph==GR_MOD){six_graph_matrix(t);return;}
 if(pg->graph==GR_LFO){graph_lfo(t,T_TEXT);cv_text_in(8,graph_h()-12,224,&AF_X,lfo_page_second(pg)?"ROUTE: LFO 2 DEST / MOD":"ROUTE: LFO 1 DEST / MOD",T_TEXT,T_BG);return;}
 if(pg->id[0]==P_LD_PIT||pg->id[0]==ID_L2DEST){graph_lfodest(t,pg);return;}
 if(!graph_tech(t,pg))six_graph_vectors(t);
}

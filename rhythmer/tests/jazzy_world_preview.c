/* Render the opt-in world design in the actual FM-1 UI at 240x240.
 * Four deterministic scenes isolate idle, knob, chord and rhythmic behavior. */
#define UI_TEST_NO_MAIN 1
#include "jazzy_host.h"
static void save_screen(const char *root,unsigned theme,unsigned e,unsigned mode,unsigned frame){
 char path[1024];snprintf(path,sizeof path,"%s/%u-%02u-%u-%02u.ppm",root,theme,e,mode,frame);
 FILE *o=fopen(path,"wb");if(!o)exit(2);
 fprintf(o,"P6\n240 240\n255\n");
 unsigned char rgb[240*240*3];
 for(unsigned i=0;i<240*240;i++){unsigned p=swap16(host_screen[i]);rgb[3*i]=(p>>11)*255/31;rgb[3*i+1]=((p>>5)&63)*255/63;rgb[3*i+2]=(p&31)*255/31;}
 if(fwrite(rgb,1,sizeof rgb,o)!=sizeof rgb||fclose(o))exit(2);
}
static void chord_pose(track_t *t,unsigned n,unsigned vel,unsigned age){
 memset(t->v,0,sizeof t->v);t->nheld=n;
 static const uint8_t chord[]={48,55,60,64};
 for(unsigned k=0;k<n;k++){
  t->held[k]=n==1?60:chord[k];
  if(k==0||ENGINES[t->engine]->poly!=1){t->v[k].active=t->v[k].gate=1;t->v[k].note=t->held[k];}
 }
 t->m_env=n?vel*214:0;
 six_vis_note_at[0]=n?fm1_ms-age+1:0;six_vis_note_vel[0]=n?vel:0;
}
static void utility_preview(const char *root,unsigned theme){
 track_t *t=&trk[0];song.sel=0;ui.home=ui.layer=0;trk_live=6;
 const uint8_t engine[]={ENGI_S1,ENGI_ACID,ENGI_CZ,ENGI_JUNO,ENGI_HORT,ENGI_BREAK};
 for(int k=0;k<NTRK;k++){
  track_t *a=&trk[k];set_engine_of(a,engine[k]);apply_preset_to(a,0);a->engine=a->eng_req=engine[k];
  a->p[P_LEVEL]=111-k*12;a->p[P_MUTE]=k==4;a->p[P_PAN]=k*19-36;
  a->p[P_DIST]=k>3?57:0;a->p[P_CHOR]=k&1?33:0;a->p[P_DLY]=k%3?50:0;a->p[P_REV]=33;
 }
 t->p[P_SLEN]=16;
 for(unsigned k=0;k<16;k++){
  step_t *st=&t->step[k];memset(st,0,sizeof *st);
  if(k==3||k==7||k==11||k==14){st->time=ST_REST;continue;}
  st->time=ST_NOTE;st->n=(k%4==0)?3:1;
  st->note[0]=48+(k*5)%17;st->note[1]=st->note[0]+4;st->note[2]=st->note[0]+7;st->vel=90;
  if(k%4==0)st->flags=SF_ACCENT;
 }
 song.g[G_DTIME]=10;song.g[G_DFDBK]=101;song.g[G_DMIX]=97;song.g[G_DPING]=1;
 song.g[G_RSIZE]=98;song.g[G_RTYPE]=1;song.g[G_CDEPTH]=85;song.g[G_CRATE]=43;
 static const char *const labels[]={"MIXER","STEP","DLY","REVERB","PHASER","FX"};
 for(unsigned u=0;u<7;u++){
  ui.menu=u==6;
  if(u<6){unsigned pg=0;while(pg<NPAGES&&strcmp(PAGES[pg].title,labels[u]))pg++;if(pg==NPAGES)exit(3);ui.page=pg;}
  ui.bank=0;ui.cursor=8;
  for(unsigned f=0;f<24;f++){
   fm1_ms=7000+f*80;song.playing=u<6;
   t->seq_idx=(f/2)&15;scope_w=512;
   for(int k=0;k<NTRK;k++)trk[k].m_env=(10+(f*31+k*39)%111)*240;
   for(int k=0;k<512;k++)scope_buf[k]=(int16_t)(osc_sine((unsigned)k*0x06000000u)*(1+(int)(f%8))/8);
   ui.force=1;ui_draw();save_screen(root,theme,90+u,3,f);
  }
 }
 ui.menu=0;trk_live=4;
}
/* Native screens driven by real note-ons, releases and the mixer clock. */
static void controls_preview(const char *root)
{
    static const uint8_t pages[][2] = {
        {SEC_ENV, 2}, {SEC_FX, 4}, {SEC_FX, 7}, {SEC_FX, 9},
        {SEC_LFO, 1}, {SEC_FX, 2}, {SEC_ENV, 0}, {SEC_ENV, 4}, {SEC_LFO, 6},
        {SEC_FX, 3}
    };
    track_t *t = &trk[0];
    set_engine_of(t, ENGI_ANALOG);
    apply_preset_to(t, 0);
    t->engine = t->eng_req;
    t->p[P_MUTE] = 0;
    t->p[P_ATK] = 71;
    t->p[P_DEC] = 63;
    t->p[P_SUS] = 63;
    t->p[P_REL] = 82;
    t->p[P_DLY] = 84;
    t->p[P_REV] = 71;
    t->p[P_CHOR] = 77;
    t->p[P_APDEP] = 91;
    t->p[P_APSYNC] = 0;
    t->p[P_APRATE] = 72;
    t->p[P_LEVEL] = 110;
    t->p[P_LRATE] = 49;
    t->p[P_LFADE] = 0;
    t->p[P_L2WAVE] = 4;
    song.g[G_DTIME] = 5;
    song.g[G_DFDBK] = 81;
    song.g[G_DMIX] = 106;
    song.g[G_DPING] = 1;
    song.g[G_RSIZE] = 89;
    song.g[G_RPRE] = 96;
    song.g[G_CDEPTH] = 89;
    song.g[G_CSTER] = 46;
    for (unsigned theme = 0; theme < NPALETTES; theme++) {
        settings.palette = theme;
        palette_set(theme);
        for (unsigned page = 0; page < NELEM(pages); page++) {
            trk_all_off(t);
            nav_go(pages[page][0], pages[page][1], 1);
            ui.stage = 3;
            for (unsigned frame = 0; frame < 36; frame++) {
                fm1_ms += 80;
                if (page == 2) {
                    song.g[G_RTYPE] = frame < 18 ? 0 : 4;
                    song.g[G_RPRE] = frame < 18 ? 96 : -12;
                }
                if (frame == 1 || frame == 19)
                    trk_note_on(t, frame == 1 ? 60 : 64, 105);
                if (frame == 13 || frame == 29)
                    trk_note_off(t, frame == 13 ? 60 : 64);
                int32_t samples[2 * CTL];
                for (unsigned k = 0; k < FS * 80u / (1000u * CTL); k++) {
                    mix_block(samples, CTL);
                    for (unsigned j = 0; j < CTL; j++)
                        scope_buf[scope_w++ & (SCOPE_N - 1u)] = (int16_t)clamp(samples[2 * j], -32768, 32767);
                }
                ui.force = 1;
                ui_draw();
                save_screen(root, theme, 70 + page, 3, frame);
            }
        }
    }
}

int main(int argc,char **argv){
 if(argc<2||argc>3)return 2;
 ui_power_on();fm6_init();power_on_parts();ux.skin=JAZZY_LAYOUT;ux.style=JAZZY_STYLE;ui.home=0;ui.confirm=0;song.g[G_BPM]=120;
 if (argc == 3 && !strcmp(argv[2], "--controls")) { controls_preview(argv[1]); return 0; }
 int audit=argc==3&&!strcmp(argv[2],"--audit");
 int gallery=argc==3&&!strcmp(argv[2],"--gallery");
 static const unsigned frames[]={24,25,32,40};
 track_t *t=&trk[0];
 for(unsigned theme=0;theme<(gallery?1u:NPALETTES);theme++){
 settings.palette=theme;palette_set(theme);
 for(unsigned j=0;j<NENG_SHOWN;j++){
  unsigned e=ENGINE_ORDER[j];if(e==ENGI_EMPTY||(argc==3&&!audit&&!gallery&&e!=(unsigned)atoi(argv[2])))continue;
  set_engine_of(t,e);apply_preset_to(t,0);t->engine=t->eng_req=e;t->p[P_MUTE]=0;
  unsigned k=JW_KNOB[jazzy_object(e)];const param_desc_t *p=&ENGINES[e]->edit[k];
  for(unsigned pg=0;pg<NPAGES;pg++)if(PAGES[pg].scope==SC_ENGINE&&PAGES[pg].graph==GR_NONE&&PAGES[pg].id[0]==(k<4?P_E0:P_E4)){ui.page=pg;break;}
  ui.hot_col=k&3;
  const int original=t->p[P_E0+k];
  if(!theme)printf("%u\t%u\t%d\t%d\t%s\n",e,k,p->min,p->max,p->label);
  unsigned gallery_mode=e==ENGI_CS||e==ENGI_HYDRA?2u:3u;
  for(unsigned m=0;m<4;m++)for(unsigned f=0;f<frames[m];f++){
   if(gallery&&m!=gallery_mode)continue;
   static const unsigned sample[]={0,24,16,1};
   if(audit&&f!=sample[m])continue;
   fm1_ms=2000+f*50;
   t->p[P_E0+k]=original;t->seq_idx=0;t->slide_glide=0;song.playing=0;
   if(m==0)chord_pose(t,0,0,400);
   if(m==1){
    /* Lock time while the knob moves; every pixel difference comes from the knob. */
    fm1_ms=2410;t->p[P_E0+k]=p->min+((p->max-p->min)*(int)f+12)/24;chord_pose(t,1,98,100);
   }
   if(m==2){
    unsigned count=f<4||f>=28?0:f<10||f>=23?1:f<15?3:4;
    unsigned start=f<10?4:f<15?10:f<23?15:23;
    chord_pose(t,count,90,count?(f-start)*50:0);
   }
   if(m==3){
    static const uint8_t hits[]={112,0,76,118,0,90,127,0};
    unsigned step=f/5,vel=hits[step];
    song.playing=1;t->seq_idx=step*2+(f%5>=3);t->slide_glide=e==ENGI_ACID&&(step==2||step==5);
    chord_pose(t,vel?1:0,vel,(f%5)*58);
   }
   ui.force=1;ui_draw();save_screen(argv[1],theme,e,m,f);
  }
 }
 if(argc==2)utility_preview(argv[1],theme);
 }
 return 0;
}

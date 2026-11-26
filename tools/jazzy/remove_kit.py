from pathlib import Path
import re
R=Path(__file__).resolve().parents[2];S=R/'rhythmer/firmware/src'
def remove_fn(s,name):
 m=re.search(r'^static[^\n]*\b'+name+r'\s*\([^;]*?\)\s*\{',s,re.M)
 if not m:return s
 start=m.start();i=m.end();depth=1
 while depth:
  if s[i]=='{':depth+=1
  elif s[i]=='}':depth-=1
  i+=1
 return s[:start]+s[i:]
# Detached Hortator kernels, with exactly ONE hit state per track. No kit allocator.
s=(S/'drum_md.c').read_text();a=s.index('static uint32_t pow2_q16');b=s.index('/* The extra model bit')
s='''/* GPL-3.0-only. Hortator individual-hit adapter; no JIANT kit. */
#include "md_states.h"
typedef struct {md_state_t ms;uint32_t t;int32_t rng,last;uint8_t active,vel,kind;} md_voice_t;
typedef struct {int16_t p[8];int8_t nt;} md_track_t;
static md_voice_t hort_hit[NTRK];
'''+s[a:b]
s+='''
static void hort_reset(void){memset(hort_hit,0,sizeof hort_hit);}
static void hort_on(track_t *t,voice_t *v){
 md_voice_t *h=&hort_hit[t-trk];memset(h,0,sizeof *h);h->active=1;h->vel=v->vel;h->rng=0x2545f491u+(unsigned)(t-trk)*977u+v->age;
 unsigned kind=(unsigned)t->p[P_E0]%MD_NMODEL;h->kind=kind;
 const md_model_t *model=&MD_MODELS[kind];md_track_t ctx;memcpy(ctx.p,model->def,sizeof ctx.p);ctx.nt=0;
 ctx.p[0]=clamp(t->p[P_E1],-24,24);ctx.p[1]=t->p[P_E2];
 for(unsigned k=0;k<3;k++)ctx.p[model->ctl[k]]=t->p[P_E3+k];
 model->trigger(&ctx,h);
}
static void hort_render(track_t *t,voice_t *v,int32_t *out,uint32_t n,const vmod_t *m){
 (void)v;md_voice_t *h=&hort_hit[t-trk];int32_t tmp[CTL]={0};if(n>CTL)n=CTL;
 if(h->active)MD_MODELS[h->kind].render(0,h,tmp,n);
 for(unsigned i=0;i<n;i++)out[i]+=mulq15(tmp[i],amp_at(m,i));
}
static int hort_done(track_t *t,voice_t *v){(void)v;return !hort_hit[t-trk].active;}
'''
# Presets retain each native single sound, mapped to eight host controls.
models=re.findall(r'\{"([^"\n]+)",\{[^\n]+?\},\{([^}]+)\},\{([^}]+)\},',s)
s+='static const preset_t HORT_PRESETS[]={\n'
for i,(name,defs,ctls) in enumerate(models):
 d=list(map(int,defs.split(',')));c=list(map(int,ctls.split(',')))
 s+=' {"HT '+name+'",{'+','.join(map(str,[i,d[0],d[1],d[c[0]],d[c[1]],d[c[2]],0,0]))+'},{0,60,127,0},0,1|TAG(DRUM)},\n'
s+='};\n'
s+='''static const engine_t ENG_HORT={.name="HORTATOR",.page_title={"SINGLE HIT","TIMBRE"},
.edit={{"SOUND",F_INT,0,MD_NMODEL-1,3,0,0},{"TUNE",F_SEMI,-24,24,0,0,0},{"DECAY",F_INT,0,127,64,0,0},{"COLOR",F_INT,0,127,64,0,0},{"BODY",F_INT,0,127,64,0,0},{"EDGE",F_INT,0,127,64,0,0},{"-",F_INT,0,0,0,0,0},{"-",F_INT,0,0,0,0,0}},
.presets=HORT_PRESETS,.npresets=sizeof HORT_PRESETS/sizeof HORT_PRESETS[0],.poly=1,.oneshot=1,.ownenv=1,.note_on=hort_on,.render=hort_render,.done=hort_done,.knob={P_E1,P_E2,P_E3,P_E4}};
'''
(S/'eng_hort.c').write_text(s)
# Minimal reserved layout definitions ONLY. No voice, sound, kit tables or audio.
(S/'legacy_kit_wire.h').write_text('''/* GPL-3.0-only. Reserved pre-JAZZY project byte layout. No kit DSP or sounds. */
enum { DV_KICK,DV_SNARE,DV_CLAP,DV_HATC,DV_HATO,DV_TOM,DV_RIM,DV_BELL,DV_NLANE };
enum { DXP_PITCH,DXP_PMOD,DXP_DECAY,DXP_NOISE,DXP_COLOR,DXP_N };
enum { XM_RATE,XM_DPTH,XM_SHPE,XM_RAND };
enum { DXG_KICK=1,DXG_SNARE=2,DXG_HAT=4,DXG_PERC=8,DXG_ALL=15 };
#define DXM_ALL 0xFF0Fu
#define DXM_LANE(l) (1u<<(8u+(l)))
#define DXS_BUS(s) ((unsigned)(s)>>6)
#define DXS_AMT(s) ((int)(s)&63)
#define DX_LAY_L(s) ((unsigned)(s)&15)
#define DX_LAY_FB(s) ((unsigned)(s)>>4)
#define DX_TONE_BP(s) ((unsigned)(s)&15)
#define DX_TONE_FB(s) ((unsigned)(s)>>4)
typedef struct {uint8_t mode,a[5],b[5];} dx_lane_t;
static dx_lane_t dx_kit[8];
static const dx_lane_t DX_KIT_DEF[8]={{0}};
static const uint8_t DX_LAY_DEF[8]={0};
static uint8_t dx_md_hi,dx_tone,dx_hands,dx_lay[8],dx_snd[8],dx_mot[4];
static uint16_t dx_mute;
static int16_t clip_eff,pnch_eff;
static volatile uint8_t duck_hit;
static void dx_mute_set(uint32_t v){(void)v;dx_mute=0;}
static void dx_kit_load(uint32_t v){(void)v;memset(dx_kit,0,sizeof dx_kit);}
static int dx_kit_ok(const dx_lane_t *k){(void)k;return 1;}
static int md_ext_ok(const dx_lane_t *k,unsigned h){(void)k;(void)h;return 1;}
static int drum_track(const track_t *t){(void)t;return 0;}
''')
# FM6 no longer shares anything with a kit.
p=S/'eng_fm6.c';s=p.read_text();s=re.sub(r'_Static_assert\(sizeof\(fm6_note_t\).*?;','static fm6_note_t jazzy_fm6[NTRK][4];',s);s=s.replace('    md_memory((unsigned)(t-trk),ENGI_FM6);','').replace('&md_shared[t-trk][i].fm6','&jazzy_fm6[t-trk][i]');p.write_text(s)
p=S/'engines.c';s=p.read_text();s=re.sub(r'#include "eng_drum.c"[^\n]*','#include "legacy_kit_wire.h"',s).replace('#include "eng_jazzy.c"','#include "eng_jazzy.c"\n#include "eng_hort.c"\n#include "eng_frodhes.c"');p.write_text(s)
p=S/'six_engines.c';s=p.read_text().replace(' drum_md_reset();',' memset(jazzy_fm6,0,sizeof jazzy_fm6);');p.write_text(s)
# Remove kit-only audio processing, buffers and transient privilege.
p=S/'voice.c';s=p.read_text();s=remove_fn(s,'tf_sides');s=re.sub(r'static int32_t tf_side\[NTRK\]\[4\];[^\n]*','',s)
s=re.sub(r'        if \(\(dx_xon & 1u\).*?\n\s*tf_sides\([^;]*;','',s,flags=re.S)
s=re.sub(r'    if \(t->engine == ENGI_DRUM\) \{\n        voice_t \*v = drum_reuse.*?\n    }','',s,flags=re.S)
s=s.replace('(t->engine == ENGI_DRUM && drum_muted(note))','0')
s=re.sub(r'    dx_xon = 0;[^\n]*\n\s*if \([^\n]+\)\n\s*drum_side_begin\([^;]+;','',s)
s=re.sub(r'    if \([^\n]*ENG_DRUM[^\n]*\)\n\s*drum_bus\([^;]+;','',s)
s=remove_fn(s,'drum_attack').replace('drum_attack(t,v)','0').replace('drum_attack(&trk[p],v)','0')
p.write_text(s)
p=S/'audio.c';s=p.read_text().replace('!drum_attack(&trk[p],v) && ','').replace('!drum_attack(t,v) &&','');p.write_text(s)
p=S/'fx.c';s=p.read_text();s=remove_fn(s,'drum_mix');s=remove_fn(s,'dx_mot_block');s=re.sub(r'    dx_mot_block\(n\);[^\n]*','',s)
s=re.sub(r'        if \(dx_xon[^\n]+\n(?:[^\n]*\n){0,4}?\s*drum_mix\([^;]*;\n\s*}', '',s)
p.write_text(s)
p=S/'seq.c';s=p.read_text();s=re.sub(r'static int drum_track\([^\n]+\n','',s);p.write_text(s)
for f in ['eng_drum.c','drumx_voice.c','drum_md.c','md_factory_kits.h','md_factory_map.json','md_model_map.json','ui_dx.c']:
 (S/f).unlink()
# GEN: four melodic slots, no drum role or kit creation.
p=S/'gen.c';s=p.read_text();a=s.index('    /* the orchestration:');b=s.index('    gen_scale_page();',a)
s=s[:a]+'''    /* Four voices of composition: bass, chords, arpeggio, melody. */
    { static const uint8_t roles[4]={RL_BASS,RL_PAD,RL_ARP,RL_LEAD};
      drums=0;dr=NTRK;gs.amt[GP_DRUMS]=0;
      for(k=0;k<RL_N;k++){gs.act[k]=0;gs.trk_of[k]=NTRK;}
      next=0;
      for(k=six_gen_next(0);k<SIX_GEN_TRACKS;k=six_gen_next(k+1u)){
        unsigned r=roles[next++%4u];gs.role[k]=r;gs.act[r]=1;gs.trk_of[r]=k;
      }
      for(k=GP_BASS;k<GP_N;k++)if(!gs.amt[k])gs.amt[k]=60;
    }
'''+s[b:];s=s.replace('if (r == RL_DRUM) gen_kit(t);\n        else {','{')
# Remove gen_kit function and its factory sound banks after first compile pass.
s=remove_fn(s,'gen_kit');s=s.replace('ALL: 6 TRACKS / SPECIAL KEPT','4 SYNTHS / SPECIAL KEPT').replace('ALL: 4 TRACKS / OTHERS KEPT','4 SYNTHS / OTHERS KEPT');p.write_text(s)
p=S/'voice.c';s=p.read_text().replace('while(k<trk_live&&!((six_gen_work_mask>>k)&1u))','while(k<4u&&!((six_gen_work_mask>>k)&1u))').replace('return k<trk_live?k:NTRK;','return k<4u&&k<trk_live?k:NTRK;').replace('while(k<trk_live&&(trk[k].eng_req==ENGI_ACID||trk[k].eng_req==ENGI_BREAK))','while(k<4u&&(trk[k].eng_req==ENGI_ACID||trk[k].eng_req==ENGI_BREAK||trk[k].eng_req==ENGI_HORT))');p.write_text(s)
# Remove former kit detail renderer completely.
for p in S.glob('*.c'):
 s=p.read_text().replace('#include "ui_dx.c"','')
 p.write_text(s)

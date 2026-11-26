#!/usr/bin/env python3
"""Pinned S1Vave / Saadet DSP extraction; host workflow and storage stay JAZZY's."""
from pathlib import Path
import re, json, importlib.util, subprocess, sys, shutil, struct
R=Path(__file__).resolve().parents[2]; U=R/'upstream'; D=R/'rhythmer/firmware/jazzy'
B=Path('/Volumes/SSD/Development/BuildCache/jazzy-engine-review/probe')
B.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(R/'rhythmer/tools')); import lz4blk
def put(n,s): (D/n).write_text(s)
def array(n,v,typ='uint8_t',cols=64):
 return 'static const '+typ+' '+n+'[]={\n'+'\n'.join(','.join(map(str,v[i:i+cols]))+',' for i in range(0,len(v),cols))+'\n};\n'
def fn(s,name):
 m=re.search(r'^static[^\n]*\b'+name+r'\([^;]*?\)\s*(?:/\*.*?\*/\s*)?\{',s,re.M|re.S)
 assert m,name
 i=s.index('{',m.start());j=i+1;depth=1
 while depth:
  depth+=int(s[j]=='{')-int(s[j]=='}');j+=1
 return s[m.start():j]+'\n'
# S1 uses Ober's exact oscillator / coefficient / first-stage helpers. Only its
# saturated second filter stage and DRAW/CHOP/pink extensions are extracted.
s=(U/'s1vave/firmware/src/obv_dsp.h').read_text()
ob=(U/'obervave/firmware/src/obv_dsp.h').read_text()
def norm(x):return re.sub(r'\s+','',re.sub(r'/\*.*?\*/|//[^\n]*','',x,flags=re.S))
for name in ('osc_naive','osc_event','osc_step','svf_coef','svf_step','xorshift','softclip'):
 assert norm(fn(s,name))==norm(fn(ob,name)), 'shared native DSP drift: '+name
for name in ('SVF_G','TANH_Q15'):
 ts=[(U/repo/'firmware/gen/obv_tables.h').read_text() for repo in ('obervave','s1vave')]
 arrays=[re.findall(r'-?\d+',re.search(name+r'\[[^]]+\]\s*=\s*\{(.*?)\}',t,re.S)[1]) for t in ts]
 assert arrays[0]==arrays[1], 'shared native table drift: '+name
ext=s[s.index('/* ---- Roland S-1 Extensions:'):]
lp=fn(s,'svf_lp')
for a,b in [('svf_coef_t','jo_svf_coef_t'),('svf_state_t','jo_svf_state_t'),('softclip','jo_softclip')]:lp=re.sub(r'\b'+a+r'\b',b,lp)
lp=lp.replace('svf_lp','js_svf_lp')
names=re.findall(r'^static[^\n]*\b(\w+)\s*\(',ext,re.M)+['pink_noise_t','DRAW_OFF','DRAW_STEP','DRAW_SLOPE']
ext=re.sub(r'\b('+'|'.join(names)+r')\b',lambda m:'js_'+m[0],ext)
put('s1_dsp.h','/* SPDX-License-Identifier: GPL-3.0-only\n * Copyright (C) 2026 Andrew GG. S1Vave native extensions; shared Ober DSP remains in jo_dsp.h. */\n'+lp+ext)
tab=(U/'s1vave/firmware/gen/obv_tables.h').read_text()
curve=re.search(r'static const uint16_t CUTOFF_TAPER_WARM\[128\].*?\};',tab,re.S)[0]
put('s1_curve.h',curve.replace('CUTOFF_TAPER_WARM','JS_CUTOFF')+'\n')
# Expand factory programs with the source's defaults, retain DRAW/CHOP exactly.
src='''#include <stdint.h>
#include <stdio.h>
#include "'''+str(U/'s1vave/firmware/src/obv_params.h')+'''"
#include "'''+str(U/'s1vave/firmware/src/obv_patches.h')+'''"
int main(void){for(unsigned k=0;k<NFACT;k++){uint8_t p[NPARAM];for(unsigned i=0;i<NPARAM;i++)p[i]=PDEF[i].def;const uint8_t *v=FACTORY[k].set;for(;v[0]!=255;v+=2)p[v[0]]=v[1];printf("%s|",FACTORY[k].name);for(unsigned i=0;i<NPARAM;i++)printf("%u,",p[i]);puts("");}return 0;}
'''
(B/'s1_extract.c').write_text(src);subprocess.run(['clang','-w',str(B/'s1_extract.c'),'-o',str(B/'s1_extract')],check=True)
rows=subprocess.check_output([str(B/'s1_extract')],text=True);(B/'s1-presets.txt').write_text(rows)
w=(U/'s1vave/firmware/src/obv_patches.h').read_text().split('static const fact_wave_t FACT_WAVE[NFACT] = {')[1]
pairs=[(tuple(map(int,re.findall(r'-?\d+',a))),tuple(map(int,re.findall(r'\d+',b)))) for a,b in re.findall(r'\{\s*\{([^}]+)\},\s*\{([^}]+)\}\s*\}',w)]
draw=list(dict.fromkeys(a for a,b in pairs));chop=list(dict.fromkeys(b for a,b in pairs))
put('s1_factory.h',array('JS_DRAW',[x for a in draw for x in a],'int16_t')+array('JS_CHOP',[x for a in chop for x in a],'uint16_t')+array('JS_WAVE',[x for a,b in pairs for x in (draw.index(a),chop.index(b))]))
ep=(U/'s1vave/firmware/src/obv_params.h').read_text().split('enum {',1)[1].split('};',1)[0]
ep=re.sub(r'/\*.*?\*/','',ep,flags=re.S);en={};i=0
for x in ep.split(','):
 x=x.strip()
 if not x:continue
 if '=' in x:x,v=x.split('=');i=int(v.strip().rstrip('u'))
 en[x.strip()]=i;i+=1
cfg=[]
for row in rows.splitlines():
 nm,vals=row.split('|');p=list(map(int,vals.strip(',').split(',')))
 cfg.extend(p[en[k]] for k in ('P_PULSE_LVL','P_SAW_LVL','P_SUB_TYPE','P_NOISE_MODE','P_PWM_SRC','P_DRAW_SW','P_CHOP_COMB','P_KEYTRK','P_FENV_AMT'))
with (D/'s1_factory.h').open('a') as f:f.write(array('JS_CFG',cfg))
# Native HYDRA patch enums and names retain their MPL attribution. No user bank,
# external converter, vendor patches, original scheduler or editor is imported.
s=(U/'saadet/firmware/src/eng_hydra.c').read_text()
shutil.copy2(U/'saadet/firmware/src/hydra_patch.h',D/'hydra_patch.h')
spec=importlib.util.spec_from_file_location('hywaves',U/'saadet/tools/gen_hy_waves.py');wg=importlib.util.module_from_spec(spec);spec.loader.exec_module(wg)
wg.main(str(B/'melodee_hy.h'))
# The independent extractor contains upstream INIT verbatim; recreate it here.
init=s[s.index('static const uint8_t HY_INIT'):s.index('static hy_patch_t *hy_patch_of')]
factory=(U/'saadet/firmware/src/hydra_factory.h').read_text()
f=fn(s,'hy_factory')
ex='#include <stdint.h>\n#include <stdio.h>\n#include <string.h>\n#define NELEM(a) (sizeof(a)/sizeof((a)[0]))\n#define clamp(x,l,h) ((x)<(l)?(l):(x)>(h)?(h):(x))\n#include "melodee_hy.h"\n#include "hydra_patch.h"\n'+init+factory+f+'\nint main(void){for(unsigned i=0;i<HY_FACTORY_N;i++){hy_patch_t p;hy_factory(i,&p);for(unsigned j=0;j<HY_BYTES;j++)printf("%u,",p.raw[j]);puts("");}}\n'
(B/'hydra_patch.h').write_text((D/'hydra_patch.h').read_text());(B/'hy_extract.c').write_text(ex)
subprocess.run(['clang','-w',str(B/'hy_extract.c'),'-o',str(B/'hy_extract')],check=True)
patches=[list(map(int,l.strip(',').split(','))) for l in subprocess.check_output([str(B/'hy_extract')],text=True).splitlines()]
ids=set()
for p in patches:
 for o in (0,14):ids.update(x-1 for x in p[o+2:o+10] if x) if p[o] else ids.add(p[o+1])
 ids.add(p[28])
ids=sorted(ids);assert len(ids)==24
waves=[wg.finish(wg.WAVES[i][1]) for i in ids]
# Lossless byte-plane + modulo delta transform, then LZ4. Decode once at boot,
# never in an audio callback; one immutable RAM table shared by all tracks.
v=[x&65535 for w in waves for x in w];delta=[]
for w in waves:
 last=0
 for x in w:delta.append((x-last)&65535);last=x
raw=bytes(x&255 for x in delta)+bytes(x>>8 for x in delta);packed=lz4blk.compress(raw)
assert lz4blk.decompress(packed)==raw
put('hydra_waves.h',array('JH_WAVE_IDS',ids)+array('JH_WAVE_PACK',packed)+'#define HY_PTS 256u\n')
put('hydra_factory.h','/* MPL-2.0. Saadet factory sounds by Kerem Kilic (Ellic Studio), expanded from pinned source. */\nstatic const hy_patch_t JH_FACTORY[16]={\n'+',\n'.join('{{'+','.join(map(str,p))+'}}' for p in patches)+'\n};\n')
types=s[s.index('typedef struct {'):s.index('/* the wave copies a patch needs:')]
# Keep the entire native voice, including 2x decimators, inside the host union.
voice=types[:types.index('typedef struct {\n    hy_voice_t voice')]
put('hydra_types.h',s[:s.index('#include')]+voice)
base=s[s.index('static inline __attribute__((always_inline)) float hy_clampf'):s.index('/* A heavier sound loaded')]
base=base[:base.index('static void hy_worst')]+base[base.index('static void hy_base'):]
base=base.replace('b->fallback = hy_rows(r) > hy_held((uint32_t)(t - trk));','b->fallback = 0;')
kernel=s[s.index('static float hy_env1'):s.index('/* ------------------------------------------------------------------------------------------- presets')]
kernel=re.sub(r'_Static_assert\(sizeof\(hy_job_t\).*?;','',kernel)
kernel=kernel.replace('hy_voice_t *s = &P->voice[jb->vi];','hy_voice_t *s = jb->voice;').replace('s = &P->voice[jb.vi];','s = jh_voice(t);')
kernel=kernel.replace('typedef struct { hy_part_t *P; uint16_t dk; uint8_t n, vi; hy_blk_t c; }','typedef struct { hy_part_t *P; hy_voice_t *voice; uint16_t dk; uint8_t n, vi; hy_blk_t c; }')
kernel=kernel.replace('jb.P = P;','jb.P = P; jb.voice = jh_voice(t);')
kernel=kernel.replace('P->wave[r->a]','jh_wave(P->tag[r->a])').replace('P->wave[r->b]','jh_wave(P->tag[r->b])').replace('P->wave[b->row3]','jh_wave(P->tag[b->row3])')
kernel=kernel.replace('const float *dither = dith_row(jb->dk);','')
kernel=kernel.replace('dith_cutf_d((y - dc) * amp * c->scale, dither[i])','(int32_t)((y - dc) * amp * c->scale)')
kernel=kernel.replace('v->mvel','v->vel').replace('2.0f * VOICE_FS * AUDIO_ONE','16384.0f')
kernel=kernel.replace(' % HY_SLOTS',' % 1u').replace('section(".audio_text")','section(".text.jh")')
a=kernel.index('    if (audio_batch_active)'); b=kernel.index('\n    { ',a)
kernel=kernel[:a]+kernel[b:]
kernel=kernel.replace('hy_patch_of(t)->raw','jh_patch(t)->raw')
kernel=kernel.replace('static void hy_render(track_t *t, voice_t *v, int32_t *out, uint32_t n, const vmod_t *m)\n{','static void hy_render(track_t *t, voice_t *v, int32_t *out, uint32_t n, const vmod_t *m)\n{\n    if(!jazzy_assets_valid)return;')
put('hydra_core.h',s[:s.index('#include')]+base+kernel)
h=2166136261
for x in struct.pack('<'+str(len(v))+'H',*v):h=((h^x)*16777619)&0xffffffff
put('hydra_expect.h','#define JH_WAVE_EXPECT '+str(h)+'u\n')
manifest={'hydra_wave_fnv':h,'s1_factory_count':len(pairs),'s1_wave_raw_bytes':len(pairs)*40,'s1_wave_dedup_bytes':len(draw)*32+len(chop)*8+len(pairs)*2,'hydra_factory_count':len(patches),'hydra_wave_ids':ids,'hydra_wave_raw_bytes':len(v)*2,'hydra_wave_lossless_bytes':len(packed)}
(R/'expansion-selection.json').write_text(json.dumps(manifest,indent=2)+'\n')
locks=json.loads((U/'commits.json').read_text());locks.update(s1vave='8588da5064fe4e8a0d10fd93be6e68ea50509b8d',saadet='c83b05f5377703c30d649e7f2b39181c371a2a11');(U/'commits.json').write_text(json.dumps(locks,indent=2)+'\n')
for repo in ('s1vave','saadet'):
 dest=D/'licenses'/repo;dest.mkdir(exist_ok=True)
 for f in (U/repo).glob('*'):
  if f.is_file() and any(x in f.name.upper() for x in ('LICENSE','LICENSING','COPYING','TRADEMARK')):shutil.copy2(f,dest/f.name)
print(json.dumps(manifest))

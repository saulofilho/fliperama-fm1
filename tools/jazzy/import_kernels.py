"""Reproducible native DSP extraction. Sources pinned in upstream/commits.json."""
from pathlib import Path
import re,shutil,json,subprocess,hashlib
R=Path(__file__).resolve().parents[2]; U=R/'upstream'; D=R/'rhythmer/firmware/jazzy';D.mkdir(exist_ok=True)
def read(repo,name):return (U/repo/'firmware/src'/name).read_text()
def put(name,s): (D/name).write_text(s)
def namespace(s,prefix,names):
 names=set(names)-{"__attribute__"}
 names.update(re.findall(r"\b(?:int32_t|uint32_t|int|void|float|uint16_t)\s+(\w+)\s*\(",s))
 return re.sub(r'\b('+ '|'.join(map(re.escape,sorted(set(names),key=len,reverse=True)))+r')\b',lambda m:prefix+m[0],s)
def kernel(repo,filename,prefix):
 s=read(repo,filename); table=re.search(r'#include "([^"]*tables.h)"',s)[1]
 tables=(U/repo/'firmware/src'/table)
 if not tables.exists():tables=U/repo/'firmware/gen'/table
 ts=tables.read_text()
 names=re.findall(r'^static[^\n]*?\b(\w+)\s*(?:\(|\[|=)',s,re.M)+re.findall(r'}\s*(\w+)\s*;',s)+re.findall(r'^#define\s+(\w+)',s,re.M)+re.findall(r'^static[^\n]*?\b(\w+)\s*\[',ts,re.M)
 s=s.replace('#include "'+table+'"',ts)
 put(prefix+'dsp.h',namespace(s,prefix,names))
kernel('obervave','obv_dsp.h','jo_');kernel('cs1','cs1_dsp.h','jc_')
for f in ['fm106_osc.h','fm106_vcf.h','fm106_tables.h']:
 p=U/'fm106/firmware/src'/f
 if not p.exists():p=U/'fm106/firmware/gen'/f
 shutil.copy2(p,D/f)
# K-WASUB's complete nine oscillator kernels, no sequencer / sample / FX / drum-kit runtime.
s=(U/'kwasub/source/firmware/src/ksub_dsp.c').read_text();s=s[s.index('static inline int32_t sin32'):s.index('/* ================================================================ envelopes')]
data=(U/'kwasub/source/firmware/src/ksub_data.c').read_text()
tables=(U/'kwasub/source/firmware/gen/ksub_tables.h').read_text()
extra=data[data.index('static const uint16_t RATIO_Q8'):data.index('static const uint16_t FM_R34')];extra+=data[data.index('static const uint16_t FM_R34'):data.index(';',data.index('static const uint16_t FM_R34'))+1]
s='/* GPL-3.0-only. K-WASUB native oscillator kernels; Guizmoh and upstream authors. */\n'+tables+'\n'+re.search(r'enum \{ E_ANALOG[^\n]+',data)[0]+'\n'+extra+'\n'+s
names=re.findall(r'^static[^\n]*?\b(\w+)\s*(?:\(|\[|=)',s,re.M)+['osc_t','oscp_t','growl_t','SYNC_STEP']+re.findall(r'\bE_[A-Z0-9_]+',s)
s=namespace(s,'jk_',names)
# Noise is core-private; track oscillator state remains per voice.
s=s.replace('static uint32_t jk_ks_rng = 0x9E3779B9u;', 'static uint32_t jk_rng_core[2] = {0x9E3779B9u,0x6D2B79F5u};\n#define jk_ks_rng jk_rng_core[MC_CPU() & 1u]')
put('kwasub.h',s+'\n#undef jk_ks_rng\n')
# Melodee TRIO uses the host voice state, without any extra pool.
s=read('melodee','eng_trio.c').replace('tuned_pitch_inc(', 'pitch_inc(')
put('melodee_trio.c',s)
# FMini native oscillators + transistor ladder + contour. Factory patch selected by E7;
# no second sequencer, patch RAM bank, FX, or delayed main-loop loading.
s=read('fmini','eng_fmini.c')
a=s[:s.index('static uint32_t fmini_max')]
a=re.sub(r'#define ENGI_FMINI[^\n]+','',a)
a+=s[s.index('#define FGP('):s.index('/* what a factory')]
a+=s[s.index('typedef struct {',s.index('static uint32_t fmini_max')):s.index('static void fmini_set_patch')]
a+=s[s.index('static void fmini_block'):s.index('/* --------------------------------------------------------------- the engine')]
a=a.replace('m->fine','v->fine').replace(' + glo_tune_c * 237 / 100','')
a=a.replace('static void fmini_block(track_t *t)\n{','static void fmini_block(track_t *t)\n{\n    unsigned slot=(unsigned)clamp(t->p[P_E7],0,199), ti=(unsigned)(t-trk);\n    memcpy(fmini_patch[ti],FMINI_FACTORY[slot],FG_SIZE); fmini_pgen[ti]++;\n    if(!fmini_nst[ti])fmini_nst[ti]=0x2F6E2B1+ti;')
put('fmini.c',a)
for f in ['eng_fmini_filter.h','eng_fmini_presets.h']:shutil.copy2(U/'fmini/firmware/src'/f,D/f)
# Licenses are part of the redistributable source.
for repo in ['melodee','fmini','obervave','fm106','cs1','frodhes','kwasub','hortator']:
 dest=D/'licenses'/repo;dest.mkdir(parents=True,exist_ok=True)
 for f in (U/repo).glob('*'):
  if f.is_file() and any(n in f.name.upper() for n in ['LICENSE','LICENSING','COPYING']):shutil.copy2(f,dest/f.name)
locks=json.loads((U/'commits.json').read_text())
if (U/'kwasub/.git').exists():locks['kwasub']=subprocess.check_output(['git','-C',str(U/'kwasub'),'rev-parse','HEAD'],text=True).strip()
(U/'commits.json').write_text(json.dumps(locks,indent=2))
put('UPSTREAM.json',json.dumps({'commits':locks,'files':{str(f.relative_to(D)):hashlib.sha256(f.read_bytes()).hexdigest() for f in D.glob('*') if f.is_file()}},indent=2))

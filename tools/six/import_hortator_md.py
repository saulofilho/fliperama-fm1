#!/usr/bin/env python3
"""Reproduce the selected MD kernels from the pinned local Hortator snapshot."""
from pathlib import Path
import re,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
SRC=Path('/Volumes/SSD/Development/Toolchains/fm1-six-tooling/hortator-reference/firmware/src')
OUT=ROOT/'rhythmer/firmware/src'
assert subprocess.check_output(['git','-C',str(SRC.parent.parent),'rev-parse','HEAD'],text=True).strip()=='44c9ad4aa57bebf63f412bd552e57143c30b4065','Hortator reference revision changed'
# Each model keeps its own common oscillator/filter scratch inside the union.
common={'kt':{'ph':2,'env':3,'k':3,'f':2,'c':1},'sd':{'ph':3,'inc':3,'f':4},'xt':{'ph':1},'rs':{'ph':1,'inc':1},'cl':{'ph':3,'inc':3},'b2':{'ph':1,'inc':2},'bdefm':{'ph':2}}
types={'kt':'ktrx_t','sd':'sdtrx_t','xt':'xttrx_t','rs':'rstrx_t','cl':'cltrx_t','b2':'b2trx_t','bdefm':'bdefm_t','cp':'cptrx_t','ma':'matrx_t','tm':'trxm_t','cb':'trxcb_t','en':'efmn_t','er':'efmrs_t','cbe':'cbefm_t','hhe':'hhefm_t','cye':'cyefm_t'}
state=(SRC/'dm_state.h').read_text();state=state[:state.index('/* SAMPLE\'s LOOP')]
state=state[state.index('typedef struct { int32_t g, r'):]
# Remove unrelated Plaits state declarations; all MD type dependencies begin at KTRX.
state=state[state.index('typedef struct {                        /* KTRX'):]
text='/* SPDX-License-Identifier: GPL-3.0-only\n * Copyright (C) 2026 Leo Kuroshita, Hugelton Instruments\n * Drum machine fork: 2026 DEADACTIVE\n * Hortator MD state and kernels: 2026 DEADACTIVE.\n * Pinned source: 44c9ad4aa57bebf63f412bd552e57143c30b4065.\n * Rhythmer: union-local common scratch, fixed hit pool and macro adapters. */\n'
text+='typedef struct {int32_t a1,a2,a3,k;} dsvf_t;\n'+state+'\ntypedef union {\n'
for member,typ in types.items():
 fields=' '.join(('dsvf_t' if key=='c' else 'int32_t' if key in ['f','env'] else 'uint32_t')+' '+key+'['+str(n)+'];' for key,n in common.get(member,{}).items())
 text+=' struct {'+typ+' s; '+fields+'} '+member+';\n'
text+='} md_state_t;\n'
(OUT/'md_states.h').write_text(text)
files=[('ktrx','kt'),('sdtrx','sd'),('xttrx','xt'),('trxn',None),('rstrx','rs'),('trxm',None),('trxcb',None),('cltrx','cl'),('b2trx','b2'),('bdefm','bdefm'),('efmn',None),('efmm',None)]
models=[]
for filename,member in files:
 text=(SRC/('dm_'+filename+'.c')).read_text()
 # Descriptors are not compiled: Rhythmer stores compact macros in its existing kit.
 descriptors=re.findall(r'#define DM_(\w+)_DEF \{"([^"]+)"(.*?)(?=\n(?:#define DM_|/\*|static)|\Z)',text,re.S)
 for sym,name,body in descriptors:
  pd=re.findall(r'PD\("([^"]+)",\s*\w+,\s*(-?\d+),\s*(-?\d+),\s*(-?\d+)\)',body)
  fns=re.findall(r'(\w+_trigger),\s*\\?\s*(\w+_render)',body)
  if len(pd)==8 and fns:models.append((name,[p[0] for p in pd],[int(p[3]) for p in pd],*fns[0]))
 lines=text.splitlines(keepends=True); kept=[]; skip=False
 for line in lines:
  if line.startswith('#define DM_') and '_DEF ' in line:skip=True
  if skip:
   skip=line.rstrip().endswith(chr(92));continue
  kept.append(line)
 text=''.join(kept)
 text=re.sub(r'v->ms\.(\w+)\b',lambda m:'v->ms.'+m[1]+'.s',text)
 if member:
  for field in common[member]:text=re.sub(r'v->'+field+r'\b','v->ms.'+member+'.'+field,text)
 (OUT/('md_'+filename+'_kernels.h')).write_text(text)
order=['HHEFM','CBEFM','CYEFM','BDTRX','SDTRX','TMTRX','CGTRX','CPTRX','RSTRX','CBTRX','CHTRX','OHTRX','CYTRX','SHTRX','CLTRX','B2TRX','BDEFM','SDEFM','TMEFM','CPEFM','RSEFM']
lookup={m[0]:m for m in models};assert set(order)==set(lookup),(set(order)-set(lookup))
# Three model-specific controls, plus tune and decay, retain the section codec.
controls=[[4,5,7],[4,5,3],[4,5,2],[2,4,5],[2,3,4],[2,4,5],[2,4,5],[2,3,4],[2,3,4],[2,3,4],[2,3,4],[2,3,4],[2,3,4],[2,3,4],[2,4,3],[2,3,4],[4,5,2],[4,5,2],[4,5,2],[4,5,2],[2,3,4]]
text='/* SPDX-License-Identifier: GPL-3.0-only\n * Adapted Hortator MD factory defaults; original authors retained in kernel files. */\n'
text+='typedef struct {const char *name; const char *label[3]; int16_t def[8]; uint8_t ctl[3]; void (*trigger)(md_track_t*,md_voice_t*); void (*render)(md_track_t*,md_voice_t*,int32_t*,uint32_t);} md_model_t;\nstatic const md_model_t MD_MODELS[]={\n'
for name,ctl in zip(order,controls):
 _,labels,params,trig,render=lookup[name]
 text+=' {"'+name+'",{'+','.join('"'+labels[c]+'"' for c in ctl)+'},{'+','.join(map(str,params))+'},{'+','.join(map(str,ctl))+'},'+trig+','+render+'},\n'
# Extra factory colours retain the hidden controls absent from the five-macro codec.
# Retain the first 32 IDs from the earlier local candidate; append the rest.
variants=['METALHAT','TINHAT','TRASHHAT','TREMHAT','SPITHAT','WIDECLAP','PINGBELL','LONGRIDE','SUBDIRT','LOWCHIME','DARKOPEN']
alias={'KTRX':'BDTRX','XTTRX':'TMTRX','XCTRX':'CGTRX','XTEFM':'TMEFM'}
rows=re.findall(r'\{DM_(\w+), \{([^}]+)\}, "([^"]+)"\}',(SRC/'preset_bank.h').read_text())[:55]
assert len(rows)==55
bank={name:(alias.get(model,model),[int(v) for v in values.split(',')]) for model,values,name in rows}
base=list(range(21));signatures={(name,tuple(lookup[name][2])):i for i,name in enumerate(order)}
def append(name):
 global text
 model,params=bank[name];ix=order.index(model);ctl=controls[ix];kind=len(base);base.append(ix)
 _,labels,_,trig,render=lookup[model]
 text+=' {"'+name[:7]+'",{'+','.join('"'+labels[c]+'"' for c in ctl)+'},{'+','.join(map(str,params))+'},{'+','.join(map(str,ctl))+'},'+trig+','+render+'},\n'
 signatures[(model,tuple(params))]=kind
for name in variants:append(name)
for name,(model,params) in bank.items():
 if (model,tuple(params)) not in signatures:append(name)
assert len(base)==57
soundkind={name:signatures[(model,tuple(params))] for name,(model,params) in bank.items()}
text+='};\n#define MD_NMODEL '+str(len(base))+'u\n'
text+='static unsigned md_base(unsigned k){static const uint8_t b['+str(len(base)-21)+']={'+','.join(map(str,base[21:]))+'};return k<21?k:b[(k-21)%'+str(len(base)-21)+'];}\n'
text+='typedef struct {char name[9];uint8_t kind;} md_sound_t;\nstatic const md_sound_t MD_SOUNDS[]={\n'
for name,kind in soundkind.items():text+=' {"'+name+'",'+str(kind)+'},\n'
text+='};\n#define MD_NSOUND 55u\n'
# A usable closed hat in conventional kits; exotic articulation is explicit in LAB.
kits=[['SUBTHUMP','POPSNARE','WIDECLAP','NOISEHAT','DARKOPEN','SHORTTOM','GRITRIM','PINGBELL'],
      ['FMSUB','TONESNR','BUZZCLAP','NOISEHAT','AIROPEN','LONGTOM','FMRIM','LOWCHIME'],
      ['SUBDIRT','HARDSNAP','ROOMCLAP','NOISEHAT','SIZZLE','GRITCONG','KNOCK','LONGRIDE'],
      ['NOISEZAP','RIMSNARE','RATTLE','TRASHHAT','TREMHAT','RISETOM','FMZAP','GONG'],
      ['ZAPKICK','TONESNR','DEEPBLIP','SPITHAT','SIZZRIDE','GRITTOM','LONGBELL','FMSPLASH']]
kittext='/* Generated Hortator factory colours, GPL-3.0-only. BD SD CP CH OH TM RS CB. */\n'
for ki,kit in enumerate(kits):
 kittext+=' {.lane={\n';hi=0
 for lane,name in enumerate(kit):
  model,params=bank[name];kind=soundkind[name];ctl=controls[order.index(model)]
  if ki<3 and lane==3:params=params.copy();params[1]=min(params[1],12)
  hi|=(kind>>5)<<lane
  q=[max(0,min(127,64+((-1 if params[0]<0 else 1)*((abs(params[0])*4+2)//3)))),params[ctl[0]],params[1],params[ctl[1]],params[ctl[2]]]
  kittext+=' {DX_MD('+str(kind)+'),{'+','.join(map(str,q))+'},{'+','.join(map(str,q))+'}},\n'
 kittext+=' },.lay={0},.snd={0},.md_hi='+str(hi)+'},\n'
(OUT/'md_factory_kits.h').write_text(kittext)
(OUT/'md_models.h').write_text(text)
(OUT/'md_model_map.json').write_text(json.dumps(dict(zip(order,controls)),indent=2)+'\n')
(OUT/'md_factory_map.json').write_text(json.dumps([dict(name=name,kind=soundkind[name],model=model,params=params) for name,(model,params) in bank.items()],indent=2)+'\n')
print('Imported 21 MD kernels, 55 complete factory sounds, 57 parameter articulations; MODERN/CLASSIC excluded.')

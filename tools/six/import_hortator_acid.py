#!/usr/bin/env python3
"""Reproduce the fixed-state Hortator ACID adapter (GPL-3.0-only)."""
from pathlib import Path
import re,subprocess
ROOT=Path(__file__).resolve().parents[2]
SRC=Path('/Volumes/SSD/Development/Toolchains/fm1-six-tooling/hortator-reference/firmware/src/dm_acid.c')
PREFIX='/* Rhythmer adapter. Source: DeadActive/hortator 44c9ad4aa57bebf63f412bd552e57143c30b4065.\n * Original synthesis and constants retained; existing ACID gate/slide sequencer drives it.\n * Q24 helpers are shared with the already imported MD code. No allocation. */\ntypedef struct {int16_t p[8];int32_t pitch16,wow,glide;} ha_track_t;\ntypedef struct {uint32_t t,ph[3],k[3];int32_t env[3],f[4],x[4],last,wow;\n struct {int32_t a1,a2,a3;} c[1];uint8_t active,vel;} ha_voice_t;\nstatic inline int32_t ha_qdiv(int32_t a,int32_t b){return b?(int32_t)(((int64_t)a*QONE)/b):0;}\nstatic int32_t ha_min(int32_t a,int32_t b){return a<b?a:b;}\nstatic uint32_t ha_note_inc(int32_t note){return pitch_inc(clamp(note,0,127)*16);}\nstatic int32_t ha_vel_gain(const ha_voice_t *v){return v->vel*258; /* ownenv leaves velocity to this engine, exactly once. */}\nstatic void ha_env_step(ha_voice_t *v,unsigned i){v->env[i]=mulq16(v->env[i],v->k[i]);}\nstatic void ha_end(ha_voice_t *v){v->active=0;v->last=0;}\n#define P_E0 0\n#define LIFE_A ((uint32_t)FS*11u/2u)\n'
assert subprocess.check_output(['git','-C',str(SRC.parent.parent.parent),'rev-parse','HEAD'],text=True).strip()=='44c9ad4aa57bebf63f412bd552e57143c30b4065','Hortator reference revision changed'
s=SRC.read_text();s=s[:s.index('static const char *const N_ACIDWAVE')]
s=s.replace('acid_','ha_').replace('track_t','ha_track_t').replace('dvoice_t','ha_voice_t')
for a,b in [('qlim','clamp'),('qdiv','ha_qdiv'),('qmin','ha_min'),('qnote_inc','ha_note_inc'),('vel_gain','ha_vel_gain'),('env_step','ha_env_step'),('dm_end','ha_end')]:s=re.sub(r'\b'+a+r'\b',b,s)
s=re.sub(r'\bdk\(', 'md_decay_k(',s)
s=re.sub(r'(static int32_t ha_pitch\([^}]+?\{).*?\n}',r'\1\n    return t->pitch16;\n}',s,flags=re.S)
s=s.replace('d * ACID_GLIDE','d * t->glide')
(ROOT/'rhythmer/firmware/src/hortator_acid.c').write_text(PREFIX+s+'\n#undef P_E0\n#undef LIFE_A\n')
print('Imported Hortator ACID; fixed union state, no allocation.')

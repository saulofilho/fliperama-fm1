#!/usr/bin/env python3
"""Pinned Melodee CZ phase functions and Prophet sample kernel; host scheduling/ENV/FX only."""
from pathlib import Path
import re,math
R=Path(__file__).resolve().parents[2];U=R/'upstream/melodee/firmware/src';D=R/'rhythmer/firmware/jazzy'
(D/'mel_fastmath.h').write_text((U/'x0x/fastmath.h').read_text())
s=(U/'cz_native.c').read_text();notice=s[:s.index('#include')];s=s[s.index('typedef struct { uint32_t wave[2]'):s.index('#if MELODEE_CZ_FAST')]
s=s.replace('(FM6_SIN[i]+(FM6_SIN[i+1u]-FM6_SIN[i])*f)','((float)sine_i((i&1023u)<<22)*(1.0f/32768.0f)+((float)sine_i(((i+1u)&1023u)<<22)-(float)sine_i((i&1023u)<<22))*f*(1.0f/32768.0f))')
(D/'mel_cz_wave.h').write_text(notice+'/* JAZZY: native phase functions; shared host sine, envelopes, scheduler and modulation. */\n'+s)
s=(U/'eng_prophet_test.c').read_text();out=s[:s.index('#include')]
out+='/* JAZZY: native sample kernel, three voices/track, shared host ENV/LFO/FX. Native patch editor/worker removed. */\n#define P5_OVERSAMPLE 1\n'
pp=(U/'prophet_patch.c').read_text();out+=pp[pp.index('enum {'):pp.index('typedef struct {')]
out+=s[s.index('typedef struct { float value;'):s.index('typedef struct { p5_voice_t voice')]
out+=s[s.index('static inline __attribute__((always_inline)) float p5_fast_blep'):s.index('/* Stored knobs')]
out+="/* JAZZY uses the existing Q24 exponential table; avoids a duplicate 2 KiB ROM. */\nstatic inline float p5_pitch_ratio(float x){return (float)fm6_exp2((int32_t)(x*16777216.0f))*(1.0f/16777216.0f);}\n"
out+=s[s.index('/* Four trapezoidal'):s.index('typedef struct {\n    p5_voice_t *voice;')]
out=out.replace('fm_fabsf(x)*128.0f','fm_fabsf(x)*64.0f').replace('a>=1024.0f','a>=512.0f')
out=out.replace('__attribute__((section(".dsp_text")))','').replace('dith_cutf(', 'jp_pcm(')
out='static inline int32_t jp_pcm(float x,uint32_t seed){(void)seed;return (int32_t)fm_clampf(x,-131072.0f,131072.0f);}\n'+out
arr=lambda n,v:'static const float '+n+'['+str(len(v))+']={'+','.join(f'{x:.9e}f' for x in v)+'};\n'
tables=arr('P5_TPT_G',[math.tan(math.pi*(30*(16000/30)**(v/127))/44100)/(1+math.tan(math.pi*(30*(16000/30)**(v/127))/44100)) for v in range(128)])+arr('P5_TANH',[math.tanh(i/64) for i in range(513)])+arr('P5_EXP2',[2**(i/512) for i in range(514)])
(D/'mel_prophet.h').write_text(tables+out)
# Upstream licence referenced by the imported CZ file.
for f in (R/'upstream/melodee').rglob('BSD-3-Clause-uPD933*'):
 (D/'licenses/melodee'/f.name).write_bytes(f.read_bytes())

/* SPDX-License-Identifier: BSD-3-Clause
 * Modifications Copyright (C) 2026 Kerem Kilic (Ellic Studio)
 * Copyright (c) Devin Acker
 * Modifications Copyright (c) 2026 Kerem Kilic (Ellic Studio)
 * License: LICENSES/BSD-3-Clause-uPD933.txt
 * Native CZ-1 tone playback. Parameter encoding: Casio MIDI specification.
 * Chip envelope rate, phase functions and logarithmic DCA law follow the
 * independently documented uPD933 model by Devin Acker (MAME, BSD-3-Clause).
 * See docs/CZ1_SYSEX.md for sources and remaining calibration limits. */
/* JAZZY: native phase functions; shared host sine, envelopes, scheduler and modulation. */
typedef struct { uint32_t wave[2],window; float dcw,pivot,k0,k1; } cz_hw_pd_t;
static __attribute__((noinline)) void cz_native_pd(cz_hw_pd_t *p,uint32_t word,float dcw)
{
    p->wave[0]=(word>>13)&7u;p->wave[1]=word&512u?(word>>10)&7u:p->wave[0];
    p->window=(word>>6)&7u;p->dcw=fm_clampf(dcw,0.0f,1023.0f);
    p->pivot=1024.0f-p->dcw;p->k0=1024.0f/p->pivot;p->k1=1024.0f/(2048.0f-p->pivot);
}
static __attribute__((noinline)) float cz_native_wave(const cz_hw_pd_t *b,uint32_t ph,uint32_t toggle)
{
    float pos=(float)ph*(2048.0f/4294967296.0f),half=pos>=1024.0f?pos-1024.0f:pos;
    float pivot=b->pivot,phase=0.0f,window=0.0f;
    switch(b->wave[toggle&1u]){
    case 0:phase=pos<pivot?pos*b->k0:1024.0f+(pos-pivot)*b->k1;break;
    case 1:phase=(half<pivot?half*b->k0:1024.0f)+(pos>=1024.0f?1024.0f:0.0f);break;
    case 2:phase=pos<pivot*2.0f?pos*b->k0:2048.0f;break;
    case 3:return 0.0f;
    case 4:phase=pos<pivot?pos*b->k0*2.0f:(pos-pivot)*b->k1*2.0f;break;
    case 5:phase=pos<1024.0f?pos:pos<pivot+1024.0f?1024.0f+half*b->k0:2048.0f;break;
    case 6:phase=pos*(1.0f+b->dcw*(1.0f/64.0f));break;
    default:phase=half<pivot?half*b->k0:2048.0f;break;
    }
    if(phase>=2048.0f)phase-=(float)(uint32_t)(phase*(1.0f/2048.0f))*2048.0f;
    switch(b->window){
    case 0:break;
    case 1:window=pos;break;
    case 2:window=pos<1024.0f?2048.0f-half*2.0f:half*2.0f;break;
    case 3:if(pos>=1024.0f)window=half*2.0f;break;
    case 4:window=pos<1024.0f?pos*2.0f:2048.0f;break;
    default:window=(1024.0f-half)*2.0f;break;
    }
    /* The normalized sine table is shared with FM6. Interpolate its cosine
     * quadrant in float: no chip-phase or PCM truncation before the mixer. */
    float x=phase*0.5f+256.0f;uint32_t i=(uint32_t)x;float f=x-(float)i;
    i&=1023u;
    float carrier=1.0f-((float)sine_i((i&1023u)<<22)*(1.0f/32768.0f)+((float)sine_i(((i+1u)&1023u)<<22)-(float)sine_i((i&1023u)<<22))*f*(1.0f/32768.0f));
    return carrier*(1.0f-window*(1.0f/2048.0f))-1.0f;
}

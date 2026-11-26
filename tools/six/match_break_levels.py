#!/usr/bin/env python3
"""Offline, circular look-ahead peak control for the corrected two-bar Think.
No real-time DSP, new RAM, time/pitch changes, or source replacement. Amen stays exact.
"""
import argparse, hashlib, json, math, shutil
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, convolve1d
from scipy.signal import resample_poly
from import_loop import build, unpack

def rms(x): return float(np.sqrt(np.mean(x*x)))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def control(x, gain, ceiling):
    # Minimum over a wider window, followed by a nonnegative unit-sum Hann,
    # guarantees g[i] <= ceiling/abs(x[i]) while smoothing the gain. Circular
    # padding prevents a different gain/release at the two-bar loop boundary.
    required=np.minimum(1.0,ceiling/np.maximum(np.abs(x*gain),1e-12))
    window=np.hanning(161);window/=window.sum()   # 2.5 ms at 64 kHz
    lower=minimum_filter1d(required,size=321,mode='wrap')
    envelope=convolve1d(lower,window,mode='wrap')
    return x*gain*envelope, envelope

def run(source,out):
    if source.resolve()==out.resolve():raise ValueError('Preserve original sample assets; choose another output directory')
    out.mkdir(parents=True,exist_ok=True)
    for f in source.iterdir():
        if f.is_file():shutil.copy2(f,out/f.name)
    manifest=json.loads((source/'break-samples.json').read_text())
    sr,a=wavfile.read(source/'amen-160.wav');rate,b=wavfile.read(source/'think-160.wav')
    assert sr==rate==16000 and a.shape==b.shape==(48000,)
    a=a.astype(float)/32768;b=b.astype(float)/32768
    # 0.5 dB below Amen: leave headroom rather than force exact crest factor.
    target=rms(a)*10**(-0.5/20)
    hi=resample_poly(b,4,1,padtype='wrap')
    ceiling=10**(-1.5/20);lo,high=1.0,10**(9/20)
    for _ in range(28):
        gain=(lo+high)/2;y,env=control(hi,gain,ceiling)
        if rms(resample_poly(y,1,4,padtype='wrap'))<target:lo=gain
        else:high=gain
    gain=high;y,env=control(hi,gain,ceiling)
    y=resample_poly(y,1,4,padtype='wrap')
    # Keep the exact existing splice silences after the FIR round trip.
    y[b==0]=0
    pcm=np.rint(y*32767).astype(np.int16)
    wavfile.write(out/'think-160.wav',16000,pcm)
    header,data=build(out/'think-160.wav','THINKDRM')
    decoded=np.asarray(unpack(data),dtype=np.int16)
    true_peak=float(np.max(np.abs(resample_poly(decoded.astype(float)/32768,4,1,padtype='wrap'))))
    if true_peak>10**(-1/20):raise ValueError('True peak exceeds -1 dBFS; refuse sample')
    for ext,raw in (('.hdr',header),('.bin',data),('.slot',header+bytes(32)+data+b'\xff'*(81920-512-len(data)))):
        (out/('think-160'+ext)).write_bytes(raw)
    wavfile.write(out/'think-160-preview.wav',16000,decoded)
    wavfile.write(out/'think-160-repeat.wav',16000,np.tile(decoded,4))
    result={'source_slot_sha256':sha(source/'think-160.slot'),'slot_sha256':sha(out/'think-160.slot'),
            'gain_db':20*math.log10(gain),'max_peak_attenuation_db':-20*math.log10(float(env.min())),
            'amen_rms':rms(a),'think_before_rms':rms(b),'think_after_rms':rms(decoded.astype(float)/32768),
            'rms_difference_db':20*math.log10(rms(decoded.astype(float)/32768)/rms(a)),
            'true_peak_dbfs':20*math.log10(true_peak),'clipped_samples':int(np.count_nonzero(np.abs(decoded.astype(int))>=32767)),
            'frames':48000,'seam_jump_pcm16':int(decoded[0])-int(decoded[-1]),'runtime_cpu_cost_added':0}
    assert result['clipped_samples']==0 and result['seam_jump_pcm16']==0
    record=manifest[1];record['level_match']=result;record['slot_sha256']=result['slot_sha256']
    record['peak_pcm16']=int(np.abs(decoded.astype(int)).max());record['rms_pcm16']=rms(decoded.astype(float))
    record['processing']+='; offline 4x circular look-ahead level match, no hard clipping'
    (out/'break-samples.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'level-match.json').write_text(json.dumps(result,indent=2)+'\n')
    assert sha(out/'amen-160.slot')==sha(source/'amen-160.slot')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    print(json.dumps(run(a.source,a.out),indent=2))

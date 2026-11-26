#!/usr/bin/env python3
"""Assemble the supplied Think drum-only intervals. No network or device writes."""
import argparse, hashlib, json, math, shutil
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly
from import_loop import build, unpack
ROOT=Path(__file__).resolve().parents[2]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(a,b,out):
    out.mkdir(parents=True,exist_ok=True)
    bars=[];sources=[]
    for p in (a,b):
        sr,x=wavfile.read(p)
        assert sr==44100 and x.dtype==np.int16 and x.ndim==2
        y=x.astype(np.float64).mean(axis=1)/32768
        y-=y.mean();g=math.gcd(len(y),24000)
        bars.append(resample_poly(y,24000//g,len(y)//g,window=('kaiser',8.6),padtype='line'))
        sources.append(dict(name=p.name,sha256=digest(p),rate=sr,frames=len(x),source_beats=4))
    # Exclude file 1's pitched tail (beat 4) and file 2's pitched carry-in (beat 1).
    # Preserve two different one-bar phrases, with every downbeat on the grid.
    pieces=[bars[0][:18000].copy(),bars[1][18000:].copy(),bars[0][:6000].copy(),bars[1][6000:].copy()]
    for y in pieces:
        y[:8]*=np.sin(np.linspace(0,np.pi/2,8))**2
        y[-48:]*=np.cos(np.linspace(0,np.pi/2,48))**2
    y=np.concatenate(pieces);assert len(y)==48000
    y*=10**(-1/20)/np.max(np.abs(y));pcm=np.rint(y*32767).astype(np.int16)
    name=out/'think-160';wavfile.write(name.with_suffix('.wav'),16000,pcm)
    h,data=build(name.with_suffix('.wav'),'THINKDRM');decoded=np.array(unpack(data),dtype=np.int16)
    name.with_suffix('.hdr').write_bytes(h);name.with_suffix('.bin').write_bytes(data)
    name.with_suffix('.slot').write_bytes(h+bytes(32)+data+b'\xff'*(81920-512-len(data)))
    wavfile.write(out/'think-160-preview.wav',16000,decoded)
    wavfile.write(out/'think-160-repeat.wav',16000,np.tile(decoded,4))
    boundaries=[0,18000,24000,30000,48000]
    assert all(decoded[i]==0 and decoded[i-1]==0 for i in boundaries[1:-1])
    assert decoded[0]==decoded[-1]==0 and len(data)==72000 and max(abs(decoded.astype(int)))<32767
    record=dict(name='think-160',edit='Think drums / two complementary assembled bars',source='user-supplied Classic Break Pack',sources=sources,
                edit_segments=[dict(source=1,beats=[0,3]),dict(source=2,beats=[3,4]),dict(source=1,beats=[0,1]),dict(source=2,beats=[1,4])],
                excluded_segments=[dict(source=1,beats=[3,4],reason='pitched tail'),dict(source=2,beats=[0,1],reason='pitched carry-in')],
                bars=2,beats=8,bpm=160,output_rate=16000,output_frames=48000,bits=12,payload_bytes=len(data),slot_bytes=81920,slot_sha256=digest(name.with_suffix('.slot')),
                processing='mono, DC removal, per-bar Kaiser anti-alias repitch, drum interval assembly, 0.5ms/3ms edge fades at every splice, common -1dBFS peak, PCM12',
                boundaries=boundaries,seam_jump_pcm16=0,peak_pcm16=int(max(abs(decoded.astype(int)))),rms_pcm16=float(np.sqrt(np.mean(decoded.astype(float)**2))))
    # Retain the existing Amen byte-for-byte and preserve the historical banks.
    old=ROOT/'build/six'
    for suffix in ('.wav','.hdr','.bin','.slot'):
        shutil.copy2(old/('amen-160'+suffix),out/('amen-160'+suffix))
    shutil.copy2(old/'amen-160-repeat.wav',out/'amen-160-repeat.wav')
    amen=json.loads((old/'break-samples.json').read_text())[0]
    assert digest(out/'amen-160.slot')==amen['slot_sha256']
    (out/'break-samples.json').write_text(json.dumps([amen,record],indent=2)+'\n')
    return record
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('first',type=Path);p.add_argument('second',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    print(json.dumps(run(a.first,a.second,a.out),indent=2))

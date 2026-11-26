#!/usr/bin/env python3
"""Reproduce local Amen/Think 2-bar loops. numpy/scipy required; no network or upload.
Think: Rhythm Lab part1 starts on the downbeat. First two bars end immediately
before the next kick attack at ~4.245 s. Keep the live drummer's internal timing;
classic sampler repitch (not pitch-preserving stretch) makes eight beats / 3 s.
Original recordings remain separately licensed from the firmware source.
"""
import argparse, hashlib, json, math
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly
from import_loop import build, unpack
ROOT=Path(__file__).resolve().parents[2]
def prepare(source,name,frames,source_url):
 rate,raw=wavfile.read(source)
 assert raw.dtype.kind=="i", "integer PCM source required"
 x=raw.astype(np.float64)/(2**(raw.dtype.itemsize*8-1))
 if x.ndim==2:x=x.mean(axis=1)
 assert frames<=len(x)
 x=x[:frames];x-=x.mean()
 g=math.gcd(len(x),48000)
 # Wrap padding makes the anti-alias FIR aware of both sides of the loop.
 y=resample_poly(x,48000//g,len(x)//g,window=("kaiser",8.6),padtype="wrap")
 assert len(y)==48000
 # 0.5 ms at the attack, 3 ms tail; keep exact bar length and zero sample seam.
 y[:8]*=np.sin(np.linspace(0,np.pi/2,8))**2
 y[-48:]*=np.cos(np.linspace(0,np.pi/2,48))**2
 y*=10**(-1/20)/np.max(np.abs(y))
 pcm=np.rint(y*32767).astype(np.int16)
 out=ROOT/"build/six"/name;out.parent.mkdir(parents=True,exist_ok=True)
 wavfile.write(out.with_suffix(".wav"),16000,pcm)
 h,d=build(out.with_suffix(".wav"),"AMEN160" if name.startswith("amen") else "THINK160")
 out.with_suffix(".hdr").write_bytes(h);out.with_suffix(".bin").write_bytes(d)
 out.with_suffix(".slot").write_bytes(h+bytes(32)+d+b"\xff"*(81920-512-len(d)))
 decoded=np.array(unpack(d),dtype=np.int16)
 # Preview uses actual quantized samples, four seamless repeats (12 seconds).
 wavfile.write(out.with_name(name+"-repeat").with_suffix(".wav"),16000,np.tile(decoded,4))
 assert len(d)==72000 and decoded[0]==decoded[-1]==0
 assert np.max(np.abs(decoded.astype(np.int32)))<32767
 assert np.sqrt(np.mean(decoded.astype(float)**2))>1000
 qerr=pcm.astype(float)-decoded.astype(float)
 return dict(name=name,source_url=source_url,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),source_rate=rate,source_frames=len(raw),crop_frames=[0,frames],crop_seconds=frames/rate,bars=2,beats=8,bpm=160,output_rate=16000,output_frames=48000,bits=12,payload_bytes=len(d),slot_bytes=81920,slot_sha256=hashlib.sha256(out.with_suffix(".slot").read_bytes()).hexdigest(),processing="mono, DC removal, Kaiser polyphase anti-alias repitch, 0.5ms/3ms endpoint fades, -1dBFS peak, PCM12",pitch_semitones=12*math.log2(frames/rate/3),seam_jump_pcm16=int(decoded[0])-int(decoded[-1]),peak_pcm16=int(np.max(np.abs(decoded.astype(np.int32)))),rms_pcm16=float(np.sqrt(np.mean(decoded.astype(float)**2))),quantization_max_error=float(np.max(abs(qerr))))
def main():
 p=argparse.ArgumentParser();p.add_argument("--amen",type=Path,required=True);p.add_argument("--think",type=Path,required=True);a=p.parse_args()
 results=[prepare(a.amen,"amen-160",144000,"https://github.com/ejtb76/amenity/blob/main/assets/third-party/amen/amen.wav"),prepare(a.think,"think-160",187200,"https://rhythm-lab.com/sstorage/53/2015/03/Lyn%20Collins%20-%20Think%20(part1).wav")]
 (ROOT/"build/six/break-samples.json").write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
if __name__=="__main__":main()

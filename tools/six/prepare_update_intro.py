#!/usr/bin/env python3
"""Add four seconds of original boot sound; preserve approved PCM after it."""
from pathlib import Path
import wave,shutil,hashlib,json,struct
import numpy as np
R=Path(__file__).resolve().parents[2];OLD=R/'outputs/Rhythmer-update-2026-11-07';O=R/'outputs/Rhythmer-update-2026-11-07-v2'
assert O.resolve().is_relative_to(Path('/Volumes/SSD/Development'))
shutil.copytree(OLD/'source',O/'source',dirs_exist_ok=True)
shutil.copy2(OLD/'Rhythmer-Update-Original-Score.wav',O/'Rhythmer-Update-Original-Score.wav')
blob=(OLD/'Rhythmer-Update-Original-Score.wav').read_bytes();pos=12;chunks={}
assert blob[:4]==b'RIFF' and blob[8:12]==b'WAVE'
while pos+8<=len(blob):
 tag=blob[pos:pos+4];n=struct.unpack_from('<I',blob,pos+4)[0];chunks[tag]=blob[pos+8:pos+8+n];pos+=8+n+(n&1)
raw=chunks[b'data'];fmt=chunks[b'fmt '];_,channels,rate,_,align,bits=struct.unpack_from('<HHIIHH',fmt)
assert channels==2 and rate==48000 and bits==24 and align==6
sr=48000;t=np.arange(4*sr)/sr;x=np.zeros((len(t),2))
for j,n in enumerate([50,57,60,64,69]):
 f=440*2**((n-69)/12);env=(1-np.exp(-t/.15))*np.exp(-t/2.8)
 for ch in range(2):x[:,ch]+=.023*np.sin(2*np.pi*f*(1+(ch*2-1)*.0007)*t+j*.8)*env
for at,f in [(.28,660),(1.0,880),(1.8,990),(2.8,1320)]:
 n=int(.22*sr);u=np.arange(n)/sr;y=.035*np.sin(2*np.pi*f*u)*np.exp(-u*28)*np.minimum(u/.002,1)
 i=round(at*sr);x[i:i+n]+=y[:,None]*np.array([.8,1.0])
x*=np.minimum(t/.025,1)[:,None]*np.minimum((4-t)/.2,1)[:,None]
i=(np.clip(x,-.98,.98)*8388607).astype('<i4').view('u1').reshape(-1,4)[:,:3].copy().tobytes()
with wave.open(str(O/'Rhythmer-Update-Score-With-Intro.wav'),'wb') as f:
 f.setnchannels(2);f.setsampwidth(3);f.setframerate(sr);f.writeframes(i+raw)
with wave.open(str(O/'Rhythmer-Update-Score-With-Intro.wav'),'rb') as f:
 f.readframes(4*sr);assert f.readframes(f.getnframes())==raw
(O/'source'/'intro-audio-provenance.json').write_text(json.dumps({'introSeconds':4,'introAudio':'Original suspended ninth pad and four quiet boot tones.','originalScorePCMPreservedAfterIntro':True,'originalScorePCMsha256':hashlib.sha256(raw).hexdigest(),'versionTitle':'v0.1.1-beta3 / FIRMWARE UPDATE / DEVELOPMENT BETA PREVIEW'},indent=2)+'\n')
print('68-second audio ready; original 64-second PCM preserved after the intro.')

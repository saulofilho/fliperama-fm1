#!/usr/bin/env python3
"""Original atmospheric breakbeat score. No third-party audio or artist MIDI."""
from pathlib import Path
import sys,math,wave,json,subprocess
import numpy as np
from scipy.signal import butter,sosfilt,resample_poly
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/Rhythmer-update-2026-11-07'
FF='/Volumes/SSD/Development/Toolchains/rhythmer-motion/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1'
SR=48000;BPM=135;BEAT=60/BPM;DURATION=64
rng=np.random.default_rng(748005)
music=np.zeros((SR*DURATION,2),np.float64);drums=np.zeros_like(music);sfx=np.zeros_like(music)
def filt(x,f,kind='lowpass',order=2):return sosfilt(butter(order,f,btype=kind,fs=SR,output='sos'),x)
def add(bus,y,at,gain=1,pan=0):
 i=round(at*SR)
 if i<0:y=y[-i:];i=0
 n=min(len(y),len(bus)-i)
 if n<=0:return
 if y.ndim==1:y=np.column_stack((y*math.sqrt((1-pan)/2),y*math.sqrt((1+pan)/2)))
 bus[i:i+n]+=y[:n]*gain
def kick():
 t=np.arange(int(.42*SR))/SR;ph=2*np.pi*(47*t+83*.023*(1-np.exp(-t/.023)))
 y=np.sin(ph)*np.exp(-t*12)+filt(rng.normal(size=len(t)),4500,'highpass')*.11*np.exp(-t*240)
 return np.tanh(y*1.3)*np.minimum(t/.0007,1)
def snare(ghost=False):
 t=np.arange(int(.28*SR))/SR;n=filt(rng.normal(size=len(t)),[600,11500],'bandpass')
 tone=np.sin(2*np.pi*182*t)*np.exp(-t*28)+.3*np.sin(2*np.pi*330*t)*np.exp(-t*35)
 y=(n*.33*np.exp(-t*23)+tone*.31)*np.minimum(t/.001,1)
 return filt(y,7000 if ghost else 12500)
def hat(opened=False):
 t=np.arange(int((.19 if opened else .065)*SR))/SR
 y=filt(rng.normal(size=len(t)),[5000,14500],'bandpass')*.24*np.exp(-t*(24 if opened else 95))
 return y*np.minimum(t/.0008,1)
k=kick();s=snare();g=snare(True);h=hat();oh=hat(True)
for bar in range(36):
 at=bar*4*BEAT
 density=0 if bar<2 or bar>=35 else .5 if bar in (2,3,24,25) else 1
 if density:
  ks=[0,6,10] if bar%4 in (0,1) else [0,7,10,14]
  if bar%8==7:ks=[0,6,11]
  for j in ks:add(drums,k,at+j*BEAT/4,.64*density)
  for j in [4,12]:add(drums,s,at+j*BEAT/4+.006,.66*density,(-.06 if j==4 else .07))
  for j in ([3,7,11,15] if bar%2 else [7,10,15]):add(drums,g,at+j*BEAT/4+(.009 if j%2 else -.004),.16*density,(-1 if j%3 else 1)*.28)
  for j in range(16):
   if j%4==0 or rng.random()<.2:continue
   add(drums,oh if j==14 and bar%2 else h,at+j*BEAT/4+(.009 if j%2 else 0),(.26 if j%2 else .4)*density,(-.24 if j%3 else .3))
  if bar%8==7:
   for j in range(4):add(drums,g,at+(14+j*.5)*BEAT/4,.22+j*.045,(-1)**j*.25)
# Long, detuned suspended ninths; original voicings and progression.
chords=[[50,57,60,64,69],[46,53,57,60,65],[48,55,58,62,67],[45,52,55,59,64]]
for phrase in range(9):
 at=phrase*4*4*BEAT;dur=8.6;t=np.arange(round(dur*SR))/SR
 env=(1-np.exp(-t/1.1))*np.exp(-t/5)*np.minimum((dur-t)/1.2,1)
 stereo=[]
 for side in range(2):
  y=np.zeros(len(t))
  for j,note in enumerate(chords[phrase%4]):
   f=440*2**((note-69)/12)*(1+(-1 if side else 1)*(.0007+j*.00011))
   phase=2*np.pi*f*t+.4*np.sin(2*np.pi*(.12+j*.016)*t+j)
   y+=np.sin(phase)+.16*np.sin(phase*2)+.08*np.sin(phase*3)
  y=filt(y,1800)*env*.041
  stereo.append(y)
 add(music,np.column_stack(stereo),at)
# Rounded syncopated sub: D / Bb / C / A, not a borrowed bass line.
for bar in range(4,35):
 root=[38,34,36,33][(bar//4)%4]
 for j,offset,dur in [(0,0,.48),(6,7,.24),(10,0,.5),(15,12,.14)]:
  if bar in (24,25) and j!=0:continue
  t=np.arange(round(dur*SR))/SR;f=440*2**((root+offset-69)/12)
  y=(np.sin(2*np.pi*f*t)+.16*np.sin(2*np.pi*f*2*t))*np.minimum(t/.018,1)*np.minimum((dur-t)/.06,1)*np.exp(-t*1.4)
  add(music,y,bar*4*BEAT+j*BEAT/4,.24)
# Sparse dub plucks with alternating stereo echoes.
for bar in range(2,35):
 for j,n in [(3,0),(11,3)]:
  note=chords[(bar//4)%4][n]+12;dur=.65;t=np.arange(round(dur*SR))/SR;f=440*2**((note-69)/12)
  y=np.sin(2*np.pi*f*t+1.4*np.sin(2*np.pi*f*2*t)*np.exp(-t*9))*np.exp(-t*8)*np.minimum(t/.003,1)
  at=bar*4*BEAT+j*BEAT/4
  for echo in range(5):add(music,filt(y,6000/(1+echo*.6)),at+echo*BEAT*.75,.075*.49**echo,(-1)**echo*.62)
# Air texture and tempo ducking keep the drum transients readable.
air=filt(rng.normal(size=len(music)),[1800,6500],'bandpass')*.005
music[:,0]+=air;music[:,1]+=np.roll(air,911)
t=np.arange(len(music))/SR;duck=1-.18*np.exp(-((t/BEAT)%1)*9);music*=duck[:,None]
for at in [0,9,19,29,40,48,60]:
 d=.55;tt=np.arange(round(d*SR))/SR
 y=np.sin(2*np.pi*(1000*tt+1100*tt**2))*np.exp(-tt*20)*.045
 add(sfx,y,at+.02,1,-.25)
 # quiet reverse granular breath rather than a piercing high sweep
 tt=np.arange(int(.5*SR))/SR;n=filt(rng.normal(size=len(tt)),[700,3800],'bandpass')*(tt/.5)**2*.018
 add(sfx,n,at-.5)
mix=music+drums+sfx
fade=np.minimum(t/1.4,1)*np.minimum((DURATION-t)/1.4,1);mix*=fade[:,None]
mix=np.tanh(mix*1.13);mix*=.83/max(np.max(np.abs(mix)),1e-9)
def wav(path,x):
 with wave.open(str(path),'wb') as f:f.setnchannels(2);f.setsampwidth(4);f.setframerate(SR);f.writeframes((np.clip(x,-.999,.999)*2147483647).astype('<i4').tobytes())
raw=OUT/'source'/'score-unmastered.wav';raw.parent.mkdir(exist_ok=True);wav(raw,mix)
subprocess.run([FF,'-hide_banner','-loglevel','info','-y','-i',str(raw),'-af','loudnorm=I=-16:TP=-2:LRA=9:print_format=json','-ar','48000','-c:a','pcm_s24le',str(OUT/'Rhythmer-Update-Original-Score.wav')],stderr=(OUT/'source'/'audio-master.log').open('w'),check=True)
# A clean two-bar original drum loop for the uploader demonstration.
loop=drums[round(8*BEAT*SR):round(16*BEAT*SR)];loop*=.7/max(abs(loop).max(),1e-9)
wav(OUT/'source'/'JR-Atmos-Break-135BPM-2bars.wav',loop)
(OUT/'source'/'score-provenance.json').write_text(json.dumps({'title':'Rhythmer / Afterimage','bpm':BPM,'seconds':64,'composition':'Original procedurally composed atmospheric breakbeat, sub bass, suspended ninth pads, dub plucks and UI sound effects.','third_party_audio':False,'artist_midi':False,'firmware_audio_demo':False,'note':'Mood reference only; no Skee Mask recording, melody or samples used.'},indent=2)+'\n')
print('Original score and original upload-demo loop ready',flush=True)

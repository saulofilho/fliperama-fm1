#!/usr/bin/env python3
"""PCM12 format properties and reproducible, original synthetic test loops."""
from pathlib import Path
import importlib.util, math, random, struct, tempfile, wave, zlib
root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("six_import",Path(__file__).with_name("import_loop.py"))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
a=[(i%4096-2048)*16 for i in range(48000)]
assert m.unpack(m.pack(a))==a
r=random.Random(1776);a=[r.randint(-32768,32767) for _ in range(48000)]
b=m.unpack(m.pack(a));assert max(abs(x-y) for x,y in zip(a,b))<=15
for n in (0,1,47999,48001):
 try:m.pack([0]*n);raise AssertionError("accepted wrong length")
 except ValueError:pass
out=root/"build/six";out.mkdir(parents=True,exist_ok=True)
for k in range(2):
 samples=[];r=random.Random(900+k)
 for i in range(48000):
  beat=i%6000;t=beat/16000
  x=math.sin(2*math.pi*(52*t+3*(1-math.exp(-t*30))))*math.exp(-t*22)*0.65
  sn=i%12000
  if sn>=6000:x+=(r.random()*2-1)*math.exp(-(sn-6000)/400)*0.32
  x+=(r.random()*2-1)*math.exp(-(i%(1500 if k else 3000))/80)*0.12
  samples.append(max(-32768,min(32767,round(x*28000))))
 path=out/("original-loop-"+str(k+1)+".wav")
 with wave.open(str(path),"wb") as w:
  w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(struct.pack("<48000h",*samples))
 h,d=m.build(path,"SIX_"+str(k+1))
 assert len(h)==480 and len(d)==72000
 assert struct.unpack_from("<I",h,20)[0]==zlib.crc32(d)
 assert struct.unpack_from("<H",h,4)[0]==12
 assert struct.unpack_from("<I",h,48)[0]==23777
 path.with_suffix(".hdr").write_bytes(h);path.with_suffix(".bin").write_bytes(d)
 path.with_suffix(".slot").write_bytes(h+bytes(32)+d+bytes([255])*(81920-512-len(d)))
 assert path.with_suffix(".slot").stat().st_size==81920
with tempfile.TemporaryDirectory(prefix="six-loop-test-") as td:
 for channels,rate,frames in ((2,16000,48000),(1,32000,48000),(1,16000,47999)):
  path=Path(td)/"bad.wav"
  with wave.open(str(path),"wb") as w:
   w.setnchannels(channels);w.setsampwidth(2);w.setframerate(rate);w.writeframes(bytes(channels*2*frames))
  try:m.build(path,"BAD");raise AssertionError("accepted wrong WAV format")
  except ValueError:pass
print("PASS: all 4096 PCM12 values, quantization <=15 PCM16 units, exact length/rate/channels, header CRC, 80 KiB slots")

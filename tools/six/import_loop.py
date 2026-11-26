#!/usr/bin/env python3
"""Pack a 160 BPM, 4/4 two-bar WAV. Input must be 16 kHz mono PCM16, 48000 frames.
No implicit time stretching or downsampling: prepare the source explicitly in a DAW.
Output: X0X-compatible slot framing, format version 12, signed packed 12-bit audio.
"""
import argparse, struct, wave, zlib
from pathlib import Path
def pack(samples):
 if len(samples)!=48000: raise ValueError("requires exactly 48000 frames (3 s)")
 out=bytearray()
 for i in range(0,len(samples),2):
  a=max(-2048,min(2047,round(samples[i]/16)))&4095
  b=max(-2048,min(2047,round(samples[i+1]/16)))&4095
  out+=bytes((a&255,(a>>8)|((b&15)<<4),b>>4))
 return bytes(out)
def unpack(data):
 out=[]
 for i in range(0,len(data),3):
  for v in (data[i]|((data[i+1]&15)<<8),(data[i+1]>>4)|(data[i+2]<<4)):
   out.append(((v^2048)-2048)*16)
 return out
def build(wav,name):
 with wave.open(str(wav),"rb") as w:
  if (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes())!=(1,2,16000,48000):
   raise ValueError("expected mono PCM16 / 16000 Hz / 48000 frames")
  samples=struct.unpack("<48000h",w.readframes(48000))
 data=pack(samples)
 header=bytearray(480)
 struct.pack_into("<IHBB8sIIII",header,0,0x504d5346,12,1,0,name.encode("ascii")[:8],72000,zlib.crc32(data),0,0)
 struct.pack_into("<IIIIIhhBBBB",header,32,0,48000,0,48000,round(16000/44100*65536),60*16,0,0,0,127,1)
 return bytes(header),data
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument("wav",type=Path);a.add_argument("output",type=Path)
 a.add_argument("--name",default="BREAK");args=a.parse_args();h,d=build(args.wav,args.name)
 args.output.with_suffix(".hdr").write_bytes(h);args.output.with_suffix(".bin").write_bytes(d)
 args.output.with_suffix(".slot").write_bytes(h+bytes(32)+d+b"\xff"*(81920-512-len(d)))
 print("72000 B packed PCM12, 512 B header area, 9408 B slot headroom")
if __name__=="__main__": main()

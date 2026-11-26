#!/usr/bin/env python3
"""Upload a prepared .hdr/.bin pair to SIX only. Playback must be stopped.
Uses the X0X/Felucca slot protocol; refuses old firmware. Slot 1 or 2.
"""
from pathlib import Path
import sys,struct,zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fm1_sample_upload import Link,pack7
def main():
 if len(sys.argv)!=3 or sys.argv[1] not in ("1","2"):raise SystemExit("upload_loop.py SLOT PREFIX")
 slot=int(sys.argv[1])-1;p=Path(sys.argv[2]);h=p.with_suffix(".hdr").read_bytes();d=p.with_suffix(".bin").read_bytes()
 if len(h)!=480 or len(d)!=72000 or struct.unpack_from("<H",h,4)[0]!=12 or zlib.crc32(d)!=struct.unpack_from("<I",h,20)[0]:
  raise SystemExit("invalid SIX loop")
 link=Link();info=bytes(link.req(1,[]))
 if not info.startswith(b"SIX "):raise SystemExit("refusing upload: target is not SIX firmware")
 r=link.req(11,[slot])
 if r[-1]:raise SystemExit("stop playback before uploading; begin rejected")
 for i in range(0,len(d),256):
  off=512+i;r=link.req(12,[slot,off&127,(off>>7)&127,(off>>14)&127]+pack7(d[i:i+256]))
  if r[-1]:raise SystemExit(f"write failed at {off}: {r[-1]}")
 r=link.req(13,[slot]+pack7(h))
 if r[-1]:raise SystemExit(f"commit rejected: {r[-1]}")
 print("Loop committed and CRC checked by SIX.")
if __name__=="__main__":main()

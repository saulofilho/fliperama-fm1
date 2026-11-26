#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Upload a prepared PCM12 .hdr/.bin pair to SIX JIANT integration only (USB MIDI)."""
from pathlib import Path
import sys,struct,zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fm1_sample_upload import Link,pack7

def main():
 if len(sys.argv)!=3 or sys.argv[1] not in ("1","2"):raise SystemExit("upload_loop_jiant.py SLOT PREFIX")
 slot=int(sys.argv[1])-1;p=Path(sys.argv[2]);h=p.with_suffix(".hdr").read_bytes();d=p.with_suffix(".bin").read_bytes()
 if len(h)!=480 or len(d)!=72000 or struct.unpack_from("<I",h,48)[0]!=23777 or struct.unpack_from("<H",h,4)[0]!=12 or zlib.crc32(d)!=struct.unpack_from("<I",h,20)[0]:raise SystemExit("invalid SIX PCM12 loop")
 link=Link()
 if not bytes(link.req(80,[])).startswith(b"SIX3\0"):raise SystemExit("target is not the SIX JIANT integration")
 def req(a):
  r=link.req(80,a,8)
  if len(r)!=4 or r[:2]!=a[:2] or r[2]:raise SystemExit(f"upload stopped, reply={r}; stop playback and retry the slot")
 req([1,slot])
 for off in range(0,72000,256):req([2,slot,off&127,(off>>7)&127,(off>>14)&127]+pack7(d[off:off+256]))
 req([3,slot]+pack7(h));print("Loop committed; target CRC checked. Other slot and songs preserved.")
if __name__=="__main__":main()

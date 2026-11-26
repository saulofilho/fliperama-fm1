#!/usr/bin/env python3
"""Replay a private read-only device capture; never connects to hardware."""
from pathlib import Path
import argparse,json,struct,zlib
ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--seed',type=Path,required=True);ap.add_argument('--label',required=True);a=ap.parse_args()
r=Path(__file__).resolve().parents[2];p=r/'tools/six/test_rhythmer_emulator.py';g={'__file__':str(p)}
exec(p.read_text().split("if sys.argv[1:]==['--nav-flex']:")[0],g)
o=g['OUT']
assert a.seed.parent.resolve()==o.resolve(),'Use the seed produced by this firmware build; an old full NOR image boots its old app'
nav=json.loads((o/'six-current-results.json').read_text())
assert nav['firmware_sha256']==g['report']['firmware_sha256'],'Regenerate this candidate’s fresh NOR seed before replay'
data=(a.capture/'device.project').read_bytes();flash=bytearray(a.seed.read_bytes())
for off,kind in ((0x97000,1),(0xe5000,9)):
 h=struct.pack('<IHHIIIII',0x33584953,kind,0,1,len(data),zlib.crc32(data),0xffffffff,0xffffffff);h+=struct.pack('<I',zlib.crc32(h))
 s=bytearray([255])*4096;s[:32]=h;s[256:256+len(data)]=data;flash[off:off+4096]=s
seed=o/('captured-'+a.label+'.flash');seed.write_bytes(flash)
g['run']('captured-'+a.label,18000,'2500:12,2620:12^',seed,True)
g['report']['scope']='Replay of privately captured 123 BPM DRUM / SWAV-SAW / LOFI / WHEEL / ACID / BREAK settings and notes. Emulator evidence; not predicted real-device CPU usage.'
(a.capture/('native-'+a.label+'.json')).write_text(json.dumps(g['report'],indent=2)+'\n')

#!/usr/bin/env python3
"""Exact-image four-track default and explicit six-track opt-in smoke tests."""
from pathlib import Path
import json,struct,zlib
r=Path(__file__).resolve().parents[2];p=r/'tools/six/test_rhythmer_emulator.py'
g={'__file__':str(p)};exec(p.read_text().split("if sys.argv[1:] in (['--upgrade'],['--upgrade-ensemble']):")[0],g)
b=g['OUT'];base=b/'rollback-boot.flash';ram=g['run']('rollback-boot',2800,flash=base,strict=True)
assert 'audio_guard' not in g['SYM']
assert ram[g['SYM']['trk_live']]==4
original=base.read_bytes()
def put(f,off,kind,data):
 h=struct.pack('<IHHIIIII',0x33584953,kind,0,1,len(data),zlib.crc32(data),0xffffffff,0xffffffff);h+=struct.pack('<I',zlib.crc32(h));s=bytearray(b'\xff'*4096);s[:32]=h;s[256:256+len(data)]=data;f[off:off+4096]=s
for live in (4,6):
 f=bytearray(original);cfg=bytearray(f[0xfc100:0xfc100+572]);cfg[52+15*32+15]=0x60+(live==6);cfg[52+15*32+30]|=128;put(f,0xfc000,0,cfg)
 data=(b/'upgrade-owner-all.project').read_bytes()
 for at,kind in ((0x97000,1),(0xe5000,9)):put(f,at,kind,data)
 seed=b/f'rollback-{live}.flash';seed.write_bytes(f)
 ram=g['run'](f'rollback-owner-{live}',8000,'2500:12,2620:12^',seed,True)
 assert ram[g['SYM']['trk_live']]==live
 d=g['report']['runs'][f'rollback-owner-{live}'];assert d['peak_pcm16']>0 and not d['fm1_mc_lost']
g['report']['scope']='Public renderer restored; new boot four tracks, saved owner song in four and explicitly confirmed six; physical listening pending.'
(b/'rollback-emulator-results.json').write_text(json.dumps(g['report'],indent=2)+'\n')
print('Rollback default/explicit-six emulator checks PASS')

#!/usr/bin/env python3
"""Exact-package, full-renderer comparison. No physical-device I/O."""
from pathlib import Path
import json,struct,zlib
r=Path(__file__).resolve().parents[2];p=r/'tools/six/test_rhythmer_emulator.py'
g={'__file__':str(p)};exec(p.read_text().split("if sys.argv[1:] in (['--upgrade'],['--upgrade-ensemble']):")[0],g)
b=g['OUT'];base=b/'minimal-base.flash';g['run']('minimal-boot',2800,flash=base,strict=True)
original=base.read_bytes()
def put(f,off,kind,data):
 h=struct.pack('<IHHIIIII',0x33584953,kind,0,1,len(data),zlib.crc32(data),0xffffffff,0xffffffff);h+=struct.pack('<I',zlib.crc32(h));s=bytearray(b'\xff'*4096);s[:32]=h;s[256:256+len(data)]=data;f[off:off+4096]=s
for case,ms in [('owner-all-short',5500),('owner-all',12000),('owner-no-acid',12000),('owner-no-drum',12000),('lfo2-direct',12000)]:
 f=bytearray(original);cfg=bytearray(f[0xfc100:0xfc100+572]);cfg[52+15*32+30]|=128;put(f,0xfc000,0,cfg)
 project='owner-all' if case.endswith('-short') else case;data=(b/('upgrade-'+project+'.project')).read_bytes()
 for at,kind in [(0x97000,1),(0xe5000,9)]:put(f,at,kind,data)
 seed=b/('minimal-'+case+'.flash');seed.write_bytes(f)
 ram=g['run']('minimal-'+case,ms,'2500:12,2620:12^',seed,True)
 d=g['report']['runs']['minimal-'+case]
 assert d['peak_pcm16']>0 and d['usb_capture_frames']>1000,(case,d)
 assert d['fm1_mc_on']==1 and d['fm1_mc_lost']==0,(case,d)
 assert struct.unpack_from('<I',ram,g['SYM']['audio_guard']+28)[0]==0,'Clock-only substitution is still active'
g['report']['scope']='Full audio renderer; owner song all/without Acid/without Drum, plus six direct LFO2 sources; no physical test'
(b/'minimal-audio-results.json').write_text(json.dumps(g['report'],indent=2)+'\n')
print('Minimal-renderer exact-package comparison recorded')

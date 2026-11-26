#!/usr/bin/env python3
"""Fast, separate MD timing gate; exact current package, no hardware."""
from pathlib import Path
import json,struct,zlib
r=Path(__file__).resolve().parents[2];p=r/'tools/six/test_rhythmer_emulator.py';g={'__file__':str(p)};exec(p.read_text().split("if sys.argv[1:]==['--nav-flex']:")[0],g)
o=g['OUT']
import time
base=o/('md-preflight-boot-'+str(time.time_ns())+'.flash')
g['run']('md-preflight-boot',2200,flash=base)
flash=bytearray(base.read_bytes())
# Copy only the stable preference record, never another application's image.
settings=(o/'six-nav-fixture.flash').read_bytes()[0xfc000:0xfd000]
assert settings[:4]==struct.pack('<I',0x33584953)
flash[0xfc000:0xfd000]=settings
for k,name in enumerate(('amen-160','think-160')):
 loop=(g['SAMPLES']/(name+'.slot')).read_bytes();off=0xa0000+k*0x14000;flash[off:off+len(loop)]=loop
original=bytes(flash)
data=(o/'six-capacity-md-model-9.project').read_bytes()
for off,kind in [(0x97000,1),(0xe5000,9)]:
 h=struct.pack('<IHHIIIII',0x33584953,kind,0,1,len(data),zlib.crc32(data),0xffffffff,0xffffffff);h+=struct.pack('<I',zlib.crc32(h));b=bytearray([255])*4096;b[:32]=h;b[256:256+len(data)]=data;flash[off:off+4096]=b
f=o/'md-preflight.flash';f.write_bytes(flash);g['run']('md-preflight',6000,'2500:12,2620:12^',f,True)
j=g['report'];(o/'md-preflight-results.json').write_text(json.dumps(j,indent=2));d=j['runs']['md-preflight'];assert d['track_engines']==[10]*6
assert d['max_us']<512/44100*1e6 and not any(d[k] for k in ['late','audio_lost','fm1_mc_lost','usb_underruns','usb_overruns','usb_missed']),d
print('MD worst-model preflight PASS')

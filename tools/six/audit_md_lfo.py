#!/usr/bin/env python3
"""Exact-package worst MD with two LFO sources and all FX sends. No hardware."""
from pathlib import Path
import json,struct,zlib
r=Path(__file__).resolve().parents[2];p=r/'tools/six/test_rhythmer_emulator.py';g={'__file__':str(p)};exec(p.read_text().split("if sys.argv[1:]==['--nav-flex']:")[0],g)
o=g['OUT'];assert json.loads((o/'six-current-results.json').read_text())['firmware_sha256']==g['report']['firmware_sha256']
f=bytearray((o/'six-nav-fixture.flash').read_bytes());d=(o/'six-capacity-md-lfo.project').read_bytes()
for off,kind in [(0x97000,1),(0xe5000,9)]:
 h=struct.pack('<IHHIIIII',0x33584953,kind,0,1,len(d),zlib.crc32(d),0xffffffff,0xffffffff);h+=struct.pack('<I',zlib.crc32(h));b=bytearray([255])*4096;b[:32]=h;b[256:256+len(d)]=d;f[off:off+4096]=b
p=o/'md-lfo.flash';p.write_bytes(f);g['run']('md-lfo',6500,'2500:12,2620:12^',p,True)
j=g['report'];j['scope']='Six DRUM tracks, CBTRX, four-note input, 240 BPM, dual LFO sources to pan/cut, DIST/PHASER/DELAY/REVERB sends; enforced MD voice limits.'
(o/'md-lfo-results.json').write_text(json.dumps(j,indent=2));d=j['runs']['md-lfo'];assert d['track_engines']==[10]*6
assert d['max_us']<512/44100*1e6 and not any(d[k] for k in ['late','audio_lost','fm1_mc_lost','usb_underruns','usb_overruns','usb_missed']),d
print('MD dual-LFO / all-FX strict stress PASS')

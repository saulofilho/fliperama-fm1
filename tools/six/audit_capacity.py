#!/usr/bin/env python3
"""Bound exact-package strict-emulator capacity checks. No physical I/O."""
from pathlib import Path
import json,struct,zlib
root=Path(__file__).resolve().parents[2]
source=root/'tools/six/test_rhythmer_emulator.py'
g={'__file__':str(source),'__name__':'rhythmer_capacity'}
exec(source.read_text().split("if sys.argv[1:]==['--nav-flex']:")[0],g)
out=g['OUT'];fw_hash=g['report']['firmware_sha256']
nav=json.loads((out/'six-current-results.json').read_text());assert nav['firmware_sha256']==fw_hash,'Run --nav-flex on this package first; never reuse raw flash from another firmware'
seed=out/'six-nav-fixture.flash';baseline=seed.read_bytes()
priority=["md-model-9","md-model-3","md-model-4","md-model-12","md-single-9","md-single-12"]
cases=[17,12,2,18,19,20,10,"md-0","md-1"]+["md-model-"+str(i) for i in range(21)]+["md-single-"+str(i) for i in [2,7,9,12]]
for engine in priority+[e for e in cases if e not in priority]:
 flash=bytearray(baseline);data=(out/f'six-capacity-{engine}.project').read_bytes()
 for off,kind in [(0x97000,1),(0xe5000,9)]:
  h=struct.pack('<IHHIIIII',0x33584953,kind,0,1,len(data),zlib.crc32(data),0xffffffff,0xffffffff);h+=struct.pack('<I',zlib.crc32(h))
  b=bytearray([255])*4096;b[:32]=h;b[256:256+len(data)]=data;flash[off:off+4096]=b
 path=out/f'six-capacity-{engine}.flash';path.write_bytes(flash)
 g['run'](f'six-capacity-{engine}',6000 if isinstance(engine,str) and ('model-' in engine or 'single-' in engine) else 12000,'2500:12,2620:12^',path,True)
 d=g['report']['runs'][f'six-capacity-{engine}']
 assert d['max_us']<g['HALF']/44100*1e6 and not any(d[k] for k in ['late','audio_lost','fm1_mc_lost','usb_underruns','usb_overruns','usb_missed']),(engine,d)
# Recheck the singleton Break with five independent Acid engines, with real SEQ chops now populated.
data=(out/'six-fiveacid-break-stress.project').read_bytes();flash=bytearray(baseline)
for off,kind in [(0x97000,1),(0xe5000,9)]:
 h=struct.pack('<IHHIIIII',0x33584953,kind,0,1,len(data),zlib.crc32(data),0xffffffff,0xffffffff);h+=struct.pack('<I',zlib.crc32(h));b=bytearray([255])*4096;b[:32]=h;b[256:256+len(data)]=data;flash[off:off+4096]=b
path=out/'six-capacity-break.flash';path.write_bytes(flash)
g['run']('six-capacity-break',16000,'2500:12,2620:12^',path,True)
r=g['report'];r['scope']='Six-track high-density capacity audit: all tracks same model; four-note hits; 240 BPM; four FX sends; standard cases include dual LFO and the MD dual-LFO case is reported separately; strict cache/LCD and USB 44.1 kHz. Break plus five Acid uses the current populated SEQ fixture.'
(out/'six-capacity-results.json').write_text(json.dumps(r,indent=2))
for name,d in r['runs'].items():
 assert d['boots']==1 and d['fm1_mc_on']==1 and d['max_us']<g['HALF']/44100*1e6,(name,d)
 assert not any(d[k] for k in ['late','audio_lost','fm1_mc_lost','usb_underruns','usb_overruns','usb_missed']),(name,d)
 assert d['peak_pcm16']>0 and d['usb_capture_frames']>1000,(name,d)
 if name.startswith('six-capacity-md-'):
  assert d.get('track_engines')==[10]*6,(name,'MD must be six real DRUM tracks')
 if name=='six-capacity-10':assert 0<d.get('core1_track_mask',0)<63,(name,'drums must share both cores')
print('Rhythmer capacity audit PASS',flush=True)

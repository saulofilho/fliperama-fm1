#!/usr/bin/env python3
from pathlib import Path
import json,struct,zlib
root=Path(__file__).resolve().parents[2];p=root/'tools/six/test_rhythmer_emulator.py';g={'__file__':str(p)};exec(p.read_text().split("if sys.argv[1:]==['--nav-flex']:")[0],g)
out=g['OUT'];nav=json.loads((out/'six-current-results.json').read_text());assert nav['firmware_sha256']==g['report']['firmware_sha256']
for kind in ['only','empty']:
 flash=bytearray((out/'six-nav-fixture.flash').read_bytes());data=(out/f'six-capacity-break-{kind}.project').read_bytes()
 for off,obj in [(0x97000,1),(0xe5000,9)]:
  h=struct.pack('<IHHIIIII',0x33584953,obj,0,1,len(data),zlib.crc32(data),0xffffffff,0xffffffff);h+=struct.pack('<I',zlib.crc32(h));sec=bytearray([255])*4096;sec[:32]=h;sec[256:256+len(data)]=data;flash[off:off+4096]=sec
 f=out/f'break-sequence-{kind}.flash';f.write_bytes(flash);g['run'](f'break-sequence-{kind}',8000,'2500:12,2620:12^',f,True)
r=g['report'];(out/'break-sequence-results.json').write_text(json.dumps(r,indent=2))
for kind,d in r['runs'].items():
 assert d['boots']==1 and not(d['late'] or d['audio_lost'] or d['fm1_mc_lost'] or d['usb_underruns']),d
 assert (d['peak_pcm16']>0)==kind.endswith('only'),d
print('Isolated Break SEQ audio / empty LOOP silence PASS',flush=True)

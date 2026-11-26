#!/usr/bin/env python3
"""Replay the read-only physical-device pattern in the community emulator.
Bench timings are emulator evidence, not predicted physical CPU percentages.
"""
from pathlib import Path
import hashlib, json, re, struct, sys, zlib

R=Path(__file__).resolve().parents[2];Q=R/'qa/hardware-fix'
source=R/'tools/six/test_rhythmer_emulator.py'
g={'__file__':str(source)}
exec(source.read_text().split("if sys.argv[1:]==['--nav-flex']:")[0],g)
kind=sys.argv[1] if len(sys.argv)>1 else 'after'
if kind=='before':
    g['FW']=Q/'before-felucca.fwsc'
    g['SYM']={m[2]:int(m[1],16)-0x1c00000 for m in re.finditer(r'^([0-9a-f]+).*?\s([A-Za-z_][A-Za-z_0-9]*)$',(Q/'before-felucca.sym').read_text(),re.M)}
    g['report']['firmware_sha256']=hashlib.sha256(g['FW'].read_bytes()).hexdigest()
else:
    assert kind=='after'
if kind=='before':
    seed=Q/'before-six-nav-fixture.flash'
else:
    nav=json.loads((g['OUT']/'six-current-results.json').read_text())
    assert nav['firmware_sha256']==g['report']['firmware_sha256'],'Regenerate the raw NOR seed from this candidate first'
    seed=g['OUT']/'six-nav-fixture.flash'
flash=bytearray(seed.read_bytes())
data=(Q/'device.project').read_bytes()
for off,obj in ((0x97000,1),(0xe5000,9)):
    h=struct.pack('<IHHIIIII',0x33584953,obj,0,1,len(data),zlib.crc32(data),0xffffffff,0xffffffff)
    h+=struct.pack('<I',zlib.crc32(h));sec=bytearray([255])*4096;sec[:32]=h;sec[256:256+len(data)]=data
    flash[off:off+4096]=sec
f=Q/f'device-{kind}.flash';f.write_bytes(flash)
g['run'](f'device-pattern-{kind}',16000,'2500:12,2620:12^',f,True)
d=g['report']['runs'][f'device-pattern-{kind}']
assert d['track_engines']==[10,20,12,20,16,15] and d['peak_pcm16']>0 and d['six_loop_mask']==3,d
if kind=='after':
    assert d['max_us']<512/44100*1e6,d
    assert not any(d[k] for k in ['late','audio_lost','fm1_mc_lost','usb_underruns','usb_overruns','usb_missed']),d
g['report']['scope']='Community-emulator replay of captured 121 BPM six-track device parameters and sequence; includes independent Acid generation, FM6, two SID tracks and both available factory Break banks. Physical performance after reinstall remains unverified.'
(Q/f'device-{kind}-results.json').write_text(json.dumps(g['report'],indent=2))
print(f'Device pattern {kind}: recorded'+(' and deadline checks PASS' if kind=='after' else ''),flush=True)

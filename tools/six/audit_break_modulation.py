#!/usr/bin/env python3
"""Candidate-bound PCM checks: fresh Amen defaults and audible filter/modulation."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,struct,zlib,hashlib,array
r=Path(__file__).resolve().parents[2];p=r/'tools/six/test_rhythmer_emulator.py';g={'__file__':str(p)}
exec(p.read_text().split("if sys.argv[1:]==['--nav-flex']:")[0],g)
o=g['OUT'];q=r/'qa/break-modulation';nav=json.loads((o/'six-current-results.json').read_text())
assert nav['firmware_sha256']==g['report']['firmware_sha256']
layout=json.loads((o/'six-model-layout.json').read_text())
ram=(o/'six-nav-boot.ram').read_bytes();at=g['SYM']['trk']+5*layout['track_stride']
assert struct.unpack_from('<h',ram,at+(119+4)*2)[0]==0,'Fresh Break source must be A'
for i in range(32):
 s=at+layout['step']+i*20
 assert ram[s+5]==(1 if i&1 else 0) and (i&1 or ram[s+4]==1 and ram[s]==i//2),'Fresh Break sequence is not straight'
def run(kind):
 flash=bytearray((o/'six-nav-fixture.flash').read_bytes());data=(q/f'break-mod-{kind}.project').read_bytes()
 for off,obj in ((0x97000,1),(0xe5000,9)):
  h=struct.pack('<IHHIIIII',0x33584953,obj,0,1,len(data),zlib.crc32(data),0xffffffff,0xffffffff);h+=struct.pack('<I',zlib.crc32(h))
  sector=bytearray([255])*4096;sector[:32]=h;sector[256:256+len(data)]=data;flash[off:off+4096]=sector
 f=o/f'break-mod-{kind}.flash';f.write_bytes(flash)
 g['run']('break-mod-'+kind,10000,'2500:12,2620:12^',f,True)
 v=g['report']['runs']['break-mod-'+kind]
 assert v['boots']==1 and v['fm1_mc_on'] and v['six_loop_mask']==3 and v['peak_pcm16']>0 and v['max_us']<512/44100*1e6,v
 assert not any(v.get(k,0) for k in ('late','audio_lost','fm1_mc_lost','usb_underruns','usb_overruns','usb_missed')),v
 pcm=(o/f'break-mod-{kind}.pcm').read_bytes();v['pcmSha256']=hashlib.sha256(pcm).hexdigest();v['pcmEnergy']=sum(x*x for x in array.array('h',pcm))
with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(run,('dry','lp','lfo1','lfo2','env','ensemble','comb-ensemble')))
v=g['report']['runs'];dry=v['break-mod-dry']
for kind in ('lp','lfo1','lfo2','env'):assert v['break-mod-'+kind]['pcmSha256']!=dry['pcmSha256'],'No audible PCM change: '+kind
assert v['break-mod-lp']['pcmEnergy']<dry['pcmEnergy']*.8,'Low-pass did not attenuate recorded Amen output'
g['report']['freshAmenStraightDefaultVerified']=True;g['report']['physicalCandidateTested']=False
(q/'native-results.json').write_text(json.dumps(g['report'],indent=2)+'\n')
print('Actual firmware: Amen straight defaults, filter, LFO, ENV and six-track PCM/deadline checks PASS',flush=True)

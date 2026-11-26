#!/usr/bin/env python3
"""Play the exact replacement bank through native Break SEQ, then switch A/B."""
from pathlib import Path
import json,struct,zlib,hashlib
r=Path(__file__).resolve().parents[2];p=r/'tools/six/test_rhythmer_emulator.py';g={'__file__':str(p)};exec(p.read_text().split("if sys.argv[1:]==['--nav-flex']:")[0],g)
o=g['OUT'];sample=g['SAMPLES']/'think-160.slot';sha=hashlib.sha256(sample.read_bytes()).hexdigest()
for kind in ('b-seq','ab-switch'):
 flash=bytearray((o/'six-nav-fixture.flash').read_bytes());assert flash[0xb4000:0xc8000]==sample.read_bytes()
 data=(o/('think-'+kind+'.project')).read_bytes()
 for off,obj in ((0x97000,1),(0xe5000,9)):
  h=struct.pack('<IHHIIIII',0x33584953,obj,0,1,len(data),zlib.crc32(data),0xffffffff,0xffffffff);h+=struct.pack('<I',zlib.crc32(h));s=bytearray([255])*4096;s[:32]=h;s[256:256+len(data)]=data;flash[off:off+4096]=s
 f=o/('think-'+kind+'.flash');f.write_bytes(flash);ram=g['run']('think-'+kind,8500,'2500:12,2620:12^',f,True)
 d=g['report']['runs']['think-'+kind];d['final_source']=ram[g['SYM']['six_loop_now']]
 if kind=='b-seq':assert d['final_source']==1
 assert d['peak_pcm16']>0 and d['max_us']<512/44100*1e6
 assert not any(d.get(k,0) for k in ['late','audio_lost','fm1_mc_lost','usb_underruns','usb_overruns','usb_missed'])
j=g['report'];j['think_slot_sha256']=sha;(o/'think-drum-results.json').write_text(json.dumps(j,indent=2));print('Think drum bank B SEQ and A/B native playback PASS')

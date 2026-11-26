#!/usr/bin/env python3
"""Run the new Break authors and their saved automation in the real FM-1 emulator."""
from pathlib import Path
import json,struct,zlib,os
from concurrent.futures import ThreadPoolExecutor
r=Path(__file__).resolve().parents[2];p=r/'tools/six/test_rhythmer_emulator.py';g={'__file__':str(p)}
exec(p.read_text().split("if sys.argv[1:]==['--nav-flex']:")[0],g)
o=g['OUT'];q=Path(os.environ.get('RHYTHMER_BREAK_QA',r/'qa/break-seq-tools'));nav=json.loads((o/'six-current-results.json').read_text())
assert nav['firmware_sha256']==g['report']['firmware_sha256'],'Fresh candidate NOR seed required'
layout=json.loads((o/'six-model-layout.json').read_text());extra=json.loads((o/'break-tools-layout.json').read_text())
def check_kind(kind):
 flash=bytearray((o/'six-nav-fixture.flash').read_bytes());data=(o/f'break-tools-{kind}.project').read_bytes()
 for off,obj in ((0x97000,1),(0xe5000,9)):
  h=struct.pack('<IHHIIIII',0x33584953,obj,0,1,len(data),zlib.crc32(data),0xffffffff,0xffffffff);h+=struct.pack('<I',zlib.crc32(h))
  sec=bytearray([255])*4096;sec[:32]=h;sec[256:256+len(data)]=data;flash[off:off+4096]=sec
 f=o/f'break-tools-{kind}.flash';f.write_bytes(flash)
 ram=g['run']('break-tools-'+kind,10500,'2500:12,2620:12^',f,True)
 d=g['report']['runs']['break-tools-'+kind];d['final_source']=ram[g['SYM']['six_loop_now']]
 assert d['peak_pcm16']>0 and d['usb_capture_frames']>1000 and d['max_us']<512/44100*1e6,d
 assert d['boots']==1 and d['fm1_mc_on'] and d['six_loop_mask']==3 and not any(d.get(k,0) for k in ['late','audio_lost','fm1_mc_lost','usb_underruns','usb_overruns','usb_missed']),d
 at=g['SYM']['trk']+5*layout['track_stride']
 d['step_commands']=[[ram[at+layout['step']+i*20+j] for j in range(ram[at+layout['step']+i*20+4])] for i in range(32)]
 assert all(len(ns)<=4 and all(n<35 for n in ns) for ns in d['step_commands']),d
 if kind.startswith('auto-') or kind=='ensemble-auto':
  before=(o/f'break-tools-{kind}.steps').read_bytes()
  now=ram[at+layout['step']:at+layout['step']+1280]
  assert now!=before,'Saved automatic action never changed the real sequence'
 if kind=='straight':
  sel=ram[g['SYM']['song']+layout['song_sel']];delta=(5-sel)%6
  keys=','.join(f'{2400+i*160}:e1:1' for i in range(delta))
  keys+=(',' if keys else '')+'3600:11,4500:n0,4620:n0^,4800:n2,4920:n2^,5100:n4,5220:n4^'
  screen=g['run']('break-tools-menu',5700,keys,f)
  u=g['report']['runs']['break-tools-menu'];u['layer']=screen[g['SYM']['ui']+extra['layer']]
  assert u['selected_track']==5 and u['layer']==5 and screen[g['SYM']['song']+extra['rec']]==0,u
  assert u['peak_pcm16']==0,'SEQ menu keys must never audition or record notes'
with ThreadPoolExecutor(max_workers=2) as pool:
 list(pool.map(check_kind,('straight','mutate','random','fill','ab-random','auto-fill','auto-random','ensemble-auto')))
j=g['report'];j['scope']='Seven isolated Break author/automation PCM scenarios, default six-track ensemble with automatic Break randomization, plus a real SEQ hold and keyboard shortcut navigation; strict cache/LCD and USB audio on playback runs. No physical flashing.'
(q/'native-results.json').write_text(json.dumps(j,indent=2));print('Break generators, auto actions and real SEQ keyboard layer PASS',flush=True)

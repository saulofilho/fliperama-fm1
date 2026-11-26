#!/usr/bin/env python3
"""Exact-package ensemble / chords check, independent MD work limit; no hardware."""
from pathlib import Path
import json,struct,zlib
r=Path(__file__).resolve().parents[2];p=r/'tools/six/test_rhythmer_emulator.py';g={'__file__':str(p)};exec(p.read_text().split("if sys.argv[1:]==['--nav-flex']:")[0],g)
o=g['OUT'];layout=json.loads((o/'six-model-layout.json').read_text())
for kind in ('classic-default','md-default','classic-chords','md-chords','classic-analog-load','md-analog-load'):
 flash=bytearray((o/'six-nav-fixture.flash').read_bytes());data=(o/('ensemble-'+kind+'.project')).read_bytes()
 for off,obj in ((0x97000,1),(0xe5000,9)):
  h=struct.pack('<IHHIIIII',0x33584953,obj,0,1,len(data),zlib.crc32(data),0xffffffff,0xffffffff);h+=struct.pack('<I',zlib.crc32(h));s=bytearray([255])*4096;s[:32]=h;s[256:256+len(data)]=data;flash[off:off+4096]=s
 f=o/('ensemble-'+kind+'.flash');f.write_bytes(flash);ram=g['run']('ensemble-'+kind,5600,'2500:12,2620:12^',f,True)
 d=g['report']['runs']['ensemble-'+kind]
 d['retained_notes']=[]
 for k in range(6):
  at=g['SYM']['trk']+k*layout['track_stride']+layout['voices'];notes=[]
  for i in range(8):
   v=at+i*layout['voice_stride']
   if ram[v+layout['voice_active']] and ram[v+layout['voice_stage']]!=4:notes.append(ram[v+layout['voice_note']])
  d['retained_notes'].append(notes)
 d['gov_cap']=ram[g['SYM']['gov_cap']]
 d['latest_voice_age']=[]
 for k in range(5):
  at=g['SYM']['trk']+k*layout['track_stride']+layout['voices']
  d['latest_voice_age'].append(max(struct.unpack_from('<I',ram,at+i*layout['voice_stride']+layout['voice_age'])[0] for i in range(8)))
 if kind=='md-default':assert d['latest_voice_age'][0]+4>=max(d['latest_voice_age'][1:]),('MD must still trigger in the latest bar',d)
 assert d['peak_pcm16']>0 and d['max_us']<512/44100*1e6,d
 assert not any(d.get(k,0) for k in ['late','audio_lost','fm1_mc_lost','usb_underruns','usb_overruns','usb_missed']),d
 for k in range(1,5):
  expected=[36] if k==4 else [48+k*2+j*4 for j in range(3 if (kind.endswith('chords') or kind.endswith('load')) else 1)]
  assert set(expected)<=set(d['retained_notes'][k]),(kind,k,expected,d)
 # Drum hits have their own physical decay; retained-note assertions are tested
 # at admission by the host regression, not inferred from a quiet tail snapshot.
j=g['report'];j['scope']='Default six tracks with all FX sends; three ANALOG triads with FX sends off and classic/MD drums plus Acid (Break muted), asserting every melodic note in the twelve-voice synthesis pool. Additional ANALOG triad cases add real sequenced Break and assert every melodic chord tone remains. All scenarios assert audio deadlines; heavier untested presets/FX remain subject to the CPU guard.'
(o/'ensemble-results.json').write_text(json.dumps(j,indent=2));print('Rhythmer native ensemble and chords PASS')

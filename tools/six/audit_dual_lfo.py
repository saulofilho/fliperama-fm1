#!/usr/bin/env python3
"""Exercise the packaged firmware's dual-LFO navigation in the community emulator."""
from pathlib import Path
import json,re,struct
r=Path(__file__).resolve().parents[2]
p=r/'tools/six/test_rhythmer_emulator.py'
g={'__file__':str(p)}
exec(p.read_text().split("if sys.argv[1:] in (['--upgrade'],['--upgrade-ensemble']):")[0],g)
b=g['OUT'];base=b/'lfo-boot.flash'
g['run']('lfo-boot',2800,flash=base,strict=True)
original=base.read_bytes()
titles=re.findall(r'^\s*\{"([^"]+)",\s*FAM_', (r/'rhythmer/firmware/src/params.c').read_text().split('static const page_t PAGES[] = {',1)[1],re.M)
layout=json.loads((b/'six-model-layout.json').read_text())
start='2400:e1:1,2800:5,2920:5^,3150:e0:-1'
for name,title,keys in [
 ('matrix','MOD',start),
 ('one','LFO',start+',3300:5,3420:5^'),
 ('two','LFO 2',start+',3300:5,3420:5^,3800:5,3920:5^,4300:e3:3'),
 ('two-phase','LFO 2 PHASE',start+',3300:5,3420:5^,3800:5,3920:5^,4300:e0:1'),
 ('two-dest','LFO 2 DEST',start+',3300:5,3420:5^,3800:5,3920:5^,4300:e0:2,4550:e2:12,4670:e3:-13,4790:e4:14,4910:e5:80'),
 ('two-free','LFO 2',start+',3300:5,3420:5^,3800:5,3920:5^,4300:e4:1'),
]:
 seed=b/('lfo-'+name+'.flash');seed.write_bytes(original)
 ram=g['run']('lfo-ui-'+name,5000,keys,seed,True)
 d=g['report']['runs']['lfo-ui-'+name]
 assert d['selected_track']==1 and d['page']==titles.index(title),(name,d)
 assert not any(d.get(k,0) for k in ('late','audio_lost','fm1_mc_lost','usb_underruns','usb_overruns','usb_missed')),(name,d)
 if name=='two-free':
  at=g['SYM']['trk']+layout['track_stride']+layout['p']
  assert struct.unpack_from('<h',ram,at+117*2)[0]==-1,'LFO2 MODE did not set its own FREE phase'
  assert struct.unpack_from('<h',ram,at+11*2)[0]>=0,'LFO2 MODE changed LFO1'
 if name=='two-dest':
  at=g['SYM']['trk']+layout['track_stride']+layout['p']
  vals=struct.unpack_from('<127h',ram,at)
  assert vals[65]>64 and vals[68]<64 and vals[72]>64 and vals[80]<64,vals[65:81]
  before=(b/'lfo-ui-one.ram').read_bytes()
  baseline_params=struct.unpack_from('<127h',before,at)
  assert vals[49:61]==baseline_params[49:61],'Direct DEST consumed MOD slots'
g['report']['scope']='Exact-package LFO tabs, separate phase page and independent FREE mode; no physical test'
(b/'lfo-emulator-results.json').write_text(json.dumps(g['report'],indent=2)+'\n')
print('Actual firmware dual-LFO UI: PASS')

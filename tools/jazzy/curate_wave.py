#!/usr/bin/env python3
"""Retain native frames nearest the pinned factory WAVE programs; preserve both mip levels.
Offline selection only. Runtime remains eight-frame fixed-point interpolation.
"""
import json,re,math
from pathlib import Path
R=Path(__file__).resolve().parents[2];D=R/'rhythmer/firmware/jazzy'
def make(rows):
 s=(D/'kwasub.h').read_text();body=re.search(r'jk_KS_WT\[32768\]\s*=\s*\{(.*?)\};',s,re.S)[1];v=list(map(int,re.findall(r'-?\d+',body)));assert len(v)==32768
 def frame(bank,f,mip=0):return v[((mip*8+bank)*8+f)*256:((mip*8+bank)*8+f+1)*256]
 ids=sorted(set((min(7,r['e'][3]//16),min(7,round(r['e'][2]*7/127))) for r in rows));assert len(ids)<=8
 while len(ids)<8:
  candidates=[(b,f) for b in range(8) for f in range(8) if (b,f) not in ids]
  ids.append(max(candidates,key=lambda t:min(sum((a-b)**2 for a,b in zip(frame(*t),frame(*i))) for i in ids)))
 # Greedy neighboring frames makes the playable scan less discontinuous.
 order=[ids.pop(0)]
 while ids:
  i=min(ids,key=lambda t:sum((a-b)**2 for a,b in zip(frame(*t),frame(*order[-1]))));order.append(i);ids.remove(i)
 table=[x for m in range(2) for b,f in order for x in frame(b,f,m)]
 (D/'wave_curated.h').write_text('/* Generated native K-WASUB frames, both mip levels. See wave-selection.json. */\nstatic const int16_t jk_KS_WT[4096]={\n'+'\n'.join(','.join(map(str,table[i:i+64]))+',' for i in range(0,len(table),64))+'\n};\n')
 mappings=[]
 for r in rows:
  bank=min(7,r['e'][3]//16);pos=r['e'][2]*7/127;lo=min(6,int(pos));t=pos-lo;a=frame(bank,lo);b=frame(bank,lo+1);target=[x*(1-t)+y*t for x,y in zip(a,b)]
  errors=[]
  for scan in range(128):
   q=scan*7/127;l=min(6,int(q));f=q-l;a=frame(*order[l]);b=frame(*order[l+1]);errors.append(sum((x*(1-f)+y*f-z)**2 for x,y,z in zip(a,b,target))/256)
  scan=min(range(128),key=errors.__getitem__);mappings.append({'name':r['name'],'source_bank':bank,'source_scan':r['e'][2],'selected_scan':scan,'waveform_rms_error':round(math.sqrt(errors[scan]),2)})
  r['e'][2]=scan;r['e'][3]=0;r['approximation']+=' Curated native frames, scan projected by waveform least-squares; not a complete 8-bank WAVE copy.'
 (R/'wave-selection.json').write_text(json.dumps({'frames':[{'bank':b,'frame':f} for b,f in order],'mip_levels':2,'table_bytes':len(table)*2,'original_table_bytes':len(v)*2,'preset_mapping':mappings},indent=2)+'\n')
 return rows

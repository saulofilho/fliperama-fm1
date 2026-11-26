#!/usr/bin/env python3
"""Losslessly pack all 200 FMini programs by each native parameter's alphabet."""
from pathlib import Path
import re,struct,json
R=Path(__file__).resolve().parents[2];D=R/'rhythmer/firmware/jazzy'
s=(D/'eng_fmini_presets.h').read_text().split('FMINI_FACTORY')[1].split('\n};')[0]
rows=[list(map(int,a.split(',')))+[0]*8 for a in re.findall(r'FGP\(([^)]+)\)',s)];assert len(rows)==200 and all(len(r)==32 for r in rows)
bits=[];dictionary=[];meta=[]
for j in range(32):
 a=[r[j] for r in rows];u=sorted(set(a));w=(len(u)-1).bit_length();raw=max(a).bit_length()
 use=len(u)+(200*w+7)//8<(200*raw+7)//8
 if not use:w=raw
 meta.append((len(bits),len(dictionary) if use else 65535,w))
 if use:dictionary+=u
 for x in a:
  v=u.index(x) if use else x;bits.extend((v>>k)&1 for k in range(w))
payload=bytes(sum(bits[i+k]<<k for k in range(min(8,len(bits)-i))) for i in range(0,len(bits),8))+b'\0\0'
blob=b''.join(struct.pack('<HHB',pos,160+len(payload)+di if di!=65535 else di,w) for pos,di,w in meta)+payload+bytes(dictionary)
for k,row in enumerate(rows):
 for j,y in enumerate(row):
  pos,di,w=struct.unpack_from('<HHB',blob,j*5);pos+=k*w;off=160+pos//8;v=(int.from_bytes(blob[off:off+2],'little')>>(pos&7))&((1<<w)-1)
  assert (blob[di+v] if di!=65535 else v)==y
lines=['/* Generated GPL-3.0-only FMini native programs; all 200 x 32 bytes preserved. */','static const uint8_t JF_PACK[]={']+[','.join(map(str,blob[i:i+96]))+',' for i in range(0,len(blob),96)]+['};']
(D/'fmini_compact.h').write_text('\n'.join(lines)+'\n');(R/'fmini-compact.json').write_text(json.dumps({'programs':200,'original_bytes':6400,'packed_bytes':len(blob),'values_verified':6400},indent=2)+'\n');print('FMini:',len(blob),'bytes, 6400 original values verified')

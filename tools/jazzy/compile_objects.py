#!/usr/bin/env python3
"""Compile the approved artwork to fixed-palette scanline runs. No decoder state or heap at runtime."""
from pathlib import Path
import sys
from PIL import Image
R=Path(__file__).resolve().parents[2];im=Image.open(R/'rhythmer/assets/jazzy/field-objects-final-v3.png').convert('RGB')
W=64;H=64;pal=[(0,0,0),(223,225,215),(115,152,171),(191,160,92),(240,90,40),(21,24,29)]
rows=[];data=[];previews=[]
for k in range(16):
 x=k%4;y=k//4;tile=im.crop((x*im.width//4,y*im.height//4,(x+1)*im.width//4,(y+1)*im.height//4))
 if k in (1,13):tile=Image.open(R/('rhythmer/assets/jazzy/cat-standing-v1.png' if k==1 else 'rhythmer/assets/jazzy/skater-v1.png')).convert('RGB')
 mask=tile.convert('L').point(lambda a:255 if a>32 else 0);box=mask.getbbox();tile=tile.crop(box);scale=min(58/tile.width,58/tile.height);wh=(round(tile.width*scale),round(tile.height*scale));tile=tile.resize(wh,Image.Resampling.LANCZOS)
 canvas=Image.new('RGB',(W,H));canvas.paste(tile,((W-wh[0])//2,(H-wh[1])//2));pix=[]
 for rgb in canvas.getdata():
  # Preserve the cat's thin neutral ivory contours through low-resolution quantization.
  if k==1 and max(rgb)-min(rgb)<25 and sum(rgb)>192:pix.append(1)
  else:pix.append(min(range(len(pal)),key=lambda i:sum((rgb[j]-pal[i][j])**2 for j in range(3))))
 if k==7 or (k==8 and "--rhodes" not in sys.argv):pix=[0]*(W*H) # Procedural LP and disabled Rhodes need no raster payload.
 off=[]
 for yy in range(H):
  off.append(len(data));xx=0
  while xx<W:
   c=pix[yy*W+xx];end=xx+1
   while end<W and pix[yy*W+end]==c:end+=1
   n=end-xx
   while n:
    take=min(n,32);data.append(((take-1)<<3)|c);n-=take
   xx=end
 off.append(len(data));rows.append(off)
# Share byte-identical scanlines across all objects, losslessly.
old=data;packed=[];seen={};shared=[]
for offsets in rows:
 row=[]
 for a,b in zip(offsets,offsets[1:]):
  runs=tuple(old[a:b]);assert sum((v>>3)+1 for v in runs)==64
  if runs not in seen:seen[runs]=len(packed);packed.extend(runs)
  row.append(seen[runs])
 shared.append(row)
rows=shared;data=packed
assert len(data)<65536
lines=['/* Generated from JAZZY original artwork. 64x64 indexed run sprites. */','static const uint16_t JO_PAL[6]={'+','.join('0x%04x'%((r>>3)<<11|(g>>2)<<5|(b>>3)) for r,g,b in pal)+'};','static const uint16_t JO_ROW[16][64]={']
lines+=['{'+','.join(map(str,row))+'},' for row in rows];lines+=['};','static const uint8_t JO_RUNS[]={'];lines +=[','.join(map(str,data[i:i+96]))+',' for i in range(0,len(data),96)];lines+=['};']
(R/'rhythmer/firmware/jazzy/objects.h').write_text('\n'.join(lines)+'\n');print('Object art bytes:',len(data)+16*64*2+12,'encoded runs',len(data))

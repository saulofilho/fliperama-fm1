#!/usr/bin/env python3
"""Compile original transparent artwork into bounded 48x48, 4-bit firmware sprites.
No image loading, quantization or allocation occurs on the FM-1.
"""
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[2];im=Image.open(R/'rhythmer/assets/jazzy/pets-atlas-v1.png').convert('RGBA');size=48
palettes=[];data=[]
for k in range(9):
 x=k%3;y=k//3;tile=im.crop((x*im.width//3,y*im.height//3,(x+1)*im.width//3,(y+1)*im.height//3))
 # Ignore partially transparent edge pixels in the firmware's binary alpha.
 alpha=tile.getchannel('A').point(lambda a:255 if a>=192 else 0);box=alpha.getbbox();tile=tile.crop(box);alpha=alpha.crop(box)
 scale=min((size-4)/tile.width,(size-4)/tile.height);wh=(round(tile.width*scale),round(tile.height*scale));tile=tile.resize(wh,Image.Resampling.NEAREST);alpha=alpha.resize(wh,Image.Resampling.NEAREST)
 rgb=Image.new('RGB',(size,size),(0,0,0));mask=Image.new('L',(size,size));pos=((size-wh[0])//2,(size-wh[1])//2);rgb.paste(tile.convert('RGB'),pos);mask.paste(alpha,pos)
 q=rgb.quantize(colors=15,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE);pal=q.getpalette();palettes.append([0]+[((pal[j*3]>>3)<<11)|((pal[j*3+1]>>2)<<5)|(pal[j*3+2]>>3) for j in range(15)])
 indices=[v+1 if a else 0 for v,a in zip(q.getdata(),mask.getdata())];data.append([(indices[i]<<4)|indices[i+1] for i in range(0,len(indices),2)])
lines=['/* Generated from original JAZZY pet artwork; zero is transparent. */','static const uint16_t JAZZY_PET_PAL[9][16]={']
lines+=['{'+','.join('0x%04x'%v for v in row)+'},' for row in palettes];lines+=['};','static const uint8_t JAZZY_PET_PIX[9][1152]={']
for row in data:lines+=['{']+[','.join(str(v) for v in row[j:j+48])+',' for j in range(0,len(row),48)]+['},']
lines+=['};'];(R/'rhythmer/firmware/jazzy/pets.h').write_text('\n'.join(lines)+'\n');print('Pet flash:',9*(1152+32),'bytes, no runtime state')

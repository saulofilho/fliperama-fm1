#!/usr/bin/env python3
"""Export original Rhythmer UI stills and every animation frame for the owner."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,shutil,zipfile
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[2];O=R/'outputs/Rhythmer-UI-images-2026-11-07'
assert O.resolve().is_relative_to(Path('/Volumes/SSD/Development'))
order=['drum','serum','phase','lofi','analog','fm6','wheel','fmstat','swavsaw','sid','acid','acid-generate','break','break-perform']
labels=['DRUM','SERUM','PHASE','LOFI','ANALOG','FM6','WHEEL','FM+STAT','SWAV-SAW','SID-6581','ACID / SOUND','ACID / GENERATOR','BREAK / SOUND','BREAK / PERFORMANCE']
for name in ('Selected-2400','All-frames-2400','Original-animation','Original-240','Pages-2400'):(O/name).mkdir(exist_ok=True)
font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',23)
sheet=Image.new('RGB',(1600,1650),'#0d0e0e');draw=ImageDraw.Draw(sheet)
manifest={'source':'Rhythmer website actual host-rendered firmware UI captures. Not physical-device photographs.','nativePixels':[240,240],'exportPixels':[2400,2400],'scaling':'Nearest-neighbor 10x. No invented detail, smoothing, cropping or color changes.','animations':[],'pages':[]}
def write_frame(job):
 name,i,im=job
 im.resize((2400,2400),Image.Resampling.NEAREST).save(O/'All-frames-2400'/name/f'{name}-{i:03}.png',compress_level=3)
 return 1
total=0
with ThreadPoolExecutor(max_workers=4) as workers:
 for j,(name,label) in enumerate(zip(order,labels)):
  src=R/'site/media/motion'/f'{name}.webp';anim=Image.open(src)
  shutil.copy2(src,O/'Original-animation'/src.name)
  folder=O/'All-frames-2400'/name;folder.mkdir(exist_ok=True)
  selected={'acid-generate':13,'break-perform':8,'fm6':3}.get(name,min(22,anim.n_frames-1))
  frames=[];dur=[]
  for i in range(anim.n_frames):
   anim.seek(i);im=anim.convert('RGB').copy();dur.append(anim.info.get('duration',0));frames.append((name,i,im))
   if i==selected:
    im.save(O/'Original-240'/f'{j+1:02}-{name}.png')
    im.resize((2400,2400),Image.Resampling.NEAREST).save(O/'Selected-2400'/f'{j+1:02}-{name}.png')
    x=40+(j%4)*390;y=40+(j//4)*400
    sheet.paste(im.resize((330,330),Image.Resampling.NEAREST),(x,y));draw.text((x,y+348),label,font=font,fill='#eeeee2')
  total+=sum(workers.map(write_frame,frames))
  manifest['animations'].append({'id':name,'label':label,'frames':len(frames),'frameDurationsMs':dur,'selectedFrame':selected,'originalSHA256':hashlib.sha256(src.read_bytes()).hexdigest()})
  print(name,len(frames),flush=True)
# Additional page layouts from the exact optimized build, preserving whole squares.
b=Path('/Volumes/SSD/Development/BuildCache/rhythmer/audio-overload')
for kind,count in [('acid',2),('break',3)]:
 src=Image.open(b/f'Rhythmer-{kind}-tabs.png').convert('RGB');w,h=src.size
 for i in range(count):
  im=src.crop((w*i//count,0,w*(i+1)//count,h));name=f'{kind}-page-{i+1}.png'
  im.resize((2400,2400),Image.Resampling.NEAREST).save(O/'Pages-2400'/name)
  manifest['pages'].append(name)
for path,name in [(b/'Rhythmer-home.png','home.png'),(R/'site/media/boot/rhythmer-startup-2400.png','startup.png')]:
 im=Image.open(path).convert('RGB');im.resize((2400,2400),Image.Resampling.NEAREST).save(O/'Pages-2400'/name);manifest['pages'].append(name)
sheet.crop((0,0,1600,1640)).save(O/'All-machines-preview.jpg',quality=96,subsampling=0)
manifest['totalAnimationFrames']=total;(O/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(O/'README.txt').write_text(f'''RHYTHMER / HIGH-RES UI IMAGE COLLECTION

14 machine/animation views; {total} animation frames; 7 additional pages.
Selected-2400: one representative still for each view.
All-frames-2400: every animation frame, ordered by frame number.
Pages-2400: Acid generator pages 1/2, Break pages 1/2/3, HOME and STARTUP.
Original-animation: original animated WebP files; play in a browser.
Original-240: native-resolution selected stills.

Source graphics are 240x240 firmware pixels. 2400x2400 exports use exact
10x nearest-neighbor scaling. They preserve the pixel style; they do not add
new original detail. Additional page captures are expanded from the exact
optimized build's 480px host renders. No edges of the UI are cropped.

These are host-rendered actual firmware UI, not FM-1 hardware photographs.
Rhythmer is built on JIANT with retained upstream sources and licenses.
Please keep the project/upstream credits in accompanying public posts.
No posting, website update or external upload was performed by this export.
''')
def pack(name,folders):
 with zipfile.ZipFile(O/name,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for f in ('README.txt','manifest.json','All-machines-preview.jpg'):z.write(O/f,f)
  for folder in folders:
   for p in sorted((O/folder).rglob('*')):
    if p.is_file():z.write(p,str(p.relative_to(O)))
pack('Rhythmer-UI-Selected-2400.zip',['Selected-2400','Pages-2400'])
pack('Rhythmer-UI-All-Frames-2400.zip',['All-frames-2400','Selected-2400','Pages-2400','Original-animation','Original-240'])
print('DONE:',total,'high-resolution animation frames;',len(manifest['pages']),'additional pages',flush=True)

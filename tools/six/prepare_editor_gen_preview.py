#!/usr/bin/env python3
"""Isolated local preview from the exact emulator-validated candidate."""
import hashlib,json,os,shutil,sys,html,wave,struct,base64,zlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];B=Path('/Volumes/SSD/Development/BuildCache/rhythmer/editor-gen-20261107');O=R/'outputs/editor-gen-20261107/preview'
assert O.resolve().is_relative_to(Path('/Volumes/SSD/Development'))
digest=hashlib.sha256((B/'felucca.fwsc').read_bytes()).hexdigest();report=json.loads((B/'upgrade-emulator-results.json').read_text());assert report['firmware_sha256']==digest and len(report['runs'])==31
O.mkdir(exist_ok=True);(O/'downloads').mkdir(exist_ok=True)
shutil.copy2(B/'felucca.fwsc',O/'downloads/Rhythmer.fwsc');shutil.copy2(B/'Rhythmer-start.fm1save',O/'downloads/Rhythmer-start.fm1save')
(O/'release.json').write_text(json.dumps({'version':'0.1.1-beta2','product':'FM-1_748004','sha256':digest,'localOnly':True,'physicalHardwareTested':False})+'\n')
os.environ['RHYTHMER_BUILD_DIR']=str(B);sys.path.insert(0,str(R/'tools/six'));from site_editor import build_editor;from site_emulator import build_emulator
build_editor(R,O);build_emulator(R,O,digest)
v=json.loads((O/'emulator/firmwares.json').read_text());v['firmwares'][0]['version']='0.1.1-beta2';(O/'emulator/firmwares.json').write_text(json.dumps(v)+'\n')
for name in ['GEN-STYLE-DESIGN.md','GEN-GENRE-ORDER.json']:shutil.copy2(R/'docs/six'/name,O/name)
for name in ['GEN-new-styles.png','GEN-ambient-breaks-drunken.png']:shutil.copy2(O.parent/name,O/name)
order=json.loads((R/'docs/six/GEN-GENRE-ORDER.json').read_text());families=['House / Disco','Techno / Electro','Hip-hop / Bass / Breaks','Soul / Jazz','Band / Post','Dub','Ambient / Experimental']
blocks=''.join('<h3>'+f+'</h3><p>'+html.escape(' · '.join(ns))+'</p>' for f,ns in zip(families,order['families']))
# Short captures are clearly labelled; full sessions can be loaded into PLAY.
seed=json.loads((B/'Rhythmer-start.fm1save').read_text());demos=''
for name in ['AMBIENT IDM','ATMOS BREAKS','DRUNKEN HH']:
 slug=name.lower().replace(' ','-');src=B/('upgrade-'+name+'.wav');dst=O/'downloads'/('GEN-'+slug+'.wav')
 with wave.open(str(src),'rb') as f:
  params=f.getparams();raw=f.readframes(f.getnframes());samples=struct.unpack('<'+'h'*(len(raw)//2),raw);first=next((i//2 for i,x in enumerate(samples) if abs(x)>12),0);raw=raw[max(0,first-64)*4:]
 with wave.open(str(dst),'wb') as f:f.setparams(params);f.writeframes(raw)
 project=(B/('upgrade-'+name+'.project')).read_bytes();session=json.loads(json.dumps(seed));session['name']='GEN / '+name;session.pop('startingProject',None)
 for sector in session['sectors']:
  if sector['at'] not in (0x97000,0xe5000):continue
  kind=1 if sector['at']==0x97000 else 9;head=struct.pack('<IHHIIIII',0x33584953,kind,0,1,len(project),zlib.crc32(project),0xffffffff,0xffffffff);head+=struct.pack('<I',zlib.crc32(head));bank=bytearray(b'\xff'*4096);bank[:32]=head;bank[256:256+len(project)]=project;sector['data']=base64.b64encode(bank).decode()
 save='GEN-'+slug+'.fm1save';(O/'downloads'/save).write_text(json.dumps(session)+'\n')
 demos+='<article><h3>'+name+'</h3><audio controls preload="none" src="downloads/'+dst.name+'"></audio><a download href="downloads/'+save+'">DOWNLOAD FULL PLAY SESSION ↓</a></article>'
(O/'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Rhythmer / GEN + Editor</title><style>body{background:#101111;color:#eee;font:15px/1.7 monospace;max-width:1120px;margin:auto;padding:30px}a{color:inherit;display:inline-block;margin:12px 24px 12px 0}h1{line-height:1.2}h3{font-size:14px;margin-bottom:8px}img{width:100%;height:auto}.demos{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}article{border:1px solid #444;padding:18px}article a{font-size:11px}audio{width:100%}@media(max-width:750px){.demos{grid-template-columns:1fr}}</style><h1>RHYTHMER / 0.1.1 BETA2</h1><p>Local development candidate. Physical validation pending. This page does not start an installation.</p><a href="emulator/?fw=rhythmer&mhz=240">PLAY THE ACTUAL FIRMWARE →</a><a href="editor/?target=browser#projects">FOUR-PROJECT WORKSPACE →</a><a href="editor/?target=browser#samples">PREPARE BREAK SAMPLES →</a><h2>59 GEN STYLES / ALL PREVIOUS 49 RETAINED</h2><p>HOME + SELECT opens GEN. Choose GENRE with knob 1; OCT+ generates tracks 1–4. Serum remains eligible with a one-instance automatic allowance. Tracks 5–6 retain their music. The empty start contains no demo notes.</p><img src="GEN-ambient-breaks-drunken.png" alt="Actual FM-1 GEN screens for Ambient IDM, Atmos Breaks and Drunken Hip-Hop"><h2>SHORT RAW FIRMWARE CAPTURES</h2><p>Generated with seed 0031. Short emulator captures, not seamless loops or mastered demos. For the complete repeating phrase, download a PLAY session, open the emulator, use its import control and press PLAY. Imported sessions have blank Acid/Break sequences; the drum part is synthesized.</p><div class="demos">'''+demos+'''</div><a href="GEN-STYLE-DESIGN.md">RESEARCH & MUSICAL DESIGN →</a><h2>MENU GROUPS</h2>'''+blocks+'<img src="GEN-new-styles.png" alt="All ten additional GEN profiles on the actual firmware UI"></html>')
print('Prepared isolated preview',O,'SHA',digest)

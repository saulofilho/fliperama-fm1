#!/usr/bin/env python3
"""Local-only target GEN package. No deployment or device writes."""
from pathlib import Path
import os,sys,json,hashlib,re,shutil,base64,tarfile,zipfile
R=Path(__file__).resolve().parents[2];B=Path('/Volumes/SSD/Development/BuildCache/rhythmer/gen-target-20261107');Q=R/'qa/gen-target-20261107';O=R/'outputs/gen-target-20261107'
assert O.resolve().is_relative_to(Path('/Volumes/SSD/Development'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();digest=sha(B/'felucca.fwsc')
r=json.loads((B/'target-emulator-results.json').read_text());assert r['firmware_sha256']==digest and len(r['runs'])==7
for name in ['target-test.log','regression.log']:
 text=(Q/name).read_text();assert 'PASS' in text and not any(x in text for x in ['FAIL','runtime error:','ERROR: AddressSanitizer']),name
assert 'LIVE TARGET GEN: PASS' in (Q/'emulator.log').read_text()
m=re.search(r'image (\d+) B of the (\d+) B slot \((\d+) B free\); RAM .data\+.bss (\d+) B of (\d+); pool (\d+) B, spare (\d+) B',(Q/'build.log').read_text());assert m and int(m[3])>0 and int(m[7])>=8192
for d in r['runs'].values():assert d['max_us']<r['half_frames']/44100*1e6 and not any(d.get(k,0) for k in ['late','audio_lost','fm1_mc_lost','usb_underruns','usb_overruns','usb_missed'])
report={'version':'0.1.1-beta3','product':'FM-1_748005','firmware_sha256':digest,'physical_hardware_tested':False,'publicly_deployed':False,'native_genre_track_cases':354,'loop_lengths':[1,64],'break_owner_locations':6,'whole_gen_regression':True,'undo_verified':True,'live_target_midi_and_preservation_verified':True,'emulator_cases':7,'max_render_us':max(d['max_us'] for d in r['runs'].values()),'deadline_us':r['half_frames']/44100*1e6,'memory':dict(zip(['image','image_limit','image_free','data_bss','data_bss_limit','pool','pool_reserve'],map(int,m.groups()))),'sources_sha256':{str(p.relative_to(R)):sha(p) for p in sorted((R/'rhythmer/firmware').rglob('*')) if p.is_file()},'native_test_sha256':sha(R/'rhythmer/tests/six_gen_target_test.c'),'logs_sha256':{p.name:sha(p) for p in Q.glob('*.log')}}
(Q/'VALIDATION.json').write_text(json.dumps(report,indent=2)+'\n')
preview=O/'preview';preview.mkdir(exist_ok=True);downloads=preview/'downloads';downloads.mkdir(exist_ok=True)
seed=json.loads((Path('/Volumes/SSD/Development/BuildCache/rhythmer/editor-gen-20261107')/'Rhythmer-start.fm1save').read_text());seed['hash']=digest;seed['package']=base64.b64encode((B/'felucca.fwsc').read_bytes()).decode();seed['name']='Rhythmer / empty start / beta3'
(downloads/'Rhythmer-start.fm1save').write_text(json.dumps(seed)+'\n');shutil.copy2(B/'felucca.fwsc',downloads/'Rhythmer.fwsc');(preview/'release.json').write_text(json.dumps({'version':'0.1.1-beta3','product':'FM-1_748005','sha256':digest,'localOnly':True,'physicalHardwareTested':False})+'\n')
os.environ['RHYTHMER_BUILD_DIR']=str(B);sys.path.insert(0,str(R/'tools/six'));from site_emulator import build_emulator;from site_editor import build_editor
build_emulator(R,preview,digest);build_editor(R,preview)
shutil.copy2(O/'GEN-Break.png',preview/'GEN-Break.png');shutil.copy2(R/'docs/six/GEN-TARGET.md',preview/'GEN-TARGET.md')
(preview/'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Rhythmer / Target GEN</title><style>body{background:#101111;color:#eee;font:16px/1.7 monospace;max-width:1000px;margin:auto;padding:30px}a{color:inherit;margin-right:20px}img{width:480px;max-width:100%;image-rendering:pixelated}code{color:white}</style><h1>RHYTHMER / TARGET GEN</h1><p>Local 0.1.1-beta3 candidate. Physical FM-1 validation pending.</p><p><a href="emulator/?fw=rhythmer&mhz=240">PLAY THE FIRMWARE →</a><a href="editor/?target=browser#projects">PROJECT WORKSPACE →</a></p><img src="GEN-Break.png" alt="Actual firmware: DRUNKEN HH, TARGET BREAK, tempo 87 preserved"><p>Hold HOME and turn SELECT, then release HOME. In GEN, knob 1 selects the genre; knob 4 selects ALL LOOP / ALL PARTS / ALL SONG / T1–T6 MIDI / BREAK. OCT+ generates. BREAK finds the machine wherever it is assigned.</p><p>Partial generation keeps tempo, key, sound, effects, automation, loop length and other tracks. Hip-hop Breaks use space and timing; fast-tempo hip-hop uses a half-time event grid. Jungle adds bounded answer rolls. GLO + G4 undoes the operation.</p><p><a href="GEN-TARGET.md">FULL GUIDE →</a></p></html>''')
pkg=O/'Rhythmer-0.1.1-beta3-local-test';pkg.mkdir(exist_ok=True)
shutil.copy2(B/'felucca.fwsc',pkg/'Rhythmer-0.1.1-beta3.fwsc');shutil.copy2(downloads/'Rhythmer-start.fm1save',pkg/'Rhythmer-start.fm1save');shutil.copy2(Q/'VALIDATION.json',pkg/'VALIDATION.json');shutil.copy2(R/'docs/six/GEN-TARGET.md',pkg/'GEN-TARGET.md');shutil.copy2(R/'rhythmer/LICENSE',pkg/'LICENSE');shutil.copytree(R/'rhythmer/LICENSES',pkg/'LICENSES',dirs_exist_ok=True);shutil.copy2(R/'rhythmer/LICENSING.md',pkg/'LICENSING.md');shutil.copytree(preview,pkg/'preview',dirs_exist_ok=True)
(pkg/'README.md').write_text('''# Rhythmer 0.1.1-beta3 — local test candidate

GEN knob 4 is TARGET: ALL LOOP / PARTS / SONG, T1–T6 MIDI, or BREAK. Partial generation uses the currently selected genre and preserves sound, tempo, SCL, loop length, automation and other tracks. BREAK resolves the singleton owner and never assigns or replaces a machine. Drunken Hip-Hop adds intentional push/pull and dynamics; at 120+ BPM hip-hop Breaks use a half-time event grid. Jungle uses stronger chops and bounded phrase-end rolls. See GEN-TARGET.md.

This FWSC includes both corrected Amen/Think sample banks, the full MD/Acid scope and all 59 GEN styles from beta2. The initial session remains empty, with Amen A selected. The updated editor/runtime is in preview; serve the folder on localhost rather than opening it as file://.

Validation binds this exact SHA to 354 native genre/track cases, loop-length/owner/undo checks, whole GEN regression and seven real-FW emulator cases, including actual button/knob generation while playback continues. No physical installation, listening or recovery for this exact image has been performed. This is a local test candidate, not a public deployment. Preserve a musical backup before any later device test and use the official V15 transition route. Keep power/USB connected during updates.

Break recording/composition rights are separate from code licenses. Bundled Amen/Think public redistribution clearance is not documented; attribution and checkboxes do not grant a license. Original sample sources and licensing notes remain in the included source tree. User audio can be replaced with the web editor.
''')
with tarfile.open(pkg/'Rhythmer-source.tar.gz','w:gz') as t:
 for path in ['rhythmer/firmware','rhythmer/tests','rhythmer/tools','rhythmer/LICENSE','rhythmer/LICENSES','rhythmer/LICENSING.md','tools/six','site/editor','site/native','site/emulator','site/vendor/upstream-editor','site/vendor/fm1-emu','docs/six']:
  p=R/path
  for f in ([p] if p.is_file() else sorted(p.rglob('*'))):
   if f.is_file() and '__pycache__' not in f.parts and f.name!='.DS_Store':t.add(f,arcname=str(f.relative_to(R)))
(pkg/'SHA256SUMS').write_text('\n'.join(sha(p)+'  '+str(p.relative_to(pkg)) for p in sorted(pkg.rglob('*')) if p.is_file() and p.name!='SHA256SUMS')+'\n')
zp=O/(pkg.name+'.zip')
with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(pkg.rglob('*')):
  if p.is_file():z.write(p,str(p.relative_to(O)))
print(json.dumps({'zip':str(zp),'firmware_sha256':digest,'validation':report},indent=2))

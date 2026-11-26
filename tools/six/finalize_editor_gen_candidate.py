#!/usr/bin/env python3
"""Freeze the local GEN/editor candidate after exact-image checks. Never deploys."""
import hashlib,json,re,shutil,tarfile,zipfile,wave
from pathlib import Path
R=Path(__file__).resolve().parents[2]
B=Path('/Volumes/SSD/Development/BuildCache/rhythmer/editor-gen-20261107')
Q=R/'qa/editor-gen-20261107';O=R/'outputs/editor-gen-20261107'
assert O.resolve().is_relative_to(Path('/Volumes/SSD/Development'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
fw=B/'felucca.fwsc';digest=sha(fw)
new=['BOUNCE HOUSE','90S HOUSE','G-FUNK','NOCTURNAL HH','TRIP HOP','LOFI HOUSE','ABSTRACT IDM','AMBIENT IDM','ATMOS BREAKS','DRUNKEN HH']
refined=['R&B','NEO SOUL','JAZZY CHORDS','BOOM BAP','JUNGLE','LIQUID DNB','UK GARAGE','FUTURE BASS',*new]
emu=json.loads((B/'upgrade-emulator-results.json').read_text())
expected={'upgrade-boot',*['upgrade-'+x for x in refined],*[f'upgrade-acid-{x}' for x in range(5)],*[f'upgrade-md-{x}' for x in range(14,19)],*[f'upgrade-ensemble-{x}' for x in range(2)]}
assert emu['firmware_sha256']==digest and set(emu['runs'])==expected
for name,d in emu['runs'].items():
 assert d['boots']==1 and d['fm1_mc_on']==1 and d['six_loop_mask']==3
 assert d['max_us']<emu['half_frames']/44100*1e6
 assert not any(d.get(x,0) for x in ['late','audio_lost','fm1_mc_lost','usb_underruns','usb_overruns','usb_missed'])
 assert d['peak_pcm16']==0 if name=='upgrade-boot' else d['peak_pcm16']>0
for a,b in [('md-one.pcm','md-two.pcm'),('hort-0.pcm','hort-1.pcm'),('six-drum-core-one.pcm','six-drum-core-two.pcm'),('six-break-core-one.pcm','six-break-core-two.pcm')]:assert (B/'regression'/a).read_bytes()==(B/'regression'/b).read_bytes()
logs={}
for name,markers in [('native-regression.log',['SEQ viewport regression: PASS','Hortator two-core PCM: PASS','NEXT UPGRADE: PASS','Drum named sound selection: PASS']),('upgrade-test.log',['NEXT UPGRADE: PASS']),('editor-test.log',['55 actual four-project']),('break-test.log',['PASS: 30'])]:
 text=(Q/name).read_text();assert all(x in text for x in markers),(name,markers)
 assert not any(x in text for x in ['FAIL','runtime error:','ERROR: AddressSanitizer']),name
 logs[name]=sha(Q/name)
conv=json.loads((Q/'break-upload-results.json').read_text());editor=json.loads((Q/'editor-results.json').read_text())
assert conv['passed']==30 and editor['passed']==55
buildlog=(Q/'build.log').read_text()
m=re.search(r'image (\d+) B of the (\d+) B slot \((\d+) B free\); RAM .data\+.bss (\d+) B of (\d+); pool (\d+) B, spare (\d+) B',buildlog);assert m and int(m[7])>=8192
seed=json.loads((B/'Rhythmer-start.fm1save').read_text());assert seed['hash']==digest and seed['startingProject']['tracksWithNotes']==[]
preview=O/'preview';assert json.loads((preview/'release.json').read_text())['sha256']==digest
assert sha(preview/'downloads/Rhythmer.fwsc')==digest
assert json.loads((preview/'downloads/Rhythmer-start.fm1save').read_text())==seed
assert sha(preview/'editor/workspace.wasm')==sha(B/'workspace.wasm')
order=json.loads((R/'docs/six/GEN-GENRE-ORDER.json').read_text());assert order['total']==59
metrics=[]
for line in (Q/'upgrade-test.log').read_text().splitlines():
 if line.startswith('GEN '):metrics.append(line)
report={'version':'0.1.1-beta2','product':'FM-1_748004','firmware_sha256':digest,'publicly_deployed':False,'physical_hardware_tested':False,'gen':{'retained_previous_styles':49,'total':59,'new_styles':new,'refined_profiles':18,'seeds_per_profile':12,'quality_seed_cases':216,'additional_repeatability_cases':20,'profile_results':metrics,'menu':order},'memory':dict(zip(['app_bytes','app_limit','app_free','data_bss','data_bss_limit','pool_bytes','pool_reserve'],map(int,m.groups()))),'emulator':{'cases':len(expected),'worst_render_us':max(x['max_us'] for x in emu['runs'].values()),'deadline_us':emu['half_frames']/44100*1e6,'faults_or_missed_audio':0,'test_window_ms':6500},'editor_checks':editor,'break_conversion_checks':conv,'projects':4,'sections_per_project':4,'backup_object_count':27,'polyphony':{'ordinary_per_track':8,'ordinary_dual_shared':12,'md_only_shared':4,'break_ordinary_voice_cost':0},'logs_sha256':logs,'workspace_wasm_sha256':sha(B/'workspace.wasm'),'sources_sha256':{str(p.relative_to(R)):sha(p) for directory in ['rhythmer/firmware','site/editor','site/native'] for p in sorted((R/directory).rglob('*')) if p.is_file() and '__pycache__' not in p.parts}}
(Q/'candidate-validation.json').write_text(json.dumps(report,indent=2)+'\n')
pkg=O/'Rhythmer-0.1.1-beta2-local-test';pkg.mkdir(exist_ok=True)
for src,dest in [(fw,'Rhythmer-0.1.1-beta2.fwsc'),(B/'Rhythmer-start.fm1save','Rhythmer-start.fm1save'),(Q/'candidate-validation.json','VALIDATION.json'),(R/'docs/six/NEXT-0.1.1.md','CHANGES.md'),(R/'docs/six/GEN-STYLE-DESIGN.md','GEN-STYLE-DESIGN.md'),(R/'rhythmer/LICENSE','LICENSE'),(R/'rhythmer/LICENSING.md','LICENSING.md')]:shutil.copy2(src,pkg/dest)
shutil.copytree(R/'rhythmer/LICENSES',pkg/'LICENSES',dirs_exist_ok=True)
samples=Path('/Volumes/SSD/Development/BuildCache/rhythmer/next-20261107/samples')
for f in ['break-samples.json','level-match.json']:shutil.copy2(samples/f,pkg/f.upper())
(pkg/'README.md').write_text('''# Rhythmer 0.1.1-beta2 — local test candidate

Includes both Amen/Think two-bar banks in the FWSC; Think is the corrected drums-only level-matched source. Includes the complete 55-sound MD bank, four Hortator Acid presets plus X0X, individual drum-lane selection, 19 drum kits, all 59 GEN styles and an empty initial session. MODERN and CLASSIC Hortator banks remain out of scope.

GEN: HOME + SELECT, choose GENRE, OCT+ generates tracks 1–4. New names: BOUNCE HOUSE, 90S HOUSE, G-FUNK, NOCTURNAL HH, TRIP HOP, LOFI HOUSE, ABSTRACT IDM, AMBIENT IDM, ATMOS BREAKS, DRUNKEN HH. The existing 49 styles remain available. Serum remains eligible, with no additional automatic instance when a kept track already uses it.

The local preview folder is an isolated static website containing the real firmware emulator, four-project editor and improved two-bar uploader. Serve it using a localhost HTTP server; do not open editor/index.html as a file URL. It needs Chrome/Edge Web Locks, WebAssembly and browser storage. Connect USB only deliberately; this package does not initiate an install. No public deployment has been performed.

Browser workspace: four separate projects, each with sections A–D. SAVE CURRENT MUSIC creates/replaces a section. SAVE & SWITCH retains the outgoing music. Download the musical archive to preserve all projects/settings/presets; sample audio is separate. SAVE FOR PLAY exports the current music and both audio slots for the emulator. Browser storage is not a substitute for downloaded backups.

Break conversion: select known source BPM and exactly two bars in 4/4. Compare the original crop and the real 160-BPM PCM12 preview. Classic repitch changes pitch with tempo; export at 160 BPM in your DAW first if pitch preservation is required. Conversion runs in a browser worker; USB upload receives a fixed 80-KiB slot and validates payload CRC before committing its header. Current device samples cannot be downloaded with this protocol. Musical backups do not contain audio.

Validation is bound to the exact firmware SHA in VALIDATION.json. Native regression checks pass. Actual-FW community emulation passes 31 cases; its timing is not a physical FM-1 CPU measurement. Browser/C-WASM and conversion tests pass. This exact candidate has not been installed, listened to or load-tested on the physical FM-1. Back up first before any later installation, use the official V15 route and keep power/USB connected. Recovery work remains paused.

Sample recording/composition rights remain separate from the firmware code licenses. Bundled Amen/Think public redistribution permission is not documented. Credits and user checkboxes do not grant a sample license; source and attribution details are included. User-provided audio rights are not assessed.
''')
# Include the reviewed local editor/runtime rather than an installer that serves an older release.
shutil.copytree(preview,pkg/'preview',dirs_exist_ok=True)
source=pkg/'Rhythmer-0.1.1-beta2-source.tar.gz'
with tarfile.open(source,'w:gz') as t:
 for path in ['rhythmer/firmware','rhythmer/tools','rhythmer/tests','rhythmer/LICENSE','rhythmer/LICENSES','rhythmer/LICENSING.md','site/editor','site/native','site/tests','site/vendor/upstream-editor','site/vendor/fm1-emu','site/emulator','tools/six','docs/six']:
  p=R/path
  for f in ([p] if p.is_file() else sorted(p.rglob('*'))):
   if f.is_file() and '__pycache__' not in f.parts and f.name!='.DS_Store':t.add(f,arcname=str(f.relative_to(R)))
checks=[sha(p)+'  '+str(p.relative_to(pkg)) for p in sorted(pkg.rglob('*')) if p.is_file() and p.name!='SHA256SUMS']
(pkg/'SHA256SUMS').write_text('\n'.join(checks)+'\n')
zpath=O/(pkg.name+'.zip')
with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for f in sorted(pkg.rglob('*')):
  if f.is_file():z.write(f,str(f.relative_to(O)))
print(json.dumps({'zip':str(zpath),'zip_bytes':zpath.stat().st_size,'firmware_sha256':digest,'emulator_cases':31,'worst_us':report['emulator']['worst_render_us'],'app_free':report['memory']['app_free']},indent=2))

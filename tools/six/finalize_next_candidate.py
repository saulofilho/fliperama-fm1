#!/usr/bin/env python3
"""Package the local 0.1.1 candidate only after exact-FW emulation/native checks."""
import hashlib,json,os,re,shutil,tarfile,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[2]
B=Path(os.environ.get('RHYTHMER_BUILD_DIR','/Volumes/SSD/Development/BuildCache/rhythmer/next-20261107'))
Q=R/'qa/next-version-20261107';O=R/'outputs/next-version-20261107'
assert O.resolve().is_relative_to(Path('/Volumes/SSD/Development')),'Register the output with ssd-qa-output first'
fw=B/'felucca.fwsc';sha=hashlib.sha256(fw.read_bytes()).hexdigest()
emu=json.loads((B/'upgrade-emulator-results.json').read_text());assert emu['firmware_sha256']==sha
expected={'upgrade-boot',*[f'upgrade-acid-{i}' for i in range(5)],*[f'upgrade-md-{i}' for i in range(14,19)],*[f'upgrade-ensemble-{i}' for i in range(2)],*['upgrade-'+n for n in ['R&B','NEO SOUL','JAZZY CHORDS','BOOM BAP','JUNGLE','LIQUID DNB','UK GARAGE','FUTURE BASS']]}
assert set(emu['runs'])==expected
for name,d in emu['runs'].items():
 assert d['boots']==1 and d['fm1_mc_on']==1 and d['six_loop_mask']==3
 assert d['max_us']<emu['half_frames']/44100*1e6
 assert not any(d.get(k,0) for k in ['late','audio_lost','fm1_mc_lost','usb_underruns','usb_overruns','usb_missed'])
 assert (d['peak_pcm16']==0) if name=='upgrade-boot' else d['peak_pcm16']>0
logs={}
for name,marker in [('regression-final.log','SEQ viewport regression: PASS'),('upgrade-test.log','NEXT UPGRADE: PASS'),('drum-voice.log','Drum named sound selection: PASS'),('hortator-core-final.log','Hortator two-core PCM: PASS'),('editor-test.log','31 C/WASM')]:
 data=(Q/name).read_text();assert marker in data,(name,marker)
 assert not any(x in data for x in ['FAIL','runtime error:','ERROR: AddressSanitizer']),name
 logs[name]=hashlib.sha256(data.encode()).hexdigest()
assert (B/'md-one.pcm').read_bytes()==(B/'md-two.pcm').read_bytes()
assert (B/'hort-0.pcm').read_bytes()==(B/'hort-1.pcm').read_bytes()
assert json.loads((Q/'import-reproducibility.json').read_text())['match']
seed=json.loads((B/'Rhythmer-start.fm1save').read_text());assert seed['hash']==sha and seed['startingProject']['tracksWithNotes']==[]
level=json.loads((B/'samples/level-match.json').read_text());assert level['clipped_samples']==0 and level['true_peak_dbfs']<=-1 and level['frames']==48000 and level['seam_jump_pcm16']==0
buildlog=(Q/'upgrade-build.log').read_text();m=re.search(r'image (\d+) B of the (\d+) B slot \((\d+) B free\); RAM .data\+.bss (\d+) B of (\d+); pool (\d+) B, spare (\d+) B',buildlog);assert m and int(m[7])>=8192
report={'version':'0.1.1-beta','identity':'FM-1_748003','firmware_sha256':sha,'physical_hardware_tested':False,'publicly_deployed':False,'emulator_cases':len(expected),'worst_emulator_us':max(d['max_us'] for d in emu['runs'].values()),'deadline_us':emu['half_frames']/44100*1e6,'faults_or_audio_misses':0,'memory':dict(zip(['app_bytes','app_limit','app_free','data_bss','data_bss_limit','pool_bytes','pool_reserve'],map(int,m.groups()))),'md':{'kernels':21,'factory_sounds':55,'articulations':57,'factory_kits':19,'independent_lane_roundtrips':440},'acid_presets':['X0X ACID','HT SQUELCH','HT DEEPBASS','HT SCREAMER','HT SQUAREAC'],'gen_genres':['R&B','NEO SOUL','JAZZY CHORDS','BOOM BAP','JUNGLE','LIQUID DNB','UK GARAGE','FUTURE BASS'],'gen_seed_checks':96,'projects':4,'polyphony':{'per_track':8,'dual_shared':12,'single_shared':8,'md_only_shared':4},'level_match':level,'native_logs_sha256':logs,'source_sha256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((R/'rhythmer/firmware').rglob('*')) if p.is_file()}}
(Q/'candidate-validation.json').write_text(json.dumps(report,indent=2)+'\n')
pkg=O/'Rhythmer-0.1.1-beta-local-test';pkg.mkdir(exist_ok=True)
shutil.copy2(fw,pkg/'Rhythmer-0.1.1-beta.fwsc');shutil.copy2(B/'Rhythmer-start.fm1save',pkg/'Rhythmer-start.fm1save');shutil.copy2(Q/'candidate-validation.json',pkg/'VALIDATION.json');shutil.copy2(R/'docs/six/NEXT-0.1.1.md',pkg/'CHANGES.md');shutil.copy2(R/'rhythmer/LICENSE',pkg/'LICENSE');shutil.copytree(R/'rhythmer/LICENSES',pkg/'LICENSES',dirs_exist_ok=True);shutil.copy2(R/'rhythmer/LICENSING.md',pkg/'LICENSING.md');shutil.copy2(B/'samples/break-samples.json',pkg/'BREAK-SAMPLES.json');shutil.copy2(O/'Drum-Voice.png',pkg/'Drum-Voice.png')
(pkg/'README.md').write_text('''# Rhythmer 0.1.1 beta — local test candidate

This candidate includes both two-bar Amen/Think breaks, all 55 Hortator MD sounds, four Hortator Acid presets and original X0X, the individual drum-sound browser, 19 drum kits, eight enhanced/new GEN genres and empty initial sequences.

DRUM VOICE: select a Drum track, press EDIT to SOUND / SELECT. Knobs: LANE, BANK, SOUND, LEVEL. Play the selected lane key to audition. Save the project/section to retain the kit. The section kit is shared by Drum tracks, as in JIANT. Existing custom projects keep their stored kit; reload a factory kit to use its updated closed hats.

The FWSC includes both sample banks. There is no separate sample-adding procedure. Rhythmer-start.fm1save is an empty starting session for the community FM-1 emulator. Export a backup before resetting an existing browser save. The public website/installer still serves the previous public release; this local candidate has not been deployed.

Native tests and actual-FW community-emulator checks pass. Physical listening, CPU peaks, install transfer and V15 recovery for this exact candidate have not been tested. Back up the FM-1 before any later physical installation; use the V15 route. Do not disconnect power/USB during an update.

See CHANGES.md for scope, adaptation details, licenses and remaining physical checks; VALIDATION.json binds results to the exact firmware SHA. The included source snapshot reproduces the firmware changes; build dependencies/toolchains are described in the source documentation.
''')
source=pkg/'Rhythmer-0.1.1-beta-source.tar.gz'
paths=['rhythmer/firmware','rhythmer/tools','rhythmer/LICENSE','rhythmer/LICENSES','rhythmer/LICENSING.md','tools/six','docs/six','site/native','site/editor','site/src','site/tests/test_editor.py']
with tarfile.open(source,'w:gz') as t:
 for rel in paths:
  p=R/rel
  if p.is_file():t.add(p,arcname=rel)
  else:
   for f in sorted(p.rglob('*')):
    if f.is_file() and '__pycache__' not in f.parts and f.name!='.DS_Store':t.add(f,arcname=str(f.relative_to(R)))
checks=[]
for p in sorted(pkg.rglob('*')):
 if p.is_file() and p.name!='SHA256SUMS':checks.append(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(pkg)))
(pkg/'SHA256SUMS').write_text('\n'.join(checks)+'\n')
zip_path=O/(pkg.name+'.zip')
with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(pkg.rglob('*')):
  if p.is_file():z.write(p,str(p.relative_to(O)))
print(json.dumps({'firmware_sha256':sha,'zip':str(zip_path),'emulator_cases':len(expected),'max_us':report['worst_emulator_us'],'app_free':report['memory']['app_free']},indent=2))

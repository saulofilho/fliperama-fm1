#!/usr/bin/env python3
"""Bind the hardware-diagnosed candidate to fresh tests; no hardware writes."""
from pathlib import Path
import hashlib,json,re,shutil
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'rhythmer/build-ssd';Q=R/'qa/hardware-fix'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
fw=sha(O/'felucca.fwsc');app=sha(O/'felucca.bin')
nav=json.loads((O/'six-current-results.json').read_text());think=json.loads((O/'think-drum-results.json').read_text());device=json.loads((Q/'device-after-results.json').read_text())
loader=json.loads((R/'qa/embedded-install/loader-results.json').read_text());assert loader['firmwareSha256']==fw
for report in (nav,think,device):
 assert report['firmware_sha256']==fw,'Stale emulator evidence'
 for name,d in report['runs'].items():
  assert d['boots']==1 and d['max_us']<512/44100*1e6 and not any(d.get(x,0) for x in ['late','audio_lost','fm1_mc_lost','usb_underruns','usb_overruns','usb_missed']),name
for log in ('hardware-fix-host.log','hardware-fix-governor.log','hardware-fix-loader.log'):
 s=(O/log).read_text();assert not any(x in s for x in ('FAIL','runtime error:','ERROR: AddressSanitizer')),log
assert 'Rhythmer actual-budget governor: PASS' in (O/'hardware-fix-governor.log').read_text()
assert 'Integrated loader:' in (O/'hardware-fix-loader.log').read_text()
assert 'Rhythmer ensemble and chord ownership: PASS' in (O/'hardware-fix-host.log').read_text()
build=(O/'hardware-fix-build.log').read_text();assert 'build: checks failed' not in build and 'package ' in build
samples=[]
for i,name in enumerate(('amen-160.slot','think-160.slot')):
 p=R/'build/six-ssd'/name;raw=R/f'qa/embedded-install/hardware-bank-{i}-raw.bin'
 assert p.read_bytes()==raw.read_bytes();samples.append({'slot':i,'sha256':sha(p),'previousDeviceRawBytesMatch':True})
shutil.copy2(O/'felucca.fwsc',O/'Rhythmer.fwsc')
for name in ('Rhythmer-demo.fm1save','Rhythmer-six-track-test.fm1save'):
 assert json.loads((O/name).read_text())['hash']==fw
for kind,count in (('acid',2),('break',3)):
 panel=Image.new('RGB',(480*count,480),'black')
 for i in range(count):panel.paste(Image.open(O/f'six-nav-{kind}-{i+1}.ppm').crop((370,42,850,522)),(480*i,0))
 panel.save(O/f'Rhythmer-{kind}-tabs.png')
Image.open(O/'six-nav-strict.ppm').crop((370,42,850,522)).save(O/'Rhythmer-home.png')
manifest=json.loads((O/'Rhythmer-artifacts.json').read_text());manifest.pop('audio_baseline',None)
manifest.update(firmware_sha256=fw,app_sha256=app,physical_hardware_tested=False,embedded_factory_banks=True,separate_audio_upload=False,
 validation=['qa/hardware-fix/FINAL-VALIDATION.json','six-current-results.json','think-drum-results.json','qa/hardware-fix/device-after-results.json','qa/embedded-install/loader-results.json'],
 sample_manifest=json.loads((R/'build/six-ssd/break-samples.json').read_text()),
 source_sha256={str(p.relative_to(R)):sha(p) for p in sorted((R/'rhythmer/firmware').rglob('*')) if p.is_file()})
(O/'Rhythmer-artifacts.json').write_text(json.dumps(manifest,indent=2)+'\n')
before=json.loads((Q/'device-before-results.json').read_text())
result=dict(firmwareSha256=fw,appSha256=app,physicalHardwareTested=False,candidateWrittenToHardware=False,publicUploaded=False,localOnly=True,
 samples=samples,previousHardwarePackage=sha(Q/'before-felucca.fwsc'),
 hardwareFindings=['Both complete raw NOR audio slots matched the prepared assets byte-for-byte','XIP header reads differed from raw SPI reads; the boot path omitted fl_plain_window_init','Dual core was active; live pre-fix playback measured 69-90% CPU and 26 additional lost halves over approximately nine seconds'],
 changes=['Initialise the plain XIP data window before persistence and sample scanning','Place four unchanged 303 DSP hot loops in bounded RAM; group its remaining private helpers ahead of UI code','Include measured post-FX, master and output work in core balancing','Automatic load relief uses a shared ceiling of ten voices, restoring twelve when calm; existing emergency protection remains'],
 nativeScenarios=sum(len(x['runs']) for x in (nav,think,device)),emulatorBefore=before['runs'],emulatorAfter=device['runs'],loader=loader,
 hardwareFollowUp='Reinstall candidate by explicit user action; verify both banks are recognised and repeat the same pattern on the physical FM-1. Emulator timings do not predict physical CPU percentages.')
(Q/'FINAL-VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n');shutil.copy2(Q/'FINAL-VALIDATION.json',R/'qa/performance/FINAL-VALIDATION.json')
(R/'docs/six/CURRENT-VALIDATION.md').write_text(f'''# Current Rhythmer candidate

SHA-256: `{fw}`. App: `{app}`. Local only; this candidate has not been installed or audio-validated on physical hardware.

The previous package was installed on the owner's FM-1 and failed bank recognition. Read-only CDC diagnostics confirmed both full 80 KiB raw sample banks match the prepared Amen and corrected Think slots exactly. XIP reads returned different bytes. The firmware omitted the plain-window initialisation call; the candidate calls it before persistence and sample scanning. The old installer correctly stopped at its final read-only bank check. This candidate retains that check and reports which bank is unreadable.

Pre-fix real playback used both cores and showed 69–90% CPU, 26 additional lost audio halves in about nine seconds, and a recorded worst render above the 11.6 ms deadline. Four unchanged 303 hot loops now use the remaining bounded RAM code space, and private helpers are grouped in the audio layout. Core balancing accounts for serial output work. On measured load, the automatic ceiling becomes ten shared voices instead of twelve; calm operation restores twelve. Primary per-track notes retain protection; existing emergency overload rules remain.

Fresh host sanitizers, loader tests, {result['nativeScenarios']} native scenarios and a replay of the device's captured 121 BPM pattern validate this candidate. Physical CPU reduction and audible crackle resolution remain to be confirmed after the user installs it. Earlier byte-identical-app claims and old scenario counts are historical evidence, not validation of this changed app.

Both samples remain two bars / 160 BPM / mono 16 kHz / PCM12. Corrected Think SHA-256: `{samples[1]['sha256']}`. They are embedded in the firmware; no separate audio upload stage is used. No public upload or candidate device write was performed. See `qa/hardware-fix/FINAL-VALIDATION.json`.
''')
print('Hardware-fix candidate finalized',fw,'native scenarios',result['nativeScenarios'])

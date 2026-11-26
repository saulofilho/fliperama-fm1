#!/usr/bin/env python3
"""Bind an embedded-bank release to loader tests and unchanged audio-app evidence."""
from pathlib import Path
import json,hashlib,shutil
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'rhythmer/build-ssd';Q=R/'qa/embedded-install'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
fw=sha(O/'felucca.fwsc');app=sha(O/'felucca.bin');assert app==sha(Q/'previous-app.bin')
loader=json.loads((Q/'loader-results.json').read_text());assert loader['firmwareSha256']==fw and loader['appUnchanged']
for log in ['loader-positive.log','loader-legacy.log','bad-marker.log','bad-range.log','bad-bank-header.log','bad-bank-payload.log','ota-stage.log']:
 s=(Q/log).read_text();assert 'FAIL' not in s and 'runtime error' not in s and 'AddressSanitizer' not in s,log
assert 'ota test passed' in (Q/'ota-stage.log').read_text()
assert 'loader test passed' in (Q/'loader-positive.log').read_text() and 'loader test passed' in (Q/'loader-legacy.log').read_text()
nav=json.loads((O/'six-current-results.json').read_text());think=json.loads((O/'think-drum-results.json').read_text())
for report in [nav,think]:
 assert report['firmware_sha256']==fw
 for name,d in report['runs'].items():
  assert d['boots']==1 and d['max_us']<512/44100*1e6 and not any(d.get(x,0) for x in ['late','audio_lost','fm1_mc_lost','usb_underruns','usb_overruns','usb_missed']),name
for label in ['amen-160','think-160']:assert (R/'build/six-ssd'/(label+'.slot')).read_bytes()==(Q/(label+'.slot')).read_bytes()
assert think['think_slot_sha256']==sha(R/'build/six-ssd/think-160.slot')
shutil.copy2(O/'felucca.fwsc',O/'Rhythmer.fwsc')
for name in ['Rhythmer-demo.fm1save','Rhythmer-six-track-test.fm1save']:assert json.loads((O/name).read_text())['hash']==fw
for kind,count in [('acid',2),('break',3)]:
 panel=Image.new('RGB',(480*count,480),'black')
 for i in range(count):panel.paste(Image.open(O/f'six-nav-{kind}-{i+1}.ppm').crop((370,42,850,522)),(480*i,0))
 panel.save(O/f'Rhythmer-{kind}-tabs.png')
Image.open(O/'six-nav-strict.ppm').crop((370,42,850,522)).save(O/'Rhythmer-home.png')
previous=json.loads((Q/'previous-artifacts.json').read_text());manifest={**previous,'firmware_sha256':fw,'app_sha256':app,'physical_hardware_tested':False,'embedded_factory_banks':True,'separate_audio_upload':False,'audio_baseline':{'firmware_sha256':previous['firmware_sha256'],'app_sha256':app,'native_scenarios':53,'scope':'Prior 53 scenarios apply to byte-identical app code; the integrated loader/package is tested separately.'},'validation':['qa/embedded-install/loader-results.json','qa/embedded-install/loader-positive.log','qa/embedded-install/ota-stage.log','six-current-results.json','think-drum-results.json'],'sample_manifest':json.loads((R/'build/six-ssd/break-samples.json').read_text())}
manifest['source_sha256']={str(p.relative_to(R)):sha(p) for p in sorted((R/'rhythmer/firmware').rglob('*')) if p.is_file()}
(O/'Rhythmer-artifacts.json').write_text(json.dumps(manifest,indent=2)+'\n')
result=dict(firmwareSha256=fw,appSha256=app,localOnly=True,publicUploaded=False,hardwareWritten=False,physicalHardwareTested=False,embeddedFactoryBanks=True,separateSampleUpload=False,packageBytes=(O/'felucca.fwsc').stat().st_size,loader=loader,newNativeScenarios=len(nav['runs'])+len(think['runs']),audioBaseline=manifest['audio_baseline'],think=dict(slotSha256=think['think_slot_sha256'],rebuiltFromSuppliedOriginals=True,bytesMatchReviewedDrumEdit=True,bars=2,bpm=160,sampleRate=16000,bits=12,seamJumpPcm16=0),browserSimulation='pending',webChecks='pending')
(Q/'FINAL-VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n')
(R/'docs/six/EMBEDDED-INSTALL.md').write_text(f'''# Rhythmer integrated factory-audio installation

Current local firmware SHA-256: `{fw}`; {(O/'felucca.fwsc').stat().st_size:,} bytes. The app is byte-identical to the previously reviewed polyphony build: `{app}`. Previous 53 audio/navigation scenarios remain evidence for that app; the new loader/package has its own tests. Physical installation and power-loss recovery are not established by these host/native simulations.

The .fwsc itself now contains both fixed 80 KiB audio slots. A RHYBRK1 package marker identifies only `[0xA0000,0xC8000)`. The loader writes the original app window plus these two fixed banks; it never writes intervening project sectors or song/settings sectors. The entire package CRC and both payload CRC32 values are checked before erase; sectors are compared and read back; each bank's header sector is committed last; final NOR payload CRC32 checks precede success and resume-record clearing. Legacy code-only packages remain supported by the loader.

Portable loader tests, under ASan/UBSan, verify exact resulting banks, project/settings/head preservation, header-last order, changed-transfer retries, idempotent reinstallation, five interrupted-write/resume cases, and four malformed-content cases with valid outer CRCs rejected before erase. The actual first-stage OTA implementation also passes its host test with the new compressed loader. Nine new native boot/navigation runs and two Think B / A-B sequencing runs use the exact integrated package. Newly cold-booted firmware detects both embedded banks.

The installer no longer contains the factory-loop checkbox, repair action or A/B upload stages. It performs one package transfer, then queries bank validity read-only. Installing this factory package always replaces A/B audio; musical archives and original custom audio should be retained. Rights and independence acknowledgements remain. Official V15 restoration is unchanged.

Think B was regenerated from the owner's supplied lyncollins_think_1.wav and lyncollins_think_2.wav and matches the reviewed drum edit byte-for-byte: `{think['think_slot_sha256']}`. It assembles source 1 beats 0–3 + source 2 beats 3–4, then source 1 beats 0–1 + source 2 beats 1–4, excluding the previously identified pitched tail/carry-in. Output is two bars / 160 BPM / mono 16 kHz / PCM12 / 48,000 samples, with zero endpoint/splice jump. The installer offers an optional preview of the exact included edit. This verifies provenance, edit construction, slot/CRC integrity and native playback; it is not a claim of isolated-stem separation or a new listening review.

No GitHub/public upload or physical device write was performed. Full validation: `qa/embedded-install/FINAL-VALIDATION.json`.
''')
print('Integrated package finalized',fw,'native runs',result['newNativeScenarios'])

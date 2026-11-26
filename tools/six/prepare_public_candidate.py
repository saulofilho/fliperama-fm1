#!/usr/bin/env python3
"""Finalize a separately tested public candidate without replacing the owner's build."""
from pathlib import Path
import hashlib,json,os,shutil
from PIL import Image
R=Path(__file__).resolve().parents[2]
O=Path(os.environ['RHYTHMER_BUILD_DIR']);Q=Path(os.environ.get('RHYTHMER_RELEASE_QA',R/'qa/launch'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
digest=sha(O/'felucca.fwsc')
nav=json.loads((O/'six-current-results.json').read_text())
think=json.loads((O/'think-drum-results.json').read_text())
br=json.loads((Q/'break/native-results.json').read_text())
loader=json.loads((Q/'loader/loader-results.json').read_text())
assert loader['firmwareSha256']==digest
for report in (nav,think,br):
 assert report['firmware_sha256']==digest,'Stale candidate validation'
 for name,v in report['runs'].items():
  assert v['boots']==1 and v['max_us']<512/44100*1e6,name
  assert not any(v.get(k,0) for k in ('late','audio_lost','fm1_mc_lost','usb_underruns','usb_overruns','usb_missed')),name
assert 'Break sequence authoring and automation: PASS' in (O/'host.log').read_text()
assert 'FM-1_748001' in (O/'build.log').read_text()
assert b'ota-FM-1_748001' in (O/'loader/loader.bin').read_bytes(),'Loader identity is not project-specific'
shutil.copy2(O/'felucca.fwsc',O/'Rhythmer.fwsc')
for kind,count in (('acid',2),('break',3)):
 panel=Image.new('RGB',(480*count,480),'black')
 for i in range(count):panel.paste(Image.open(O/f'six-nav-{kind}-{i+1}.ppm').crop((370,42,850,522)),(480*i,0))
 panel.save(O/f'Rhythmer-{kind}-tabs.png')
Image.open(O/'six-nav-strict.ppm').crop((370,42,850,522)).save(O/'Rhythmer-home.png')
shutil.copy2(R/'rhythmer/build-ssd/md-one.pcm.ui.ppm',O/'md-one.pcm.ui.ppm')
manifest={'version':'0.1.0-beta.1','product':'FM-1_748001','firmware_sha256':digest,'app_sha256':sha(O/'felucca.bin'),'physical_hardware_tested':False,'embedded_factory_banks':True,'source_sha256':{str(p.relative_to(R)):sha(p) for p in sorted((R/'rhythmer/firmware').rglob('*')) if p.is_file()}}
(O/'Rhythmer-artifacts.json').write_text(json.dumps(manifest,indent=2)+'\n')
status={'version':manifest['version'],'product':manifest['product'],'firmwareSha256':digest,'appSha256':manifest['app_sha256'],'nativeScenarios':sum(len(r['runs']) for r in (nav,think,br)),'physicalCurrentCandidateTested':False,'previousOwnerTest':json.loads((R/'site/site.config.json').read_text())['ownerTest'],'samples':json.loads((R/'site/audio-rights.json').read_text()),'publicRepository':None,'pagesURL':None,'githubReleasePublished':False,'hubSubmitted':False,'hubListed':False,'publicUploadPerformed':False}
if (Q/'native-results.json').exists():
 extra=json.loads((Q/'native-results.json').read_text());assert extra['firmware_sha256']==digest
 status.update(nativeScenarios=status['nativeScenarios']+len(extra['runs']),breakModulation=extra)
(Q/'CANDIDATE.json').write_text(json.dumps(status,indent=2)+'\n')
print('Separate public candidate ready:',digest,'native scenarios:',status['nativeScenarios'])

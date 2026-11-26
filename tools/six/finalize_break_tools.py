#!/usr/bin/env python3
"""Finalize the Break authoring release only after fresh candidate tests."""
from pathlib import Path
import hashlib,json,runpy,shutil
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'rhythmer/build-ssd';Q=R/'qa/break-seq-tools'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
fw=sha(O/'felucca.fwsc');native=json.loads((Q/'native-results.json').read_text());assert native['firmware_sha256']==fw
assert len(native['runs'])==9
for name in ('break-tools-host.log','break-tools-compat.log','break-tools-integration.log'):
 s=(O/name).read_text();assert not any(x in s for x in ('FAIL','runtime error:','ERROR: AddressSanitizer')),name
assert 'Break sequence authoring and automation: PASS' in (O/'break-tools-host.log').read_text()
assert 'SIX integration: PASS (0 failures)' in (O/'break-tools-integration.log').read_text()
old=json.loads((Q/'before-Rhythmer-artifacts.json').read_text())
unchanged=['audio.c','fx.c','voice.c','six_engines.c']
for n in unchanged:
 p=R/'rhythmer/firmware/src'/n;assert sha(p)==old['source_sha256'][str(p.relative_to(R))],n
for p in (R/'rhythmer/firmware/six').iterdir():
 if p.is_file():assert sha(p)==old['source_sha256'][str(p.relative_to(R))],p.name
# Preserve the previous hardware-fix report as historical evidence. That
# finalizer checks the fresh nav, Think and captured-device runs for this hash.
runpy.run_path(str(R/'tools/six/finalize_hardware_fix.py'),run_name='__main__')
result=json.loads((R/'qa/hardware-fix/FINAL-VALIDATION.json').read_text())
result.update(feature='Break SEQ authoring and saved automation',breakToolsNative=native['runs'],newNativeScenarios=result['nativeScenarios']+len(native['runs']),unchangedAudioSources=unchanged,
 sharedGenerator='rhythmer/firmware/src/break_sequence.c',controls='docs/six/BREAK-SEQUENCE-TOOLS.md',browserChecks='pending')
(Q/'FINAL-VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n');shutil.copy2(Q/'FINAL-VALIDATION.json',R/'qa/performance/FINAL-VALIDATION.json')
Image.open(O/'break-tools-menu.ppm').crop((370,42,850,522)).save(Q/'break-seq-menu.png')
manifest=json.loads((O/'Rhythmer-artifacts.json').read_text());manifest['validation'].append('qa/break-seq-tools/FINAL-VALIDATION.json');manifest['breakSequenceTools']=True
(O/'Rhythmer-artifacts.json').write_text(json.dumps(manifest,indent=2)+'\n')
p=R/'docs/six/CURRENT-VALIDATION.md';s=p.read_text();s+=f'\n## Break SEQ extension\n\nThis candidate adds STRAIGHT / MUTATE / RANDOM and Break-only held-SEQ tools, saved periodic actions and ORBIT/DRIFT, using the shared pattern generator. All nine additional native scenarios and host authoring/automation checks pass. Total fresh native scenarios: {result["newNativeScenarios"]}. Detailed controls: [BREAK-SEQUENCE-TOOLS.md](BREAK-SEQUENCE-TOOLS.md). The earlier hardware fixes and load-sensitive ten-voice ceiling remain. Synth/drum/Acid/Break DSP sources are unchanged from the previous candidate. No physical flash or public upload was performed.\n';p.write_text(s)
print('Break SEQ candidate finalized',fw,'fresh native scenarios',result['newNativeScenarios'])

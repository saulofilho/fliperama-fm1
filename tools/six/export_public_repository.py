#!/usr/bin/env python3
"""Prepare a fresh curated repository; never pushes or publishes it."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,re,os
R=Path(__file__).resolve().parents[2]
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True,type=Path);ap.add_argument('--site',required=True,type=Path);ap.add_argument('--owner');a=ap.parse_args()
out=a.output.resolve();assert out.is_relative_to(Path('/Volumes/SSD/Development'))
if out.exists() and any(out.iterdir()):raise SystemExit('Refusing to replace a non-empty export tree')
out.mkdir(parents=True,exist_ok=True)
def tree(src,dst):
 shutil.copytree(R/src,out/dst,ignore=shutil.ignore_patterns('__pycache__','.DS_Store','*.o','build','build-ssd','.git'))
for src,dst in [('rhythmer/firmware','rhythmer/firmware'),('rhythmer/tools','rhythmer/tools'),('rhythmer/assets','rhythmer/assets'),('rhythmer/tests','rhythmer/tests'),('rhythmer/LICENSES','rhythmer/LICENSES'),('site/src','site/src'),('site/editor','site/editor'),('site/emulator','site/emulator'),('site/installer','site/installer'),('site/native','site/native'),('site/vendor','site/vendor')]:tree(src,dst)
for n in ('LICENSE','LICENSING.md','BUILDING.md'):shutil.copy2(R/'rhythmer'/n,out/'rhythmer'/n)
for n in ('LICENSE','fmhub.json'):shutil.copy2(R/n,out/n)
for n in ('audio-rights.json','LEGAL-NOTICE.txt','public.config.json'):shutil.copy2(R/'site'/n,out/'site'/n)
shutil.copy2(R/'site/LEGAL-NOTICE.txt',out/'LEGAL-NOTICE.txt');shutil.copy2(R/'site/audio-rights.json',out/'audio-rights.json')
(out/'docs').mkdir();shutil.copy2(R/'docs/six/THIRD_PARTY.md',out/'docs/THIRD_PARTY.md')
for name in ('BREAK-SEQUENCE-TOOLS.md','BREAK-MODULATION.md','MACHINES-LFO-STORAGE.md','GARDEN-MODELS.md'):
 p=R/'docs/six'/name
 if p.exists():shutil.copy2(p,out/'docs'/name)
(out/'docs/launch').mkdir();shutil.copy2(R/'docs/launch/card.png',out/'docs/launch/card.png')
for name in ('ACID.md','BREAK.md'):shutil.copy2(R/'docs/launch'/name,out/'docs'/name)
if (R/'docs/motion').exists():shutil.copytree(R/'docs/motion',out/'docs/motion')
if (R/'site/media').exists():shutil.copytree(R/'site/media',out/'site/media')
(out/'tools/six').mkdir(parents=True)
for name in ('capture_web_motion.c','render_web_motion.py'):shutil.copy2(R/'tools/six'/name,out/'tools/six'/name)
(out/'HARDWARE-TEST-STATUS.json').write_text(json.dumps(json.loads((R/'site/public.config.json').read_text())['ownerTest'],indent=2)+'\n')
shutil.copy2(R/'docs/launch/README-public.md',out/'README.md')
(out/'assets/breaks').mkdir(parents=True)
for name in ('amen-160.slot','think-160.slot','break-samples.json'):shutil.copy2(R/'build/six-ssd'/name,out/'assets/breaks'/name)
shutil.copytree(a.site,out/'www')
for name in ('tests.html','tests.mjs','ui-tests.html','ui-fixture.mjs','fake.mjs'):
 p=out/'www/installer'/name
 if p.exists():p.unlink() # disposable generated test surfaces inside this new export only
shutil.copy2(out/'www/downloads/THIRD-PARTY-AUDIO.txt',out/'THIRD-PARTY-AUDIO.txt')
status=json.loads((Path(os.environ.get('RHYTHMER_RELEASE_QA',R/'qa/launch'))/'CANDIDATE.json').read_text());status['previousOwnerTest'].pop('notConfirmed',None)
status['sourceFiles']={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((out/'rhythmer/firmware').rglob('*')) if p.is_file()}
(out/'RELEASE-VALIDATION.json').write_text(json.dumps(status,indent=2)+'\n')
repo=f'{a.owner}/Rhythmer' if a.owner else None;base=f'https://{a.owner.lower()}.github.io/Rhythmer/' if a.owner else None
hub=json.loads((out/'fmhub.json').read_text())
if base:
 hub.update(play=base+'#play',editor=base+'editor/',cheat=base+'#guide')
 p=out/'README.md';p.write_text(p.read_text().replace('The project website includes a browser emulator, guide, web editor, installer and official V15 recovery. Its URL is set after the GitHub account/repository is connected. Until then this tree is a local release preparation, not a published release.',f'[Play in your browser]({base}#play) · [Guide]({base}#guide) · [Editor]({base}editor/) · [Install]({base}installer/) · [Releases](https://github.com/{repo}/releases)'))
(out/'fmhub.json').write_text(json.dumps(hub,indent=2)+'\n')
(out/'PUBLISH.json').write_text(json.dumps({'repository':repo,'site':base,'version':status['version'],'product':status['product'],'firmwareSha256':status['firmwareSha256'],'ownerDistributionDecision':True,'rightsHolderClearanceDocumented':False},indent=2)+'\n')
(out/'.github/workflows').mkdir(parents=True);shutil.copy2(R/'docs/launch/pages.yml',out/'.github/workflows/pages.yml')
(out/'.github/FUNDING.yml').write_text('custom: ["https://ko-fi.com/jazzyrhythmer"]\n')
(out/'.github/ISSUE_TEMPLATE').mkdir()
(out/'.github/ISSUE_TEMPLATE/bug_report.md').write_text('''---
name: Bug report
about: Report a reproducible Rhythmer problem
title: ""
labels: bug
---

**Where did this happen?**
Physical FM-1 / browser emulator / editor / installer; browser and OS if relevant.

**Version**
Release tag and firmware SHA-256 (from the installer or download checksums).

**Steps and expected result**
1.

**Actual result**
Include the track models, CPU profile and settings if this is an audio issue.

**Diagnostic material**
Attach a minimal pattern or redacted report if useful. Remove personal details and never include tokens, passwords or unrelated device dumps.
''')
(out/'.github/ISSUE_TEMPLATE/feature_request.md').write_text('''---
name: Feature request
about: Suggest a musical workflow improvement
title: ""
labels: enhancement
---

**Musical goal**
What are you trying to play or create?

**Proposed interaction**
Describe the buttons, screen or editor workflow.

**Hardware tradeoffs**
Any CPU, memory or voice-budget considerations you know of.
''')
(out/'.gitignore').write_text('build/\n__pycache__/\n*.o\n.DS_Store\n')
(out/'build.sh').write_text('''#!/bin/sh
set -eu
cd "$(dirname "$0")/rhythmer"
export RHYTHMER_BUILD_DIR="${RHYTHMER_BUILD_DIR:-../build/firmware}"
export RHYTHMER_EMBEDDED_BANKS="${RHYTHMER_EMBEDDED_BANKS:-../assets/breaks}"
exec python3 tools/build.py --product FM-1_748001 "$@"
''')
(out/'BUILDING.md').write_text('''# Build Rhythmer

See rhythmer/BUILDING.md for the pinned JieLi toolchain, AC79 SDK, Docker/Linux and font prerequisites. Run `sh build.sh`; the wrapper selects Rhythmer's independent app/loader identity and includes both prepared sample slots. Output is build/firmware. Set JIELI_TOOLCHAIN, AC79_SDK and RHYTHMER_BUILD_DIR for your environment. On a Mac with the configured development SSD, keep outputs and caches there.

The active source is rhythmer/firmware. Do not use an upstream X0X release workflow. The checked-in www/ directory is the reviewed static website, including the matching app/loader/sample package, browser runtime and browser data engine. The Pages workflow publishes only www/. The original browser runtime is retained with its source links and MIT notice in site/vendor/fm1-emu.

An emulator/host result is not a hardware result. See RELEASE-VALIDATION.json and re-test the exact rebuilt package before publishing a different binary. Replacing the bundled samples changes the release checksum and requires reviewing the sample notices too.
''')
(out/'scripts').mkdir()
shutil.copy2(R/'docs/launch/check_public.py',out/'scripts/check_public.py')
bad=[]
for p in out.rglob('*'):
 if p.is_symlink():bad.append(str(p.relative_to(out)))
 if p.is_file() and (p.name.endswith(('.flash','.ram','.pcm')) or 'install-report' in p.name or p.name in ('hosts.yml','.env')):bad.append(str(p.relative_to(out)))
assert not bad,bad
subprocess.run(['git','init','-b','main',str(out)],check=True,stdout=subprocess.DEVNULL)
print('Prepared only; no remote, push or deployment:',out)
print('Repository owner:',a.owner or 'pending GitHub signup')

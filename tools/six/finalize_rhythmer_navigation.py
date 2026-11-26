#!/usr/bin/env python3
"""Finalize focused machine-navigation evidence; earlier DSP reports stay separately hashed."""
import hashlib,json,shutil
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'rhythmer/build';D=R/'docs/six'
j=json.loads((O/'six-current-results.json').read_text());fw=O/'felucca.fwsc';sha=hashlib.sha256(fw.read_bytes()).hexdigest()
assert j['firmware_sha256']==sha and j.get('scope','').startswith('navigation')
required=['six-nav-boot','six-nav-strict','six-nav-sixacid','six-nav-fiveacid-break','six-nav-acid-1','six-nav-acid-2','six-nav-break-1','six-nav-break-2','six-nav-break-3']
for n in required:
 d=j['runs'][n];assert d['boots']==1 and d['fm1_mc_on']==1 and not(d['late'] or d['audio_lost'] or d['fm1_mc_lost'])
 p=O/(n+'.ppm');assert p.stat().st_mtime>=fw.stat().st_mtime;Image.open(p).save(p.with_suffix('.png'))
for n in required[1:4]:
 d=j['runs'][n];assert d['peak_pcm16']>0 and d['max_us']<512/44100*1e6 and d['usb_capture_frames']>1000 and not(d['usb_underruns'] or d['usb_overruns'] or d['usb_missed'])
for n in ('Rhythmer-demo.fm1save','Rhythmer-six-track-test.fm1save'):assert json.loads((O/n).read_text())['hash']==sha
host=(O/'current-host-validation.log').read_text()
for marker in ('SIX integration: PASS','SIX GEN forms: PASS','Garden + MONO2K model presets: PASS','SIX flexible machines: PASS','SIX machine navigation: PASS'):assert marker in host,marker
assert 'runtime error:' not in host and 'ERROR: AddressSanitizer' not in host
shutil.copyfile(fw,O/'Rhythmer.fwsc')
def lcd(n):return Image.open(O/(n+'.ppm')).crop((370,42,850,522))
for family,count in [('acid',2),('break',3)]:
 panel=Image.new('RGB',(480*count,480),'black')
 for k in range(count):panel.paste(lcd('six-nav-'+family+'-'+str(k+1)),(480*k,0))
 panel.save(O/('Rhythmer-'+family+'-tabs.png'))
lcd('six-nav-strict').save(O/'Rhythmer-home.png')
resources=next(x.strip() for x in (O/'six-build-validation.log').read_text().splitlines() if 'RAM .data+.bss' in x)
rows=[]
for label,key in [('Default six tracks, all FX sends, 8 s','strict'),('Six independent Acid machines, all FX sends, 6 s','sixacid'),('Break on T1 plus five Acid machines, all FX sends, 6 s','fiveacid-break')]:
 d=j['runs']['six-nav-'+key];rows.append(f"| {label} | {d['max_us']} us | 0 / 0 / 0 | {d['usb_capture_frames']} | 0 / 0 / 0 |")
baseline=json.loads((O/'pre-nav-dd959/results.json').read_text());old=baseline['runs'];stress=old['six-current-strict'];usb=old['six-current-usb48']
(D/'CURRENT-VALIDATION.md').write_text(f'''# Rhythmer current local validation

Current firmware SHA-256: `{sha}`. Physical FM-1 testing: not performed. No publication or physical flashing.

{resources}

Linker, code-reach and register-access checks passed. The 8 KiB pool reserve remains enabled. Rendering uses both cores, 512-frame halves (~11.6 ms), with bounded UI refresh and the existing six-voice synthesis budget (five when Break is active).

## Current behavior and host verification

All six tracks can choose Drum, musical Synth, Acid or Break. Fresh settings enable six tracks with Drum / Serum / Phase / LoFi / Acid / Break defaults. GLO TRACK MODE selects 4 TRK / 6 TRK; inactive sounds, sequences, automation and mutes are preserved. HOME GEN replaces only T1–T4, with T1 Drum, and preserves T5/T6 and the chosen count. JIANT's original section-wide editable drum kit remains shared; hit/sequence state is per track.

Break is a singleton across all six tracks, including inactive/muted ownership. Other tracks hide its factory A/B presets, user presets, favorites and model entry in both directions. Releasing ownership makes it available again. Direct loads and duplicate-Break project imports are rejected. Acid has independent DSP, note/gate and generator state per track; render scratch is separate per core.

EDIT tabs are SOUND / ACID / TONE / FOCUS or SOUND / BREAK / TONE / FOCUS. From SOUND, EDIT enters the dedicated tab and walks every custom page: ACID GEN 1 -> GEN 2; BREAK PERF -> SEQ -> RETURN; then TONE, FOCUS, SOUND. SELECT keeps its linear chain. Other synths hide both custom tabs and keep their original EDIT group stepping. Host button tests cover default and relocated Acid/Break, complete cycles, unchanged SELECT and normal synth navigation.

The current ASan/UBSan host suite passed: singleton browsing and direct-load protection; track modes; six independent Acid gates/generation; all 12 roots x 16 SCL scales for NEW/MUTATE; Break sequencing, holds, A/B, RETURN and recording; inherited save/overwrite/cancel/load; all 41 Garden and 17 adapted MONO2K presets with bounded audio and project round trips. See `rhythmer/build/current-host-validation.log`.

## Current exact package in the native community emulator

240 MHz, strict cache/LCD timing with USB audio:

| Workload | Maximum render | Audio / late / core-1 loss | USB frames | USB under / over / missed |
| --- | --- | --- | --- | --- |
{chr(10).join(rows)}

Virgin-flash boot confirmed six-track mode. Five separate captures press EDIT repeatedly to reach both ACID pages and all three BREAK pages; each asserts the selected track and actual firmware page ID. All nine current runs have one boot and zero audio/late/core-1 losses. Results: `rhythmer/build/six-current-results.json`.

## Earlier broader timing evidence

The immediately preceding package `{baseline['firmware_sha256']}` (before the EDIT tab-only change and compact TRACK MODE wording) has {len(old)} completed runs archived in `rhythmer/build/pre-nav-dd959/results.json`, bound to that earlier hash. Its 24 s all-FX/roll/A-B test reached {stress['max_us']} us maximum render; USB 48 kHz reached {usb['max_us']} us. Both have zero audio/late/core-1 loss and USB under/over/missed. These are separate evidence, not current-package runs. The broad sweep was interrupted when the user requested the navigation changes; only completed cases are retained.

## Local review files

- `rhythmer/build/Rhythmer.fwsc`: current package, not physically installed.
- `rhythmer/build/Rhythmer-six-track-test.fm1save`: current package plus six enabled default machines, patterns and two break samples; transport stopped.
- `rhythmer/build/Rhythmer-demo.fm1save`: current package plus an explicit four-track demo.
- `rhythmer/build/Rhythmer-acid-tabs.png`, `Rhythmer-break-tabs.png`: actual current native firmware screens.

Browser checks are recorded separately after Import. Earlier browser checking on the preceding package confirmed 118 presets without Break versus 120 on its owner, release/reassignment to T1, and the relocated BRK STEP UI. At about 200 s the browser reported audio dropouts despite an average load around 33 percent; native chip timing passed. Browser real-time reliability and physical-unit behavior remain unproven. Four complete projects and both two-bar PCM12 Amen/Think samples are retained; the packed section limit remains 3840 bytes. See [storage layout](MACHINES-LFO-STORAGE.md).
''')
(O/'Rhythmer-artifacts.json').write_text(json.dumps({'firmware_sha256':sha,'physical_hardware_tested':False,'artifacts':['Rhythmer.fwsc','Rhythmer-six-track-test.fm1save','Rhythmer-demo.fm1save','Rhythmer-acid-tabs.png','Rhythmer-break-tabs.png','Rhythmer-home.png']},indent=2))
browser_path=O/'Rhythmer-browser-validation.json'
if browser_path.exists():
 browser=json.loads(browser_path.read_text())
 if browser['firmware_sha256']==sha:
  with (D/'CURRENT-VALIDATION.md').open('a') as f:
   f.write("\n## Current package in the browser\n\nLocal Import of this exact hash passed visual button checks for ACID GEN 1 -> GEN 2 and BREAK PERF -> SEQ -> RETURN, with the corresponding top tab lit. The canonical six-track fixture is loaded and stopped at BREAK PERF. Browser screenshots and checks are in `rhythmer/build/Rhythmer-browser-validation.json`. The browser again showed an audio-dropout warning around 56 emulated seconds (reported average load 33 percent); it was recorded before dismissal. UI navigation passes; reliable browser audio is not claimed. No external publication occurred.\n")
print('Rhythmer focused artifacts finalized:',sha)

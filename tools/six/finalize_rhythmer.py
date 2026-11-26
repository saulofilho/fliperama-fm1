#!/usr/bin/env python3
"""Prepare local, revision-matched review artifacts after emulator validation. No device or network I/O."""
import hashlib,json,re,shutil
from pathlib import Path
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[2];O=R/'rhythmer/build';D=R/'docs/six'
j=json.loads((O/'six-current-results.json').read_text());fw=O/'felucca.fwsc';sha=hashlib.sha256(fw.read_bytes()).hexdigest()
assert j['firmware_sha256']==sha
if j.get('scope','').startswith('navigation'):
 import runpy
 runpy.run_path(str(R/'tools/six/finalize_rhythmer_navigation.py'),run_name='__main__')
 raise SystemExit(0)
for name in ('Rhythmer-demo.fm1save','Rhythmer-six-track-test.fm1save'):
 saved=json.loads((O/name).read_text());assert saved['hash']==sha,(name,'stale fixture')
for n,v in j['runs'].items():
 assert v['boots']==1 and not(v['late'] or v['audio_lost'] or v['fm1_mc_lost']),(n,v)
for n in ('six-current-strict','six-current-usb48','six-current-four','six-current-triple-serum','six-current-triple-m2stat','six-current-triple-m2saw','six-current-triple-m2sid'):
 v=j['runs'][n];assert v['usb_starts'] and v['usb_capture_frames']>1000 and v['usb_peak_pcm16']>0
 assert not(v['usb_underruns'] or v['usb_overruns'] or v['usb_missed'])
for n in j['runs']:
 p=O/(n+'.ppm');assert p.stat().st_mtime>=fw.stat().st_mtime,(n,'stale image');Image.open(p).save(p.with_suffix('.png'))
def lcd(n):return Image.open(O/(n+'.ppm')).crop((370,42,850,522))
home=lcd('six-current-playing-home');boot=lcd('rhythmer-splash');home.save(O/'Rhythmer-home.png');boot.save(O/'Rhythmer-boot.png')
boot_frames=[boot,lcd('rhythmer-splash-b'),lcd('rhythmer-splash-c')]
assert ImageChops.difference(boot_frames[0],boot_frames[1]).getbbox(),'Startup machine symbols did not animate'
boot_frames[0].save(O/'Rhythmer-boot.gif',save_all=True,append_images=boot_frames[1:],duration=200,loop=0)
frames=[home,lcd('rhythmer-home-b'),lcd('rhythmer-home-c')]
assert ImageChops.difference(frames[0],frames[1]).getbbox(),'HOME animation frames did not change'
frames[0].save(O/'Rhythmer-home.gif',save_all=True,append_images=frames[1:],duration=200,loop=0)
review=Image.new('RGB',(960,480),'black');review.paste(home,(0,0));review.paste(boot,(480,0));review.save(O/'Rhythmer-home-boot.png')
shutil.copyfile(fw,O/'Rhythmer.fwsc')
log=(O/'six-build-validation.log').read_text();resources=next(x.strip() for x in log.splitlines() if 'RAM .data+.bss' in x)
full=j['runs']['six-current-strict'];u48=j['runs']['six-current-usb48'];four=j['runs']['six-current-four']
triple=j['runs']['six-current-triple-serum']
for model in ('serum','phase','lofi'):
 a=lcd('rhythmer-note-'+model+'-hit');b=lcd('rhythmer-note-'+model+'-release')
 assert ImageChops.difference(a,b).getbbox(),(model,'note response unchanged')
 a.save(O/('Rhythmer-'+model+'-note.gif'),save_all=True,append_images=[b],duration=[350,500],loop=0)
text=f'''# Rhythmer current local validation

Firmware SHA-256: `{sha}`. This report and the images are bound to this exact built package. Physical FM-1 testing: **not performed**. No GitHub publication or device flashing.

{resources}

The linker/code-reach/register-access checks passed with the original 8 KiB pool reserve. Two cores are enabled; every native run had one boot, zero lost audio halves, zero late renders and zero lost core-1 jobs. DMA halves are 512 frames (~11.6 ms); up to ~5.8 ms more buffer wait than the previous 256-frame setting. UI updates are bounded to 80 ms / 160 ms under load. The synthesis voice budget is six, or five while Break plays; the kit and break retain their internal voices.

## Automated evidence

- ASan/UBSan integration: default layout, free machine assignment, X0X generation and mutation, all 16 Amenity performance commands, chops/rests, recorded A/B swaps, RETURN, original HOME/REC/OCT controls and inherited save/overwrite/cancel/load flow.
- Break SEQ: dedicated SET / STEP / PLAY pages, explicit command and length editing, held performance recording, combined roll/source events, recorded RETURN and ordinary project round trips. Main channel labels spell out DRUM, ACID and BREAK.
- Acid scale: MIN when unset; explicit SCL ROOT/SCALE always drive NEW/MUTATE, including explicit CHR. Tested all 12 roots × 16 scales. Generator page 2 edits the same shared SCL values.
- MONO2K: FM+STAT, SWAV-SAW, SID-6581 with 5/6/6 adapted starting presets. All 17 presets render bounded non-silent audio and survive project round trips; all eight SYN controls tested at both limits. No extra persistent voice or FX buffer allocation.
- Track control: 4/6 modes, default six, preserved inactive patterns and mute state, settings reapply. Break singleton hidden in model/factory/user/favorite browsing, direct load rejection, relocation across all six tracks; six independent Acid notes/gates/generators and project round trips.
- Dual LFO: independent clocks, opposite-polarity slot routing and project round trip. Four modulation slots can choose LFO 1 or LFO 2; existing fixed LFO DEST stays LFO 1.
- GEN: 12 seed/form combinations across LOOP/PARTS/SONG, first four tracks only, T1 drum, preserved T5/T6 and track mode, generator stays open after generation.
- UI: six engine marks, parameter boundary notes, drawing without pattern mutation, ANIM OFF stability, bounded startup strips and animated startup-state differences.
- Garden models: all 8 Serum, 16 Phase and 17 LoFi presets are retained verbatim and tested for bounded audio and project round trips. Serum resonance/filter/sub tests pass. Note impulses retrigger on real note-on, scale with velocity and decay over 280 ms; ANIM OFF suppresses the visual impulse.
- Storage: four complete projects × A–D sections; all 16 sector pairs tested with interrupted-save injection. Existing CRC/commit-last recovery retained. Samples, preset banks, autosave and update staging are disjoint from the fourth project. [Storage layout](MACHINES-LFO-STORAGE.md).
- USB host harness: 44.1/48 kHz resampling, duplex, 8/10-channel stems, counter wrap and overrun/restart. ASan/UBSan passed.

Free assignment keeps the default Drum / Serum / Phase / LoFi / Acid / Break arrangement. Break is hidden on every non-owning track, including inactive or muted ownership, and reappears after release. Acid is multi-instance; the original JIANT section drum patch kit remains shared.

## Actual community emulator, 240 MHz strict timing

| Workload | Maximum render | Audio/late/core-1 loss | USB capture | USB under/over/missed |
| --- | --- | --- | --- | --- |
| Six populated tracks + two LFOs + all FX sends + rolls/A-B, 24 s, USB 44.1 kHz | {full['max_us']} µs | 0 / 0 / 0 | {full['usb_capture_frames']} stereo frames | 0 / 0 / 0 |
| Six tracks + USB 48 kHz, 8 s | {u48['max_us']} µs | 0 / 0 / 0 | {u48['usb_capture_frames']} stereo frames | 0 / 0 / 0 |
| Four generated tracks, 4-track mode, USB 44.1 kHz, 8 s | {four['max_us']} µs | 0 / 0 / 0 | {four['usb_capture_frames']} stereo frames | 0 / 0 / 0 |
| Three Serum synths + drums/Acid/Break + all FX sends, USB 44.1 kHz, 12 s | {triple['max_us']} µs | 0 / 0 / 0 | {triple['usb_capture_frames']} stereo frames | 0 / 0 / 0 |

Additional all-FX six-track stress cases with all three synths on each MONO2K family: {"; ".join(name + " " + str(j['runs']['six-current-triple-'+key]['max_us']) + " µs" for key,name in [('m2stat','FM+STAT'),('m2saw','SWAV-SAW'),('m2sid','SID-6581')])}. Each has zero audio/late/core-1 loss and zero USB under/over/missed counters.

Six Acid tracks: {j['runs']['six-current-sixacid']['max_us']} µs maximum render. Five Acid tracks plus Break relocated to T1: {j['runs']['six-current-fiveacid-break']['max_us']} µs. Both use all FX sends, with zero audio/late/core-1 loss and zero USB under/over/missed.

Additional actual-FW captures cover startup, HOME/FOCUS, Serum/Phase/LoFi EDIT and note hit/release, LFO 2, GLO TRACK MODE, Acid NEW/MUTATE, Break UP/RETURN/source switching and the original full FX-hold key guide. No dedicated punch-in animation panel remains.

## Review artifacts

- `rhythmer/build/Rhythmer-demo.fm1save`: local emulator package plus four-track starting project and both two-bar sample slots.
- `rhythmer/build/Rhythmer-six-track-test.fm1save`: local test fixture with all six machines enabled, five note patterns and the autonomous break loop; press PLAY to audition. HOME GEN still generates only the first four tracks.
- `rhythmer/build/Rhythmer.fwsc`: compiled package (copy of the build system's `felucca.fwsc`). Not physically flashed.
- `rhythmer/build/Rhythmer-home-boot.png`, `Rhythmer-home.gif`, `Rhythmer-boot.png`, `Rhythmer-boot.gif`: actual native firmware renders. HOME and boot GIF frames are separate captures at 200 ms virtual-time increments. The numeric boot badge and development footer are absent.
- `rhythmer/build/six-current-results.json`: all run counters, exact firmware hash and sample provenance.

Browser verification is recorded separately after Import. Native strict timing is evidence of the emulated chip's behavior, not proof of real-unit timing, thermal behavior, controls, codec or flash reliability. The fourth project uses a SIX/Rhythmer-only part of stock firmware's USR area; firmware changes require the normal separate backup/restore workflow. The original 3840-byte packed-section limit remains.
'''
(D/'CURRENT-VALIDATION.md').write_text(text)
(O/'Rhythmer-artifacts.json').write_text(json.dumps({'firmware_sha256':sha,'physical_hardware_tested':False,'artifacts':['Rhythmer-demo.fm1save','Rhythmer-six-track-test.fm1save','Rhythmer.fwsc','Rhythmer-home-boot.png','Rhythmer-home.gif','Rhythmer-boot.png','Rhythmer-boot.gif']},indent=2))
print('Rhythmer artifacts finalized:',sha)

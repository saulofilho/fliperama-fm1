#!/usr/bin/env python3
"""Bind local review artifacts to the current tested firmware; no deployment or MIDI."""
import hashlib, json, os, shutil, re
from pathlib import Path
from PIL import Image

R = Path(__file__).resolve().parents[2]
O = Path(os.environ.get('RHYTHMER_BUILD_DIR', R/'rhythmer/build-ssd'))
fw = O/'felucca.fwsc'
sha = hashlib.sha256(fw.read_bytes()).hexdigest()
nav = json.loads((O/'six-current-results.json').read_text())
capacity = json.loads((O/'six-capacity-results.json').read_text())
think = json.loads((O/'think-drum-results.json').read_text())
md_lfo = json.loads((O/'md-lfo-results.json').read_text())
ensemble = json.loads((O/'ensemble-results.json').read_text())
from sample_assets import sample_dir
active_samples=json.loads((sample_dir(R)/'break-samples.json').read_text())
for report in (nav, capacity,think,md_lfo,ensemble):
    assert report["sample_manifest"]==active_samples,"Stale sample evidence"
    assert report['firmware_sha256'] == sha, 'Stale audio evidence'
    for name, d in report['runs'].items():
        assert d['boots'] == 1 and d['fm1_mc_on'] == 1, name
        assert d['max_us'] < 512/44100*1e6, name
        assert not any(d.get(k, 0) for k in ('late','audio_lost','fm1_mc_lost','usb_underruns','usb_overruns','usb_missed')), name
for name,d in ensemble['runs'].items():
    if 'chords' in name or 'analog-load' in name:
        for k in range(1,5):
            expected=[36] if k==4 else [48+k*2+j*4 for j in range(3)]
            assert set(expected)<=set(d['retained_notes'][k]),(name,k,'chord tone missing')
        assert d['gov_cap']==12,(name,'twelve-voice ceiling not retained')
    if name=='ensemble-md-default':assert d['latest_voice_age'][0]+4>=max(d['latest_voice_age'][1:]),'MD primary hit skipped latest bar'
for name in ('Rhythmer-demo.fm1save', 'Rhythmer-six-track-test.fm1save'):
    assert json.loads((O/name).read_text())['hash'] == sha
host = (O/'current-host-validation.log').read_text()
for marker in ('SIX integration: PASS', 'SIX flexible machines: PASS', 'SIX machine navigation: PASS',
               'Rhythmer display and GEN: PASS', 'Rhythmer actual-budget governor: PASS',
               'Break two-core render PASS', 'Rhythmer ensemble and chord ownership: PASS', 'governor below ensemble minimum still admits primary MD drum'):
    assert marker in host, marker
assert not any(line.rstrip().endswith('FAIL') for line in host.splitlines())
assert 'runtime error:' not in host and 'ERROR: AddressSanitizer' not in host
md_host=(O/'md-final-validation.log').read_text()
assert 'MD one-core render: PASS' in md_host and 'MD two-core render: PASS' in md_host
assert 'runtime error:' not in md_host and 'FAIL' not in md_host and 'AddressSanitizer' not in md_host
for marker in ('dense MD note input never exceeds actual shared budget','stolen pending MD notes never execute a full trigger','MD burst renders only the retained voice budget'):
    assert marker in md_host, marker
assert (O/'md-one.pcm').read_bytes()==(O/'md-two.pcm').read_bytes()
for i in range(int(re.search(r'#define MD_NMODEL (\d+)u',(R/'rhythmer/firmware/src/md_models.h').read_text())[1])):
    d=capacity['runs']['six-capacity-md-model-'+str(i)]
    assert d['track_engines']==[10]*6
assert think['think_slot_sha256']==hashlib.sha256((sample_dir(R)/'think-160.slot').read_bytes()).hexdigest()
assert (O/'six-break-core-one.pcm').read_bytes() == (O/'six-break-core-two.pcm').read_bytes()
shutil.copyfile(fw, O/'Rhythmer.fwsc')
def lcd(name):
    p = O/(name+'.ppm')
    assert p.stat().st_mtime >= fw.stat().st_mtime
    return Image.open(p).crop((370,42,850,522))
for family, count in (('acid',2), ('break',3)):
    panel = Image.new('RGB', (480*count,480), 'black')
    for i in range(count):panel.paste(lcd(f'six-nav-{family}-{i+1}'), (480*i,0))
    panel.save(O/f'Rhythmer-{family}-tabs.png')
lcd('six-nav-strict').save(O/'Rhythmer-home.png')
manifest = {'firmware_sha256':sha, 'physical_hardware_tested':False,
            'artifacts':['Rhythmer.fwsc','Rhythmer-six-track-test.fm1save','Rhythmer-demo.fm1save',
                         'Rhythmer-acid-tabs.png','Rhythmer-break-tabs.png','Rhythmer-home.png'],
            'validation':['six-current-results.json','six-capacity-results.json','think-drum-results.json','md-lfo-results.json','ensemble-results.json','current-host-validation.log','md-final-validation.log'],
            'md_models':21,'md_articulations':int(re.search(r'#define MD_NMODEL (\d+)u',(R/'rhythmer/firmware/src/md_models.h').read_text())[1]),'md_hit_limit_per_track':3,'polyphony':{'per_track':8,'shared_dual_core':12,'shared_single_core':8,'eco':6,'md_only_shared':4,'md_only_per_track':3,'md_trx_metal_per_track':2,'governor':'FX LITE first, then adaptive voice reduction if overload persists'},'sample_manifest':active_samples,
            'source_sha256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in sorted((R/'rhythmer/firmware').rglob('*')) if p.is_file()}}
(O/'Rhythmer-artifacts.json').write_text(json.dumps(manifest,indent=2)+'\n')
md_runs={n:d for n,d in capacity['runs'].items() if '-md-' in n}
md_worst_name,md_worst=max(md_runs.items(),key=lambda item:item[1]['max_us'])
ensemble_rows='\n'.join('| '+n+' | '+ '/'.join(str(len(v)) for v in d['retained_notes'][1:5])+' | '+str(d['gov_cap'])+' | '+str(d['max_us'])+' |' for n,d in ensemble['runs'].items())
resources = next(x.strip() for x in (O/'six-build-validation.log').read_text().splitlines() if 'RAM .data+.bss' in x)
previous = json.loads((R/'rhythmer/build/six-current-results.json').read_text())
rows = []
for title,key in (('Default six tracks, all FX sends, 8 s','strict'),('Six Acid machines, 6 s','sixacid'),('Break + five Acid machines, 6 s','fiveacid-break')):
    d=nav['runs']['six-nav-'+key]
    rows.append(f"| {title} | {previous['runs']['six-nav-'+key]['max_us']} | {d['max_us']} | 0 |")
(R/'docs/six/CURRENT-VALIDATION.md').write_text(f'''# Rhythmer current local validation

Current firmware SHA-256: `{sha}`. Generated artifacts: `rhythmer/build-ssd` (SSD BuildCache); historical `rhythmer/build` is preserved. No external publication or physical write was performed.

The owner reports approximately 80% CPU and pops/crackles on an earlier build on a physical FM-1, varying with instruments and notes. Exact installed version, core mode and clock are not established. This new package has not been tested on that physical unit; emulator timing does not establish that its crackles are resolved.

`{resources}`

## Changes

- Break has measured nonzero scheduler cost despite using no ordinary voice slots. Its singleton DSP can render on either core. One/two-core host renders are byte-identical; the two-core test assigns Break to the worker for 1,021 blocks.
- Restored JIANT per-track eight voices and a twelve-voice shared ceiling on two cores (eight on one core, six in explicit ECO). MD selection and Break playback do not lower that ceiling. The governor first uses the existing LITE FX path, then reduces voices if sustained overload remains. Release fades, clock defaults and core-loss fallback remain. This is finite, CPU-adaptive polyphony, not a promise that every combination of six heavy machines can hold all notes.
- Display graph traffic is capped at 200 ms under high load or the playing six-track overview. Input scanning is unchanged. No additional framebuffer, audio buffer or sample RAM is allocated. WHEEL voice state is split across ordinary RAM and pool, and MD state is in the pool to fit the restored voice arrays; the linker retains its 8 KiB pool reserve.
- HOME GEN defaults to LOOP. Its first four tracks use Drum + three musical synths. Normal/EXPLORE engine pools include SERUM, PHASE, LOFI, FM+STAT, SWAV-SAW and SID-6581, as well as the existing musical models; Acid/Break are excluded and T5/T6 remain unchanged. A 128-seed host sweep reaches all six added models.
- GLO has a clock/beat cursor and height motion; global parameter and animation changes invalidate its graph. ANIM OFF stays stable. Four display colors (MONO, INVERT, RED, RED INV), three skins (STACK, GRID, FLOAT), and SOLID/DOTS styles survive redraw and palette round trips. Legacy JIANT colors migrate to MONO. The red schemes retain at least 4.5:1 primary text contrast, with separate dim graphics.
- Four own palette tables replace the old JIANT color library. Creature, SVG illustration, rainbow/thermal and signature art paths are removed. Legacy colors convert once on archive import, never in frame redraw. The retired VOICE lyric generator no longer builds its unused dictionary/cache; stored lyric text is retained solely for archive round trips.
- All 21 Hortator MD synthesis models fit in five extra DRUM kits (MD METAL, MD WIRE, MD TRX, MD EFM, MD PERC). Three fixed hit states per track use union-local state, with a 32-sample handoff, shared hat choke, no heap and no copied audio assets. SOUND 3 selects the model; SOUND / SOUND 2 expose tune, decay and three named macros. Other original controls use factory defaults. Model changes take effect at the next hit. MD hits occupy slots in the twelve-voice pool and have their own additional four-voice shared work cap, at most three per part or two while an expensive TRX cowbell/cymbal is sounding. This applies only to MD hits, including in mixed kits. MD admission may replace MD hits but cannot evict another part’s classic drum, synth or Acid voice. A primary MD hit can use a reserved part voice when the adaptive ceiling is below the ensemble minimum; the twelve-voice nominal and four-MD limits remain binding. Ordinary kits and melodic parts retain JIANT polyphony. One/two-core PCM is identical under the same four-voice test budget; all models pass extreme-parameter host checks and exact project round trips. MD is a synthesis-bank adaptation, not the whole Hortator firmware or all its presets.
- ABOUT identifies Jazzy Rhythmer with YouTube/Instagram @jazzyrhythmer. JIANT's original copyright/source and other upstream credits remain; its personal biography/support links are removed from the creator section. The USB INFO family string remains compatible with the existing editor/installer protocol.
- Rhythmer install review has a separate, unchecked sample-rights acknowledgement. It does not supply a licence or clear Amen/Think redistribution rights. Official V15 restoration has no sample stage. Both two-bar PCM12 loops remain in the local bundle; the public audio release block remains enabled.

## Ensemble and chord retention

Six strict native scenarios check the default six-track ensemble with high sends to all four FX, three simultaneous ANALOG triads plus two drum hits and Acid with FX sends off and Break muted, and two additional ANALOG triad cases that add real sequenced Break, each using classic or MD percussion. All four chord cases retain every expected chord tone and the twelve-voice ceiling in the exact current package. The default cases use high FX sends and validate each melodic part plus the MD primary hit in the latest bar. These are bounded test fixtures; a nominal twelve-voice ceiling does not promise full chords under every engine/preset/FX load, and the 80% overload guard remains. Native RAM snapshots verify each expected melodic note remains; host checks separately verify kick/snare/hat admission, eight held notes on one synth, twelve simultaneous shared voices, independent audio from each ordinary track, and that an MD burst leaves every other part’s voice state byte-identical. Drum tails may naturally end before a native snapshot. Break rendering/SEQ has separate audio tests.

| Native scenario | T2/T3/T4/Acid retained notes | Adaptive ceiling | Max us |
| --- | --- | ---: | ---: |
{ensemble_rows}

## Exact-package timing

Community native emulator at 240 MHz, strict cache/LCD and USB 44.1 kHz. Deadline 11,610 us. Previous comparison package: `{previous['firmware_sha256']}`. Same focused fixtures/durations; these are emulation results, not physical measurements.

| Scenario | Previous max us | Current max us | Late/lost/core faults |
| --- | ---: | ---: | ---: |
{chr(10).join(rows)}

MD timing worst case: `{md_worst_name}`, {md_worst['max_us']} us of the 11,610 us deadline, no late/lost/USB faults. This includes deliberate four-note input that is bounded by the documented polyphony guard.

All {len(ensemble['runs'])} ensemble/chord scenarios, {len(nav['runs'])} focused boot/navigation scenarios and {len(capacity['runs'])} dense capacity scenarios pass with no deadline misses, lost audio, worker loss or USB under/over/missed packets. Capacity exercises six identical SERUM, FM6, PHASE, FM+STAT, SWAV-SAW, SID-6581 or DRUM machines, every one of the 21 MD models on six DRUM tracks, both initial MD kits, plus Break + five Acid, at 240 BPM with FX sends. Standard model cases use dual LFO sources; a separate six-CBTRX `md-lfo-results.json` run explicitly adds both LFOs to the MD workload. Full machine/save/scale/generator/navigation host regression suite passes under ASan/UBSan. Four projects and both Break banks are retained.

Screens: `qa/performance/themes.png`, `qa/performance/about.png`, `Rhythmer-acid-tabs.png`, `Rhythmer-break-tabs.png`. Browser installer/protocol evidence is recorded separately. No claim of physical-device validation follows from those mock transfers.
''')
print('Rhythmer performance artifacts finalized:', sha)

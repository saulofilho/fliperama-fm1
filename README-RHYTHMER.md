# Rhythmer

A hands-on groovebox firmware for the FM-1. Sound into motion. The active firmware is in `rhythmer/`; the root firmware tree is the earlier X0X prototype.

| Default track | Machine |
| --- | --- |
| 1 | JIANT drum kit |
| 2–4 | Serum / Phase / LoFi defaults; all nine musical synth models selectable |
| 5 | EMPTY — choose an engine when needed |
| 6 | EMPTY — choose an engine when needed |

HOME uses a monochrome Elektron-inspired workstation: selected machine and sound, project/section/pattern position, six animated machine symbols with small level rails and a 16-step strip. FOCUS and EDIT show geometric instrument marks driven by real parameters and voiced activity. The boot screen shares these machine glyphs beneath the centered RHYTHMER pixel wordmark. Note-on adds a velocity-sensitive 280 ms visual impulse and restarts note-driven wave motion. FX hold retains its full button guide; no additional punch-in animation panel is present.

All six tracks freely select Drum, Synth, Acid or Break; EDIT/SEQ and the HOME identity follow the assigned category. Acid can occupy multiple tracks with independent DSP, note/gate and generation state. **Break is a project-wide singleton**: while assigned anywhere, its factory/user presets, favorites and model choice disappear on other tracks, including when the owner is inactive or muted. Switching the owner to another model releases it for all tracks. Direct loads and project imports also reject duplicate Break assignments. JIANT's original section-wide editable drum kit remains shared between drum tracks; their hit/sequence state is independent.

GLO > SYSTEM > TRACK MODE selects **4 TRACK / 6 TRACK**. Four tracks are enabled on fresh settings; OCT+ confirms the CPU notice before enabling six. On that activation, empty T5/T6 receive Acid/Break; assigned instruments and MIDI remain intact, and a Break assigned elsewhere is never duplicated. Four-track mode suspends T5/T6 while retaining their sounds, steps, automation and mute state. HOME GEN fills the active four or six ordinary/empty tracks and preserves manually assigned Acid/Break machines, wherever assigned. Its existing `SR_ACID` recipe selects native Hortator Acid only for its mono bass part; ordinary bass, lead and chord sound pools exclude Acid. Break remains excluded from automatic assignment.

LFO has two independent oscillators per track. SELECT moves along the remembered LFO pages, including LFO 2. LFO > MOD: knob 1 chooses slot 1–4, knob 2 chooses LFO 1 or LFO 2 (or the other original sources), knobs 3–4 set destination and amount. LFO 2 has rate, wave, phase (FREE at -1) and fade. Both LFO 1 and LFO 2 have matching DEST pages, as well as access through the modulation slots.

SAVE > PROJECT supports four complete projects, each A–D sections. Each section keeps six tracks, sounds, steps and automation within the original 3840-byte packed-section limit. All 16 sections retain CRC and A/B commit-last interrupted-save recovery. See the [storage map and controls](docs/six/MACHINES-LFO-STORAGE.md).

Break A is Amenity's Amen. Break B is Think. Each is two 4/4 bars at 160 BPM, packed 12-bit mono, 16 kHz. Automatic LOOP and sequenced CHOP coexist with the original 16 roll/performance commands, UP/DOWN, stretch/echo, recorded A/B switching and explicit RETURN. The JIANT HOME button keeps its original role. Source credits are in [third-party notices](docs/six/THIRD_PARTY.md).

Dual-core dispatch and the existing audio governor remain. The original JIANT shared synthesis ceiling is twelve on two cores, eight on one core, subject to its original load governor. Drum attacks have 40 ms of protection; older tails participate normally. MD retains eight physical states per drum track without a separate MD-only cap. DMA halves are 512 frames (~11.6 ms each); this adds up to ~5.8 ms buffer wait versus 256-frame halves. Display updates slow from 80 to 160 ms under load. The original linker, code reach and 8 KiB pool-reserve checks remain enabled.

Local validation:

```sh
sh tools/six/test_rhythmer.sh
sh tools/six/build_rhythmer_local.sh --reuse-generated
/Volumes/SSD/fm1-six-tooling/python/bin/python3 tools/six/test_rhythmer_emulator.py
```

The build wrapper uses the local JieLi toolchain VM; start `fm1-six` first. It builds locally and does not publish or flash hardware. The emulator export is `rhythmer/build/Rhythmer-demo.fm1save`; open it with the community emulator's Import control. The compiled package keeps the build system's filename `rhythmer/build/felucca.fwsc`.

See [current validation](docs/six/CURRENT-VALIDATION.md) and the [animation-placement audit](docs/six/RHYTHMER-ANIMATION-AUDIT.md). The owner reports the e705abe3 development package works on the FM-1, including V15 installation and exit. The separately rebuilt public candidate uses a new identity and requires its own physical confirmation.

The website emulator starts with empty sequences and optional tracks unassigned. Acid is a native Hortator-based monophonic synth: HT SQUELCH, HT DEEPBASS, HT SCREAMER and HT SQUAREAC. X0X audio DSP is removed; only its TB-3PO-derived MIDI generator and mutation remain. NEW/MUTATE follow SCL, using the common CHR default. Generation runs only on explicit action or a deliberately enabled AUTO bar interval.

Garden models retain every original preset: Serum 8, Phase 16 and LoFi 17. Their DSP/preset files are unchanged; engine IDs and favorites are adapted to preserve Rhythmer projects. See `docs/six/GARDEN-MODELS.md`.

### Local update: MONO2K and Break event sequencing

Three additional synth choices are FM+STAT (5 starting presets), SWAV-SAW (6), SID-6581 (6), on any track; default tracks remain Serum / Phase / LoFi and all 41 Garden presets remain. These are mono machines (one voice each). No new sample or chorus buffers are allocated. Existing HOME GEN choices and priority stay unchanged; these added machines can be selected from the synth sound browser.

Any assigned Break track → SEQ opens **BRK STEP** directly. SELECT left opens **BRK SET** (LOOP/CHOP, A/B, freeze, auto roll); SELECT right opens **BRK PLAY** (original Amenity performance keys, with ordinary REC). STEP knobs are STEP, COMMAND, LENGTH, TYPE. C1–C16 trigger slices; R1–R16 are the original repeat/build/stretch/echo/down/up/shrink commands; A/B select the source; RET returns VAR/WARP to straight. Length writes ordinary TIE steps. Rolls and their held lengths, A/B swaps and RETURN record into the normal track pattern and save with project/section data. A source switch during a held roll records both events in the same step. Other live knob changes use inherited sequence automation.

Any assigned Acid track: from EDIT SOUND, tap EDIT for **ACID / 303 GEN 1**, tap again for **303 GEN 2**. SELECT still walks the pages as before. OCT+ NEW, OCT− MUTATE; the second page edits the shared SCL root and scale, octave and auto-mutation interval. GEN 2 shows the same ROOT/SCALE as SCL. The default is CHR; NEW and MUTATE use the displayed common values with no separate scale fallback. Changing SCL by itself does not rewrite an existing pattern; NEW/MUTATE apply the current scale.

Acid and Break have separate visible EDIT tabs: SOUND / ACID / TONE / FOCUS or SOUND / BREAK / TONE / FOCUS. From SOUND, repeated EDIT taps walk every machine-specific action: Acid GEN 1 → GEN 2; Break PERF → SEQ → RETURN, then TONE, FOCUS and back to SOUND. Other machines do not show these tabs. Common synth EDIT keeps its original group stepping; SELECT navigation is unchanged.

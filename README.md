# FLIPERAMA

**A neighbourhood arcade inside the M-VAVE FM-1.** Every cabinet is a sound chip with its own made-up game on the
screen, and the one who plays the game is **the music**. Every note is a jump, every kick is a shot at goal, every
chord is a firework. You write the beat and the game plays itself, like the attract mode of an old arcade machine
that runs until someone drops in a coin.

> **Status: early development.** The plan, the mood board and the base firmware are in place. The six chips and the
> six games are not written yet, so there is nothing to install. Do not flash the current build expecting FLIPERAMA.

## The cabinets

| Cabinet | Chip (in the style of) | Game on screen | What the sound moves |
| --- | --- | --- | --- |
| PULSO | two pulses, triangle and noise, 8-bit console | CORREDOR: a runner across the rooftops at dusk | each note is a jump, higher for a higher note; a coin per note |
| ONDA | 4-bit wave channel (32 samples), handheld | SURFE: the sea wave **is** the waveform | the wave is drawn from the wavetable; the level lifts the sea |
| RUÍDO | LFSR noise (long and short) and a 12.5 % pulse | PÊNALTI: a penalty shoot-out | the kick shoots, the snare makes the keeper dive, the hi-hat stirs the crowd |
| FM | 2- to 4-operator FM, 16-bit | PIPA: a kite over the rooftops of a hillside | pitch is the kite's height; the bass is a gust of wind |
| PWM | variable pulse width and a resonant filter, 8-bit computer | PISTA: a dancer under a spotlight | the pulse width is the width of the spotlight |
| ARPEJO | fast chord arpeggios (25 % pulse) | RÉVEILLON: New Year's fireworks over the sea | each chord launches a rocket; each note is a spark in the note's colour |

**The golden rule:** everything that moves on the screen comes from an event in the audio: a note, its pitch, an
accent, an envelope, an LFO, a sequencer step. Outside attract mode, no sound means no motion.

Every game, character and level is original. Nothing is taken from an existing game: no characters, levels,
music or sound effects.

## Mood board

[`docs/moodboard/index.html`](docs/moodboard/index.html) is a playable sketch of the six cabinets. Download it and
open it in a browser. Drop a coin into a cabinet to hear its chip in Web Audio and watch its scene follow every
note, then play along with the keys A to L. Its visual language is a 1990s neighbourhood arcade: a hand-painted
sign, metal tokens, plywood cabinets and tube screens.

## Plan

[`PLAN.md`](PLAN.md) (in Portuguese) holds the open decisions, the neighbours on the FM Hub, the phases and the
risks. The proposed identity is `FM-1_939`.

Where it stands:

- **Phase 0, on the computer:** done. The base firmware builds and matches its release package byte for byte,
  except for the checksum fields.
- **First cut:** done. Only six engines stay (ANALOG, FM6, ACID, BREAK, drums, EMPTY), which frees 53 KB of the
  app's flash for the chips and games.
- **Next:** check the build on an FM-1 and measure the CPU there, then give the firmware its own identity, then
  write the scene engine, the six chips and the six games.

## Building

You need the JieLi pi32v2 toolchain (`~/.jieli/toolchain`), the JieLi AC79 SDK at tag
`AC79NN_SDK_V1.2.1_2023-12-13`, Python 3.10 or later with Pillow and fontTools, and Docker. On a Mac, the toolchain
runs in a `linux/amd64` container.

```sh
python3 -m venv .venv && .venv/bin/pip install Pillow fonttools
AC79_SDK=/path/to/fw-AC79_AIoT_SDK ./build-mac.sh
```

The package is written to `build/felucca.fwsc`. [`BUILDING.md`](BUILDING.md) and
[`rhythmer/BUILDING.md`](rhythmer/BUILDING.md) cover the build options and the host tests
(`rhythmer/tests/run_tests.sh`).

## Licence

Free software under the GNU General Public License, version 3 only (`GPL-3.0-only`, see [`LICENSE`](LICENSE)). Where
each part comes from, and the licence of each, is in [`LICENSING.md`](LICENSING.md) and in the source files. If you
distribute this firmware, or firmware derived from it, you must give your recipients its complete source under the
same licence.

M-VAVE and FM-1 are trademarks of their owners. FLIPERAMA is an independent project, not affiliated with or
endorsed by them.

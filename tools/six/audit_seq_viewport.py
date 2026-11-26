#!/usr/bin/env python3
"""Run low/high-register SEQ fixtures through the actual FM-1 firmware."""
from pathlib import Path
import json, struct, zlib
from PIL import Image

r=Path(__file__).resolve().parents[2]
p=r/'tools/six/test_rhythmer_emulator.py'
g={'__file__':str(p)}
exec(p.read_text().split("if sys.argv[1:]==['--nav-flex']:")[0],g)
o=g['OUT'];q=r/'qa/seq-viewport'
nav=json.loads((o/'six-current-results.json').read_text())
assert nav['firmware_sha256']==g['report']['firmware_sha256']
for name,track in [('acid-low',4),('synth-high',1)]:
    flash=bytearray((o/'six-nav-fixture.flash').read_bytes())
    data=(q/(name+'.project')).read_bytes()
    for off,kind in ((0x97000,1),(0xe5000,9)):
        h=struct.pack('<IHHIIIII',0x33584953,kind,0,1,len(data),zlib.crc32(data),0xffffffff,0xffffffff)
        h+=struct.pack('<I',zlib.crc32(h))
        sec=bytearray([255])*4096;sec[:32]=h;sec[256:256+len(data)]=data
        flash[off:off+4096]=sec
    seed=o/('seq-'+name+'.flash');seed.write_bytes(flash)
    g['run']('seq-'+name,3800,'2700:11,2820:11^',seed)
    v=g['report']['runs']['seq-'+name]
    assert v['selected_track']==track and v['home']==0,v
    assert v['boots']==1 and v['fm1_mc_on']==1 and not(v['late'] or v['audio_lost'] or v['fm1_mc_lost']),v
    panel=Image.open(o/('seq-'+name+'.ppm')).crop((370,42,850,522))
    panel.save(q/('native-'+name+'.png'))
    # Step 4 has a note, away from the cursor/step-1 outline. White pixels
    # inside its column in the roll establish that the note is actually drawn.
    white=sum(min(c)>220 for c in panel.crop((94,218,126,442)).getdata())
    assert white>12,(name,'SEQ note outside visible roll',white)
    v['visibleNotePixels']=white
g['report']['scope']='Actual firmware low Acid and high synth SEQ screen checks'
(q/'native-seq-results.json').write_text(json.dumps(g['report'],indent=2)+'\n')
print('Actual firmware SEQ viewport: PASS',flush=True)

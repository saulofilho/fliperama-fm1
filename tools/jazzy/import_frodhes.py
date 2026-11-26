from pathlib import Path
import re
R=Path(__file__).resolve().parents[2];U=R/'upstream/frodhes';D=R/'rhythmer/firmware/jazzy'
s=(U/'firmware/src/rhodes.c').read_text();s=s[:s.index('static void rh_shed')]
s=s.replace('#include "fm1_keep.h"','#define FM1_KEEP(x) ((void)0)')
for name in ['fxp.h','rhodes_tables.h','rh_tone_g.h','rhodes_phim.h','pulse_pz.h']:
 p=U/'firmware/src'/name
 if not p.exists():p=U/'firmware/gen'/name
 shutil_text=p.read_text();s=s.replace('#include "'+name+'"',shutil_text)
# Use original host branch (no special hardware sections / inline assembly).
s='#define DINGHY_HOST 1\n#define FR_VOICES 1\n'+s
names=set(re.findall(r'\b(?:rh_\w+|RH_\w+)\b',s))
names.update(re.findall(r'^static[^\n]*?\b(\w+)\s*(?:\(|\[|=)',s,re.M));names.update(re.findall(r'^#define\s+(\w+)',s,re.M));names.update(['rv','ev_r','ev_drop','sd_st','SUB','EV_NOTE_ON','EV_NOTE_OFF','EV_PEDAL','EV_OFF','EV_PEDAL_LEVEL'])
names.update(re.findall(r'\b(?:int32_t|uint32_t|int|void|float|uint16_t|int64_t)\s+(\w+)\s*\(',s))
names-=set(['__attribute__','DINGHY_HOST','FR_VOICES','FR_RAM','FR_FAR','RING_PUBLISH','FM1_KEEP'])
names={n for n in names if re.match(r'^[A-Za-z_]\w*$',n)}
s=re.sub(r'\b('+'|'.join(sorted(names,key=len,reverse=True))+r')\b',lambda m:'jf_'+m[0],s)
# The DSP's two hot scratch arrays must be independent on the two cores.
s=s.replace('jf_rh_x[jf_SUB]','jf_rh_x_core[2][jf_SUB]').replace('jf_rh_F[jf_SUB]','jf_rh_F_core[2][jf_SUB]')
pos=s.index('static uint32_t jf_rh_ages')
s=s[:pos]+'#define jf_rh_x jf_rh_x_core[MC_CPU() & 1u]\n#define jf_rh_F jf_rh_F_core[MC_CPU() & 1u]\n'+s[pos:]
(D/'frodhes.h').write_text(s)

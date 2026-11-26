#!/usr/bin/env python3
"""Project pinned original factory programs onto JAZZY's control contract, then coverage-select and LZ4-pack.
No factory decoding or file I/O occurs in the audio renderer.
"""
import re,json,sys,importlib.util,math,collections,subprocess,os
from pathlib import Path
R=Path(__file__).resolve().parents[2];U=R/'upstream';D=R/'rhythmer/firmware/jazzy';B=Path('/Volumes/SSD/Development/BuildCache/jazzy')
sys.path.insert(0,str(R/'rhythmer/tools'));import lz4blk
cl=lambda x,a=0,b=127:max(a,min(b,round(x)))
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def enums(s):
 env={};s=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
 for body in re.findall(r'enum\s*(?:\w+)?\s*\{(.*?)\}',s,re.S):
  n=0
  for token in body.split(','):
   t=token.strip()
   if not t:continue
   if '=' in t:
    t,v=t.split('=',1)
    try:n=eval(re.sub(r'(?<=\d)[uU]\b','',v),{},env)
    except:continue
   env[t.strip()]=n;n+=1
 return env
# Expand sparse upstream banks using their own defaults, reproducibly from pinned sources.
B.mkdir(parents=True,exist_ok=True)
for mode,out in [('OB','ob'),('KW','kw')]:
 exe=B/(out+'_extract');subprocess.run(['clang','-w','-D'+mode,str(R/'tools/jazzy/preset_extract.c'),'-o',str(exe)],check=True)
 (B/(out+'_presets.txt')).write_bytes(subprocess.check_output([str(exe)]))
banks=collections.OrderedDict();audit=[]
def add(e,name,p,env=(0,65,100,45),fenv=0,mono=0,fx=(0,0,0,0),extra=(60,0,0,0,0,0,0),note=''):
 name=name.strip()
 # Tags describe musical use, so GEN never mistakes a synth snare/noise patch for a lead.
 tag=8 if re.search(r'KICK|SNARE|CLAP|DRUM|CONGA|TIMPANI|SHAKER|MARACA|TOM TOMS|PERC HIT|HITHAT|HI.HAT',name,re.I) else 1 if re.search('BASS|SUB|808',name,re.I) else 3 if re.search('PAD|STRING|DRONE|ENSEM|CELLO|VIOLIN',name,re.I) else 4 if re.search('PIANO|KEY|BRASS|ORGAN|ORGN|FLUTE|HARMONICA|RECORDER|RHODES|SOFT EP',name,re.I) else 5 if re.search('PLUCK|CLAV|ARP|GUITAR|KOTO|HARP',name,re.I) else 6 if re.search('BELL|METAL|GLASS|CHIME|GONG|VIBRA|MARIMBA',name,re.I) else 7 if re.search('VOICE|CHOIR|VOCAL|VOX',name,re.I) else 9 if re.search('FX|NOISE|WIND|SWEEP|ROAR|TYPHOON|HELICOPTER|THUNDER|DUST|STORM|ROCKET MEN|GOING UP|CAVERN',name,re.I) else 2

 v={'name':name,'e':[cl(x,-64,127) for x in p],'env':[cl(x) for x in env],'fenv':cl(fenv,-64,63),'mono':mono|tag<<1,'fx':[cl(x)+1 for x in fx],'extra':[cl(x,-64,127) for x in extra],'approximation':note};banks.setdefault(e,[]).append(v)
# FMini: retain all 200 oscillator programs, original host-envelope/FX values and LFO intent.
s=(U/'fmini/firmware/src/eng_fmini_presets.h').read_text();body=s.split('static const preset_t FMINI_PRESETS[] = {')[1].split('\n};')[0]
rows=re.findall(r'\{"([^"]+)",\s*\{([^}]+)\},\s*\{([^}]+)\},\s*(-?\d+),\s*(\d+),\s*FX\(([^)]+)\)',body)
xs=s.split('static const fmini_x_t FMINI_X')[1]
xrows=re.findall(r'\{\{[^}]+\},\s*\{([^}]+)\},\s*\{[^}]+\},\s*\d+,\s*\{([^}]+)\}',xs)
for i,(nm,ed,en,fe,mo,fx) in enumerate(rows):
 p=list(map(int,ed.split(',')));depth=p[6];p[6]=i//128;p[7]=i%128;lf=list(map(int,xrows[i][0].split(',')));mods=list(map(int,xrows[i][1].split(',')))
 add(23,nm,p,list(map(int,en.split(','))),int(fe),int(mo),list(map(int,fx.split(','))),[lf[0],cl(lf[1],0,4),mods[0],cl(depth/4,-64,63),0,mods[1],0], 'Original oscillator program retained; bank/program replaces MOD macro.')
assert len(rows)==200
# OberVave sparse patches expanded by the upstream parameter defaults (extract helper).
text=(U/'obervave/firmware/src/obv_params.h').read_text();enums_ob=enums(text)
for row in (B/'ob_presets.txt').read_text().splitlines():
 nm,data=row.split('|');p=list(map(int,data.strip(',').split(',')));g=lambda k:p[enums_ob[k]]
 ft=g('P_FTYPE');mode=43 if ft==2 else 86 if ft==1 else 0
 add(24,nm,[g('P_CUTOFF'),g('P_RESO'),{0:0,1:0,2:127,3:64}[g('P_O1_WAVE')],cl(g('P_O2_FINE')-64,-64,63),g('P_O1_PW'),mode,127 if ft==4 else 0,g('P_O2_SEMI')-24],[g('P_AA'),g('P_AD'),g('P_AS'),g('P_AR')],g('P_FENV_AMT')-64,int(g('P_MODE')==3),[g('P_DRIVE'),g('P_CHO_MIX'),g('P_DLY_MIX'),g('P_REV_MIX')],[g('P_LFO_RATE'),[1,2,2,3,4,4][g('P_LFO_SHAPE')],cl(g('P_LFO_PITCH')/2,-64,63),cl(g('P_LFO_FLT')/2,-64,63),cl(g('P_LFO_PWM')/2,-64,63),cl(g('P_LFO_AMP')/2,-64,63),g('P_GLIDE')], 'Dual tuning/levels, SEM/notch, native sync/X-mod and separate filter EG approximate to shared macros; arp/sequence not loaded.')
# FM-106 original decoded factory controls.
for v in json.loads((U/'fm106/tests/factory_presets.json').read_text()):
 p=v['raw'];shape=85 if p[23] and p[24] else 127 if p[23] else 42 if p[24] else 0
 add(25,v['name'],[p[10],p[11],shape,p[7] if p[25] else 0,p[6]/2 if not p[33] else p[6],p[8],cl(p[12]/2,0,63)*(-1 if p[34] else 1),cl(p[9],0,3)],[*p[16:20]],0,0,[0,90 if p[27] and p[28] else 60 if p[28] else 40 if p[27] else 0,0,0],[p[3],1,cl(p[5]/2,-64,63),cl(p[13]/2,-64,63),cl(p[6]/4,0,63) if not p[33] else 0,0,0], 'Native chorus becomes shared chorus; PWM movement uses host LFO. DCO range is not forced into sequencer pitch.')
# CS-1 tones from the Yamaha chart bank and supplied additions.
s=(U/'cs1/firmware/gen/cs1_presets.h').read_text();names=re.findall(r'"([^"]+)"',s.split('TONE_NAMES')[1].split(';')[0]);rows=re.findall(r'\{([\d, ]+)\},',s.split('static const chan_patch_t TONES')[1].split('};')[0])
for nm,row in zip(names,rows):
 p=list(map(int,row.split(',')));wave=[0,64,127][p[1]]
 add(26,nm,[cl((p[11]-16)*127/111),p[12],wave,4,p[2],p[9],0,48],p[18:22],cl((p[14]-p[13])/2,-64,63),0,[0,30,0,25],[cl(p[4]*127/40),0,0,0,cl(p[3]/2,-64,63),0,0], 'Paired channels use common shape/filter macros; sine/noise layer and separate filter EG are approximated.')
# Native CZ programs: decode, select dominant line, project native rate/level EG to common ADSR.
ts=module('czfactory',U/'melodee/tools/gen_cz1_factory.py').tones()
def cz_env(b,base,end):
 n=b[end]&7;sus=next((j for j in range(n) if b[base+2*j+1]&128),max(0,n-1));rate=lambda j:cl((127-(b[base+2*min(j,n)]&127))*.85)
 return [rate(0),rate(1),cl((b[base+2*sus+1]&127)),rate(n)]
for b in ts:
 ls=b[0]&3;off=57 if ls==1 else 0;w=((b[14+off]<<8)|b[15+off]);wavemap={0:0,1:1,2:2,4:3,5:4,6:5,7:6,3:0};other=((b[71]<<8)|b[72]);wave=wavemap[(w>>13)&7];env=cz_env(b,21+off,20+off);dcw=b[39+off]&127
 add(38,b[128:].decode().strip(),[wave,0 if ls<2 else wavemap[(other>>13)&7]+1,dcw,cl(b[3]*(-1 if b[1] else 1),-24,24),64,int(((b[15]>>3)&7)==1),cl((w>>6)&7,0,5),cl((b[41+off]&127)-dcw)],env,0,0,note='Native 8-stage DCO/DCW/DCA envelopes reduced to common ADSR and DCW amount; velocity/native vibrato approximate.')
# Native Prophet factory SysEx, all 200 converted before selection.
rows=module('p5factory',U/'melodee/tools/gen_prophet_factory.py').records()
for p in rows:
 nm=p[65:85].decode('ascii').strip();osc=4 if p[16]>max(p[14],p[15]) else 2 if p[6] and not(p[3] or p[4] or p[5] or p[7]) else 7 if p[6] and p[3] else 5 if p[15]<p[14]//4 and p[3] else 6 if p[15]<p[14]//4 and p[4] else 3 if (p[3] and p[4]) or (p[5] and p[7]) else 1 if p[4] or p[7] else 0
 add(39,nm,[p[17],p[18],int(bool(p[20])),osc,cl((p[1]//2-p[0]//2),-48,48),p[40],max(p[32],p[33]),int(bool(p[10]))],[p[44],p[46],p[48],p[50]],0,int(bool(p[52])),[0,0,0,0],[cl(p[21]*.7),2 if p[23] else 1 if p[24] else 3 if p[25] else 0,cl(p[26]/2 if p[27] or p[28] else 0,-64,63),cl(p[26]/2 if p[31] else 0,-64,63),cl(p[26]/2 if p[29] or p[30] else 0,-64,63),0,p[13]], 'Native oscillator levels/coarse tuning, separate filter EG, modulation routing and unison reduced to common controls; no internal performance sequence.')
# K-WASUB preset oscillator-A identity, including the fourth engine macro.
s=(U/'kwasub/source/firmware/src/ksub_data.c').read_text();ek=enums(s);getrows=[]
for row in (B/'kw_presets.txt').read_text().splitlines():
 nm,data=row.split('|');p=list(map(int,data.strip(',').split(',')));g=lambda n:p[ek[n]]
 e={0:27,1:28,2:29,3:30,4:31,6:32,8:33,9:34,10:35}.get(g('A_ENG'))
 if e is None:continue
 getrows.append((nm,p,e));fx=[g('DR_MIX') if g('DR_ON') else 0,g('CH_MIX') if g('CH_ON') else 0,g('DL_MIX') if g('DL_ON') else 0,g('RV_MIX') if g('RV_ON') else 0]
 add(e,nm,[g('F_CUT'),g('F_RES'),g('A_P1'),g('A_P2'),g('A_P3'),g('A_P4'),0,0],[g('AE_A'),g('AE_D'),g('AE_S'),g('AE_R')],g('F_ENV'),int(g('V_MODE')!=0),fx,[g('L1_RATE'),cl(g('L1_SHP'),0,3),0,cl(g('L1_DEP') if g('L1_DST')==1 else 0,-64,63),0,0,g('V_GLIDE')], 'Oscillator A retained. B/sample layer, multiband/compressor/matrix/step effects reduced to shared engine/FX; preset pattern is not loaded.')
import curate_wave
banks[29]=curate_wave.make(banks[29])
# S1Vave: all 64 programs. Native mixer proportions / DRAW / CHOP / sub modes
# are immutable per program; stored P_LN0 identifies them across project/user saves.
enums_s1=enums((U/'s1vave/firmware/src/obv_params.h').read_text())
for row in (B.parent/'jazzy-engine-review/probe/s1-presets.txt').read_text().splitlines():
 nm,data=row.split('|');p=list(map(int,data.strip(',').split(',')));g=lambda k:p[enums_s1[k]]
 add(40,nm,[g('P_CUTOFF'),g('P_RESO'),0,g('P_SUB_LVL'),g('P_NOISE_LVL'),g('P_PWM_DEPTH'),g('P_DRAW_MULT'),g('P_CHOP_OVTN')/2],[g('P_ATTACK'),g('P_DECAY'),g('P_SUSTAIN'),g('P_RELEASE')],0,int(g('P_POLY_MODE')==0),[0,40 if g('P_CHO_MODE') else 0,g('P_DLY_LVL'),g('P_REV_LVL')],[g('P_LFO_RATE'),[2,2,1,3,4,4][g('P_LFO_WAVE')],cl(g('P_LFO_PITCH')/3,-64,63),cl(g('P_FLFO_AMT')/3,-64,63),cl(g('P_PWM_DEPTH')/3,-64,63) if g('P_PWM_SRC')==2 else 0,0,g('P_PORTA_TIME') if g('P_PORTA_MODE') else 0], 'Native oscillator mixer/DRAW/CHOP, sub mode and filter taper retained; common ADSR/LFO/FX. Range/master/sequence/chord performance not loaded.')
# HYDRA's sixteen native factory patches and named macro routes remain intact;
# the common host amplitude ADSR/FX replace its source host performance settings.
hs=(D/'hydra_factory.h').read_text()
for body in re.findall(r'\{\{([\d,]+)\}\}',hs):
 p=list(map(int,body.split(',')));nm=bytes(p[132:144]).decode().strip()
 add(41,nm,[0]*8,[0,65,110,50],0,1,note='Native factory waveform IDs/mutants/filters/eight macro routes retained. One voice per track; source host modulation/FX not imported.')
# Keep mappings in project sources for full review. Firmware rows may be coverage-selected by --limit.
allbanks={str(k):v for k,v in banks.items()};(R/'preset-projections.json').write_text(json.dumps(allbanks,indent=2,ensure_ascii=False)+'\n')
# Deterministic farthest-first selection balances sound controls and envelopes, avoids a first-N bias.
limit=int(sys.argv[1]) if len(sys.argv)>1 else 16
selected={}
for e,rows in banks.items():
 if e in (23,40,41):selected[e]=rows;continue
 quota=min(len(rows),limit if e not in (25,38,39) else limit*2)
 if quota==len(rows):selected[e]=rows;continue
 tag=lambda i:rows[i]['mono']>>1
 vec=lambda r:r['e']+r['env']+[r['fenv']]
 pick=[]
 def choose(ids):
  if not pick:return ids[0]
  return max(ids,key=lambda i:min(sum((a-b)**2 for a,b in zip(vec(rows[i]),vec(rows[j]))) for j in pick))
 fx=[i for i in range(len(rows)) if tag(i)==9];dr=[i for i in range(len(rows)) if tag(i)==8]
 reserve=min(2,len(fx))+(1 if quota>=12 and dr else 0)
 weights={1:4,4:4,3:4,2:4,5:3,6:2,7:1}
 while len(pick)<quota-reserve:
  groups={t:[i for i in range(len(rows)) if tag(i)==t and i not in pick] for t in weights};groups={t:ids for t,ids in groups.items() if ids}
  if not groups:break
  t=min(groups,key=lambda t:(sum(tag(i)==t for i in pick)/weights[t],list(weights).index(t)))
  pick.append(choose(groups[t]))
 for ids,cap in [(fx,2),(dr,1 if quota>=12 else 0)]:
  for _ in range(min(cap,len(ids),quota-len(pick))):
   best=choose([i for i in ids if i not in pick]);pick.append(best)
 while len(pick)<quota:
  pick.append(choose([i for i in range(len(rows)) if i not in pick]))
 selected[e]=[rows[i] for i in sorted(pick)]
blob=bytearray();offs=[0];metadata=[];manifest={};records=[]
for fid,(e,rows) in enumerate(selected.items(),1):
 start=len(records);manifest[str(e)]={'factory_id':fid,'source_count':len(banks[e]),'selected_count':len(rows),'names':[v['name'] for v in rows]}
 for v in rows:
  records.append(v['name'].encode('ascii','replace')[:15].ljust(16,b'\0')+bytes(x&255 for x in v['e']+v['env']+[v['fenv'],v['mono']]+v['fx']+v['extra']))
 metadata.append((start,len(rows)))
# Share compression history across model boundaries too; bank offsets name records.
for i in range(0,len(records),16):
 rr=records[i:i+16];rr += [bytes(41)]*(16-len(rr));raw=bytes(r[c] for c in range(41) for r in rr);c=lz4blk.compress(raw);assert lz4blk.decompress(c)==raw;blob+=c;offs.append(len(blob))
assert len(blob)<65536
out=['/* Generated original factory projections: 16 records, byte columns, lossless LZ4. */','#define FP_BLOCK_ROWS 16u','static const uint16_t FP_AT[]={'+','.join(map(str,offs))+'};','static const uint16_t FP_BANK[][2]={{0,0},'+','.join('{%d,%d}'%v for v in metadata)+'};','static const uint8_t FP_DATA[]={']+ [','.join(map(str,blob[i:i+96]))+',' for i in range(0,len(blob),96)]+['};']
# Independent record digests for the host decoder/application regression test.
expected=[]
for e,rows in selected.items():
 for k,v in enumerate(rows):
  raw=v['name'].encode('ascii','replace')[:15].ljust(16,b'\0')+bytes(x&255 for x in v['e']+v['env']+[v['fenv'],v['mono']]+v['fx']+v['extra']);h=2166136261
  for x in raw:h=((h^x)*16777619)&0xffffffff
  expected.append('{%du,%du,%du}'%(e,k,h))
(R/'rhythmer/tests/jazzy_factory_expect.h').write_text('/* Generated normalized factory record digests, test only. */\nstatic const uint32_t FP_EXPECT[][3]={'+','.join(expected)+'};\n')
(D/'factory_meta.h').write_text('/* Generated factory bank identity and counts. */\n'+''.join('#define FP_ID_%s %s\n#define FP_COUNT_%s %s\n'%(e,v['factory_id'],e,v['selected_count']) for e,v in manifest.items()))
(D/'factory_projection.h').write_text('\n'.join(out)+'\n');(R/'preset-selection.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Factory totals',sum(len(v) for v in selected.values()),'ROM',len(blob)+len(offs)*2+len(metadata)*4,'bytes',[(e,len(v)) for e,v in selected.items()])

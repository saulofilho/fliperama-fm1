#!/usr/bin/env python3
"""Lossless small-block integer predictors for immutable DSP lookup tables.
Every source value is checked; no audio decompression buffer or approximation.
"""
from pathlib import Path
import re,json
R=Path(__file__).resolve().parents[2];D=R/'rhythmer/firmware/jazzy';G=Path('/Volumes/SSD/Development/BuildCache/jazzy/gen')
def values(p,n):return list(map(int,re.findall(r'-?\d+',re.search(r'\b'+n+r'\[[^]]*\][^=;]*=\s*\{(.*?)\};',p.read_text(),re.S)[1])))
tables=[('VCF',values(D/'fm106_tables.h','FM106_VCF_G1')),('EXP',values(G/'felucca_tables.h','FM6_EXP2')),('M2',values(R/'rhythmer/firmware/mono2k/tables.h','m2_T_INC_TOP')),('KW',values(D/'kwasub.h','jk_KS_PITCH'))]
if not tables[2][1]:
 for p in G.glob('*.h'):
  if 'm2_T_INC_TOP[' in p.read_text():tables[2]=('M2',values(p,'m2_T_INC_TOP'));break
L=['/* Generated lossless lookup tables. tools/jazzy/compact_tables.py */','typedef struct {const uint32_t *base;const int32_t *d1;const int16_t *d2;const uint16_t *at;const uint8_t *width,*bits;} jt_table_t;']
stats={}
def arr(n,t,v):L.append('static const '+t+' '+n+'[]={'+','.join(map(str,v))+'};')
for name,v in tables:
 assert v,name
 if name=='VCF':
  base=[];at=[];width=[];bits=[]
  for i in range(0,len(v),64):
   a=v[i:i+64];delta=[0]+[a[j]-a[j-1] for j in range(1,len(a))];w=max(delta).bit_length();assert min(delta)>=0
   base.append(a[0]);at.append(len(bits));width.append(w)
   for b in range(w):
    for half in range(2):bits.append(sum(((delta[j]>>b)&1)<<(j&31) for j in range(half*32,(half+1)*32)))
   for j,y in enumerate(a):assert a[0]+sum(delta[:j+1])==y
  for suf,typ,a in [('B','uint16_t',base),('A','uint16_t',at),('W','uint8_t',width),('V','uint32_t',bits)]:arr('JV_'+suf,typ,a)
  L.append('''static unsigned jt_count(uint32_t x){x-=x>>1&0x55555555u;x=(x&0x33333333u)+(x>>2&0x33333333u);x=(x+(x>>4))&0x0f0f0f0fu;return x*0x01010101u>>24;}
static unsigned jv_lookup(unsigned k){unsigned g=k>>6,j=k&63u,sum=JV_B[g];uint32_t mask=0xffffffffu>>(31u-(j&31u));const uint32_t *p=JV_V+JV_A[g];for(unsigned b=0;b<JV_W[g];b++,p+=2){uint32_t x=j<32u?p[0]&mask:p[0],y=j<32u?0:p[1]&mask;sum+=(jt_count(x)+jt_count(y))<<b;}return sum;}''')
  stats[name]={'values':len(v),'original_bytes':len(v)*2,'packed_bytes':len(base)*5+len(bits)*4}
  continue
 base=[];d1=[];d2=[];offs=[];width=[];bits=[]
 for i in range(0,len(v),16):
  a=v[i:i+16];x=a[0];b=a[1]-x if len(a)>1 else 0;c=a[2]-2*a[1]+x if len(a)>2 else 0
  if not -32768<=c<=32767:c=0
  z=[]
  for j,y in enumerate(a):
   pred=x+b*j+c*j*(j-1)//2;r=y-pred;z.append((r<<1)^(r>>63))
  w=max(z).bit_length();base.append(x);d1.append(b);d2.append(c);width.append(w);offs.append(len(bits))
  for y in z:bits.extend((y>>k)&1 for k in range(w))
  for j,y in enumerate(a):
   off=offs[-1]+j*w;u=sum(bits[off+k]<<k for k in range(w));r=(u>>1)^-(u&1)
   assert x+b*j+c*j*(j-1)//2+r==y
 blob=[sum(bits[i+k]<<k for k in range(min(8,len(bits)-i))) for i in range(0,len(bits),8)]+[0,0,0,0]
 assert max(width)<=24 and max(offs)<65536
 for suf,typ,a in [('B','uint32_t',base),('D','int32_t',d1),('Q','int16_t',d2),('A','uint16_t',offs),('W','uint8_t',width),('V','uint8_t',blob)]:arr('JT_'+name+'_'+suf,typ,a)
 L.append('static const jt_table_t JT_'+name+'={'+','.join('JT_'+name+'_'+x for x in ('B','D','Q','A','W','V'))+'};')
 stats[name]={'values':len(v),'original_bytes':len(v)*(2 if name=='VCF' else 4),'packed_bytes':len(base)*13+len(blob)+24}
L.append('''static uint32_t jt_lookup(const jt_table_t *t,unsigned k){
 unsigned b=k>>4,j=k&15u,w=t->width[b],pos=t->at[b]+j*w;const uint8_t *p=t->bits+(pos>>3);
 uint32_t u=(uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;
 u=(u>>(pos&7u))&((1u<<w)-1u);int32_t r=(int32_t)(u>>1)^-(int32_t)(u&1u);
 return t->base[b]+(uint32_t)(t->d1[b]*(int)j+t->d2[b]*(int)(j*(j-1u)/2u)+r);
}''')
(D/'compact_tables.h').write_text('\n'.join(L)+'\n');(R/'compact-tables.json').write_text(json.dumps(stats,indent=2)+'\n');print(json.dumps(stats))

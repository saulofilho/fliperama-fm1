#!/usr/bin/env python3
"""Use only the unused tails of the two reserved factory PCM slots.
PCM headers/payload and every address outside those slots remain unchanged.
"""
from pathlib import Path
import os,re,struct,zlib,json
R=Path(__file__).resolve().parents[2];D=R/'rhythmer/firmware/jazzy'
B=Path(os.environ.get('JAZZY_ASSET_BANK_DIR') or '/Volumes/SSD/Development/BuildCache/jazzy/synth-banks')
B.mkdir(parents=True, exist_ok=True)
def vals(p,n):return list(map(int,re.findall(r'-?\d+',re.search(r'\b'+n+r'\[[^]]*\]\s*=\s*\{(.*?)\};',p.read_text(),re.S)[1])))
wave=vals(D/'wave_curated.h','jk_KS_WT');hy=bytes(vals(D/'hydra_waves.h','JH_WAVE_PACK'))
factory=[int(x) for body in re.findall(r'\{\{([\d,]+)\}\}',(D/'hydra_factory.h').read_text()) for x in body.split(',')]
s1=D/'s1_factory.h';sections=[('JH_FACTORY',bytes(factory)),('JS_CFG',bytes(vals(s1,'JS_CFG'))),('JS_WAVE',bytes(vals(s1,'JS_WAVE'))),('JS_DRAW',struct.pack('<240h',*vals(s1,'JS_DRAW'))),('JS_CHOP',struct.pack('<112H',*vals(s1,'JS_CHOP')))]
offsets={};data=b''
for name,part in sections:offsets[name]=len(data);data+=part
offsets['JH_WAVE_PACK']=len(data);data+=hy
data=data.ljust((len(data)+3)//4*4,b'\0');offsets['JF_PACK']=len(data);data+=bytes(vals(D/'fmini_compact.h','JF_PACK'));assert len(data)<=16352
meta=[]
factory_banks = Path(os.environ.get('JAZZY_FACTORY_BANKS') or R/'factory-banks')
if not factory_banks.is_dir() and 'JAZZY_FACTORY_BANKS' not in os.environ:
 factory_banks = Path('/Volumes/SSD/Development/BuildCache/rhythmer/samples')
for i,n in enumerate(('amen-160','think-160')):
 original=(factory_banks/(n+'.slot')).read_bytes()
 assert len(original)==81920 and original[73728:]==b'\xff'*(81920-73728),'PCM tail must be unused'
 payload=data[i*8176:(i+1)*8176].ljust(8176,b'\xff');crc=zlib.crc32(payload)
 footer=struct.pack('<4I',0x53415a4a,i,8176,crc)+payload
 slot=original[:73728]+footer;assert len(slot)==81920 and slot[:72512]==original[:72512]
 (B/(n+'.slot')).write_bytes(slot);meta.append(crc)
(D/'synth_assets.h').write_text('''/* Generated reserved-bank tail metadata. No project/song/settings addresses. */
#pragma once
#ifndef JAZZY_EXTERNAL_ASSETS
#define JAZZY_EXTERNAL_ASSETS 0
#endif
#define JAZZY_ASSET_TAIL 73728u
#define JAZZY_ASSET_PAYLOAD 8176u
static const uint32_t JAZZY_ASSET_CRC[2]={'''+','.join(str(v)+'u' for v in meta)+'''};
#if JAZZY_EXTERNAL_ASSETS
static uint8_t jazzy_assets_valid;
static const uint8_t *jazzy_asset_at(unsigned off);
static int jazzy_assets_check(void);
#else
#define jazzy_assets_valid 1
#endif
''')
with (D/'synth_assets.h').open('a') as f:f.write(''.join('#define JA_'+k+' '+str(v)+'u\n' for k,v in offsets.items()))
(R/'synth-assets.json').write_text(json.dumps({'tail_offset':73728,'tail_bytes_per_slot':8192,'data_bytes':len(data),'offsets':offsets,'hydra_pack_bytes':len(hy),'payload_crc32':meta,'pcm_payload_unchanged':True},indent=2)+'\n')
print('Synth assets:',len(data),'of 16352 payload bytes; PCM unchanged')

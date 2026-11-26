#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""JAZZY palettes: stable RHYTHMER layout, four semantic encoder colours."""
import argparse
from pathlib import Path
PALETTES=[('DARK',(0,0,0),(237,236,218)),('LIGHT',(238,235,219),(31,41,41))]
KNOBS=[[(112,183,204),(216,180,111),(199,209,192),(249,119,88)],
       [(21,101,117),(119,81,27),(55,85,76),(156,55,29)]]
def rgb(c):return (c[0]>>3)<<11 | (c[1]>>2)<<5 | c[2]>>3
def luminance(c):
 def lin(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
 return sum(k*lin(v/255) for k,v in zip((.2126,.7152,.0722),c))
def main():
 p=argparse.ArgumentParser();p.add_argument('out',nargs='?');p.add_argument('--report',action='store_true');a=p.parse_args();rows=[]
 for i,(name,bg,fg) in enumerate(PALETTES):
  lum=sorted((luminance(bg),luminance(fg)));contrast=(lum[1]+.05)/(lum[0]+.05);assert contrast>=4.5
  if a.report:print(name,'primary text contrast',round(contrast,2))
  cols=[bg,bg,fg,KNOBS[i][0],KNOBS[i][3]];rows.append('    {"'+name+'",'+','.join('0x%04x'%rgb(c) for c in cols)+'},')
 out=['/* generated JAZZY semantic palettes */','#pragma once','static const ui_pal_t UI_PALETTES[] = {',*rows,'};','static const uint8_t UI_STORAGE_IDS[2]={73,75};','static const uint8_t UI_RAISE_OF[2]={12,12};','static const uint16_t UI_KNOBS[2][4]={'+','.join('{'+','.join('0x%04x'%rgb(c) for c in row)+'}' for row in KNOBS)+'};','#define UI_NPALETTES 2u','#define UI_BW_INDEX 0u','#define UI_INVERT_INDEX 1u','#define UI_BW_GREY 0x528au','#define UI_PAL_TAG 64u']
 for k,v in {'MID':76,'DIM':60,'LINE':25,'SEL':80,'TINT':12,'KEY':78,'RAISE':12}.items():out.append(f'#define UI_{k}_PCT {v}')
 out+=['#define UI_REC_DARK 0xfa86u','#define UI_REC_LIGHT 0xb9c3u','#define UI_QR_LIGHT 0xffffu','#define UI_QR_DARK 0u','#define UI_CRASH_BG 0u','#define UI_CRASH_INK 0xffffu']
 if a.out:Path(a.out).write_text('\n'.join(out)+'\n')
if __name__=='__main__':main()

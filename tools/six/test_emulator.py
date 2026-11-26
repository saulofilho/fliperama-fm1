#!/usr/bin/env python3
"""Run the unchanged target FWSC in upstream fm1-emu. No physical device I/O."""
import argparse, array, hashlib, json, os, re, struct, subprocess, wave, zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
a=argparse.ArgumentParser();a.add_argument('--emulator',required=True);a.add_argument('--strict',action='store_true');a.add_argument('--dense',action='store_true');a.add_argument('--fm6',action='store_true');a.add_argument('--bpm',type=int,default=160);args=a.parse_args()
out=ROOT/'build/six-emu';out.mkdir(parents=True,exist_ok=True)
fw=ROOT/'build/six-target/six-prototype.fwsc'
symbols={m[2]:int(m[1],16)-0x1c00000 for m in re.finditer(r'^([0-9a-f]+).*?\s([A-Za-z_][A-Za-z_0-9]*)$',(fw.parent/'x0x.sym').read_text(),re.M)}
results={ 'firmware_sha256':hashlib.sha256(fw.read_bytes()).hexdigest(), 'emulator':subprocess.check_output([args.emulator,'--version'],text=True).strip(),'physical_hardware_tested':False,'runs':{} }
def run(name,ms,script='',flash=None,strict=False):
 env=dict(os.environ,FM1_BENCH_KEYS=script,FM1_BENCH_PANEL=str(out/(name+'.ppm')),FM1_DUMPRAM=str(out/(name+'.ram')),FM1_BENCH_WAV=str(out/(name+'.pcm')),FM1_BENCH_JSON=str(out/(name+'.json')))
 if strict:env['FM1_STRICT']='1'
 if args.dense:env['FM1_USB_WAV']=str(out/(name+'-usb.pcm'))
 cmd=[args.emulator,'--fwsc',str(fw),'--bench',str(ms),'--midi','none','--usb']
 if flash:cmd+=['--flash',str(flash)]
 with (out/(name+'.log')).open('w') as log:subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=600)
 log=(out/(name+'.log')).read_text();assert 'halt:' not in log and 'cannot read' not in log,log
 ram=(out/(name+'.ram')).read_bytes();s=struct.unpack_from('<14I4B',ram,symbols['status'])
 st=dict(zip(['blocks','ticks','peak_pct','average_pct','overruns','worker_faults','queue_drops',*[f'job{i}' for i in range(6)],'worker_mask','quality','step','playing','loop_mask'],s))
 st['core1']=struct.unpack_from('<I',ram,symbols['fm1_c1_on'])[0]
 st['crash_magic']=struct.unpack_from('<I',ram,symbols['fm1_crash'])[0]
 st['late_halves']=struct.unpack_from('<13I',ram,symbols['x0x_dbg'])[5]
 pcm=(out/(name+'.pcm')).read_bytes();samples=array.array('h',pcm);st['audio_frames']=len(samples)//2;st['peak_pcm16']=max(map(abs,samples),default=0)
 with wave.open(str(out/(name+'.wav')),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(44100);w.writeframes(pcm)
 results['runs'][name]=st;print(name,st,flush=True)
 assert st['blocks']>100 and st['worker_faults']==st['queue_drops']==st['crash_magic']==0
 return ram,st
if args.dense:
 # A deliberately busy saved project, using the same validated binary journal format.
 ram=(out/'save_project.ram').read_bytes();project=bytearray(ram[symbols['project']:symbols['project']+1702])
 struct.pack_into('<H',project,0,args.bpm*10)
 project[2]=0;project[4:8]=bytes([32,60,48,64]);project[8:11]=bytes([90,2,64])
 for tr in range(6):
  off=33+tr*278
  if args.fm6 and tr>=3:project[off+7:off+22]=project[33+4*278+7:33+4*278+22]
  project[off+2:off+6]=bytes([64]*4)
  for step in range(32):
   at=off+22+step*8
   notes=[36+step%7,255,255] if tr==1 else [48+tr*3,55+tr*3,255]
   project[at:at+8]=bytes([*notes,110,47,1|(2 if tr==1 and step%4==0 else 0),31 if tr==2 else 0,100])
 payload=struct.pack('<4I',0x36584953,1,1702,zlib.crc32(project))+project+b'\0\0'
 header=struct.pack('<IHH5I',0x30583058,5,0,100,len(payload),zlib.crc32(payload),0,0)
 header+=struct.pack('<I',zlib.crc32(header))
 flash=bytearray((out/'stress.flash').read_bytes());flash[0x9d000:0x9e000]=b'\xff'*4096
 flash[0x9d000:0x9d020]=header;flash[0x9d100:0x9d100+len(payload)]=payload
 dense=out/'dense.flash';dense.write_bytes(flash)
 name=('dense-strict' if args.strict else 'dense')+('-fm6' if args.fm6 else '')+f'-{args.bpm}'
 ram,st=run(name,8000,'800:12,900:12^,2000:n23,3000:n23^,4000:n26,5000:n26^',dense,args.strict)
 assert st['playing']==1 and st['loop_mask']==3 and st['peak_pcm16']>100
 assert st['overruns']==st['late_halves']==0,'audio deadline exceeded'
 assert ram[symbols['project']:symbols['project']+1702]==project
elif args.strict:
 run('strict',3000,'800:e0:1,1000:10,1100:10^,1200:12,1300:12^',out/'stress.flash',True)
else:
 seed=out/'seed.flash';seed.unlink(missing_ok=True)
 run('boot',3000,flash=seed)
 flash=bytearray(seed.read_bytes())
 for slot in range(2):
  data=(ROOT/f'build/six/original-loop-{slot+1}.slot').read_bytes();assert len(data)==0x14000
  off=0xa0000+slot*0x14000;flash[off:off+len(data)]=data
 stress=out/'stress.flash';stress.write_bytes(flash)
 events=[]
 def key(t,k,d=90):events.extend([f'{t}:{k}',f'{t+d}:{k}^'])
 def enc(t,e,n):events.append(f'{t}:e{e}:{n}')
 # All tracks have wet sends into all four effects. Real panel input only.
 t=800
 for tr in range(6):
  if tr:enc(t,0,1);t+=100
  events.append(f'{t}:3');t+=100
  for fx in range(4):
   enc(t,4,45);t+=100;key(t,5);t+=150
  events.append(f'{t}:3^');t+=150
 # Distortion drive; phaser and existing delay/reverb are configured from defaults.
 key(t,2);t+=150;enc(t,2,75);t+=100;key(t,2);t+=150
 # Return to acid, generate and play the sequencer.
 enc(t,0,-4);t+=100;key(t,10);t+=150;key(t,12);start=t;t+=150
 # Simultaneous sustained synth chords, repeated drum hits, running acid and break.
 for j in range(16):
  now=t+j*375
  for ch,notes in [(3,[48,55]),(4,[60,64]),(5,[67,72])]:
   for n in notes:
    events.append(f'{now}:m{0x90+ch:02x}{n:02x}64');events.append(f'{now+300}:m{0x80+ch:02x}{n:02x}00')
  for n in [36,42,38 if j%2 else 46,39]:events.append(f'{now}:m92{n:02x}6e')
 # Program one recurring step on every synth and drum, then leave transport running.
 end=t+6100
 for tr in range(2,6):
  enc(end,0,1);key(end+100,11);key(end+250,'n0');key(end+400,11);end+=600
 enc(end,0,-5);key(end+150,'n7',600);enc(end+850,6,1)
 ram,st=run('stress',end+2700,','.join(events),stress)
 assert st['core1']==1 and st['playing']==1 and st['loop_mask']==3 and st['ticks']>768 and st['peak_pcm16']>100
 project=ram[symbols['project']:symbols['project']+1702]
 ram,st=run('save',2500,'800:9,900:9^',stress)
 # Save the stress project's RAM through panel SAVE in the same run instead:
 events.extend([f'{end+1800}:9',f'{end+1900}:9^'])
 # Reload a fresh fixture so the exact UI script starts with defaults.
 stress.write_bytes(flash)
 ram,st=run('save_project',end+2700,','.join(events),stress)
 expected=ram[symbols['project']:symbols['project']+1702];assert st['playing']==0
 ram,st=run('restore',2500,flash=stress)
 assert ram[symbols['project']:symbols['project']+1702]==expected,'project differs after reboot'
 assert st['loop_mask']==3
 results['save_restore_exact']=True
name=(name+'-results.json') if args.dense else ('strict-results.json' if args.strict else 'emulator-results.json')
(out/name).write_text(json.dumps(results,indent=2));print('PASS',name,flush=True)

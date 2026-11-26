#!/usr/bin/env python3
"""Host validation only. A Mac runtime percentage does not measure FM-1 CPU usage."""
from pathlib import Path
import os, subprocess, sys, wave, json, hashlib
root=Path(__file__).resolve().parents[2]
os.chdir(root)
out=root/"build"/"six";out.mkdir(parents=True,exist_ok=True)
for script,name in [("gen_tables.py","felucca_tables.h"),("gen_fm6_patches.py","felucca_fm6.h")]:
 subprocess.run([sys.executable,str(root/"tools"/"six"/script),str(out/name)],check=True)
subprocess.run([sys.executable,"tools/gen_drum_samples.py",str(out/"x0x_drum_samples.h")],check=True)
sources=["tests/six/host.c","firmware/six/six.c","firmware/six/jiant.c","firmware/six/shared_fx.c","firmware/six/tables.c",
 "firmware/six/vendor/amenity/jungle.c","firmware/src/dsp/bass303.c","firmware/src/dsp/fxbus.c","firmware/src/dsp/master.c","firmware/src/seq/tb3po.c"]
flags=["-std=c11","-O2","-g","-fwrapv","-ffp-contract=off","-DSIX_HOST","-DX0X_HOST","-DFM1_HOST_TEST",
 "-Ibuild/six","-Ifirmware/six","-Ifirmware/src/dsp","-pthread"]
if "--sanitize" in sys.argv:flags+=["-fsanitize=address,undefined","-fno-sanitize=shift,signed-integer-overflow","-fno-omit-frame-pointer"]
if "--threadsan" in sys.argv:flags+=["-fsanitize=thread","-fno-omit-frame-pointer"]
exe=out/"six_host"
subprocess.run([os.environ.get("CC","clang"),*flags,*sources,"-lm","-o",str(exe)],check=True)
results={}
for name,dual,fault in [("single",0,0),("dual",1,0),("fault",1,1)]:
 p=subprocess.run([str(exe),str(out/(name+".pcm")),str(dual),str(fault)],check=False,text=True,capture_output=True,env={**os.environ,"UBSAN_OPTIONS":"halt_on_error=1","ASAN_OPTIONS":"detect_leaks=0"})
 print(p.stdout,end="");print(p.stderr,end="",file=sys.stderr);p.check_returncode();results[name]=p.stdout
assert (out/"single.pcm").read_bytes()==(out/"dual.pcm").read_bytes(),"dual-core render differs"
with wave.open(str(out/"six-demo.wav"),"wb") as w:
 w.setnchannels(2);w.setsampwidth(2);w.setframerate(44100);w.writeframes((out/"dual.pcm").read_bytes())
results["bit_exact"]=True
results["sha256"]=hashlib.sha256((out/"six-demo.wav").read_bytes()).hexdigest()
(out/"host-results.json").write_text(json.dumps(results,indent=2))
print("PASS: single/dual bit-identical; fault quarantine; save CRC; voice caps; queue overflow; overload recovery")

# Exercise the actual panel controller and target font renderer headlessly.
if (root/"build/six-target/gen/felucca_font.h").exists():
 ui=out/"six_ui"
 subprocess.run([os.environ.get("CC","clang"),*flags,"-DSIX_UI_TEST","-Ibuild/six-target/gen",
                 *sources,"tests/six/ui.c","-lm","-o",str(ui)],check=True)
 subprocess.run([str(ui)],check=True)

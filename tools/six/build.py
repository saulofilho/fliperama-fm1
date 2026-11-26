#!/usr/bin/env python3
"""FM-1 hardware build. Requires JieLi Linux toolchain, Linux container runtime and pinned AC79 SDK."""
import os,runpy
from pathlib import Path
os.environ["FM1_SIX"]="1"
runpy.run_path(str(Path(__file__).resolve().parents[1]/"build.py"),run_name="__main__")

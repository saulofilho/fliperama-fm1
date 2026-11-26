from pathlib import Path
import re,sys
sys.path.insert(0,'/Volumes/SSD/Development/Toolchains/jazzy-python')
from tree_sitter import Language,Parser
import tree_sitter_c
parser=Parser(Language(tree_sitter_c.language()))
S=Path(__file__).resolve().parents[2]/'rhythmer/firmware/src'
def children(n):
 yield n
 for c in n.named_children:yield from children(c)
def value(n,b):
 if not n:return None
 s=b[n.start_byte:n.end_byte].decode()
 if n.type=='number_literal' and s in ['0','1']:return int(s)
 if n.type=='parenthesized_expression':return value(n.named_children[0],b)
 if n.type=='unary_expression' and s.startswith('!'):
  v=value(n.named_children[-1],b);return None if v is None else int(not v)
 if n.type=='binary_expression':
  l=value(n.child_by_field_name('left'),b);r=value(n.child_by_field_name('right'),b);op=n.child_by_field_name('operator').text.decode()
  if op=='&&':
   if l==0 or r==0:return 0
   if l==1 and r==1:return 1
  if op=='||':
   if l==1 or r==1:return 1
   if l==0 and r==0:return 0
 return None
def simplify(s):
 for _ in range(12):
  b=s.encode();tree=parser.parse(b);ed=[]
  for n in children(tree.root_node):
   if n.type in ['if_statement','conditional_expression']:
    v=value(n.child_by_field_name('condition'),b)
    if v is None:continue
    chosen=n.child_by_field_name('consequence' if v else 'alternative')
    if chosen and chosen.type=='else_clause':chosen=chosen.named_children[-1]
    replacement=chosen.text.decode() if chosen else ';'
    if not any(a<=n.start_byte<z for a,z,_ in ed):ed.append((n.start_byte,n.end_byte,replacement))
  if not ed:break
  for a,z,r in reversed(ed):b=b[:a]+r.encode()+b[z:]
  s=b.decode()
 return s
def rmfunc(s,names):
 b=s.encode();tree=parser.parse(b);ed=[]
 for n in children(tree.root_node):
  if n.type=='function_definition':
   d=n.child_by_field_name('declarator').text.decode();name=re.search(r'\b(\w+)\s*\(',d)
   if name and name[1] in names:ed.append((n.start_byte,n.end_byte))
 for a,z in reversed(ed):b=b[:a]+b[z:]
 return b.decode()
for p in S.glob('*.c'):
 s=p.read_text()
 # Entire retired-engine comparisons become compile-time constants, then removed structurally.
 s=re.sub(r'ENGINES\[(?:[^\[\]]|\[[^\]]*\])*\]\s*(!=|==)\s*&ENG_DRUM',lambda m:'1' if m[1]=='!=' else '0',s)
 s=re.sub(r'\be\s*(==|!=)\s*&ENG_DRUM',lambda m:'0' if m[1]=='==' else '1',s)
 s=re.sub(r'\bdrum_track\((?:[^()]|\([^()]*\))*\)','0',s)
 s=re.sub(r'(?:t->engine|t->eng_req|e)\s*==\s*ENGI_DRUM\b','0',s)
 s=s.replace('ENG_DRUM.npresets','1u')
 s=simplify(s)
 if p.name=='fx.c':s=rmfunc(s,{'drum_mix'})
 if p.name=='six_graph.c':
  s=re.sub(r'if\(t->engine==ENGI_DRUM\).*?\}\}', '',s)
 p.write_text(s)
# Keep legacy note-map conversion helpers for decoding old sequence events only.
p=S/'legacy_kit_wire.h';s=p.read_text();orig=Path('/Users/dave/Documents/Codex/fm1-six/rhythmer/firmware/src/eng_drum.c').read_text()
s+='\n'+orig[orig.index('static const int8_t DRUM_GM'):orig.index('/* (JIANT 0.8.5) the octaves')]
s+='\nstatic uint32_t drum_lane(uint32_t n){return DRUM_GM[drum_gm_ix(n)][0];}\nstatic const uint8_t DRUM_LANE_NOTE[8]={36,38,39,42,46,45,37,56};\n'
s+=orig[orig.index('static uint32_t step_lanes'):orig.index('static drum_lane_t *drum_kit_of')]
p.write_text(s)
# Shared envelope math used by FX, detached from the removed drum oscillator.
p=S/'dsp.c';s=p.read_text();o=Path('/Users/dave/Documents/Codex/fm1-six/rhythmer/firmware/src/drumx_voice.c').read_text();s+='\n'+o[o.index('static uint32_t dv_kb'):o.index('static void dx_trigger')];p.write_text(s)
p=S/'../jazzy/fmini.c';s=p.read_text().replace('FG_NUM','FMINI_FG_NUM');p.write_text(s)

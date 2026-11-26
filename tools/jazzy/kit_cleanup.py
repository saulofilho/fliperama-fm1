from pathlib import Path
import sys,re
sys.path.insert(0,'/Volumes/SSD/Development/Toolchains/jazzy-python')
from tree_sitter import Language,Parser
import tree_sitter_c
pa=Parser(Language(tree_sitter_c.language()));S=Path(__file__).resolve().parents[2]/'rhythmer/firmware/src'
def nodes(n):
 yield n
 for c in n.named_children:yield from nodes(c)
for p in S.glob('*.c'):
 s=p.read_text();s=re.sub(r'[A-Za-z_][\w.>\-\[\]]*engin0\b|\bengin0\b','0',s);p.write_text(s)
for f in ['ui_graph.c','ui_layer.c','ui_tools.c','seq.c']:
 s=(S/f).read_bytes();t=pa.parse(s)
 for n in nodes(t.root_node):
  if n.type=='function_definition' and any(x in n.text.decode() for x in ['drum_kit_of','dx_img_k','dx_in_tch','drum_lane_abbr','drum_lane_name','drum_oct_note']):
   print(f,n.child_by_field_name('declarator').text.decode().split('(')[0])

from pathlib import Path
import re
P=Path(__file__).resolve().parent
exec((P/'strip_kit_paths.py').read_text().split("for p in S.glob('*.c'):")[0])
# Extend the specialization to dead loops, and expressions as well as branches.
for p in S.glob('*.c'):
 s=p.read_text()
 for _ in range(8):
  b=s.encode();tree=parser.parse(b);ed=[]
  for n in children(tree.root_node):
   replacement=None
   if n.type=='for_statement' and value(n.child_by_field_name('condition'),b)==0:replacement=';'
   if n.type in ['binary_expression','unary_expression']:
    v=value(n,b)
    if v is not None:replacement=str(v)
   if replacement is not None and not any(a<=n.start_byte<z for a,z,_ in ed):ed.append((n.start_byte,n.end_byte,replacement))
  if not ed:break
  for a,z,r in reversed(ed):b=b[:a]+r.encode()+b[z:]
  s=simplify(b.decode())
 p.write_text(s)
p=S/'seq.c';s=p.read_text()
for name in ['rec_lmode','rec_drum','dxo_on','dxo_off','dxo_rec_hold','dxo_hit','dxo_tick','dxo_part']:s=rmfunc(s,{name})
s=re.sub(r'^\s*dx_in_(?:rat|tch)\s*=[^;]*;[^\n]*','',s,flags=re.M)
s=s.replace('(uint8_t)((dx_in_rat & 15u) | (dx_in_tch & 3u) << 4)','0').replace('drum_oct_note(x, kb_oct[k])','x')
s=re.sub(r'\bdxo_on\(t, x, kb_oct\[k\], 100u?,[^;]*;', 'input_on(t,x,100);',s)
s=re.sub(r'\bdxo_on\([^;]+;',';',s);s=re.sub(r'\bdxo_(?:off|rec_hold|tick)\([^;]+;',';',s)
# Ratchet-kit state never allocated in JAZZY.
a=s.find('#define DXO_N');b=s.find('/*',a+1)
# Leave only unused old-format types until byte-layout migration audit completes.
p.write_text(s)
p=S/'ui_graph.c';s=p.read_text();s=rmfunc(s,{'graph_dximg','graph_grid','graph_drum'});s=re.sub(r'    if \(pg->graph == GR_DXIMG\)[^\n]*\n[^\n]*\n','',s);p.write_text(s)
p=S/'ui_layer.c';s=p.read_text();s=s.replace('drum_lane_abbr(TSEL, ui.lane)','""');p.write_text(s)
p=S/'ui_tools.c';s=p.read_text().replace('drum_lane_name(t, l)','""');p.write_text(s)
# Host harness retains platform stubs and boot helper, drops RHYTHMER-specific test cases.
p=S.parent.parent/'tests/ui_test.c';s=p.read_text();s=s[:s.index('/* card slot drawn')];(p.parent/'jazzy_host.h').write_text(s)

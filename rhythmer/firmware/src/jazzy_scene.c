/* GPL-3.0-only. Bounded musical scenes. At most 16 particles, no physical simulation. */
static void jazzy_scene(const track_t *t,int en,unsigned ph){
 unsigned obj=jazzy_object(t->engine),notes=0,lo=127,hi=0;
 for(unsigned i=0;i<NVOICE;i++)if(t->v[i].active&&t->v[i].gate){unsigned n=t->v[i].note;notes++;if(n<lo)lo=n;if(n>hi)hi=n;}
 if(notes>4)notes=4;
 if(!notes){notes=1;lo=hi=60;}
 int motion=!(ui_prefs&PREF_ANIM_OFF),span=hi-lo;
 if(!motion){en=0;ph=0;notes=1;lo=hi=60;span=0;}
 int burst=en*25/127,beat=motion?(int)t->seq_idx:0;
 uint16_t a=ux.k[0],b=ux.k[1],c=ux.k[2],d=ux.k[3];
 if(t->engine==ENGI_BREAK){
  for(unsigned j=0;j<12;j++){unsigned z=ph+j*0x15555555u;int r=42+(j%3)*14+burst/2;int xx=120+osc_sine(z)*r/32768,yy=62+osc_sine(z+0x40000000u)*(r/2)/32768;cv_rect(xx,yy,j%3?2:4,2,j%3?a:d);}
  for(unsigned j=0;j<16;j++){int x=12+j*14;cv_line_t(x,104,x,104-(j==(unsigned)(beat&15)?burst:3),j==(unsigned)(beat&15)?d:T_DIM,1);}return;
 }
 if(obj==13){ /* A moving skate spot: chords add rails, attack adds landing spray. */
  cv_line_t(8,106,232,106,T_DIM,1);
  for(unsigned j=0;j<8;j++){int x=8+(j*31+(int)(ph>>25))%220;cv_line_t(x,109,x+8,109,T_DIM,1);}
  for(unsigned k=0;k<notes;k++){int rx=12+(int)k*54,ry=94-(int)(k&1u)*8;cv_line_t(rx,ry,rx+35,ry,b,1);cv_line_t(rx+5,ry,rx+5,104,T_DIM,1);cv_line_t(rx+30,ry,rx+30,104,T_DIM,1);}
  if(en>70)for(unsigned j=0;j<6;j++){int x=103+(int)j*7,y=102-(int)(j%3)*burst/6;cv_line_t(x,y,x-5,y-3,d,1);}
 }else if(obj==11||obj==9){ /* Chord intervals bend the water; tentacles ride its current. */
  for(unsigned line=0;line<4;line++){int px=8,py=30+line*23;for(unsigned j=1;j<=22;j++){int x=8+j*10,y=30+line*23+osc_sine(ph+j*(0x09000000u+span*0x100000u)+line*0x33000000u)*(2+burst/3)/32768;cv_line_t(px,py,x,y,line&1?T_DIM:a,1);px=x;py=y;}}
  for(unsigned j=0;j<notes*2;j++){int x=18+j*29,y=22+(int)((ph>>(22+j%2))%75u);jazzy_ring(x,y,2+j%2,2+j%2,b);}
 }else if(obj==1){ /* The cat bats chord blocks; velocity throws them farther. */
  cv_line_t(9,103,231,103,T_DIM,1);
  for(unsigned j=0;j<notes*3;j++){int x=12+j*19+(int)((ph>>25)&7u),lift=(j+beat)%3;int y=91-lift*(7+burst/2)-((ph>>(24+j%3))&7u)*en/127;cv_frame(x,y,7,7,ux.k[j&3]);}
 }else if(obj==5){ /* Road markings rush past while the chassis jumps on accents. */
  for(unsigned lane=0;lane<3;lane++)for(unsigned j=0;j<6;j++){int x=8+(j*40+((ph>>23)&31u))%220,y=83+lane*10;cv_line_t(x,y,x+12+burst/3,y,lane==1?b:T_DIM,1);}
  if(en>70)for(unsigned j=0;j<4;j++)cv_line_t(28+j*10,72-j*7,45+j*10,68-j*7,d,1);
 }else if(obj==14){ /* The cabinet cannot contain a dense chord: popcorn erupts. */
  for(unsigned j=0;j<16;j++){int age=(ph>>(23+j%3))&31u;int x=120+((int)j-8)*(3+burst/4),y=76-age*en/100+(age*age)/40;cv_rect(x,y,3+(j%2),3,b);}
 }else if(obj==2||obj==3||obj==4){ /* Stomps and punches shake the floor into rhythmic fractures. */
  int px=8,py=102;for(unsigned j=1;j<=24;j++){int x=8+j*9,y=102-((j+beat)&1u?1:-1)*burst*(int)(j%4+1)/12;cv_line_t(px,py,x,y,T_DIM,1);px=x;py=y;}
  if(en>20)for(unsigned j=0;j<8;j++){unsigned z=j*0x20000000u;int xx=120+osc_sine(z)*(42+burst)/32768,yy=63+osc_sine(z+0x40000000u)*(24+burst/2)/32768;cv_line_t(xx,yy,xx+osc_sine(z)*9/32768,yy+osc_sine(z+0x40000000u)*7/32768,j&1?b:d,1);}
 }else if(obj==15){ /* Harmonic branches spread out, lifted by the actual chord. */
  for(unsigned j=0;j<notes*3;j++){int xx=14+j*19,hh=12+(j*7+span*3)%38+burst/2;cv_line_t(xx,105,xx,105-hh,j&1?a:b,2);cv_line_t(xx,94,xx+7,88,j&1?a:b,1);}
 }else if(obj==12){ /* A stitched rhythm ribbon is pulled through the machine. */
  for(unsigned j=0;j<20;j++){int x=8+j*11,y=88+((j+beat)&1u?4:-4);cv_line_t(x,y,x+9,176-y,j&1?b:d,1);}
 }else if(obj==8||obj==10){ /* Notes become struck keys or marbles escaping the cradle. */
  for(unsigned j=0;j<notes*3;j++){unsigned z=ph+j*0x18000000u;int xx=16+j*18,yy=96-(osc_sine(z)+32768)*burst/65536;cv_frame(xx,yy,10,6,ux.k[j&3]);}
 }else{ /* Rocket/robot: rhythmic star field with chord-linked electric connections. */
  for(unsigned j=0;j<16;j++){int x=10+(j*47+(ph>>24))%220,y=18+(j*31+lo)%82;cv_rect(x,y,j%4?1:3,j%4?1:3,j%4?T_DIM:b);if(j<notes&&en>20)cv_line_t(x,y,120,62,ux.line,1);}
 }
}

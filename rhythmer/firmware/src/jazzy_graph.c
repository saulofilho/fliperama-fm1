/* SPDX-License-Identifier: GPL-3.0-only
 * Original JAZZY objects. All raster conversion is build-time, no heap or audio callbacks.
 * Indexed scanline runs share one palette. Each model has a bounded mechanism, not free physics.
 */
#include "../jazzy/objects.h"
#include "jazzy_pose.c"
static void jazzy_ring(int x,int y,int rx,int ry,uint16_t c){int px=x+rx,py=y;for(unsigned j=1;j<=24;j++){unsigned a=j*(0x100000000ull/24u);int xx=x+osc_sine(a+0x40000000u)*rx/32768,yy=y+osc_sine(a)*ry/32768;cv_line_t(px,py,xx,yy,c,1);px=xx;py=yy;}}
/* Stable object family per engine. Variants differ in mechanism and host parameter mapping. */
static unsigned jazzy_object(unsigned e){
 switch(e){case ENGI_ANALOG:case ENGI_M2SAW:case ENGI_KW_ANALOG:return 5;
 case ENGI_PHASE:case ENGI_KW_PHASE:case ENGI_ACID:return 1;
 case ENGI_LOFI:case ENGI_JUNO:case ENGI_M2SID:return 6;
 case ENGI_WHEEL:case ENGI_KW_ADD:return 15;
 case ENGI_FM6:return 0;
 case ENGI_SERUM:case ENGI_KW_WAVE:return 9;
 case ENGI_M2STAT:case ENGI_KW_FM:return 14;
 case ENGI_MELO_TRIO:return 10;
 case ENGI_FMINI:return 13;
 case ENGI_CZ:return 9;
 case ENGI_PROPHET:return 3;
 case ENGI_S1:return 13;
 case ENGI_HYDRA:return 9;
 case ENGI_OBER:return 3;
 case ENGI_CS:case ENGI_KW_CS:return 11;
 case ENGI_KW_SYNC:return 12;
 case ENGI_KW_KICK:case ENGI_HORT:case ENGI_LXR:return 4;
 case ENGI_KW_GROWL:return 2;
 case ENGI_FRODHES:return 8;
 default:return 6;}
}
static void six_machine_glyph(const track_t *t,unsigned e,int en,unsigned ph,int x,int y,int w,int h,uint16_t ink){
 if(e==ENGI_EMPTY){cv_frame(x+w/2-3,y+h/2-3,6,6,T_DIM);return;}
 int dim=ink==T_DIM,small=w<48,sz=h<80?h:80;if(sz>w)sz=w;
 int p=t?clamp(t->p[P_E0],0,127):64,q=t?clamp(t->p[P_E1],0,127):64;
 if(ui_prefs&PREF_ANIM_OFF){en=0;ph=0;}if(dim)en=0;
 int osc=osc_sine(ph)*en/32768,bounce=en*(small?3:9)/127,ox=x+(w-sz)/2,oy=y+(h-sz)/2;
 uint16_t ivory=dim?T_DIM:JO_PAL[1],orange=dim?T_DIM:JO_PAL[4],blue=dim?T_DIM:JO_PAL[2];
 if(e==ENGI_BREAK){ /* Vinyl is procedural: circular grooves never shimmer during rotation. */
  int r=sz*3/7,cx=x+w/2-3,cy=y+h/2;
  jazzy_ring(cx,cy,r,r,ivory);for(int j=1;j<=3;j++)jazzy_ring(cx,cy,r-j*sz/12,r-j*sz/12,dim?T_DIM:ux.line);
  jazzy_ring(cx,cy,sz/9,sz/9,dim?T_DIM:JO_PAL[3]);
  int dx=osc_sine(ph)*(sz/9-1)/32768,dy=osc_sine(ph+0x40000000u)*(sz/9-1)/32768;cv_line_t(cx,cy,cx+dx,cy+dy,orange,2);
  /* Three asymmetric groove marks make direction/speed visible, including scratch/reverse. */
  for(unsigned j=0;j<3;j++){unsigned a=ph+j*0x50000000u;int rr=r-2-(int)j*sz/10;int xx=cx+osc_sine(a)*rr/32768,yy=cy+osc_sine(a+0x40000000u)*rr/32768;cv_rect(xx,yy,small?1:2,small?1:2,blue);}
  /* Fixed shoulder pivot, delayed stylus motion and a short cue lift on heavy accents. */
  int armx=cx+r+sz/8,army=cy-r,live=(ui_prefs&PREF_ANIM_OFF)?0:en;
  int track=t?(int)(jungle_current_step()&31u):0;
  int turn=0x08000000+track*0x00100000+osc_sine(ph-0x18000000u)*live*4;
  int len=sz*3/4,ex=armx-osc_sine((unsigned)turn)*len/32768,ey=army+osc_sine((unsigned)turn+0x40000000u)*len/32768;
  int lift=live>90?(live-90)*sz/800:0;ey-=lift;
  cv_line_t(armx,army,ex,ey,ivory,1);cv_line_t(ex,ey,ex-sz/10,ey+sz/14,ivory,1);
  jazzy_ring(armx,army,small?1:2,small?1:2,blue);cv_rect(ex-sz/10-1,ey+sz/14-1,small?2:4,small?2:3,orange);
  return;
 }
 unsigned obj=jazzy_object(e);
 for(unsigned pass=0;pass<2;pass++)for(unsigned row=0;row<64;row++){
  int yy=oy+(int)row*sz/64,hh=oy+(int)(row+1)*sz/64-yy;if(!hh)continue;
  unsigned xx=0;
  for(unsigned z=JO_ROW[obj][row];xx<64u;z++){
   unsigned run=JO_RUNS[z],n=(run>>3)+1,c=run&7u;int shift=0,dy=0;
   if(c && ((c==5)==(pass==0))){
    uint16_t col=dim?T_DIM:JO_PAL[c];if(c==5)col=T_BG;
    /* Split at eight-pixel intervals so a run cannot bridge separate joints. */
    for(unsigned part=xx;part<xx+n;){unsigned end=part+4;if(end>xx+n)end=xx+n;
     int ax,ay,bx,by;jazzy_pose(obj,(int)part,(int)row,small?en/2:en,ph,&ax,&ay);jazzy_pose(obj,(int)end,(int)row,small?en/2:en,ph,&bx,&by);
     int x0=ox+ax*sz/16384,y0=oy+ay*sz/16384,x1=ox+bx*sz/16384,y1=oy+by*sz/16384;
     if(y0==y1)cv_rect(x0,y0,x1-x0,hh+(en?1:0),col);else cv_line_t(x0,y0,x1,y1,col,hh+1);
     part=end;
    }
   }xx+=n;
  }
 }
 if(small)return;
 if(obj==5&&en){for(unsigned j=0;j<2;j++){int wx=ox+(j?47:18)*sz/64,wy=oy+38*sz/64,rr=sz/18;int dx=osc_sine(ph*2u)*rr/32768,dy=osc_sine(ph*2u+0x40000000u)*rr/32768;cv_line_t(wx-dx,wy-dy,wx+dx,wy+dy,ivory,1);}}
 if(obj==14&&en){for(unsigned j=0;j<3;j++){int xx=ox+(20+(int)j*11)*sz/64,yy=oy+(38-(int)((ph>>(24+j))&15u)*en/127)*sz/64;cv_rect(xx,yy,2,2,JO_PAL[3]);}}
 if(obj==0&&en){cv_line_t(ox+5,oy+sz/2,ox-1-en/32,oy+sz/2,orange,2);}
 if(obj==9&&en){int level=oy+(46-p/8)*sz/64;for(unsigned j=0;j<3;j++){int xx=ox+sz/3+j*sz/7,yy=level+(int)j%2+osc/50;cv_rect(xx,yy,2,2,ivory);}}
 if(obj==10){for(unsigned j=0;j<3;j++){int xx=ox+(18+(int)j*14)*sz/64,yy=oy+43*sz/64;cv_line_t(xx,oy+12*sz/64,xx+osc_sine(ph+j*0x55555555u)*en/600000,yy,orange,1);}}
}

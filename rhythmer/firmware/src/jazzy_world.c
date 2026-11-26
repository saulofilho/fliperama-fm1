/* SPDX-License-Identifier: GPL-3.0-only
 * JAZZY: A LITTLE WORLD OF SOUND. Original geometric scenes, UI thread only.
 * No raster frame bank, heap, particle simulation or audio callback work.
 * A figure has attached limbs; its stage shares the same bounded musical impulse.
 */
enum {JW_DOG,JW_CAT,JW_DRYER,JW_BOXER,JW_STRIKER,JW_LIFT,JW_COCKPIT,JW_MOOSE,
 JW_SEAL,JW_SKATER,JW_UMBRELLA,JW_COW,JW_FENCE,JW_PRESS,JW_LINE,JW_COASTER,
 JW_SNAIL,JW_CLOCKS,JW_BALL,JW_VACUUM,JW_FAN,JW_TAP,JW_VINYL,JW_LIFTER,JW_RIDER,JW_GIRAFFE,JW_RACER,JW_SPAR,JW_GUST,JW_WIPER,JW_SMILE};
static unsigned jazzy_object(unsigned e){
 static const uint8_t kind[NENGINES]={
  [ENGI_SERUM]=JW_DOG,[ENGI_PHASE]=JW_CAT,[ENGI_LOFI]=JW_DRYER,[ENGI_M2STAT]=JW_BOXER,
  [ENGI_M2SAW]=JW_RIDER,[ENGI_M2SID]=JW_LIFT,[ENGI_ANALOG]=JW_RACER,[ENGI_FM6]=JW_COCKPIT,
  [ENGI_WHEEL]=JW_MOOSE,[ENGI_MELO_TRIO]=JW_SEAL,[ENGI_FMINI]=JW_SKATER,
  [ENGI_OBER]=JW_UMBRELLA,[ENGI_JUNO]=JW_COW,[ENGI_CS]=JW_FENCE,[ENGI_KW_ANALOG]=JW_PRESS,
  [ENGI_KW_CS]=JW_LINE,[ENGI_KW_WAVE]=JW_COASTER,[ENGI_KW_FM]=JW_SPAR,
  [ENGI_KW_PHASE]=JW_SNAIL,[ENGI_KW_SYNC]=JW_CLOCKS,[ENGI_KW_KICK]=JW_STRIKER,[ENGI_LXR]=JW_BALL,
  [ENGI_KW_GROWL]=JW_VACUUM,[ENGI_KW_ADD]=JW_FAN,[ENGI_HORT]=JW_TAP,
  [ENGI_ACID]=JW_SMILE,[ENGI_BREAK]=JW_VINYL,[ENGI_CZ]=JW_GIRAFFE,
  [ENGI_PROPHET]=JW_GUST,[ENGI_S1]=JW_LIFTER,[ENGI_HYDRA]=JW_WIPER};
 return kind[e<NENGINES?e:0];
}
typedef struct {int x,y,w,h,m[8],en,hit,notes,span,pitch,small,step,still,glide,age;unsigned phase,e,ops;uint16_t palette[10];} jw_context_t;
static jw_context_t jw;
enum { JWI_INK, JWI_A, JWI_B, JWI_C, JWI_DIM, JWI_SHADE, JWI_BED, JWI_BG, JWI_GOLD, JWI_AMBER };
#define JW_OP_LIMIT 480u
/* Pack the two style arguments so each stroke passes one value. */
static void jw_stroke(int x,int y,int xx,int yy,unsigned style){
 if(jw.ops>=(jw.small?120u:JW_OP_LIMIT))return;jw.ops++;
 x=clamp(x,0,240);xx=clamp(xx,0,240);y=clamp(y,0,112);yy=clamp(yy,0,112);
 cv_line_t(jw.x+x*jw.w/240,jw.y+y*jw.h/112,jw.x+xx*jw.w/240,jw.y+yy*jw.h/112,jw.palette[style&15u],jw.small?1:style>>4);
}
#define jw_line(x,y,xx,yy,c,t) jw_stroke((x),(y),(xx),(yy),(c)|((t)<<4))
static void jw_rect(int x,int y,int w,int h,uint16_t c){
 if(jw.ops>=(jw.small?120u:JW_OP_LIMIT)||w<=0||h<=0)return;jw.ops++;
 int x1=clamp(x,0,240),y1=clamp(y,0,112),x2=clamp(x+w,0,240),y2=clamp(y+h,0,112);
 if(x2>x1&&y2>y1)cv_rect(jw.x+x1*jw.w/240,jw.y+y1*jw.h/112,(x2-x1)*jw.w/240+1,(y2-y1)*jw.h/112+1,jw.palette[c]);
}
/* Four-vertex cutouts give the LCD strong silhouettes. Filled regions are
 * small, clipped, and independent of the number of notes in the audio path. */
static void jw_quad(int ax,int ay,int bx,int by,int cx,int cy,int dx,int dy,uint16_t col){
 if(jw.small)return;
 const int x[]={ax,bx,cx,dx},y[]={ay,by,cy,dy};
 int low=112,high=0;
 for(int i=0;i<4;i++){if(y[i]<low)low=y[i];if(y[i]>high)high=y[i];}
 for(int yy=clamp(low,0,112);yy<clamp(high,0,112);yy++){
  int l=240,r=0;
  for(int i=0;i<4;i++){
   int j=(i+1)&3;
   if((y[i]<=yy&&yy<y[j])||(y[j]<=yy&&yy<y[i])){
    int xx=x[i]+(x[j]-x[i])*(yy-y[i])/(y[j]-y[i]);if(xx<l)l=xx;if(xx>r)r=xx;
   }
  }
  if(r>l)jw_rect(l,yy,r-l,1,col);
 }
}
static void jw_disc(int x,int y,int rx,int ry,uint16_t col){
 if(jw.small){jw_rect(x-rx*2/3,y-ry*2/3,rx*4/3,ry*4/3,col);return;}
 int span=rx;
 for(int yy=0;yy<=ry;yy++){
  while(span>0&&span*span*ry*ry+yy*yy*rx*rx>rx*rx*ry*ry)span--;
  jw_rect(x-span,y-yy,span*2+1,1,col);
  if(yy)jw_rect(x-span,y+yy,span*2+1,1,col);
 }
}
static void jw_box(int x,int y,int w,int h,uint16_t c){jw_line(x,y,x+w,y,c,1);jw_line(x+w,y,x+w,y+h,c,1);jw_line(x+w,y+h,x,y+h,c,1);jw_line(x,y+h,x,y,c,1);}
static void jw_arc(int x,int y,int rx,int ry,unsigned start,unsigned sweep,uint16_t c){
 int px=x+osc_sine(start)*rx/32768,py=y+osc_sine(start+0x40000000u)*ry/32768;
 unsigned count=jw.small?8u:20u;
 for(unsigned i=1;i<=count;i++){unsigned a=start+(sweep/count)*i;int xx=x+osc_sine(a)*rx/32768,yy=y+osc_sine(a+0x40000000u)*ry/32768;jw_line(px,py,xx,yy,c,1);px=xx;py=yy;}
}
static void jw_ring(int x,int y,int rx,int ry,uint16_t c){jw_arc(x,y,rx,ry,0,0xffffffffu,c);}
static void jw_joint(int ax,int ay,int kx,int ky,int bx,int by,uint16_t c){jw_line(ax,ay,kx,ky,c,2);jw_line(kx,ky,bx,by,c,2);}
static int jw_wave(unsigned off,int amount){return osc_sine(jw.phase+off)*amount/32768;}
static void jw_floor(int y){
 if(jw.small)return;jw_rect(12,y+1,216,9,JWI_BED);jw_line(12,y,228,y,JWI_DIM,1);
}
static void jw_burst(int x,int y,int r){
 if(jw.small||jw.hit<24)return;
 for(unsigned i=0;i<6;i++){unsigned a=i*0x2aaaaaaau;int dx=osc_sine(a)*r/32768,dy=osc_sine(a+0x40000000u)*r/32768;jw_line(x+dx,y+dy,x+dx*5/4,y+dy*5/4,i&1?JWI_A:JWI_B,1);}
}
/* An economical articulated person: pelvis and shoulders stay attached; feet
 * plant independently, knees lead the swing and wrists have their own targets. */
static void jw_person(int x,int floor,int lean,int stride,int reach,int pose){
 int hipx=x+lean,hipy=floor-24,shx=x+lean*2,shy=hipy-23;
 jw_disc(shx,shy-11,7,8,JWI_INK);jw_rect(shx,shy-13,7,3,JWI_BED);jw_quad(shx-5,shy+1,shx+6,shy+1,hipx+5,hipy,hipx-3,hipy,JWI_SHADE);jw_line(shx-5,shy+1,hipx-3,hipy,JWI_INK,2);jw_line(shx+6,shy+1,hipx+5,hipy,JWI_INK,2);jw_line(shx-5,shy+1,shx+6,shy+1,JWI_INK,2);jw_line(hipx-3,hipy,hipx+5,hipy,JWI_INK,2);
 jw_joint(hipx,hipy,x-10-stride/2,floor-14,x-12-stride,floor,JWI_INK);
 jw_joint(hipx,hipy,x+11+stride/2,floor-12,x+13+stride,floor,JWI_INK);
 jw_joint(shx,shy+3,shx+12,shy+13,shx+23+reach,shy+7-pose,JWI_A);
 jw_joint(shx,shy+3,shx-11,shy+14,shx-15,shy+23,JWI_INK);
 jw_line(x-16-stride,floor,x-7-stride,floor,JWI_INK,2);jw_line(x+9+stride,floor,x+20+stride,floor,JWI_INK,2);
}
static void jw_dog(void){
 int stretch=38+jw.m[2]*36/127+jw.en/8,head=158+stretch/3,hip=81-stretch/3,back=61-jw.m[0]/12,flex=jw_wave(0,3+jw.m[4]/24);
 jw_floor(99);jw_rect(hip+5,back+4,head-hip-7,14,JWI_SHADE);jw_rect(hip+18,back+7,head-hip-35,8,JWI_C);int px=hip,py=back;
 for(int i=1;i<=16;i++){int x=hip+(head-hip)*i/16,y=back+jw_wave((unsigned)i*0x10000000u,2+jw.m[2]/30);jw_line(px,py,x,y,JWI_INK,2);jw_line(px,py+19,x,y+19,JWI_INK,1);px=x;py=y;}
 jw_disc(head+2,back+1,10,10,JWI_SHADE);jw_arc(head+2,back+1,14,12,0x40000000u,0xbfffffffu,JWI_INK);jw_line(head+14,back,head+24,back+5,JWI_INK,2);jw_line(head+24,back+5,head+11,back+11,JWI_INK,1);
 jw_joint(head-1,back-2,head-3,back+10,head+4,back+15,JWI_A);jw_rect(head+10,back-4,2,2,JWI_B);
 for(int k=0;k<4;k++){int x=k<2?hip+8:head-15,sg=k&1?1:-1,swing=(k&1?flex:-flex);jw_joint(x,back+18,x+sg*5,89,x+sg*10+swing,98,JWI_INK);}
 jw_joint(hip,back+4,hip-13,back-6,hip-20+flex,back-14,JWI_B);
 if(!jw.small)for(int i=0;i<jw.notes+1;i++){int x=28+i*51;jw_line(x,103,x+16,103,JWI_A,1);jw_line(x+16,103,x+12,100,JWI_A,1);}

}
static void jw_boxer(void){
 int hit=jw.hit,extend=hit*(18+jw.m[0]/7)/127,x=79+extend/5,y=47+hit/25,bag=164+extend/3;
 jw_floor(101);jw_line(23,28,23,99,JWI_DIM,2);jw_line(215,28,215,99,JWI_DIM,2);
 for(int k=0;k<3;k++){int yy=67+k*10;jw_line(23,yy,120,yy+hit/28,JWI_DIM,1);jw_line(120,yy+hit/28,215,yy,JWI_DIM,1);}
 jw_disc(x+3,y-15,8,9,JWI_INK);jw_rect(x+6,y-18,4,4,JWI_BED);jw_quad(x-5,y+1,x+10,y+2,x+5,75,x-11,75,JWI_SHADE);
 jw_line(x-5,y+1,x+10,y+2,JWI_INK,3);jw_line(x-5,y+1,x-11,76,JWI_INK,2);jw_line(x+10,y+2,x+5,76,JWI_INK,2);jw_rect(x-12,73,18,6,JWI_A);
 jw_joint(x-6,78,x-17,86,x-24,99,JWI_INK);jw_joint(x+3,78,x+18,87,x+26,98,JWI_INK);
 jw_rect(x-26,97,11,3,JWI_INK);jw_rect(x+22,96,10,3,JWI_INK);
 int glove=x+34+extend,gy=y+4-extend/6;
 jw_joint(x+7,y+5,x+20,y+16-extend/5,glove,gy,JWI_INK);jw_joint(x-4,y+6,x-12,y+21,x+1,y+19,JWI_INK);
 jw_disc(glove+3,gy,7,6,JWI_B);jw_disc(x+4,y+18,6,5,JWI_B);jw_rect(glove-5,gy+1,5,4,JWI_INK);
 jw_line(159,10,bag,31,JWI_INK,1);jw_rect(bag-10,32,20,40,JWI_SHADE);jw_box(bag-10,31,20,42,JWI_INK);jw_rect(bag+4,46,3,24,JWI_C);jw_rect(bag-9,41,19,4,JWI_A);
 jw_burst(bag-13,gy,15+jw.span/2);
}
static void jw_cow(void){
 int breath=jw_wave(0,2),dip=jw.hit/32,wide=20+jw.m[3]/10,x=118;
 if(!jw.small){
  jw_line(12,71,62,71,JWI_DIM,1);jw_line(183,71,228,71,JWI_DIM,1);
  for(int k=0;k<4;k++){
   int px=k<2?20+k*32:186+(k-2)*34;
   jw_rect(px,62,2,19,JWI_DIM);
  }
  jw_line(15,103,227,103,JWI_BED,2);
  for(int k=0;k<5;k++){
   int px=26+k*45,bend=jw_wave(k*0x28000000u,2+jw.hit/21),height=6+(k<jw.notes?jw.span/4:0);
   jw_line(px,103,px+bend,103-height,JWI_C,1);
   jw_line(px,103,px-4+bend,99,JWI_DIM,1);
  }
 }
 jw_rect(x-wide-24,46+breath,wide*2+31,29,JWI_INK);jw_rect(x-wide-20,52+breath,wide*2+23,18,JWI_SHADE);
 for(int k=0;k<4;k++){int lx=x-wide-18+k*(wide*2+20)/3,step=jw_wave(k*0x80000000u,3+jw.en/32);jw_joint(lx,75+breath,lx+step,88,lx+step/2,100,JWI_INK);}
 int hx=x+wide+15,hy=51+dip;jw_rect(hx,hy,25,27,JWI_INK);jw_rect(hx+1,hy+2,23,16,JWI_BED);jw_line(hx+2,hy,hx-3,hy-10,JWI_C,1);jw_line(hx+20,hy,hx+25,hy-10,JWI_C,1);jw_rect(hx+4,hy+7,2,2,JWI_B);jw_rect(hx+17,hy+7,2,2,JWI_B);jw_line(hx+2,hy+20,hx+23,hy+20,JWI_A,2);
 jw_rect(x-22,51+breath,12,10,JWI_A);jw_rect(x+7,58+breath,14,10,JWI_C);jw_joint(x-wide-24,49+breath,x-wide-40,47,x-wide-41+jw_wave(0x20000000u,5),63,JWI_INK);
 jw_rect(hx,hy+18,4,6+dip,JWI_A);
}
static void jw_skater(void){
 int lift=jw.hit*(7+jw.m[0]/8)/127,crouch=jw_wave(0,4),x=119;
 int tilt=jw_wave(0x20000000u,2+jw.hit/13),by=94-lift;
 int hipx=x+6,hipy=by-24+crouch,shx=x+13+jw.hit/19,shy=hipy-19-crouch/2;
 if(!jw.small){
  /* The rail moves more slowly than the pavement under the board. */
  int far=(jw.phase>>26)&31u,near=(jw.phase>>23)&255u;
  jw_line(8,72,232,72,JWI_DIM,1);
  for(int k=1;k<8;k++){
   int px=k*32-far;
   jw_line(px,72,px-3,84,JWI_DIM,1);
  }
  jw_line(8,103,232,103,JWI_BED,2);
  for(int k=0;k<4;k++){
   int px=((k*64+256-near)&255)-12;
   jw_line(px,108,px+18+jw.hit/8,108,JWI_C,1);
  }
  int curb=252-(int)(jw.phase>>23);
  jw_line(curb-18,100,curb,95,JWI_A,1);
  jw_line(curb,95,curb+24,95,JWI_DIM,1);
  if(jw.hit>26)jw_line(36,by-13,78+jw.hit/6,by-13,JWI_A,1);
 }
 jw_disc(shx+2,shy-10,7,8,JWI_INK);jw_rect(shx-7,shy-15,20,3,JWI_A);jw_quad(shx-6,shy,shx+6,shy,hipx+5,hipy,hipx-5,hipy,JWI_SHADE);
 jw_line(shx-5,shy,hipx-5,hipy,JWI_INK,3);jw_line(shx+5,shy,hipx+4,hipy,JWI_INK,2);jw_rect(hipx-5,hipy-2,12,5,JWI_INK);
 jw_joint(hipx-3,hipy,x-16,by-16,x-17,by-tilt/2,JWI_INK);
 jw_joint(hipx+4,hipy,x+21,by-13,x+15,by+tilt/2,JWI_INK);
 jw_joint(shx-4,shy,x-12,shy+4,x-29,shy-9+jw.hit/11,JWI_A);
 jw_joint(shx+5,shy,x+29,shy+9,x+43,shy-7-jw.hit/11,JWI_INK);
 jw_line(x-32,by-tilt,x+30,by+tilt,JWI_A,2);jw_line(x-37,by-tilt-4,x-32,by-tilt,JWI_A,2);jw_line(x+30,by+tilt,x+35,by+tilt-4,JWI_A,2);
 jw_ring(x-20,by+6-tilt,3,3,JWI_C);jw_ring(x+20,by+6+tilt,3,3,JWI_C);
}
static void jw_rider(void){
 int airtime=jw.age<280?osc_sine((unsigned)jw.age*0x00750750u)/256:0;
 if(airtime<0)airtime=0;
 int lift=airtime*(5+jw.m[2]/6)/127, pitch=jw.m[0]*airtime/680;
 int roll=jw.glide?jw_wave(0,13):jw_wave(0,3),front=169+roll,back=78+roll,by=88-lift;
 int landing=jw.age>=246&&jw.age<340?(340-jw.age)*(22+jw.m[4]/2)/94:0;
 jw_floor(105);jw_ring(back,by,15,15,JWI_INK);jw_ring(front,by-pitch,15,15,JWI_INK);
 jw_ring(back,by,12,12,JWI_DIM);jw_ring(front,by-pitch,12,12,JWI_DIM);
 jw_disc(back,by,3,3,JWI_A);jw_disc(front,by-pitch,3,3,JWI_A);
 jw_quad(back+5,by-6,106+roll,by-26,145+roll,by-26-pitch,116+roll,by-3,JWI_SHADE);
 if(!jw.small){for(int k=1;k<=3;k++)jw_line(22,by-7-k*6,48+jw.m[2]/4-k*4,by-7-k*6,k==1?JWI_C:JWI_DIM,1);}
 int crankx=116+roll,cranky=by-2,barx=154+roll,bary=by-32-pitch;
 jw_line(back,by,106+roll,by-26,JWI_A,2);jw_line(106+roll,by-26,crankx,cranky,JWI_A,2);jw_line(crankx,cranky,back,by,JWI_A,2);jw_line(106+roll,by-26,145+roll,by-26-pitch,JWI_A,2);jw_line(145+roll,by-26-pitch,crankx,cranky,JWI_A,2);jw_line(barx,bary,front,by-pitch,JWI_A,2);jw_line(145+roll,by-26-pitch,barx,bary,JWI_A,2);
 jw_rect(102+roll,by-32,23,4,JWI_B);jw_line(barx-3,bary,barx+9,bary-4,JWI_INK,2);
 int hx=123+roll+jw.m[1]/22+pitch/3,hy=by-53+landing/14,hipx=114+roll,hipy=by-31,shx=hx-4,shy=hy+13;
 jw_disc(hx,hy,9,9,JWI_INK);jw_rect(hx+1,hy-3,10,4,JWI_B);jw_quad(shx-6,shy,shx+5,shy-2,hipx+6,hipy,hipx-6,hipy,JWI_SHADE);jw_line(shx,shy,hipx,hipy,JWI_INK,2);jw_joint(shx,shy,142+roll,by-42,barx,bary,JWI_INK);jw_joint(hipx,hipy,131+roll,by-18,crankx+4,cranky-1,JWI_INK);
 jw_line(back,by,back+jw_wave(0,12),by+jw_wave(0x40000000u,12),JWI_C,1);jw_line(front,by-pitch,front+jw_wave(0,12),by-pitch+jw_wave(0x40000000u,12),JWI_C,1);
 if(!jw.small){for(int k=0;k<9;k++){int xx=16+k*25,yy=101-((k+jw.step)&3)*2;jw_line(xx,yy,xx+12,yy,JWI_DIM,1);}jw_line(18,100,45,91,JWI_C,1);jw_line(45,91,55,101,JWI_C,1);if(jw.glide){jw_line(back-55,87,back-17,by+4,JWI_C,1);jw_line(back-45,92,back-20,by+9,JWI_A,1);}if(landing>12){for(int i=0;i<4;i++)jw_line(back-10-i*9,103,back-18-i*10,102-landing/8-i,JWI_B,1);}}
}
static void jw_umbrella(void){
 int wind=jw_wave(0,5+jw.m[6]/8),lean=wind/4,roof=48-jw.m[0]/6,spread=26+jw.m[1]/3;
 jw_floor(105);jw_person(117,102,lean,wind/4,-7,20);
 int cx=121+lean*2,cy=roof;jw_line(cx,cy,cx-6,80,JWI_INK,1);jw_arc(cx-10,79,4,5,0xc0000000u,0x7fffffffu,JWI_INK);
 jw_arc(cx,cy,spread,18+spread/5,0x40000000u,0x7fffffffu,JWI_A);
 for(int i=-2;i<=2;i++){int x=cx+i*spread/2;jw_line(cx,cy-18-spread/5,x,cy,JWI_A,1);jw_line(x,cy,x+spread/2,cy+(i&1?3:0),JWI_INK,1);}
 if(jw.hit>85&&jw.m[6]>90)jw_arc(cx,cy,spread,8,0xc0000000u,0x7fffffffu,JWI_B);
 if(!jw.small)for(int i=0;i<12;i++){int x=15+(i*43+(jw.phase>>25))%214,y=8+(i*17)%84;jw_line(x,y,x-5-wind/2,y+9,JWI_DIM,1);}
 if(jw.e==ENGI_OBER){jw_arc(cx+45,cy+8,15+jw.m[3]/9,14,0x40000000u,0x7fffffffu,JWI_C);jw_line(cx+45,cy+8,cx+39,88,JWI_C,1);}
}
static void jw_dryer(void){
 int tilt=jw_wave(0,3),flow=10+jw.m[4]/6+jw.en/10;
 jw_rect(40,42+tilt,51,24,JWI_SHADE);jw_box(40,42+tilt,51,24,JWI_INK);jw_rect(42,44+tilt,40,6,JWI_A);jw_line(91,46+tilt,106,50+tilt,JWI_A,2);jw_line(106,50+tilt,106,58+tilt,JWI_A,2);jw_line(106,58+tilt,91,62+tilt,JWI_A,2);
 jw_line(54,66+tilt,59,92,JWI_INK,2);jw_line(59,92,70,92,JWI_INK,2);jw_line(70,92,67,66+tilt,JWI_INK,2);jw_line(61,92,58,105,JWI_DIM,1);jw_ring(49,54+tilt,4,7,JWI_A);
 int px=145,py=32;
 for(int i=0;i<12;i++){int x=145+i*5,y=32+jw_wave((unsigned)i*0x12000000u,flow);if(i)jw_line(px,py,x,y,JWI_INK,2);jw_line(x,y,x,y+37,JWI_INK,1);if(i&1)jw_rect(x,y+10,3,5,JWI_A);px=x;py=y;}
 if(!jw.small){for(int k=0;k<4;k++){int px=110,py=42+k*9;for(int i=1;i<9;i++){int x=110+i*10,y=42+k*9+jw_wave(i*0x10000000u+k*0x20000000u,3+flow/5);jw_line(px,py,x,y,k&1?JWI_DIM:JWI_B,1);px=x;py=y;}}jw_line(143,19,215,19,JWI_DIM,1);}
}
static void jw_cockpit(void){
 int lean=jw_wave(0,3+jw.en/30);
 jw_line(26,14,214,14,JWI_DIM,1);jw_line(26,14,12,70,JWI_DIM,1);jw_line(214,14,228,70,JWI_DIM,1);jw_line(12,70,228,70,JWI_INK,2);
 if(!jw.small)for(int i=0;i<8;i++){int x=33+(i*47+(jw.phase>>25))%170,y=20+(i*13)%36;jw_rect(x,y,1,1,JWI_DIM);}
 jw_ring(122,41,21+jw.m[2]/6,10+jw.m[3]/9,JWI_A);
 jw_line(122,41,122+lean*8,25,JWI_C,1);
 for(int i=0;i<6;i++){
  int x=43+i*30;
  unsigned a=jw.phase*(i+1u)+(unsigned)jw.m[i]*0x1000000u;
  jw_ring(x,89,10,10,JWI_INK);
  jw_line(x,89,x+osc_sine(a)*7/32768,89+osc_sine(a+0x40000000u)*7/32768,i&1?JWI_B:JWI_A,1);
 }
 if(!jw.small){jw_line(23,109,217,109,JWI_DIM,1);jw_rect(112,102,18+jw.hit/10,3,JWI_C);}
}
static void jw_lifter(void){
 int lift=jw.hit*(13+jw.m[3]/5)/127,bend=jw.m[3]/9+jw.en/18,y=clamp(43-lift,21,43);
 jw_floor(106);jw_person(120,103,-2,4,0,20);
 jw_joint(116,56,98,45-lift/2,82,y,JWI_INK);jw_joint(116,56,140,44-lift/2,158,y,JWI_INK);
 jw_line(57,y,88,y,JWI_A,2);jw_line(88,y,120,y+bend,JWI_A,2);jw_line(120,y+bend,153,y,JWI_A,2);jw_line(153,y,184,y,JWI_A,2);
 for(int k=0;k<3;k++){jw_rect(59+k*6,y-12-k*2,4,25+k*4,JWI_B);jw_rect(164+k*6,y-16+k*2,4,33-k*4,JWI_B);}
 if(!jw.small){jw_burst(120,y+bend,14);for(int k=0;k<3;k++)jw_line(104+k*17,14,104+k*17,18+jw.m[0]/20,JWI_DIM,1);}
}
static void jw_lift(void){
 int y=70-jw.pitch/3+jw_wave(0,3),door=8+jw.m[2]/4;
 jw_box(78,7,84,99,JWI_DIM);jw_rect(84,y-29,72,38,JWI_SHADE);jw_box(84,y-29,72,38,JWI_INK);jw_rect(88,y-25,27,29,JWI_BED);jw_rect(125,y-25,27,29,JWI_BED);jw_line(120,y-29,120,y+9,JWI_A,1);
 jw_line(120-door,y-26,120-door,y+6,JWI_B,2);jw_line(120+door,y-26,120+door,y+6,JWI_B,2);
 jw_ring(105,y-17,4,5,JWI_C);jw_line(105,y-12,105,y+1,JWI_C,1);jw_line(100,y+5,105,y+1,JWI_C,1);jw_line(105,y+1,110,y+5,JWI_C,1);
 if(!jw.small)for(int k=0;k<7;k++){int yy=15+k*13;jw_line(45,yy,66,yy,JWI_DIM,1);jw_rect(173,yy,7,k==jw.step%7?3:1,k==jw.step%7?JWI_B:JWI_DIM);}
}
static void jw_moose(void){
 int nod=jw_wave(0,3)+jw.hit/35,spread=29+jw.m[2]/4;
 jw_floor(107);jw_rect(94,65,50,23,JWI_SHADE);jw_box(94,65,50,23,JWI_INK);jw_rect(96,66,34,6,JWI_C);jw_line(99,88,98,106,JWI_INK,2);jw_line(137,88,141,106,JWI_INK,2);jw_line(126,65,139,48+nod,JWI_INK,2);jw_box(130,39+nod,29,15,JWI_INK);jw_rect(152,44+nod,2,2,JWI_B);
 for(int side=-1;side<=1;side+=2){int x=140,y=40+nod;jw_joint(x,y,x+side*spread/2,y-15,x+side*spread,y-21,JWI_A);for(int k=1;k<=3;k++){int xx=x+side*(spread/4+k*spread/5),yy=y-12-k*3;jw_line(xx,yy,xx+side*3,yy-10-jw.m[k]/13,JWI_C,1);}}
 if(!jw.small)for(int k=0;k<jw.notes;k++){int x=82+k*29;jw_line(x,8,x+9,12,JWI_DIM,1);jw_line(x+9,12,x+13,7,JWI_DIM,1);}
}
static void jw_seal(void){
 int lean=jw_wave(0,5),top=42-jw.m[4]/8;
 jw_floor(105);jw_disc(113,84,25,17,JWI_SHADE);jw_arc(113,84,28,19,0x40000000u,0xbfffffffu,JWI_INK);jw_joint(97,72,111+lean,54,123+lean,top+11,JWI_INK);jw_disc(126+lean,top+8,12,10,JWI_INK);jw_line(136+lean,top+8,146+lean,top+6,JWI_B,1);jw_rect(131+lean,top+4,2,2,JWI_C);jw_line(101,91,75,102,JWI_A,2);jw_line(126,93,149,101,JWI_A,2);
 for(int k=0;k<3;k++){int x=146+lean+jw_wave(k*0x55555555u,9+k*7),y=top-7-k*14;jw_ring(x,y,7-k,7-k, k&1?JWI_C:JWI_A);}
 if(!jw.small)jw_arc(129,102,31+jw.hit/6,5,0x40000000u,0x7fffffffu,JWI_DIM);
}
static void jw_fencer(int x,int dir,int lunge,int parry,uint16_t color){
 int hip=x+dir*lunge/3,hy=75+lunge/8;
 int shoulder=hip+dir*(4+lunge/4),sy=hy-24;
 int hand=shoulder+dir*(15+lunge/2),wy=sy+12-parry;
 int front=x+dir*(16+lunge),rear=x-dir*16;
 jw_disc(shoulder,sy-11,8,9,JWI_INK);
 jw_rect(shoulder+dir*4-3,sy-15,6,7,JWI_SHADE);
 jw_line(shoulder,sy,hip,hy,JWI_INK,9);
 jw_line(shoulder-4,sy+5,shoulder+4,sy+5,color,2);
 jw_joint(hip,hy,front-dir*6,85,front,98,JWI_INK);
 jw_joint(hip,hy,x-dir*10,87,rear,98,JWI_INK);
 jw_line(front,98,front+dir*7,98,color,2);
 jw_line(rear,98,rear-dir*5,98,JWI_INK,2);
 jw_joint(shoulder,sy+4,shoulder-dir*12,sy+13,shoulder-dir*17,sy+3,JWI_INK);
 jw_joint(shoulder,sy+4,shoulder+dir*(8+lunge/4),wy+7-lunge/4,hand,wy,JWI_INK);
 jw_line(hand,wy-3,hand,wy+3,color,2);
 jw_line(hand,wy,hand+dir*36,wy-6-parry,color,1);
}
static void jw_fence(void){
 int attack=jw.hit*(24+jw.m[3]/12)/127;
 int guard=(jw.span+jw.hit/6)/4;
 /* Each eighth note trades the lead. Live playing uses note pitch. */
 int right=(jw.step/2+jw.pitch)&1;
 int retreat=attack/4;
 if(!jw.small){
  jw_rect(18,99,204,8,JWI_BED);
  jw_line(18,99,222,99,JWI_DIM,1);
  for(int x=48;x<=192;x+=36)jw_line(x,99,x,106,JWI_DIM,1);
  jw_rect(90,103,18,2,!right&&attack>10?JWI_A:JWI_DIM);
  jw_rect(132,103,18,2,right&&attack>10?JWI_B:JWI_DIM);
 }
 jw_fencer(61-(right?retreat:0),1,right?0:attack,right?guard:0,JWI_A);
 jw_fencer(179+(right?0:retreat),-1,right?attack:0,right?0:guard,JWI_B);
}
static void jw_press(void){
 int squash=jw.hit*(8+jw.m[5]/5)/127,folds=3+jw.m[5]/24,top=40+squash;
 jw_line(62,12,62,102,JWI_INK,2);jw_line(178,12,178,102,JWI_INK,2);jw_line(62,12,178,12,JWI_INK,2);jw_rect(112,13,16,top-20,JWI_A);jw_box(77,top-4,86,8,JWI_INK);jw_box(73,95,94,8,JWI_INK);
 int px=82,py=top+13;for(int k=1;k<=folds*2;k++){int x=82+76*k/(folds*2),y=(k&1)?92:top+13;jw_line(px,py,x,y,k&1?JWI_B:JWI_C,2);px=x;py=y;}
 if(!jw.small){jw_ring(192,33,10,10,JWI_DIM);jw_line(192,33,192+jw.hit/14,26,JWI_B,1);jw_burst(120,90,15);}
}
static void jw_lineworld(void){
 int wave=jw_wave(0,5+jw.m[4]/6),height=33;
 jw_line(25,14,25,107,JWI_DIM,2);jw_line(215,14,215,107,JWI_DIM,2);
 int px=25,py=height;for(int i=1;i<=16;i++){int x=25+i*12,y=height+(i*(16-i))/12+jw_wave(i*0x06000000u,2);jw_line(px,py,x,y,JWI_INK,1);px=x;py=y;}
 for(int k=0;k<2;k++){int x=81+k*65,y=43+k*3,shift=k?-wave:wave;jw_line(x,y,x+shift,y+29,JWI_A,2);jw_line(x+shift,y+29,x+shift+18,y+33,JWI_A,2);jw_line(x+shift+18,y+33,x+shift+17,y+42,JWI_A,2);jw_line(x+shift+17,y+42,x+shift-8,y+40,JWI_A,2);jw_line(x+shift-8,y+40,x-8,y,JWI_A,2);jw_rect(x-4,y-3,4,6,JWI_B);}
 if(!jw.small)for(int i=0;i<4;i++){int x=37+i*48;jw_line(x,93+jw_wave(i*0x30000000u,3),x+18,91+jw_wave(i*0x30000000u,3),JWI_DIM,1);}
}
static int jw_rail(int x){return 65+osc_sine((unsigned)(x-10)*(0x00800000u+jw.m[2]*73728u)+jw.phase/4)*(10+jw.m[4]/5)/32768;}
static void jw_coaster(void){
 int px=15,py=jw_rail(15);
 for(int i=1;i<=24;i++){int x=15+i*9,y=jw_rail(x);jw_line(px,py,x,y,JWI_A,2);if((i&3)==0&&!jw.small)jw_line(x,y+3,x,106,JWI_DIM,1);px=x;py=y;}
 int x=120+jw_wave(0,72),y=jw_rail(x)-13,yl=jw_rail(x-9)-2,yr=jw_rail(x+9)-2;
 jw_line(x-11,yl-10,x+11,yr-10,JWI_INK,2);jw_line(x-11,yl-4,x+11,yr-4,JWI_INK,2);
 jw_line(x-11,yl-10,x-11,yl-4,JWI_INK,1);jw_line(x+11,yr-10,x+11,yr-4,JWI_INK,1);
 jw_ring(x-7,yl,3,3,JWI_C);jw_ring(x+7,yr,3,3,JWI_C);jw_ring(x-1,y-6,4,5,JWI_INK);jw_line(x-3,y-3,x-9,y-14,JWI_B,1);jw_line(x+1,y-3,x+8,y-17,JWI_B,1);
 if(jw.notes>1){int ax=x-23,ay=jw_rail(ax);jw_line(ax-8,ay-8,ax+7,ay-8,JWI_C,3);jw_line(ax-5,ay-5,ax+4,ay-5,JWI_INK,1);}
 if(!jw.small){jw_line(13,107,229,107,JWI_DIM,1);if(jw.m[4]>95)jw_arc(184,46,23,31,0x80000000u,0xcfffffffu,JWI_DIM);}
}
static void jw_snail(void){
 int ripple=jw_wave(0,4),r=23+jw.m[2]/10,cx=115,cy=66;
 jw_floor(102);jw_line(64,96,177,96,JWI_INK,2);jw_line(64,96,80,89,JWI_INK,2);jw_line(80,89,146,89,JWI_INK,2);jw_line(146,89,162,75+ripple,JWI_INK,2);jw_line(162,75+ripple,177,96,JWI_INK,2);
 jw_ring(cx,cy,r,r,JWI_A);int px=cx,py=cy;for(unsigned i=1;i<=32;i++){unsigned a=jw.phase+i*0x13000000u;int rr=(int)i*r/32,x=cx+osc_sine(a)*rr/32768,y=cy+osc_sine(a+0x40000000u)*rr/32768;jw_line(px,py,x,y,JWI_A,1);px=x;py=y;}
 jw_line(162,77+ripple,160,62+ripple,JWI_INK,1);jw_line(169,83+ripple,177,69+ripple,JWI_INK,1);jw_rect(158,59+ripple,3,3,JWI_B);jw_rect(176,66+ripple,3,3,JWI_B);
 if(!jw.small)for(int k=0;k<7;k++)jw_line(27+k*27,105,39+k*27,105,JWI_DIM,1);
}
static void jw_clocks(void){
 /* Both hands start at noon on the same note, then the slave runs ahead. */
 for(int i=0;i<2;i++){
  int x=72+i*96;
  unsigned a=(unsigned)(jw.still?0:jw.age)*(0x00900000u+i*jw.m[2]*0x20000u);
  jw_ring(x,58,30,35,JWI_INK);
  jw_rect(x-2,26,4,4,JWI_DIM);
  jw_line(x,58,x+osc_sine(a)*23/32768,58-osc_sine(a+0x40000000u)*25/32768,i?JWI_B:JWI_A,3);
 }
 jw_line(72,98,168,98,jw.hit>84?JWI_B:JWI_DIM,2);
}
static void jw_striker(void){
 /* A carnival hammer drives a puck up the strength scale. */
 int rise=jw.hit*(38+jw.m[2]/4)/127;
 jw_floor(104);
 jw_box(148,14,26,88,JWI_INK);
 for(int y=22;y<90;y+=10)jw_line(166,y,173,y,JWI_DIM,1);
 jw_rect(153,90-rise,10,5,JWI_A);
 int head=62+jw.hit/4;
 jw_line(65,91,131,head,JWI_INK,3);
 jw_rect(122,head-7,20,10,JWI_B);
}
static void jw_ball(void){
 int swing=jw.hit*(27+jw.m[2]/7)/127,ballx=132+swing,bally=69-swing/3;
 jw_floor(106);jw_line(56,100,56,13,JWI_INK,2);jw_line(56,13,128,13,JWI_INK,2);jw_line(128,13,ballx,bally-15,JWI_A,1);jw_disc(ballx,bally,15,15,JWI_B);jw_arc(ballx,bally,9,9,0x40000000u,0x30000000u,JWI_INK);jw_line(56,40,83,13,JWI_DIM,1);
 for(int k=0;k<6;k++){int j=k%2,row=k/2,x=184+j*16+(jw.hit>80?(k-2)*jw.hit/40:0),y=65+row*13-(jw.hit>80?(k&1)*jw.hit/17:0);jw_box(x,y,14,11,JWI_INK);}
 jw_burst(180,79,14+jw.hit/8);
}
static void jw_vacuum(void){
 int pull=jw.hit/9+jw.m[2]/10,tip=151+pull;
 jw_floor(106);jw_rect(57,67,42,27,JWI_SHADE);jw_box(57,67,42,27,JWI_INK);jw_rect(59,70,34,7,JWI_C);jw_ring(68,96,7,7,JWI_A);jw_ring(90,96,7,7,JWI_A);jw_arc(110,61,32,31,0x80000000u,0xafffffffu,JWI_INK);jw_line(139,61,tip,95,JWI_INK,2);jw_box(tip-11,95,29,6,JWI_B);
 for(int k=0;k<3;k++){int y=32+k*9;jw_line(60,y,60+jw.m[k]/5+15,y,JWI_A,2);}
 if(!jw.small)for(int k=0;k<5;k++){int x=147+k*14,y=104-(k==1?pull:0);jw_line(x,y,x+10,y-(k==1?pull/2:0),JWI_C,1);}
}
static void jw_fan(void){
 int spread=25+jw.m[2]/3,cx=120,cy=79;
 jw_floor(106);
 for(int k=0;k<9;k++){int angle=-72+k*18,xx=cx+angle*spread/90,yy=cy-20-(72-(angle<0?-angle:angle))*spread/90+jw_wave(k*0x10000000u,2);jw_line(cx,cy,xx,yy,k&1?JWI_A:JWI_C,1);jw_ring(xx,yy,5,8,JWI_INK);}
 jw_arc(cx,cy+7,10,17,0x40000000u,0xbfffffffu,JWI_INK);jw_joint(cx+4,cy-2,cx+11,cy-12,cx+12,cy-26,JWI_INK);jw_ring(cx+13,cy-31,6,6,JWI_INK);jw_line(cx+18,cy-31,cx+25,cy-29,JWI_B,1);jw_line(cx-3,98,cx-6,105,JWI_INK,1);jw_line(cx+4,98,cx+9,105,JWI_INK,1);
}
static void jw_tap(void){
 int tap=jw_wave(0,7+jw.hit*(16+jw.m[2]/5)/360),x=118;
 jw_floor(108);jw_person(x,96,-1,tap,0,15);
 jw_box(57,99,127,8,JWI_DIM);jw_rect(94-tap,98,14,4,JWI_A);jw_rect(124+tap,98-(jw.hit>70?5:0),16,4,JWI_B);
 if(!jw.small){for(int k=0;k<5;k++)jw_line(63+k*24,100,63+k*24,106,JWI_DIM,1);jw_burst(x+(tap>0?18:-18),97,12);}
}
static void jw_cat(void){
 int pull=jw.hit*(6+jw.m[2]/5)/127,head=117+pull/4,hip=82,tail=jw_wave(0,9),bow=jw.m[2]/8+pull/2;
 jw_floor(103);
 /* One taut string, with the same endpoint that the paw is holding. */
 for(int k=0;k<5;k++){int y=38+k*10,d=(k==2?bow:bow/4);jw_line(145,y,170-d,y+3,JWI_DIM,1);jw_line(170-d,y+3,216,y,JWI_DIM,1);}
 jw_line(216,30,216,96,JWI_INK,2);jw_line(152,58,172-bow,61,JWI_A,1);jw_line(172-bow,61,216,58,JWI_A,1);
 jw_disc(hip+12,78,25,13,JWI_SHADE);jw_arc(hip+12,78,27,15,0x40000000u,0xcfffffffu,JWI_INK);
 jw_joint(hip-8,76,58,60,51+tail,37,JWI_INK);
 jw_line(head-12,60,head-10,44,JWI_INK,2);jw_line(head-10,44,head-3,51,JWI_INK,1);
 jw_line(head-3,51,head+8,51,JWI_INK,1);jw_line(head+8,51,head+14,43,JWI_INK,1);jw_line(head+14,43,head+15,65,JWI_INK,2);
 jw_line(head+15,65,head+5,73,JWI_INK,2);jw_line(head+5,73,head-10,69,JWI_INK,2);
 jw_rect(head+5,58,3,2,JWI_B);jw_line(head+11,65,head+21,63,JWI_C,1);
 jw_joint(hip-1,83,hip-10,91,hip-4,102,JWI_INK);
 jw_joint(head,73,head+16,80-pull/3,172-bow,61,JWI_INK);
 jw_joint(head-5,76,head+3,89,head+13,101,JWI_INK);
 if(jw.notes>1)for(int i=1;i<jw.notes;i++)jw_line(148,58-i*4,206,58-i*4+jw.span/4,JWI_C,1);
}
static void jw_vinyl(void){
 int cx=94,cy=55,step=jw.step&31,cue=jw.hit>85?(jw.hit-85)/9:0;
 jw_box(29,6,182,100,JWI_DIM);jw_rect(29,103,182,4,JWI_DIM);
 jw_disc(cx,cy,42,42,JWI_BED);jw_ring(cx,cy,42,42,JWI_INK);jw_ring(cx,cy,35,35,JWI_DIM);jw_ring(cx,cy,28,28,JWI_DIM);jw_disc(cx,cy,13,13,JWI_SHADE);jw_ring(cx,cy,14,14,JWI_A);
 jw_rect(cx-1,cy-1,3,3,JWI_INK);
 for(unsigned k=0;k<6;k++){unsigned a=jw.phase+k*0x2aaaaaaau;int r=18+k*4;
  int dx=osc_sine(a),dy=osc_sine(a+0x40000000u);jw_line(cx+dx*r/32768,cy+dy*r/32768,cx+dx*(r+4)/32768,cy+dy*(r+4)/32768,k==0?JWI_B:JWI_A,1);}
 /* The bearing does not move. Both links share an angle; cueing raises the head. */
 int px=178,py=26;unsigned a=0x29000000u+step*0x00300000u;
 int dx=osc_sine(a),dy=osc_sine(a+0x40000000u);
 int elbow=px-dx*49/32768,ey=py+dy*49/32768-cue/2;
 int tip=elbow-9,ty=ey+8-cue;
 jw_ring(px,py,8,8,JWI_A);jw_ring(px,py,3,3,JWI_INK);
 jw_line(px,py,elbow,ey,JWI_INK,2);jw_line(elbow,ey,tip,ty,JWI_INK,2);
 jw_rect(tip-6,ty-1,9,4,JWI_B);if(cue)jw_line(tip-5,ty+cue+3,tip+5,ty+cue+3,JWI_C,1);
 jw_line(195,43,195,80,JWI_DIM,1);jw_rect(191,44+jw.m[2]*32/127,9,3,JWI_A);
 /* The deck's eight cue pads advance with the record, and flare on the hit. */
 for(int k=0;k<8;k++){
  int active=(step>>2)==k,x=145+(k%4)*12,y=88+(k/4)*7;
  jw_rect(x,y,8,4,active?JWI_A:JWI_BED);
  if(active&&jw.hit>34)jw_rect(x+1,y+1,6,2,JWI_B);
 }
}
static void jw_giraffe(void){
 int hip=68,back=68,bend=jw_wave(0,3)+jw.hit/13,neck=19+jw.m[2]/5,nx=127+bend,ny=60-neck;
 jw_floor(106);jw_quad(hip,back,114,back,106,84,hip+6,84,JWI_SHADE);jw_quad(110,back,nx-5,ny+8,nx+5,ny+8,106,84,JWI_SHADE);jw_line(hip,back,114,back,JWI_INK,3);jw_line(hip,back,hip+6,84,JWI_INK,2);jw_line(hip+6,84,106,84,JWI_INK,2);
 jw_line(106,84,nx+5,ny+8,JWI_INK,2);jw_line(114,back,nx-5,ny+8,JWI_INK,2);
 jw_box(nx-5,ny,23,11,JWI_INK);jw_rect(nx+11,ny+4,2,2,JWI_B);
 jw_joint(nx-3,ny,nx-4,ny-5,nx-8,ny-5,JWI_A);jw_line(nx+6,ny,nx+6,ny-6,JWI_A,2);
 for(int k=0;k<4;k++){int x=77+k*10,d=jw_wave(k*0x80000000u,5);jw_joint(x,84,x-2+d,94,x+d,105,JWI_INK);}
 jw_joint(hip,back,hip-11,75,hip-14+jw_wave(0,4),90,JWI_A);
 for(int k=0;k<4;k++)jw_rect(76+k*8,71+(k&1)*6,4,4,JWI_A);
 int hx=164,hy=32-jw.span/2;for(int k=0;k<6;k++){int yy=hy+k*11;jw_line(hx,yy,hx+(k%2?8:17),yy,JWI_DIM,1);}
 jw_line(hx,hy,hx,hy+55,JWI_DIM,1);jw_line(nx+20,ny+3,hx+22,ny+3,JWI_C,1);
}
static void jw_racer(void){
 /* Low nose and headlamp on the right, with the road sweeping left. */
 static const int8_t outline[][2]={{-59,9},{-54,-5},{-32,-7},{-13,-20},
                                  {14,-19},{39,-5},{62,-1},{64,11},{-59,11}};
 int x=126+jw.hit/5,y=68+jw.hit/24;
 for(int lane=0;lane<2;lane++){
  unsigned travel=(jw.phase<<(lane+1))>>26;
  for(int i=0;i<5;i++){
   int mark=i*64-(int)travel,road=lane?103:89;
   jw_line(mark,road,mark+15+lane*(9+jw.m[2]/5),road,lane?JWI_C:JWI_DIM,1);
  }
 }
 jw_quad(x-54,y-5,x+40,y-5,x+63,y+2,x-59,y+11,JWI_SHADE);
 for(unsigned i=1;i<NELEM(outline);i++)
  jw_line(x+outline[i-1][0],y+outline[i-1][1],x+outline[i][0],y+outline[i][1],JWI_INK,2);
 jw_line(x-47,y-10,x-63,y-10,JWI_C,2);
 jw_rect(x-57,y+1,7,3,JWI_B);
 jw_rect(x+52,y+2,9,3,JWI_A);
 for(int i=0;i<2;i++){
  int wheel=x-35+i*76,spoke=osc_sine(jw.phase*4u)*6/32768;
  jw_disc(wheel,82,10,10,JWI_BG);
  jw_ring(wheel,82,10,10,JWI_INK);
  jw_line(wheel-spoke,78,wheel+spoke,86,JWI_A,1);
 }
 if(jw.hit>26)jw_line(17,y+5,x-65,y+5,JWI_C,1);
}
static void jw_spar(void){
 /* Two athletes share one target; the padded shield deforms at impact. */
 int reach=jw.hit*(18+jw.m[2]/7)/127,pad=129+reach/5;
 jw_floor(106);jw_person(80,104,reach/8,-3,reach-3,2);jw_person(168,104,-3,2,-8,3);
 jw_rect(pad,43,14-reach/8,31,JWI_SHADE);jw_box(pad,43,14-reach/8,31,JWI_A);jw_rect(pad+4,47,6,22,JWI_B);
 jw_joint(160,61,150,68,pad+10,58,JWI_INK);
 for(int i=0;i<3;i++)jw_line(26,74+i*9,214,74+i*9+jw.hit/35,JWI_DIM,1);
 jw_burst(pad,56,12+jw.span/2);
}
static void jw_gust(void){
 /* A windsock with its mouth fixed to a bearing; fabric moves segment by segment. */
 int length=77+jw.m[6]/4,cy=43,px=67,py=cy,r=14+jw.hit/20;
 jw_floor(105);jw_line(54,21,54,102,JWI_INK,2);jw_line(54,29,67,29,JWI_A,2);
 jw_ring(67,cy,6,r,JWI_INK);
 for(int k=1;k<=10;k++){
  int x=67+k*length/10,y=cy+jw_wave(k*0x14000000u,3+k*(jw.m[6]/17+jw.hit/20)/5),dr=clamp(r-k,4,20);
  jw_quad(px,py-r,x,y-dr,x,y+dr,px,py+r,k%3==1?JWI_SHADE:JWI_BED);
  jw_line(px,py-r,x,y-dr,(k&1)?JWI_INK:JWI_A,2);
  jw_line(px,py+r,x,y+dr,(k&1)?JWI_INK:JWI_A,2);
  if(!(k&1))jw_line(x,y-dr,x,y+dr,JWI_C,1);px=x;py=y;r=dr;
 }
 for(int k=0;k<8;k++){
  int x=18+(k*38+(int)(jw.phase>>25))%190,y=15+k*11;
  jw_line(x,y,x+6+jw.span+jw.hit/10,y+(k&1?2:-2),JWI_DIM,1);
 }
}
static void jw_wiper(void){
 int yaw=jw_wave(0,48),reach=41+jw.m[0]/7;
 int wx=123+yaw,wy=78-reach+yaw*yaw/165,blade=80-wy;
 jw_rect(24,12,192,72,JWI_BED);jw_box(24,12,192,72,JWI_DIM);jw_line(24,84,216,84,JWI_INK,2);
 for(int k=0;k<16;k++){
  int x=32+(k*17)%166,y=17+(k*13+(int)(jw.phase>>24))%54;
  /* Leave a dry path along the arm, using its own pivot and angle. */
  int trail=(x-123)*blade-yaw*(80-y);
  if(trail < -12*blade || trail > 12*blade)
   jw_line(x,y,x+3+jw.hit/40,y+5+jw.span/5,JWI_DIM,1);
 }
 int px=36,py=50;
 for(unsigned k=1;k<=23;k++){
  int x=36+(int)k*7,y=50+osc_sine(jw.phase+k*(0x13000000u+(unsigned)jw.m[0]*0x180000u))*(5+jw.m[1]/7+jw.hit/21)/32768;
  jw_line(px,py,x,y,JWI_A,1);px=x;py=y;
 }
 jw_line(123,80,wx,wy,JWI_INK,2);jw_line(wx-14,wy-3,wx+11,wy+3,JWI_INK,3);jw_ring(123,80,4,4,JWI_B);
 jw_line(32,94,208,94,JWI_DIM,1);
 jw_line(87,102,153,102,JWI_C,1);jw_rect(119+yaw/3,100,4,4,JWI_B);
}
/* Acid leaves offset rings in a pool of dye. The face occludes the rings. */
static void jw_smile(void){
 int cx=118+jw.pitch/3,cy=45,rx=33+jw.m[0]/10,ry=32-jw.m[0]/16;
 int acid=jw.m[0],res=jw.m[1],drop=(acid/7+jw.hit*(18+jw.m[4]/5)/127);
 if(!jw.small)for(int k=0;k<4;k++){
  int drift=jw_wave(k*0x28000000u,4+res/13);
  jw_ring(cx+drift,cy+8+drift/3,50+k*13+jw.hit/10,14+k*8,
          k==0?JWI_AMBER:k==1?JWI_A:JWI_DIM);
 }
 int span=rx;
 for(int dy=0;dy<=ry;dy++){
  while(span>0&&span*span*ry*ry+dy*dy*rx*rx>rx*rx*ry*ry)span--;
  int wobble=jw_wave(dy*0x09000000u,2+acid/18);
  jw_rect(cx-span+wobble/3,cy-dy,2*span+1,1,JWI_GOLD);
  if(dy)jw_rect(cx-span+wobble,cy+dy,2*span+1,1,dy>ry*3/4?JWI_AMBER:JWI_GOLD);
 }
 for(int k=0;k<5;k++){
  int x=cx-28+k*13,d=drop*(1+((k+1)&3))/4+jw_wave(k*0x40000000u,3),y=cy+ry-8-(k==0||k==4?5:0),w=4+(k&1)*3;
  jw_rect(x,y,w,clamp(d,3,34),k&1?JWI_GOLD:JWI_AMBER);jw_disc(x+w/2,y+clamp(d,3,34),w/2,3,JWI_AMBER);
 }
 int wink=jw_wave(0,3),slope=jw_wave(0x50000000u,2+res/36);
 jw_disc(cx-15,cy-7+wink,3,7,JWI_BG);jw_disc(cx+14,cy-7-wink,3,7,JWI_BG);
 int px=cx-19,py=cy+7+slope;
 for(int k=1;k<=12;k++){
  int x=cx-19+k*38/12,y=cy+7+k*(12-k)/3+slope*(6-k)/6+jw.hit/45;
  jw_line(px,py,x,y,JWI_BG,3);px=x;py=y;
 }
 if(!jw.small){
  int puddle=24+acid/8+jw.hit/4;
  jw_disc(cx,103,puddle,4,JWI_BED);
  jw_arc(cx,103,puddle,4,0x40000000u,0x7fffffffu,JWI_AMBER);
  if(jw.hit>28){
   int dx=jw_wave(0,5),dy=84+jw.age/23;
   jw_disc(cx+23+dx,dy,2,3,JWI_GOLD);jw_line(cx-7,101,cx+13+jw.hit/3,101,JWI_A,1);
  }
  if(jw.glide)jw_line(cx-rx-19,76,cx-rx+2,76,JWI_A,2);
 }
}
/* Main scene affordance: the engine's EDIT index that shapes the demo's world. */
static const uint8_t JW_KNOB[]={2,2,4,0,2,2,2,2,4,0,1,3,3,5,4,4,2,2,2,2,2,2,2,3,2,2,2,2,6,0,0};
static void jw_draw(const track_t *t,unsigned e,int en,unsigned ph,int x,int y,int w,int h,uint16_t ink){
 if(e>=NENGINES||e==ENGI_EMPTY){cv_frame(x+w/2-3,y+h/2-3,6,6,T_DIM);return;}
 unsigned kind=jazzy_object(e);
 jw=(jw_context_t){.x=x,.y=y,.w=w,.h=h,.e=e,.small=w<100,.age=400};
 jw.still=!!(ui_prefs&PREF_ANIM_OFF)||ink==T_DIM||(t&&t->p[P_MUTE]);
 jw.palette[JWI_INK]=ink;jw.palette[JWI_BG]=ux.light?T_TEXT:T_BG;
 jw.palette[JWI_DIM]=ux_mix(T_BG,ink,29);
 jw.palette[JWI_SHADE]=ux_mix(T_BG,ink,48);jw.palette[JWI_BED]=ux_mix(T_BG,ink,15);
 jw.palette[JWI_C]=ux_mix(T_BG,ink,65);
 jw.palette[JWI_A]=ux_mix(ink,ux.light?0x54cc:0x8df4,70);
 jw.palette[JWI_B]=ux_mix(ink,ux.light?0xd1e6:0xfc2b,82);
 jw.palette[JWI_GOLD]=ux.light?0xd5a4:0xeec6;jw.palette[JWI_AMBER]=ux.light?0x9c66:0xed28;
 if(ink==T_DIM)for(int i=JWI_A;i<=JWI_AMBER;i++)if(i!=JWI_BG)jw.palette[i]=T_DIM;
 for(unsigned k=0;k<8;k++){
  const param_desc_t *p=&ENGINES[e]->edit[k];int v=t?t->p[P_E0+k]:p->def,range=p->max-p->min;
  jw.m[k]=range>0?clamp((v-p->min)*127/range,0,127):0;
 }
 int pitch=60,lo=128,hi=0;
 if(!jw.still){
  jw.phase=ph;jw.en=en;
  if(t){
   unsigned at=six_vis_note_at[t-trk],age=at?fm1_ms-(at-1u):400;
   jw.age=age<400?(int)age:400;
   jw.hit=jw.age<290?(290-jw.age)*(40+six_vis_note_vel[t-trk]*87/127)/290:0;
   int step=e==ENGI_BREAK?jungle_current_step():-1;
   jw.step=step>=0?step:t->seq_idx;jw.glide=t->slide_glide;
   unsigned held=t->nheld,mono=t->nmono;
   if(held>16)held=16;if(mono>8)mono=8;
   if(held||mono){
    const uint8_t *nn=held?t->held:t->mono_stack;
    for(unsigned k=0;k<(held?held:mono);k++){int n=nn[k];if(n<lo)lo=n;if(n>hi)hi=n;jw.notes++;}
   }else for(unsigned k=0;k<NVOICE;k++)if(t->v[k].active&&t->v[k].gate){
    int n=t->v[k].note;
    if(n<lo||n>hi)jw.notes++;
    if(n<lo)lo=n;if(n>hi)hi=n;
   }
   if(hi>=lo)pitch=lo;
   if(t->nmono&&t->mono_note)pitch=t->mono_note;
  }else jw.hit=en;
 }
 jw.span=clamp(hi-lo,0,24);jw.notes=clamp(jw.notes,1,4);jw.pitch=clamp(pitch-60,-28,28);
 switch(kind){
 case JW_DOG:jw_dog();break;case JW_CAT:jw_cat();break;case JW_DRYER:jw_dryer();break;
 case JW_BOXER:jw_boxer();break;case JW_LIFT:jw_lift();break;
 case JW_COCKPIT:jw_cockpit();break;case JW_MOOSE:jw_moose();break;case JW_SEAL:jw_seal();break;
 case JW_SKATER:jw_skater();break;case JW_UMBRELLA:jw_umbrella();break;case JW_COW:jw_cow();break;
 case JW_FENCE:jw_fence();break;case JW_PRESS:jw_press();break;case JW_LINE:jw_lineworld();break;
 case JW_COASTER:jw_coaster();break;case JW_SNAIL:jw_snail();break;case JW_CLOCKS:jw_clocks();break;
 case JW_STRIKER:jw_striker();break;case JW_BALL:jw_ball();break;case JW_VACUUM:jw_vacuum();break;case JW_FAN:jw_fan();break;
 case JW_TAP:jw_tap();break;case JW_VINYL:jw_vinyl();break;case JW_LIFTER:jw_lifter();break;
 case JW_RIDER:jw_rider();break;case JW_GIRAFFE:jw_giraffe();break;case JW_RACER:jw_racer();break;
 case JW_SPAR:jw_spar();break;case JW_GUST:jw_gust();break;case JW_WIPER:jw_wiper();break;case JW_SMILE:jw_smile();break;
 }
}
#undef jw_line
#undef JW_OP_LIMIT

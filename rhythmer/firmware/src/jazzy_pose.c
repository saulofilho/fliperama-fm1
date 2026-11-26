/* GPL-3.0-only. UI-only hierarchical pivots, Q8 local coordinates.
 * No pose state in the audio thread. Shared attachment points keep parts joined.
 * Phase delays provide follow-through; bounded angles preserve silhouettes.
 */
static void jp_turn(int *x,int *y,int ax,int ay,int turn){
 int sn=osc_sine((unsigned)turn),cs=osc_sine((unsigned)turn+0x40000000u),dx=*x-ax*256,dy=*y-ay*256;
 *x=ax*256+(int)(((int64_t)dx*cs-(int64_t)dy*sn)>>15);
 *y=ay*256+(int)(((int64_t)dx*sn+(int64_t)dy*cs)>>15);
}
static void jp_limb(int *x,int *y,int ax,int ay,int kx,int ky,int upper,int lower){
 if(*y>ky*256)jp_turn(x,y,kx,ky,lower);
 jp_turn(x,y,ax,ay,upper);
}
static void jazzy_pose(unsigned obj,int px,int py,int en,unsigned ph,int *x,int *y){
 *x=px*256;*y=py*256;if(!en)return;
 int s=osc_sine(ph)*en/32768,lag=osc_sine(ph-0x18000000u)*en/32768;
 int angle=s*0x160000,late=lag*0x100000;
 if(obj==1){
  if(px<17&&py<34)jp_turn(x,y,17,32,late/2); /* tail follows hips */
  else if(py>=36&&px<34)jp_limb(x,y,20,36,17,44,angle/2,-late/2);
  else if(py>=35&&px>=34)jp_limb(x,y,46,35,45,44,-angle/2,late/2);
  else if(px>45&&py<29)jp_turn(x,y,46,28,-late/8);
  /* Paw contact: no leg sinks below the ground; swing foot clears it. */
  if(*y>52*256)*y=52*256;
 }else if(obj==13){
  int flight=osc_sine(ph),lift=flight>0?flight*en/230000:0;
  if(py>=53){ /* Board leaves the feet slightly later and flips around its own centre. */
   unsigned bp=ph-0x10000000u;int bs=osc_sine(bp),blift=bs>0?bs*en/250000:0;
   int flip=(flight>0&&en>80)?osc_sine(ph*2u)*en/32768:0;
   *y=(57*256)+(*y-57*256)*(127-(flip<0?-flip:flip)*3/4)/127;
   jp_turn(x,y,31,57,late/2);*y-=blift*256;
  }else{
   if(py>=29&&px<30)jp_limb(x,y,24,29,19,40,-angle/3,late/2);
   else if(py>=29)jp_limb(x,y,32,29,36,41,angle/3,-late/2);
   else if(px<19&&py>15)jp_turn(x,y,21,16,-late/3);
   else if(px>43&&py>20)jp_turn(x,y,40,22,late/3);
   else if(py<15)jp_turn(x,y,35,16,-late/10);
   *y-=lift*256; /* Deliberate airborne motion, driven by knee/board articulation. */
  }
 }else if(obj==2||obj==3){
  if(py>36){int hip=px<32?20:43,knee=px<32?18:42;int u=px<32?angle:-angle;jp_limb(x,y,hip,36,knee,45,u/3,-u/4);if(*y>59*256)*y=59*256;}
  else if(px>40)jp_turn(x,y,41,27,late/12);
  if(obj==3&&py<24)jp_turn(x,y,41,27,-late/10);
 }else if(obj==6){
  if(px<19&&py>25)jp_limb(x,y,19,26,15,37,angle/3,-late/3);
  else if(px>45&&py>25)jp_limb(x,y,45,26,49,37,-angle/3,late/3);
  else if(py<25)jp_turn(x,y,32,27,-late/12);
  else if(py>49)jp_turn(x,y,px<32?26:38,49,px<32?late/4:-late/4);
 }else if(obj==11){
  if(py>24){int flex=(py-24)*(py-24);*x+=(int)((int64_t)osc_sine(ph-((unsigned)(py-24)<<23))*en*flex/12000000);}
  else *y=24*256+(*y-24*256)*(127+lag/15)/127;
 }else if(obj==5){
  if(py<34)jp_turn(x,y,32,42,late/20); /* wheels remain on the road */
 }else if(obj==8){if(py<40&&px<45)jp_turn(x,y,43,40,-angle/2);}
 else if(obj==12){if(px<24&&py>26&&py<48)*y+=s*5;else if(px>45)jp_turn(x,y,49,24,angle/4);}
 else if(obj==15){if(py<44&&px<48)jp_turn(x,y,32,46,late/30);}
 else if(obj==10){if(py>15&&py<51){int pivot=px<25?18:px<40?32:46;jp_turn(x,y,pivot,14,px<25?angle/2:px>40?-angle/2:late/8);}}
 else if(obj==4){jp_turn(x,y,12,42,-angle/4);}
 else if(obj==0){if(px<19)jp_turn(x,y,19,32,late/4);}
 *x=clamp(*x,-12*256,76*256);*y=clamp(*y,-12*256,76*256);
}

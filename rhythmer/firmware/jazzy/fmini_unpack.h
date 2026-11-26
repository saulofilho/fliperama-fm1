/* GPL-3.0-only. Lossless native FMini program reader for the JAZZY adapter. */
#include "fmini_compact.h"
static void jf_load(uint8_t *out,unsigned slot){
#if JAZZY_EXTERNAL_ASSETS
 if(!jazzy_assets_valid){memset(out,0,32);out[0]=out[1]=out[2]=3;out[6]=out[7]=64;out[8]=100;out[12]=1;return;}
 const uint8_t *b=jazzy_asset_at(JA_JF_PACK);
#else
 const uint8_t *b=JF_PACK;
#endif
 for(unsigned j=0;j<32;j++){const uint8_t *m=b+j*5u;unsigned w=m[4],di=m[2]|m[3]<<8,pos=(m[0]|m[1]<<8)+slot*w,off=160u+(pos>>3);unsigned v=((b[off]|b[off+1]<<8)>>(pos&7u))&((1u<<w)-1u);out[j]=(uint8_t)(di==65535u?v:b[di+v]);}
}

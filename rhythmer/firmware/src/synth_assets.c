/* SPDX-License-Identifier: GPL-3.0-only
 * Immutable synth assets occupy only reserved PCM-slot padding. Main-loop-only
 * integrity / preservation work; the audio side reads the existing XIP window. */
#if JAZZY_EXTERNAL_ASSETS
static int jazzy_catalog_check(void)
{
    jazzy_font_valid = st_crc32(fm1_xip_ptr(JAZZY_FONT_AT), AF_M_XIP_BYTES) == AF_M_XIP_CRC;
    jazzy_catalog_valid = lxr_assets_valid = 0;
    for (unsigned i = 0; i < sizeof JCAT_PARTS / sizeof JCAT_PARTS[0]; i++)
        if (st_crc32(fm1_xip_ptr(JCAT_PARTS[i].at), JCAT_PARTS[i].size) != JCAT_PARTS[i].crc)
            return 0;
    lxr_assets_valid = st_crc32(fm1_xip_ptr(0x93020u), LXR_MARKER_BYTES) == LXR_MARKER_CRC;
    jazzy_catalog_valid = 1;
    return 1;
}
static const uint8_t *jazzy_asset_at(unsigned off){return fm1_xip_ptr(0xA0000u+(off/JAZZY_ASSET_PAYLOAD)*0x14000u+JAZZY_ASSET_TAIL+16u+off%JAZZY_ASSET_PAYLOAD);}
static int jazzy_assets_check(void){
 jazzy_assets_valid=0;
 for(unsigned i=0;i<2;i++){const uint8_t *p=fm1_xip_ptr(0xA0000u+i*0x14000u+JAZZY_ASSET_TAIL);const uint32_t *h=(const uint32_t*)p;
  if(h[0]!=0x53415a4au||h[1]!=i||h[2]!=JAZZY_ASSET_PAYLOAD||h[3]!=JAZZY_ASSET_CRC[i]||st_crc32(p+16,JAZZY_ASSET_PAYLOAD)!=h[3])return 0;
 }
 jazzy_assets_valid=1;return 1;
}
#endif

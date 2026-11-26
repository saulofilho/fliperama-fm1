#include <stdint.h>
#include <stdio.h>
#include <string.h>
#ifdef OB
#include "../../upstream/obervave/firmware/src/obv_params.h"

#include "../../upstream/obervave/firmware/src/obv_patches.h"
int main(void){for(unsigned k=0;k<NFACT;k++){uint8_t p[NPARAM];for(unsigned i=0;i<NPARAM;i++)p[i]=PDEF[i].def;const uint8_t *v=FACTORY[k].set;for(;v[0]!=255;v+=2)p[v[0]]=v[1];printf("%s|",FACTORY[k].name);for(unsigned i=0;i<NPARAM;i++)printf("%d,",p[i]);puts("");}return 0;}
#else
#include "../../upstream/kwasub/source/firmware/src/ksub_data.c"
int main(void){for(unsigned k=0;k<NFACTORY;k++){int8_t p[NP_MAX];char name[32]={0};preset_factory(k,p,name);printf("%s|",name);for(unsigned i=0;i<NP_MAX;i++)printf("%d,",p[i]);puts("");}return 0;}
#endif

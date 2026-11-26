#define UI_TEST_NO_MAIN 1
#include "jazzy_host.h"
int main(void){printf("{\"engines\":[");for(unsigned i=0;i<NENG_SHOWN;i++){unsigned e=ENGINE_ORDER[i];const engine_t *p=ENGINES[e];printf("%s{\"id\":%u,\"name\":\"%s\",\"presets\":%u,\"polyphony_cap\":%u,\"one_shot\":%s,\"factory_id\":%u}",i?",":"",e,p->name,p->npresets,p->poly,p->oneshot?"true":"false",p->factory_id);}printf("]}\n");return 0;}

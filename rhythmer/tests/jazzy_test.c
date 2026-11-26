#define UI_TEST_NO_MAIN 1
#include "jazzy_host.h"
int main(void){ui_power_on();power_on_parts();printf("JAZZY engines: %u\n",NENG_SHOWN);return 0;}

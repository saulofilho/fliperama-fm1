/* SPDX-License-Identifier: GPL-3.0-only */
/* Main-loop GEN only. Keep a strict pitched-bass preset filter. */
static int gen_bass_ok(unsigned e,unsigned p)
{
    const preset_t *s=factory_preset(ENGINES[e],p);unsigned tag=PR_TAG(s);
    if(gnever(s->name)||tag==PT_FX||tag==PT_DRUM)return 0;
    if(e==ENGI_LOFI&&s->e[1]>=RW_BYTE)return 0;
    return tag==PT_BASS||dname_has(s->name,"BASS");
}

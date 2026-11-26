/* SPDX-License-Identifier: GPL-3.0-only */
#define UI_TEST_NO_MAIN 1
#define RHYTHMER_USB_HOST 1
#include "jazzy_host.h"

static void tap(unsigned label)
{
    uint32_t bit = 1u << panel.btn[label];
    fm1_in.buttons |= bit;
    host_pressed |= bit;
    fm1_ms += 16;
    ui_input();
    fm1_in.buttons &= ~bit;
    fm1_ms += 16;
    ui_input();
}

static int held(const track_t *t, unsigned note)
{
    for (unsigned i = 0; i < NVOICE; i++)
        if (t->v[i].active && t->v[i].gate && t->v[i].note == note) return 1;
    return 0;
}

int main(void)
{
    int bad = 0;
    ui_power_on();
    fm6_init();
    power_on_parts();
    song.playing = 0;
    transport_req = 0;
    bad += check("USB HOST starts off and is on MENU > USB", !uh.on && !menu_get(MI_HOST) && mi_tab(MI_HOST) == MTAB_USB);
    song.playing = 1;
    menu_put(MI_HOST, 1);
    bad += check("playing blocks Host ON", !uh.want && !ui.confirm);
    song.playing = 0;
    ui.menu = 1;
    ui.menu_sel = MI_HOST;
    host_enc[panel.enc[EN_K3]] = 1;
    ui_input();
    bad += check("K3 opens a visible local confirmation", !uh.want && ui.confirm == CF_USB_HOST && !ui.menu);
    tap(B_OCTDN);
    bad += check("OCT- cancels Host ON", !uh.want && !ui.confirm);
    menu_put(MI_HOST, 1);
    tap(B_OCTUP);
    bad += check("OCT+ requests Host ON", uh.want && !ui.confirm);
    menu_put(MI_HOST, 0);
    bad += check("Host OFF returns the port to device mode", !uh.want);

    track_t *t = &trk[0];
    set_engine_of(t, ENGI_ANALOG);
    t->engine = ENGI_ANALOG;
    t->p[P_VOICE] = V_POLY;
    t->xf = t->xf_on = 0;
    song.g[G_ROUTE] = 0;
    panic_req = 0;
    midi_event(0x90, 0, 60, 100);
    t->seq_n = 1;
    t->seq_off = CTL * 4u;
    t->seq_notes[0] = 60;
    midi_event(0x90, 0, 62, 100);
    midi_event(0xB0, 0, 64, 127);
    midi_event(0x80, 0, 62, 0);
    bad += check("fixture holds a sequenced unison and a sustained MIDI note", mn_get(0,60) && mn_get(0,62) && held(t,60) && held(t,62));
    usb_midi_lost = 1;
    midi_enqueue(0x40649009u, 1u);  /* a USB Note On queued just before loss */
    events_block(CTL);
    bad += check("USB loss releases MIDI notes and drops its pending Note On", !mn_get(0,60) && !mn_get(0,62) &&
                 !mn_get(0,100) && !midi_ch[0].pedal && !midi_owners[0]);
    bad += check("USB loss preserves the sequencer's held note", held(t,60) && !held(t,62));
    printf("USB host UI/ownership: %s (%d)\n", bad ? "FAIL" : "PASS", bad);
    return bad != 0;
}

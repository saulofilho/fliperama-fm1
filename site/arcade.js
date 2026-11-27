'use strict';
/* FLIPERAMA site: the six cabinets (from docs/moodboard), chips in Web Audio, scenes on 120x120 canvases */
const W = 120;
const hash = n => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
const mtof = m => 440 * Math.pow(2, (m - 69) / 12);
const pad = (n, l) => String(n).padStart(l, '0');

/* ---------- fonte 3x5 ---------- */
const F = {A:[2,5,7,5,5],B:[6,5,6,5,6],C:[3,4,4,4,3],D:[6,5,5,5,6],E:[7,4,6,4,7],F:[7,4,6,4,4],G:[3,4,5,5,3],
H:[5,5,7,5,5],I:[7,2,2,2,7],J:[1,1,1,5,2],K:[5,5,6,5,5],L:[4,4,4,4,7],M:[5,7,7,5,5],N:[6,5,5,5,5],O:[2,5,5,5,2],
P:[6,5,6,4,4],Q:[2,5,5,6,3],R:[6,5,6,5,5],S:[3,4,2,1,6],T:[7,2,2,2,2],U:[5,5,5,5,7],V:[5,5,5,5,2],W:[5,5,7,7,5],
X:[5,5,2,5,5],Y:[5,5,2,2,2],Z:[7,1,2,4,7],0:[7,5,5,5,7],1:[2,6,2,2,7],2:[6,1,2,4,7],3:[6,1,2,1,6],4:[5,5,7,1,1],
5:[7,4,6,1,6],6:[3,4,7,5,7],7:[7,1,1,2,2],8:[7,5,7,5,7],9:[7,5,7,1,6],' ':[0,0,0,0,0],'-':[0,0,7,0,0],
':':[0,2,0,2,0],'!':[2,2,2,0,2],'.':[0,0,0,0,2]};
function txt(g, s, x, y, c, k = 1) {
  g.fillStyle = c;
  for (const ch of s) {
    const gl = F[ch] || F[' '];
    for (let r = 0; r < 5; r++) for (let b = 0; b < 3; b++)
      if ((gl[r] >> (2 - b)) & 1) g.fillRect(x + b * k, y + r * k, k, k);
    x += 4 * k;
  }
}
const txtW = (s, k = 1) => s.length * 4 * k - k;
function txtC(g, s, y, c, k = 1) { txt(g, s, Math.round((W - txtW(s, k)) / 2), y, c, k); }
function shadowTxt(g, s, y, c, k = 1) { txtC(g, s, y + k, '#000', k); txtC(g, s, y, c, k); }

/* ---------- desenho ---------- */
function bands(g, cols, y0, y1) {
  const h = (y1 - y0) / cols.length;
  cols.forEach((c, i) => { g.fillStyle = c; g.fillRect(0, Math.round(y0 + i * h), W, Math.ceil(h) + 1); });
  for (let i = 1; i < cols.length; i++) {
    const yb = Math.round(y0 + i * h); g.fillStyle = cols[i - 1];
    for (let x = 0; x < W; x += 2) { g.fillRect(x, yb, 1, 1); if (x % 4 === 0) g.fillRect(x + 1, yb + 1, 1, 1); }
  }
}
function spr(g, rows, map, x, y, k = 1, flip = false) {
  x = Math.round(x); y = Math.round(y);
  for (let r = 0; r < rows.length; r++) {
    const row = rows[r];
    for (let c = 0; c < row.length; c++) {
      const ch = row[flip ? row.length - 1 - c : c];
      if (ch !== '.') { g.fillStyle = map[ch]; g.fillRect(x + c * k, y + r * k, k, k); }
    }
  }
}
function disc(g, cx, cy, r, c) {
  g.fillStyle = c;
  for (let y = -r; y <= r; y++) { const w = Math.round(Math.sqrt(r * r - y * y)); g.fillRect(cx - w, cy + y, w * 2 + 1, 1); }
}
function idle(g, now, active, c = '#F3E9D2') {
  if (!active && Math.floor(now * 1.6) % 2 === 0) shadowTxt(g, 'INSIRA FICHA', 108, c);
}

/* ---------- áudio ---------- */
let ac = null, master = null, WV = {}, NOISE = {}, pwm = null;
const FR = 1 / 60;
const GB = [0,2,4,6,8,10,12,14,15,15,14,13,12,11,10,9,8,7,6,5,4,3,2,1,0,0,1,2,3,2,1,0];
const TRI = [...Array(16)].map((_, i) => 15 - i).concat([...Array(16)].map((_, i) => i));
function pulseWave(d) {
  const n = 64, re = new Float32Array(n), im = new Float32Array(n);
  for (let k = 1; k < n; k++) re[k] = 2 / (k * Math.PI) * Math.sin(k * Math.PI * d);
  return ac.createPeriodicWave(re, im);
}
function tableWave(tab) {
  const N = tab.length, H = N / 2, re = new Float32Array(H), im = new Float32Array(H), x = tab.map(v => (v - 7.5) / 7.5);
  for (let k = 1; k < H; k++) {
    let a = 0, b = 0;
    for (let j = 0; j < N; j++) { a += x[j] * Math.cos(2 * Math.PI * k * j / N); b += x[j] * Math.sin(2 * Math.PI * k * j / N); }
    re[k] = a * 2 / N; im[k] = b * 2 / N;
  }
  return ac.createPeriodicWave(re, im);
}
function lfsrBuffer(short) {
  const len = ac.sampleRate, buf = ac.createBuffer(1, len, ac.sampleRate), d = buf.getChannelData(0);
  let r = 1, v = 1;
  for (let i = 0; i < len; i++) {
    if (i % 4 === 0) { const fb = (r ^ (r >> (short ? 6 : 1))) & 1; r = (r >> 1) | (fb << 14); v = (r & 1) ? 1 : -1; }
    d[i] = v;
  }
  return buf;
}
function audio() {
  if (!ac) {
    ac = new (window.AudioContext || window.webkitAudioContext)();
    const comp = ac.createDynamicsCompressor(); comp.threshold.value = -14; comp.ratio.value = 4;
    master = ac.createGain(); master.gain.value = 0.55; master.connect(comp).connect(ac.destination);
    WV = { p125: pulseWave(0.125), p25: pulseWave(0.25), p50: pulseWave(0.5), tri: tableWave(TRI), gb: tableWave(GB) };
    NOISE = { long: lfsrBuffer(false), short: lfsrBuffer(true) };
    for (const c of cabs) { c.next = ac.currentTime + 0.05; c.q = []; }
  }
  if (ac.state === 'suspended') ac.resume();
}
function stepGain(g, t, dur, vel, decay) {
  g.gain.setValueAtTime(vel, t);
  const n = Math.max(1, Math.round(dur / FR));
  for (let i = 1; i <= n; i++) {
    const lv = Math.max(0, Math.round(15 * (1 - i / decay))) / 15;
    g.gain.setValueAtTime(vel * lv, t + i * FR);
    if (lv === 0) break;
  }
  g.gain.setValueAtTime(0, t + dur);
}
function blip(t, m, dur, vel, wave, decay = 999) {
  const o = ac.createOscillator(), g = ac.createGain();
  o.setPeriodicWave(wave); o.frequency.value = mtof(m); g.gain.value = 0;
  stepGain(g, t, dur, vel, decay);
  o.connect(g).connect(master); o.start(t); o.stop(t + dur + 0.03);
}
function noise(t, short, rate, dur, vel, decay) {
  const s = ac.createBufferSource(), g = ac.createGain();
  s.buffer = short ? NOISE.short : NOISE.long; s.loop = true; s.playbackRate.value = rate; g.gain.value = 0;
  stepGain(g, t, dur, vel, decay);
  s.connect(g).connect(master); s.start(t, Math.random() * 0.9); s.stop(t + dur + 0.03);
}
function kick(t) {
  const o = ac.createOscillator(), g = ac.createGain();
  o.setPeriodicWave(WV.tri);
  for (let i = 0; i < 9; i++) o.frequency.setValueAtTime(170 * Math.pow(0.72, i), t + i * FR * 0.6);
  g.gain.setValueAtTime(0.7, t); g.gain.setValueAtTime(0, t + 0.13);
  o.connect(g).connect(master); o.start(t); o.stop(t + 0.15);
}
function drum(ch, t) {
  if (ch === 'k') kick(t);
  else if (ch === 's') { noise(t, false, 0.9, 0.16, 0.3, 9); blip(t, 52, 0.05, 0.25, WV.tri); }
  else if (ch === 'h') noise(t, true, 2.2, 0.04, 0.1, 3);
}
function fm(t, m, dur, vel, ratio, index, decay) {
  const f = mtof(m), c = ac.createOscillator(), mo = ac.createOscillator(), mg = ac.createGain(), g = ac.createGain();
  c.frequency.value = f; mo.frequency.value = f * ratio;
  mg.gain.setValueAtTime(index * f, t); mg.gain.setTargetAtTime(index * f * 0.15, t, decay / 3);
  g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(vel, t + 0.004);
  g.gain.setTargetAtTime(vel * 0.3, t + 0.004, decay / 3); g.gain.setTargetAtTime(0, t + dur, 0.04);
  mo.connect(mg).connect(c.frequency); c.connect(g).connect(master);
  c.start(t); mo.start(t); c.stop(t + dur + 0.3); mo.stop(t + dur + 0.3);
}
const PWM_RATE = 0.35, PWM_DEPTH = 0.7;
function makePWM() {
  const tri = ac.createOscillator(), off = ac.createConstantSource(), lfo = ac.createOscillator(), lg = ac.createGain();
  tri.type = 'triangle'; off.offset.value = 0; lfo.frequency.value = PWM_RATE; lg.gain.value = PWM_DEPTH;
  lfo.connect(lg).connect(off.offset);
  const sum = ac.createGain(), sh = ac.createWaveShaper(), curve = new Float32Array(1024);
  for (let i = 0; i < 1024; i++) curve[i] = (i / 1023 * 2 - 1) > 0 ? 0.5 : -0.5;
  sh.curve = curve;
  const filt = ac.createBiquadFilter(), env = ac.createGain();
  filt.type = 'lowpass'; filt.Q.value = 9; filt.frequency.value = 900; env.gain.value = 0;
  tri.connect(sum); off.connect(sum); sum.connect(sh).connect(filt).connect(env).connect(master);
  const t0 = ac.currentTime + 0.02;
  tri.start(t0); off.start(t0); lfo.start(t0);
  return { tri, filt, env, t0 };
}
function pwmNote(t, m, dur, vel) {
  if (!pwm) pwm = makePWM();
  pwm.tri.frequency.setTargetAtTime(mtof(m), t, 0.018);
  pwm.env.gain.setValueAtTime(vel, t); pwm.env.gain.setTargetAtTime(vel * 0.55, t + 0.01, 0.12);
  pwm.env.gain.setTargetAtTime(0, t + dur, 0.03);
  pwm.filt.frequency.setValueAtTime(3800, t); pwm.filt.frequency.setTargetAtTime(700, t, 0.14);
}
function duty(now) {
  const t0 = pwm ? pwm.t0 : 0;
  return (1 + PWM_DEPTH * Math.sin(2 * Math.PI * PWM_RATE * (now - t0))) / 2;
}

/* ---------- cenas ---------- */
function Corredor() {
  let jumpT = -9, jumpH = 0, score = 0, bassT = -9, coins = [];
  const M = { c: '#F3E9D2', r: '#E23D28', b: '#3EC1D3', y: '#F2C14E' };
  const RUN = [
    ['..cc.', '..cc.', '.rrr.', 'r.rr.', '..rrr', '.b.b.', 'b...b', 'b....'],
    ['..cc.', '..cc.', '.rrr.', '.rrr.', '..rr.', '..bb.', '.b.b.', '..b..']];
  const JUMP = ['..cc.', 'r.cc.', '.rrrr', '..rr.', '..rr.', '.bb.b', 'b....', '.....'];
  return {
    on(e, now) {
      if (e.type === 'lead') {
        jumpT = now; jumpH = Math.max(8, Math.min(30, 10 + (e.pitch - 64) * 1.4));
        coins.push({ x: 35, y: 84 - jumpH - 12, t: now }); score = (score + 10) % 100000;
      }
      if (e.type === 'bass') bassT = now;
    },
    draw(g, now, active) {
      bands(g, ['#1A1238', '#2E1A52', '#5C2468', '#A8346F', '#E0457B', '#F2894E'], 0, 84);
      const glow = Math.max(0, 1 - (now - bassT) * 5);
      disc(g, 92, 20, 7 + Math.round(glow * 2), '#F6DE8D');
      const sp = now * 16;
      for (let k = -1; k < 14; k++) {
        const idx = Math.floor(sp / 10) + k, x = Math.round(k * 10 - (sp % 10)), hh = 12 + Math.floor(hash(idx) * 26);
        g.fillStyle = '#2A1748'; g.fillRect(x, 84 - hh, 10, hh);
        g.fillStyle = '#5C2468'; if (hash(idx + 3) > 0.5) g.fillRect(x + 3, 84 - hh + 4, 2, 2);
      }
      const sp2 = now * 44;
      for (let k = -1; k < 6; k++) {
        const idx = Math.floor(sp2 / 26) + k, x = Math.round(k * 26 - (sp2 % 26));
        g.fillStyle = '#120C22'; g.fillRect(x, 84, 24, 36);
        g.fillStyle = '#3A2A5C'; g.fillRect(x, 84, 24, 1);
        g.fillStyle = '#F2C14E';
        for (let wy = 0; wy < 3; wy++) for (let wx = 0; wx < 3; wx++)
          if (hash(idx * 7 + wy * 3 + wx) > 0.55) g.fillRect(x + 3 + wx * 7, 90 + wy * 9, 3, 4);
      }
      const p = (now - jumpT) / 0.34;
      let y = 76, fr;
      if (p >= 0 && p < 1) { y -= Math.round(jumpH * 4 * p * (1 - p)); fr = JUMP; } else fr = RUN[Math.floor(now * 12) % 2];
      spr(g, fr, M, 33, y);
      coins = coins.filter(c => now - c.t < 0.5);
      for (const c of coins) {
        const a = now - c.t, yy = Math.round(c.y - a * 24);
        g.fillStyle = a < 0.2 ? '#F2C14E' : '#F3E9D2';
        g.fillRect(c.x, yy, 3, 3);
        if (a > 0.1) { g.fillRect(c.x - 2, yy + 1, 1, 1); g.fillRect(c.x + 4, yy + 1, 1, 1); g.fillRect(c.x + 1, yy - 2, 1, 1); }
      }
      txt(g, 'PLACAR', 3, 3, '#F3E9D2'); txt(g, pad(score, 5), 3, 10, '#F2C14E');
      idle(g, now, active);
    }
  };
}

function Surfe() {
  let swell = 0.3, last = 0, period = 2, tgt = 2, hopT = -9, ondas = 0;
  const M = { c: '#F3E9D2', r: '#E23D28', y: '#F2C14E', d: '#1B1630' };
  const S = ['..c..', '.ccc.', 'r.y.r', '.yyy.', '..y..', '.d.d.', 'd...d'];
  const waveY = (x, now, amp) => {
    const ph = ((x / W) * period + now * 0.9) % 1;
    return 86 - (GB[Math.floor(ph * 32)] / 15) * amp;
  };
  return {
    on(e, now) {
      if (e.type === 'lead') { swell = Math.min(1, swell + 0.45); tgt = 1.2 + (e.pitch - 58) / 7; hopT = now; ondas = (ondas + 1) % 1000; }
    },
    draw(g, now, active) {
      const dt = Math.min(0.1, Math.max(0, now - last)); last = now;
      swell += (0.25 - swell) * dt * 1.5; period += (tgt - period) * dt * 4;
      bands(g, ['#E0457B', '#F2894E', '#F2A65A', '#F2C14E', '#F6DE8D'], 0, 64);
      disc(g, 60, 62, 15, '#FFF1C1');
      bands(g, ['#3EC1D3', '#1E8FA8', '#13637F', '#0B3D5A'], 64, 120);
      g.fillStyle = '#FFF1C1';
      for (let i = 0; i < 6; i++) { const w = 20 - i * 3, x = 60 - w / 2 + Math.round(Math.sin(now * 2 + i) * 2); g.fillRect(Math.round(x), 67 + i * 3, w, 1); }
      const amp = 4 + swell * 18;
      for (let x = 0; x < W; x++) {
        const y = Math.round(waveY(x, now, amp));
        g.fillStyle = '#0F7E96'; g.fillRect(x, y, 1, 120 - y);
        g.fillStyle = '#0B5E73'; if ((x + y) % 3 === 0) g.fillRect(x, y + 5, 1, 1);
        g.fillStyle = '#F3E9D2'; g.fillRect(x, y, 1, 1);
      }
      const y0 = waveY(42, now, amp), y1 = waveY(50, now, amp);
      const p = (now - hopT) / 0.3, hop = p >= 0 && p < 1 ? 7 * 4 * p * (1 - p) : 0;
      const by = (y0 + y1) / 2 - 2 - hop;
      g.fillStyle = '#E23D28';
      for (let i = 0; i < 10; i++) g.fillRect(41 + i, Math.round(by + (y1 - y0) * (i - 4.5) / 9), 1, 1);
      spr(g, S, M, 44, Math.round(by - 7));
      txt(g, 'ONDAS', 3, 3, '#1B1630'); txt(g, pad(ondas, 3), 3, 10, '#E23D28');
      idle(g, now, active);
    }
  };
}

function Penalti() {
  let ball = null, dive = null, flash = null, gols = 0, defs = 0, crowd = 0, kickT = -9;
  const K = { y: '#F2C14E', d: '#1B1630', c: '#F3E9D2', g: '#E23D28' };
  const KEEP = ['.ccc.', '.ccc.', 'gyyyg', '.yyy.', '.yyy.', '.d.d.', '.d.d.'];
  const DIVE = ['gyyyyccc.', 'dyyyyccc.', 'd.yyy....'];
  const KICKER = ['.ccc.', '.ccc.', '.rrr.', 'r.r.r', '.rrr.', '.b.b.', '.b.b.'];
  const KK = { c: '#F3E9D2', r: '#3EC1D3', b: '#1B1630' };
  return {
    on(e, now) {
      if (e.type === 'kick') {
        const side = hash(now * 3.1) > 0.5 ? 1 : -1;
        ball = { t: now, tx: 60 + side * (12 + Math.floor(hash(now) * 12)), ty: 22 + Math.floor(hash(now * 1.7) * 12), side, done: false };
        kickT = now;
      }
      if (e.type === 'snare') dive = { t: now, side: hash(now * 5.3) > 0.5 ? 1 : -1 };
      if (e.type === 'hat') crowd = now;
    },
    draw(g, now, active) {
      for (let y = 0; y < 120; y += 8) { g.fillStyle = (y / 8) % 2 ? '#3E8E41' : '#46A049'; g.fillRect(0, y, W, 8); }
      g.fillStyle = '#1B1630'; g.fillRect(0, 0, W, 14);
      const seed = Math.floor(crowd * 30), pal = ['#E23D28', '#F2C14E', '#F3E9D2', '#3EC1D3', '#E0457B', '#7BD389'];
      for (let x = 1; x < W; x += 3) for (let y = 2; y < 12; y += 3) {
        g.fillStyle = pal[Math.floor(hash(x * 13 + y * 7 + seed) * pal.length)];
        g.fillRect(x, y - (now - crowd < 0.08 && hash(x + seed) > 0.6 ? 1 : 0), 2, 2);
      }
      g.fillStyle = '#E23D28'; g.fillRect(0, 14, W, 3); g.fillStyle = '#F3E9D2';
      for (let x = 4; x < W; x += 20) g.fillRect(x, 15, 10, 1);
      const bulge = flash && flash.txt === 'GOL!' && now - flash.t < 0.4 ? 1 : 0;
      g.fillStyle = '#BFD8D2';
      for (let y = 21; y < 40; y += 3) for (let x = 33; x < 88; x += 3) g.fillRect(x, y - bulge, 1, 1);
      g.fillStyle = '#F3E9D2'; g.fillRect(30, 19, 60, 2); g.fillRect(30, 19, 2, 22); g.fillRect(88, 19, 2, 22);
      g.fillRect(0, 41, W, 1); g.fillRect(18, 41, 1, 26); g.fillRect(101, 41, 1, 26); g.fillRect(18, 66, 84, 1);
      g.fillRect(59, 92, 3, 2);
      let kx = 58 + Math.round(Math.sin(now * 3) * 6);
      const dp = dive ? (now - dive.t) / 0.4 : 9;
      if (dp < 1.3) { const off = dive.side * Math.min(1, dp * 2.5) * 18; spr(g, DIVE, K, kx - 2 + off, 30, 1, dive.side < 0); }
      else spr(g, KEEP, K, kx, 30);
      spr(g, KICKER, KK, 57 + (now - kickT < 0.15 ? 2 : 0), 98);
      if (ball) {
        const p = Math.min(1, (now - ball.t) / 0.3);
        if (p >= 1 && !ball.done) {
          ball.done = true;
          const saved = dive && now - dive.t < 0.5 && dive.side === ball.side;
          if (saved) { defs = (defs + 1) % 100; flash = { t: now, txt: 'DEFESA' }; }
          else { gols = (gols + 1) % 100; flash = { t: now, txt: 'GOL!' }; }
        }
        if (now - ball.t < 0.7) {
          const bx = 60 + (ball.tx - 60) * p, by = 93 + (ball.ty - 93) * p - 6 * 4 * p * (1 - p), s = p < 0.5 ? 3 : 2;
          g.fillStyle = '#F3E9D2'; g.fillRect(Math.round(bx - 1), Math.round(by - 1), s, s);
          g.fillStyle = '#1B1630'; g.fillRect(Math.round(bx), Math.round(by), 1, 1);
        }
      }
      txt(g, 'GOL ' + pad(gols, 2), 3, 112, '#F3E9D2'); txt(g, 'DEF ' + pad(defs, 2), 88, 112, '#F3E9D2');
      if (flash && now - flash.t < 0.6 && Math.floor((now - flash.t) * 10) % 2 === 0)
        shadowTxt(g, flash.txt, 70, flash.txt === 'GOL!' ? '#F2C14E' : '#3EC1D3', 3);
      else idle(g, now, active);
    }
  };
}

function Pipa() {
  let kx = 78, ky = 40, vx = 0, vy = 0, ty = 40, gust = 0, last = 0, notas = 0;
  const tail = [];
  const KITE = ['...m...', '..mmm..', '.mmymm.', 'mmyyymm', '.mmymm.', '..mmm..', '...m...'];
  const KM = { m: '#E0457B', y: '#F2C14E' };
  const houses = [...Array(16)].map((_, i) => ({
    x: i * 9 - 4 + Math.floor(hash(i) * 3), w: 9 + Math.floor(hash(i + 9) * 4), h: 10 + Math.floor(hash(i + 20) * 12),
    c: ['#E23D28', '#F2C14E', '#7BD389', '#E0457B', '#F2894E', '#3EC1D3', '#F3E9D2'][Math.floor(hash(i + 40) * 7)]
  }));
  return {
    on(e, now) {
      if (e.type === 'lead') { ty = Math.max(12, Math.min(62, 66 - (e.pitch - 70) * 3.2)); notas = (notas + 1) % 1000; }
      if (e.type === 'bass') gust = 1;
    },
    draw(g, now, active) {
      const dt = Math.min(0.05, Math.max(0, now - last)); last = now; gust *= Math.exp(-dt * 3);
      bands(g, ['#2E9CCA', '#3EC1D3', '#7FD8E3', '#BDEBEF'], 0, 92);
      for (let i = 0; i < 3; i++) {
        const cx = Math.round(((hash(i) * 150 + now * (3 + i)) % 160) - 20), cy = 10 + i * 14;
        g.fillStyle = '#F3E9D2'; g.fillRect(cx, cy, 16, 3); g.fillRect(cx + 3, cy - 2, 8, 2); g.fillRect(cx + 5, cy - 3, 4, 1);
      }
      const tx = 74 + Math.sin(now * 0.6) * 12 + Math.sin(now * 7) * gust * 7;
      vx += ((tx - kx) * 7 - vx * 3) * dt; vy += ((ty - ky) * 7 - vy * 3) * dt; kx += vx * dt; ky += vy * dt;
      tail.unshift({ x: kx, y: ky }); if (tail.length > 24) tail.pop();
      const hx = 20, hy = 92;
      g.fillStyle = '#1B1630';
      for (let s = 0; s <= 1; s += 1 / 60) {
        const x = hx + (kx - hx) * s, y = hy + (ky + 3 - hy) * s + Math.sin(Math.PI * s) * 9 * (1 - gust * 0.6);
        g.fillRect(Math.round(x), Math.round(y), 1, 1);
      }
      for (let i = 2; i < tail.length; i += 2) {
        const p = tail[i], x = p.x + Math.sin(now * 9 + i) * (1 + gust * 2) - i * 0.5, y = p.y + 4 + i * 0.9;
        g.fillStyle = i % 4 ? '#E23D28' : '#F2C14E'; g.fillRect(Math.round(x), Math.round(y), 1, 2);
      }
      spr(g, KITE, KM, kx - 3, ky - 3);
      for (const h of houses) {
        const top = 120 - h.h - 14;
        g.fillStyle = h.c; g.fillRect(h.x, top, h.w, 120 - top);
        g.fillStyle = '#9C8F7E'; g.fillRect(h.x, top, h.w, 1);
        g.fillStyle = '#1B1630'; g.fillRect(h.x + 2, top + 4, 2, 2); if (h.w > 10) g.fillRect(h.x + 6, top + 4, 2, 2);
      }
      for (let i = 0; i < 14; i++) {
        const x = i * 9 + Math.floor(hash(i + 70) * 3), h = 6 + Math.floor(hash(i + 80) * 8);
        g.fillStyle = ['#B8452F', '#C79A3C', '#5FA86C', '#B23A63', '#3B95A3'][i % 5]; g.fillRect(x, 120 - h, 9, h);
        g.fillStyle = '#1B1630'; g.fillRect(x + 3, 120 - h + 2, 2, 2);
      }
      spr(g, ['.c.', 'rrr', '.r.', 'b.b'], { c: '#F3E9D2', r: '#1B1630', b: '#1B1630' }, hx - 1, hy - 1);
      txt(g, 'VENTO', 3, 3, '#1B1630'); g.fillStyle = '#E23D28'; g.fillRect(3, 10, 2 + Math.round(gust * 26), 3);
      idle(g, now, active, '#1B1630');
    }
  };
}

function Pista() {
  let pose = 0, flip = false, kickT = -9, step = 0;
  const M = { c: '#F3E9D2', r: '#E0457B', b: '#3EC1D3' };
  const P = [
    ['..ccc..', '..ccc..', '...c...', '.rrrrr.', 'r.rrr.r', 'r.rrr.r', '..rrr..', '..bbb..', '..b.b..', '..b.b..', '.bb.bb.'],
    ['r.ccc..', 'r.ccc..', 'r..c...', '.rrrrr.', '..rrr.r', '..rrr.r', '..rrr..', '..bbb..', '.b..b..', 'b...b..', 'b...bb.'],
    ['r.ccc.r', 'r.ccc.r', 'r..c..r', '.rrrrr.', '..rrr..', '..rrr..', '..rrr..', '..bbb..', '.b...b.', '.b...b.', 'bb...bb']];
  const TILE = ['#E0457B', '#3EC1D3', '#F2C14E', '#7BD389'], DIM = ['#4A1F3A', '#1C4A55', '#4F4120', '#2B4A31'];
  return {
    on(e, now) {
      if (e.type === 'lead') { pose = e.pitch >= 64 ? 2 : (pose === 1 ? 0 : 1); flip = !flip; }
      if (e.type === 'kick') kickT = now;
      if (e.type === 'step') step = e.step;
    },
    draw(g, now, active) {
      g.fillStyle = '#0E0B16'; g.fillRect(0, 0, W, 120);
      g.fillStyle = '#1B1630'; for (let x = 0; x < W; x += 6) g.fillRect(x, 0, 3, 88);
      const d = duty(now);
      for (let i = 0; i < 18; i++) {
        const a = i / 18 * Math.PI * 2 + now * 0.9, x = 60 + Math.cos(a) * (30 + hash(i) * 28), y = 40 + Math.sin(a) * 22;
        g.fillStyle = TILE[i % 4]; g.fillRect(Math.round(x), Math.round(y), 1, 1);
      }
      const bw = 4 + d * 42;
      for (let y = 22; y < 100; y++) {
        const hw = Math.round((y - 22) / 78 * bw);
        g.fillStyle = '#3A3058';
        for (let x = 60 - hw; x <= 60 + hw; x++) if (((x + y) & 1) === 0) g.fillRect(x, y, 1, 1);
      }
      disc(g, 60, 14, 7, '#8B84A3');
      for (let i = 0; i < 10; i++) {
        const a = i / 10 * Math.PI * 2 + now * 2.2, x = Math.round(60 + Math.cos(a) * 5), y = Math.round(14 + Math.sin(a) * 5);
        g.fillStyle = Math.cos(a) > 0.3 ? '#F3E9D2' : '#5A5378'; g.fillRect(x, y, 1, 1);
      }
      g.fillStyle = '#8B84A3'; g.fillRect(60, 0, 1, 7);
      const rows = [[92, 8], [100, 9], [109, 11]], kickOn = now - kickT < 0.12;
      for (let r = 0; r < 3; r++) for (let c = 0; c < 8; c++) {
        const lit = c === step % 8 || (kickOn && r === 2), i = (c + r) % 4;
        g.fillStyle = lit ? TILE[i] : DIM[i]; g.fillRect(c * 15, rows[r][0], 14, rows[r][1] - 1);
      }
      g.fillStyle = '#F3E9D2';
      const ew = Math.round(bw * 0.9);
      for (let x = 60 - ew; x <= 60 + ew; x++) if (x % 2 === 0) g.fillRect(x, 93, 1, 1);
      spr(g, P[pose], M, 53, 70, 2, flip);
      txt(g, 'PW ' + pad(Math.round(d * 100), 2), 3, 3, '#F3E9D2');
      g.fillStyle = '#3EC1D3'; g.fillRect(3, 10, Math.round(d * 30), 2);
      idle(g, now, active);
    }
  };
}

function Reveillon() {
  let parts = [], rocket = null, burst = { x: 60, y: 30 }, last = 0, fogos = 0;
  const stars = [...Array(30)].map((_, i) => ({ x: Math.floor(hash(i) * 120), y: Math.floor(hash(i + 50) * 56) }));
  const PC = ['#E23D28', '#F2894E', '#F2C14E', '#F6DE8D', '#7BD389', '#3EC1D3', '#6B8DEE', '#B177D8', '#E0457B', '#F3E9D2', '#F2C14E', '#3EC1D3'];
  const blds = [...Array(13)].map((_, i) => ({ x: i * 10 - 2, w: 9 + Math.floor(hash(i + 5) * 3), h: 6 + Math.floor(hash(i + 15) * 20) }));
  return {
    on(e, now) {
      if (e.type === 'chord') { rocket = { t: now, x: 24 + Math.floor(hash(now) * 72), ay: 14 + Math.floor(hash(now * 2) * 22) }; fogos = (fogos + 1) % 1000; }
      if (e.type === 'lead') {
        const c = PC[e.pitch % 12];
        for (let i = 0; i < 9; i++) {
          const a = i / 9 * Math.PI * 2 + hash(now + i) * 0.6, sp = 14 + hash(now * 3 + i) * 20;
          parts.push({ x: burst.x, y: burst.y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, t: now, c });
        }
        if (parts.length > 420) parts.splice(0, parts.length - 420);
      }
    },
    draw(g, now, active) {
      const dt = Math.min(0.05, Math.max(0, now - last)); last = now;
      bands(g, ['#070A1F', '#0B1033', '#141C4A', '#232A66'], 0, 86);
      for (const s of stars) { g.fillStyle = hash(s.x + Math.floor(now * 3)) > 0.85 ? '#5A6AA8' : '#C9D2F2'; g.fillRect(s.x, s.y, 1, 1); }
      if (rocket) {
        const p = (now - rocket.t) / 0.4;
        if (p < 1) {
          const y = 86 - (86 - rocket.ay) * (1 - (1 - p) * (1 - p));
          burst = { x: rocket.x, y };
          g.fillStyle = '#F6DE8D'; g.fillRect(rocket.x, Math.round(y), 1, 2);
          g.fillStyle = '#F2894E'; for (let i = 1; i < 6; i++) if (hash(i + now * 40) > 0.4) g.fillRect(rocket.x, Math.round(y) + 2 + i, 1, 1);
        } else burst = { x: rocket.x, y: rocket.ay };
      }
      parts = parts.filter(q => now - q.t < 1);
      for (const q of parts) {
        q.vx *= Math.exp(-dt * 1.8); q.vy = q.vy * Math.exp(-dt * 1.8) + 22 * dt; q.x += q.vx * dt; q.y += q.vy * dt;
        const a = now - q.t;
        if (a > 0.65 && Math.floor(now * 20) % 2) continue;
        g.fillStyle = a < 0.08 ? '#FFFFFF' : q.c; g.fillRect(Math.round(q.x), Math.round(q.y), 1, 1);
      }
      for (const b of blds) {
        g.fillStyle = '#05061A'; g.fillRect(b.x, 86 - b.h, b.w, b.h);
        g.fillStyle = '#F2C14E';
        for (let y = 86 - b.h + 2; y < 84; y += 4) for (let x = b.x + 2; x < b.x + b.w - 1; x += 3)
          if (hash(x * 3 + y) > 0.7) g.fillRect(x, y, 1, 1);
      }
      g.fillStyle = '#0A1030'; g.fillRect(0, 86, W, 34);
      g.fillStyle = '#18245A';
      for (let y = 88; y < 120; y += 3) { const o = Math.round((now * 8 + y * 3) % 12); for (let x = -12 + o; x < W; x += 12) g.fillRect(x, y, 5, 1); }
      for (const q of parts) {
        const ry = Math.round(86 + (86 - q.y) * 0.5);
        if (ry > 86 && ry < 120 && ry % 2 === 0) { g.fillStyle = q.c; g.fillRect(Math.round(q.x + Math.sin(now * 6 + ry) * 1.5), ry, 1, 1); }
      }
      txt(g, 'FOGOS ' + pad(fogos, 3), 3, 3, '#F3E9D2');
      idle(g, now, active);
    }
  };
}

/* ---------- máquinas ---------- */
const S = s => s.split('');
const ARP_CH = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]];
const CABS = [
  { id: 'pulso', name: 'PULSO', chip: 'PULSE + TRI', game: 'CORREDOR', c: '#F2C14E', bpm: 140, scene: Corredor,
    info: '<b>Two pulses, triangle and noise.</b> A 25 % pulse on the melody, a 4-bit triangle on the bass, envelopes in steps.',
    lead: [69,0,72,0,74,76,0,74, 72,0,69,0,67,0,69,0, 69,0,72,0,74,76,0,79, 76,0,74,72,74,0,0,0],
    bass: [45,0,45,0,57,0,45,0, 43,0,43,0,55,0,43,0, 41,0,41,0,53,0,41,0, 43,0,43,0,55,0,47,0],
    drums: S('k.h.s.h.k.h.s.hhk.h.s.h.k.hks.hh'), scale: [57,60,62,64,67,69,72,74,76],
    voice(k, m, t, d) { if (k === 'lead') blip(t, m, d * 0.9, 0.2, WV.p25, 16); else blip(t, m, d * 0.95, 0.32, WV.tri); } },
  { id: 'onda', name: 'ONDA', chip: '4-BIT WAVE', game: 'SURFE', c: '#3EC1D3', bpm: 112, scene: Surfe,
    info: '<b>A 4-bit wave channel.</b> 32 samples from 0 to 15, drawn as the sea wave too.',
    lead: [62,0,0,65,0,69,0,0, 67,0,65,0,64,0,62,0, 60,0,0,64,0,67,0,0, 69,0,67,0,65,64,62,0],
    bass: [38,0,0,0,38,0,0,0, 36,0,0,0,36,0,0,0, 34,0,0,0,34,0,0,0, 36,0,0,0,33,0,0,0],
    drums: S('..h...h...h...h...h...h...h.hhh.'), scale: [57,60,62,64,65,67,69,72,74],
    voice(k, m, t, d) { if (k === 'lead') blip(t, m, d * 1.8, 0.26, WV.gb); else blip(t, m, d * 3.5, 0.3, WV.tri); } },
  { id: 'ruido', name: 'RUÍDO', chip: 'LFSR NOISE', game: 'PÊNALTI', c: '#7BD389', bpm: 128, scene: Penalti,
    info: '<b>LFSR noise</b>, long (snare) and short (metallic hi-hat), a triangle kick and a 12.5 % pulse bass.',
    bass: [33,0,0,33,0,0,45,0, 33,0,0,33,0,0,43,0, 31,0,0,31,0,0,43,0, 31,0,0,31,0,40,0,43],
    drums: S('k.h.s.h.k.hks.h.k.h.s.h.kkh.s.hs'), scale: [], keysDrums: S('kshkshksh'),
    voice(k, m, t, d) { blip(t, m, d * 0.9, 0.2, WV.p125, 10); } },
  { id: 'fm', name: 'FM', chip: '2-OP FM', game: 'PIPA', c: '#E0457B', bpm: 100, scene: Pipa,
    info: '<b>Two-operator FM.</b> A bell at ratio 3.5 on the melody; a bass at ratio 1 with a high index that falls fast.',
    lead: [0,0,72,0,0,0,79,0, 0,0,0,77,0,75,0,0, 0,0,72,0,0,0,79,0, 84,0,82,0,79,0,0,0],
    bass: [36,0,0,36,0,0,43,0, 41,0,0,41,0,0,39,0, 44,0,0,44,0,0,43,0, 41,0,0,41,0,43,0,0],
    drums: S('k......hk..k...hk......hk..k.hhh'), scale: [60,63,65,67,70,72,75,77,79],
    voice(k, m, t, d) { if (k === 'lead') fm(t, m, d * 3, 0.16, 3.5, 2.2, 0.5); else fm(t, m, d * 1.6, 0.3, 1, 3, 0.12); } },
  { id: 'pwm', name: 'PWM', chip: 'PWM + VCF', game: 'PISTA', c: '#B177D8', bpm: 124, scene: Pista,
    info: '<b>A pulse of varying width</b> from an LFO, and a resonant filter that opens on every note. Mono, with glide.',
    lead: [57,0,60,0,64,0,60,57, 0,0,55,0,57,0,0,0, 57,0,60,0,64,0,67,64, 0,0,62,0,60,0,0,0],
    drums: S('k.h.k.h.k.h.k.hhk.h.k.h.k.h.khhh'), scale: [52,55,57,60,62,64,67,69,72],
    voice(k, m, t, d) { pwmNote(t, m, d * 0.9, 0.3); } },
  { id: 'arpejo', name: 'ARPEJO', chip: 'ARP PULSE', game: 'RÉVEILLON', c: '#F2894E', bpm: 132, scene: Reveillon,
    info: '<b>Chord arpeggios</b> on a 25 % pulse, three notes per chord over two octaves, a triangle bass.',
    lead: [...Array(32)].map((_, i) => ARP_CH[Math.floor(i / 8)][i % 3] + 12 * (Math.floor(i / 3) % 2) + 12),
    bass: [...Array(32)].map((_, i) => i % 4 === 0 ? ARP_CH[Math.floor(i / 8)][0] - 12 : 0),
    drums: S('k...s...k...s...k...s...k...s.s.'), scale: [57,60,62,64,67,69,72,74,76],
    extra(i, t, push) { if (i % 8 === 0) push({ t, type: 'chord' }); },
    voice(k, m, t, d) { if (k === 'lead') blip(t, m, d * 0.85, 0.15, WV.p25, 7); else blip(t, m, d * 3.6, 0.3, WV.tri); } },
];

/* ---------- salão ---------- */
const salao = document.getElementById('salao');
const cabs = CABS.map(def => {
  const el = document.createElement('article');
  el.className = 'gab'; el.style.setProperty('--c', def.c);
  const n = String(CABS.indexOf(def) + 1).padStart(2, '0');
  el.innerHTML = `<div class="marquee"><span class="hud">CABINET ${n} // ${def.chip}</span><b>${def.name}</b><span class="game">${def.game}</span></div>
    <div class="tube"><div class="screen"><canvas width="120" height="120" role="img" aria-label="${def.game}, the ${def.name} cabinet's game"></canvas></div></div>
    <p class="info">${def.info}</p>
    <button type="button" class="coin" aria-pressed="false">INSERT COIN</button>`;
  salao.append(el);
  const cv = el.querySelector('canvas');
  const cab = Object.assign({}, def, { el, g: cv.getContext('2d'), btn: el.querySelector('.coin'),
    scene: def.scene(), step: 0, next: 0, q: [], visible: true, drawn: false });
  cab.btn.addEventListener('click', () => toggle(cab));
  el.querySelector('.screen').addEventListener('click', () => toggle(cab));
  return cab;
});
let active = null;
const status = document.getElementById('status'), teclado = document.getElementById('teclado');
const tecladoL = document.getElementById('teclado-l');
function toggle(cab) {
  audio();
  if (active === cab) active = null; else active = cab;
  if (!active && pwm) pwm.env.gain.setTargetAtTime(0, ac.currentTime, 0.02);
  for (const c of cabs) {
    const on = c === active;
    c.el.classList.toggle('on', on); c.btn.setAttribute('aria-pressed', String(on));
    c.btn.textContent = on ? 'TAKE COIN BACK' : 'INSERT COIN';
  }
  status.textContent = active ? `PLAYING // ${active.name} · ${active.game}` : 'NO COIN // ATTRACT MODE';
  teclado.setAttribute('aria-disabled', String(!active));
  tecladoL.textContent = active ? `PLAY ALONG // ${active.name} // KEYS A S D F G H J K L` : 'INSERT A COIN TO PLAY ALONG';
}
const clock = () => ac ? ac.currentTime : performance.now() / 1000;
function runStep(c, i, t, snd) {
  const d = 60 / c.bpm / 4, push = e => c.q.push(e);
  const L = c.lead && c.lead[i], B = c.bass && c.bass[i], D = c.drums && c.drums[i];
  if (L) { if (snd) c.voice('lead', L, t, d); push({ t, type: 'lead', pitch: L }); }
  if (B) { if (snd) c.voice('bass', B, t, d); push({ t, type: 'bass', pitch: B }); }
  if (D && D !== '.') { if (snd) drum(D, t); push({ t, type: D === 'k' ? 'kick' : D === 's' ? 'snare' : 'hat' }); }
  if (c.extra) c.extra(i, t, push);
  push({ t, type: 'step', step: i });
}
function seq() {
  const now = clock();
  for (const c of cabs) {
    const snd = c === active;
    if (!snd && !motionOn()) { c.q.length = 0; c.next = now; continue; }
    if (c.next < now - 0.5 || c.next > now + 1) c.next = now;
    while (c.next < now + 0.12) { runStep(c, c.step, c.next, snd); c.next += 60 / c.bpm / 4; c.step = (c.step + 1) % 32; }
  }
}
setInterval(seq, 25);

/* ---------- movimento ---------- */
const reduce = matchMedia('(prefers-reduced-motion: reduce)');
let pref = null;
try { pref = sessionStorage.getItem('fliperama-motion'); } catch (e) {}
const motionOn = () => pref === null ? !reduce.matches : pref === 'on';
const mbtn = document.getElementById('motion');
function syncMotion() { mbtn.textContent = motionOn() ? 'PAUSE MOTION' : 'PLAY MOTION'; mbtn.setAttribute('aria-pressed', String(!motionOn())); }
mbtn.addEventListener('click', () => { pref = motionOn() ? 'off' : 'on'; try { sessionStorage.setItem('fliperama-motion', pref); } catch (e) {} syncMotion(); });
reduce.addEventListener('change', syncMotion); syncMotion();
if ('IntersectionObserver' in window) {
  const io = new IntersectionObserver(es => es.forEach(e => { const c = cabs.find(x => x.el === e.target); if (c) c.visible = e.isIntersecting; }));
  cabs.forEach(c => io.observe(c.el));
}
/* the hero screen: a second RÉVEILLON fed by the ARPEJO cabinet's own events */
const heroCv = document.getElementById('hero-screen');
const hero = heroCv ? { g: heroCv.getContext('2d'), scene: Reveillon(), drawn: false } : null;
const heroCab = cabs.find(c => c.id === 'arpejo');
function frame() {
  const now = clock();
  for (const c of cabs) {
    const live = c === active || motionOn();
    while (c.q.length && c.q[0].t <= now) {
      const e = c.q.shift();
      if (live) c.scene.on(e, now);
      if (hero && c === heroCab && (live || motionOn())) hero.scene.on(e, now);
    }
    if ((live && c.visible) || !c.drawn) { c.scene.draw(c.g, now, c === active); c.drawn = true; }
  }
  if (hero && (motionOn() || heroCab === active || !hero.drawn)) { hero.scene.draw(hero.g, now, heroCab === active); hero.drawn = true; }
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

/* ---------- teclado ---------- */
const KEYS = 'asdfghjkl', keysEl = document.getElementById('keys');
const keyBtns = [...KEYS].map((k, i) => {
  const b = document.createElement('button'); b.type = 'button'; b.className = 'key'; b.textContent = k.toUpperCase();
  b.setAttribute('aria-label', 'Key ' + (i + 1));
  b.addEventListener('pointerdown', ev => { ev.preventDefault(); play(i); });
  keysEl.append(b); return b;
});
function play(i) {
  if (!active) return;
  audio();
  const t = ac.currentTime + 0.005, d = 60 / active.bpm / 4 * 2;
  if (active.keysDrums) { const ch = active.keysDrums[i]; drum(ch, t); active.scene.on({ t, type: ch === 'k' ? 'kick' : ch === 's' ? 'snare' : 'hat' }, t); }
  else {
    const m = active.scale[i]; active.voice('lead', m, t, d); active.scene.on({ t, type: 'lead', pitch: m }, t);
    if (active.id === 'arpejo' && i % 3 === 0) active.scene.on({ t, type: 'chord' }, t);
  }
  const b = keyBtns[i]; b.classList.add('hit'); setTimeout(() => b.classList.remove('hit'), 120);
}
addEventListener('keydown', e => {
  if (e.repeat || e.metaKey || e.ctrlKey || e.altKey) return;
  const i = KEYS.indexOf(e.key.toLowerCase());
  if (i >= 0 && active) { e.preventDefault(); play(i); }
});

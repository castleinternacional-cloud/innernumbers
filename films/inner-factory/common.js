// Inner Factory · shared frame, camera, overlays and boot for the five vertical episodes (1080x1920).
// Each episode file registers EPS[n] = { id, setup(at), camera(t), world(t, cam), screen(t, cam), stub(t) }.
const SW = 1080, SH = 1920;
const EPS = {};
let ZL = 1, VB = [0, 0, SW, SH], EP = null, WORDS = [], SUBS = [], EVS = [];

// ---------- camera ----------
const toScreen = (cam, x, y) => [SW / 2 + (x - cam.x) * cam.z, SH / 2 + (y - cam.y) * cam.z];
const mixc = (a, b, u) => ({ x: lerp(a.x, b.x, u), y: lerp(a.y, b.y, u), z: Math.exp(lerp(Math.log(a.z), Math.log(b.z), u)) });
// keyframed camera: keys = [[t, {x,y,z}, ease?], ...]; holds between keys unless the next key says otherwise
function camKeys(keys, t) {
  if (t <= keys[0][0]) return { ...keys[0][1] };
  for (let i = 0; i < keys.length - 1; i++) {
    const [a, A] = keys[i], [b, B, e] = keys[i + 1];
    if (t < b) return mixc(A, B, (e || eio)(seg(t, a, b)));
  }
  return { ...keys[keys.length - 1][1] };
}
const shake = (t, a, d, amp) => pulse(t, a, d) * amp * Math.sin(t * 90);

// ---------- small parts shared by episodes ----------
function numOn(cx, cy, n, on, pop = 0, r = 24) {
  if (ZL < .2) return;
  const k = 1 + .28 * pop;
  out(`<g transform="translate(${f1(cx)} ${f1(cy)}) scale(${f1(k * 100) / 100})">`);
  shape(E(0, 0, r), on > .5 ? C.sun : C.cream, 2.8);
  txt(0, r * 0.42, n, r * 1.25, { fam: FONT.en, w: 900, anchor: 'middle', fill: on > .5 ? C.ink : '#8A8F9F' });
  out('</g>');
}
// plaque with a station number that lights (on: 0/1, pop: 0..1 bounce)
function plaqueN(x, y, en, sub, n, on, pop, size = 36) {
  const w = plaque(x + 56, y, en, sub, { size });
  const h = Math.max(size, 28) * 1.42;
  if (n) numOn(x + 24, y + h / 2, n, on, pop);
  return w + 56;
}
// station state from its arrival time: on (0/1) and pop
const st = (t, at) => [t >= at ? 1 : 0, pulse(t, at, .35)];
function belt2(a, b, k = 1, ph = 0) {
  const len = Math.hypot(b[0] - a[0], b[1] - a[1]);
  gline([a, b], 22 * k + 6 * KS, C.ink); gline([a, b], 18 * k, '#4A4D5C');
  if (ZL < .2) return;
  const r = 6.5 * k;
  for (let s = 8; s <= len - 6; s += 32 * k) {
    const u = s / len, x = a[0] + (b[0] - a[0]) * u, y = a[1] + (b[1] - a[1]) * u;
    out(`<circle cx="${f1(x)}" cy="${f1(y)}" r="${r}" fill="${C.wallD}" stroke="${C.ink}" stroke-width="${f1(2 * KS)}"/>`);
    out(`<path d="M${f1(x - Math.cos(ph) * r * .7)} ${f1(y - Math.sin(ph) * r * .7)}L${f1(x + Math.cos(ph) * r * .7)} ${f1(y + Math.sin(ph) * r * .7)}" stroke="${C.ink}" stroke-width="${f1(1.6 * KS)}"/>`);
  }
}
function detail(lo, hi, fn) { const o = ss(seg(ZL, lo, hi)); if (o <= .01) return; if (o < .99) out(`<g opacity="${f1(o * 100) / 100}">`); fn(); if (o < .99) out('</g>'); }
function inView(x0, y0, x1, y1) { return !(x1 < VB[0] || x0 > VB[2] || y1 < VB[1] || y0 > VB[3]); }
function drop(x, y, r = 12, col = C.teal, colL = C.tealL) {
  const cy = y - r, tip = cy - 1.75 * r;
  shape(`M${f1(x)} ${f1(tip)}C${f1(x + r * .3)} ${f1(cy - r * 1.1)} ${f1(x + r)} ${f1(cy - r * .6)} ${f1(x + r)} ${f1(cy)}A${r} ${r} 0 0 1 ${f1(x - r)} ${f1(cy)}C${f1(x - r)} ${f1(cy - r * .6)} ${f1(x - r * .3)} ${f1(cy - r * 1.1)} ${f1(x)} ${f1(tip)}Z`, col, 2.4);
  out(`<circle cx="${f1(x - r * .35)}" cy="${f1(cy - r * .1)}" r="${f1(r * .26)}" fill="${colL}"/>`);
}
// soft blob (mucus, paste): x,y = bottom centre
function blob(x, y, k = 1, wob = 0, col = C.olive, colL = C.oliveL) {
  const a = 1 + .08 * Math.sin(wob), b = 1 - .08 * Math.sin(wob);
  shape(`M${f1(x - 26 * k * a)} ${f1(y)}Q${f1(x - 30 * k * a)} ${f1(y - 26 * k * b)} ${f1(x - 8 * k)} ${f1(y - 24 * k * b)}Q${f1(x + 2 * k)} ${f1(y - 40 * k * b)} ${f1(x + 18 * k)} ${f1(y - 26 * k * b)}Q${f1(x + 34 * k * a)} ${f1(y - 20 * k)} ${f1(x + 28 * k * a)} ${f1(y)}Z`, col, 2.4);
  out(`<circle cx="${f1(x - 6 * k)}" cy="${f1(y - 14 * k)}" r="${f1(4 * k)}" fill="${colL}"/>`);
}
// flip-board counter bolted to a machine: digits roll into place right-to-left; value string (e.g. "11,000")
function flipboard(x, y, value, unit, p, o = {}) {
  const size = o.size || 64, cw = size * .62, h = size * 1.25;
  const chars = value.split(''); const w = chars.length * (cw + 6) + 24;
  shadow(R(x, y, w, h, 6), 10, 8);
  shape(R(x, y, w, h, 6), C.ink, 3);
  chars.forEach((ch, i) => {
    const cx = x + 12 + i * (cw + 6);
    const isD = /[0-9]/.test(ch);
    if (isD) shape(R(cx, y + 8, cw, h - 16, 3), '#2C3146', 0);
    const lock = clamp(p * (chars.length + 2) - (chars.length - 1 - i));   // lock right-to-left
    let show = ch;
    if (isD && lock < 1) show = String(Math.floor(hash(i * 13 + Math.floor((o.t || 0) * 24)) * 10));
    if (p > 0) txt(cx + cw / 2, y + h / 2 + size * .36, show, size, { fam: FONT.en, w: 900, anchor: 'middle', fill: lock >= 1 ? C.sun : C.cream });
  });
  if (unit) txt(x + w + 14, y + h / 2 + (o.us || 34) * .36, unit, o.us || 34, { fam: FONT.en, w: 800 });
  return w;
}
// body cut-away: ground fill + thick wall band with ink on both sides
function bodyWall(d) {
  shadow(d, 20, 16, C.shade);
  fillOnly(d, C.ground);
  out(`<path d="${d}" fill="none" stroke="${C.ink}" stroke-width="${f1(56 + 8 * KS)}" stroke-linejoin="round"/>`);
  out(`<path d="${d}" fill="none" stroke="${C.blush}" stroke-width="56" stroke-linejoin="round"${tr(C.blush)}/>`);
}
// a break in the wall (intake/hatch): paint over the band, cap both ends
function wallGap(x, y, w, h) {
  fillOnly(R(x, y, w, h), C.ground);
  line([[x, y], [x + w, y]], 3); line([[x, y + h], [x + w, y + h]], 3);
}

// ---------- screen overlays ----------
// work-ticket subtitles: bottom left (above the Shorts caption zone), cream ticket, ink frame, stub with the current station number
function subtitles(t) {
  for (const s of SUBS) {
    if (t < s.t0 - .01 || t > s.t1 + .01) continue;
    const pin = eo(seg(t, s.t0, s.t0 + .18)), pout = ei(seg(t, s.t1 - .12, s.t1));
    const size = 46, lines = s.lines;
    const wmax = Math.max(...lines.map(l => tw(l, size, 700, FONT.sans) + l.length * .4));
    const stub = 82, pad = 26, w = stub + pad + wmax + pad, h = 40 + lines.length * 60;
    const x = 44, y = SH - 470 - h + (1 - pin) * 34 + pout * 40;
    const op = Math.min(pin, 1 - pout);
    const n = EP.stub ? EP.stub(s.t0 + .05) : 0;
    out(`<g data-sub="1" opacity="${f1(op * 100) / 100}">`);
    out(`<path d="${R(x, y, w, h, 5)}" fill="${C.ground}" opacity=".28" transform="translate(8 7)"/>`);
    shape(R(x, y, w, h, 5), C.cream, 3);
    fillOnly(R(x + 2, y + 2, stub - 2, h - 4, 3), n ? C.sun : C.red);
    out(`<path d="M${x + stub} ${y + 8}V${y + h - 8}" stroke="${C.ink}" stroke-width="2.6" stroke-dasharray="5 6"/>`);
    shape(E(x + stub / 2, y + h / 2, 25), C.cream, 2.8);
    if (n) txt(x + stub / 2, y + h / 2 + 11, String(n), 32, { fam: FONT.en, w: 900, anchor: 'middle' });
    else { line([[x + stub / 2, y + h / 2], [x + stub / 2, y + h / 2 - 15]], 3.4); line([[x + stub / 2, y + h / 2], [x + stub / 2 + 11, y + h / 2 + 5]], 3.4); }
    shape(R(x, y, w, h, 5), null, 3);
    lines.forEach((l, i) => txt(x + stub + pad, y + 64 + i * 60, l, size, { fam: FONT.sans, w: 700 }));
    out('</g>');
  }
}
// porthole POV: circular mask grows from a world point to the screen centre; inner(t) draws a 1080x1080 scene centred at 540,540
function porthole(t, cam, wx, wy, a0, a1, b0, b1, inner, R1 = 440) {
  if (t < a0 || t > b1) return;
  const [px, py] = toScreen(cam, wx, wy);
  const r0 = 30 * cam.z;
  const r = t < a1 ? lerp(r0, R1, ei(seg(t, a0, a1))) : t < b0 ? R1 : lerp(R1, r0, eo(seg(t, b0, b1)) ** .8);
  const cx = t < a1 ? lerp(px, SW / 2, eio(seg(t, a0, a1))) : t < b0 ? SW / 2 : lerp(SW / 2, px, eo(seg(t, b0, b1)));
  const cy = t < a1 ? lerp(py, SH * .42, eio(seg(t, a0, a1))) : t < b0 ? SH * .42 : lerp(SH * .42, py, eo(seg(t, b0, b1)));
  const id = 'pov' + (UID++);
  out(`<clipPath id="${id}"><circle cx="${f1(cx)}" cy="${f1(cy)}" r="${f1(r)}"/></clipPath>`);
  out(`<g clip-path="url(#${id})">`);
  const KS0 = KS; KS = 1;
  out(`<g transform="translate(${f1(cx)} ${f1(cy)}) scale(${f1(R1 / 540 * 100) / 100}) translate(-540 -540)">`);
  inner(t);
  out('</g></g>');
  KS = KS0;
  out(`<circle cx="${f1(cx)}" cy="${f1(cy)}" r="${f1(r + 15)}" fill="none" stroke="${C.ink}" stroke-width="36"/>`);
  out(`<circle cx="${f1(cx)}" cy="${f1(cy)}" r="${f1(r + 15)}" fill="none" stroke="${C.sun}" stroke-width="28"/>`);
  for (let i = 0; i < 24; i++) { const a = i / 24 * Math.PI * 2; out(`<circle cx="${f1(cx + Math.cos(a) * (r + 15))}" cy="${f1(cy + Math.sin(a) * (r + 15))}" r="3.6" fill="${C.ink}"/>`); }
}
function speedLines(t, dirY) {
  const v = Math.abs(dirY); if (v < .2) return;
  const op = clamp((v - .2) / .8) * .5;
  for (let i = 0; i < 26; i++) {
    const x = hash(i * 3.1) * SW, len = 160 + hash(i * 7.7) * 320, y = ((hash(i * 1.3) * 2300 + t * 3200 * Math.sign(-dirY)) % 2300 + 2300) % 2300 - 200;
    out(`<path d="M${f1(x)} ${f1(y)}v${f1(len)}" stroke="${C.cream}" stroke-width="${2 + (i % 3)}" stroke-linecap="round" opacity="${f1(op)}"/>`);
  }
}

// ---------- one frame ----------
function world(t, cam) {
  ZL = cam.z;
  KS = cam.z < 1 ? Math.pow(cam.z, -0.6) : Math.pow(cam.z, -0.75);
  const m = 200 / cam.z;
  VB = [cam.x - SW / 2 / cam.z - m, cam.y - SH / 2 / cam.z - m, cam.x + SW / 2 / cam.z + m, cam.y + SH / 2 / cam.z + m];
  out(`<g transform="translate(${SW / 2} ${SH / 2}) scale(${cam.z.toFixed(5)}) translate(${(-cam.x).toFixed(2)} ${(-cam.y).toFixed(2)})">`);
  EP.world(t, cam);
  out('</g>');
}
function frame(t) {
  S.length = 0; UID = 0;
  out(`<svg xmlns="http://www.w3.org/2000/svg" width="${SW}" height="${SH}" viewBox="0 0 ${SW} ${SH}">`);
  out(`<rect width="${SW}" height="${SH}" fill="${C.paper}"/>`);
  const cam = EP.camera(t);
  const fast = EP.fast && EP.fast(t);
  if (fast) {
    const dt = 1 / 48, a = EP.camera(t - dt), b = EP.camera(t + dt);
    const vx = (b.x - a.x) * cam.z / 2, vy = (b.y - a.y) * cam.z / 2;
    const sx = Math.min(26, Math.abs(vx) * .35), sy = Math.min(26, Math.abs(vy) * .35);
    out(`<defs><filter id="mb" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="${f1(sx)} ${f1(sy)}"/></filter></defs>`);
    out(`<g filter="url(#mb)">`); world(t, cam); out('</g>');
    speedLines(t, vy / 60);
  } else world(t, cam);
  KS = 1; ZL = 1;
  if (EP.screen) EP.screen(t, cam);
  subtitles(t);
  out('</svg>');
  return S.join('\n');
}

// ---------- subtitles from word timings ----------
function buildSubs(words, dur) {
  const chunks = []; let cur = [];
  const flush = () => { if (cur.length) chunks.push(cur); cur = []; };
  words.forEach((w, i) => {
    cur.push(w);
    const txtc = cur.map(x => x.w).join(' ');
    const end = /[.?!]$/.test(w.w), comma = /[,:;]$/.test(w.w);
    if (end || (comma && cur.length >= 3) || txtc.length > 30 || cur.length >= 6) flush();
  });
  flush();
  const subs = chunks.map(c => ({ t0: Math.max(0, c[0].t0 - .08), t1: c[c.length - 1].t1 + .25, text: c.map(x => x.w).join(' ') }));
  for (let i = 0; i < subs.length; i++) {
    const nx = subs[i + 1];
    subs[i].t1 = nx ? Math.min(Math.max(subs[i].t1, subs[i].t0 + 1.0), nx.t0 - .04) : Math.min(dur - .05, Math.max(subs[i].t1 + .4, subs[i].t0 + 1.8));
  }
  // wrap into lines of ≤ 18 chars
  for (const s of subs) {
    const ws = s.text.split(' '), lines = ['']; for (const w of ws) { const L = lines[lines.length - 1]; if ((L + ' ' + w).trim().length > 18 && L) lines.push(w); else lines[lines.length - 1] = (L + ' ' + w).trim(); }
    s.lines = lines;
  }
  return subs;
}
// at('word', k): time of the k-th (0-based) word starting with that text (case-insensitive, punctuation ignored)
function makeAt(words) {
  return (w, k = 0, end = false) => {
    const norm = s => s.toLowerCase().replace(/[^a-z0-9']/g, '');
    let hits = words.filter(x => norm(x.w) === norm(w));
    if (!hits.length) hits = words.filter(x => norm(x.w).startsWith(norm(w)));
    const h = hits[Math.min(k, hits.length - 1)];
    if (!h) throw new Error('word not found: ' + w);
    return end ? h.t1 : h.t0;
  };
}
const ev = (t, type, o = {}) => EVS.push({ t: Math.round(t * 1000) / 1000, type, ...o });

// ---------- paper grain (made once, laid on top) ----------
function makeGrain() {
  const cv = document.createElement('canvas'); cv.width = SW; cv.height = SH;
  const g = cv.getContext('2d'), im = g.createImageData(SW, SH), d = im.data;
  let s = 7; const rnd = () => { s = (s * 16807) % 2147483647; return s / 2147483647; };
  for (let i = 0; i < d.length; i += 4) { const v = 255 - rnd() * 30; d[i] = v; d[i + 1] = v - 2; d[i + 2] = v - 5; d[i + 3] = 255; }
  g.putImageData(im, 0, 0);
  g.globalAlpha = .05; g.strokeStyle = '#6B5A40';
  for (let i = 0; i < 1100; i++) { const x = rnd() * SW, y = rnd() * SH, l = 20 + rnd() * 80; g.lineWidth = .6 + rnd(); g.beginPath(); g.moveTo(x, y); g.lineTo(x + l, y + (rnd() - .5) * 4); g.stroke(); }
  cv.id = 'grain'; document.body.appendChild(cv);
}

async function boot() {
  const q = new URLSearchParams(location.search), n = +(q.get('ep') || 1);
  EP = EPS[n];
  const raw = await (await fetch(`voice/${EP.id}.words.json`)).json();
  WORDS = [];   // merge whisper's split numbers ("11" + ",000", "8" + ".2")
  for (const w of raw) { const L = WORDS[WORDS.length - 1]; if (L && /^[,.][0-9]/.test(w.w) && /[0-9]$/.test(L.w)) { L.w += w.w; L.t1 = w.t1; } else WORDS.push({ ...w }); }
  const meta = await (await fetch(`voice/durations.json`)).json();
  const vdur = meta[EP.id];
  window.DUR = Math.round((vdur + (EP.tail || 1.4)) * 24) / 24;
  const at = makeAt(WORDS);
  EP.setup(at, window.DUR);
  SUBS = buildSubs(WORDS, window.DUR);
  window.EV = EVS;
  window.SUBS = SUBS;
  await Promise.all(['900', '800', '700'].map(w => document.fonts.load(`${w} 40px BSD`, 'A')).concat(['800', '700', '600'].map(w => document.fonts.load(`${w} 40px ARC`, 'A'))));
  await document.fonts.ready;
  makeGrain();
  window.render = t => { document.getElementById('stage').innerHTML = frame(Math.min(t, window.DUR - .001)); };
  window.TEXTS = t => {
    window.render(t);
    const res = [];
    for (const el of document.querySelectorAll('#stage text')) {
      if (el.closest('[data-sub]')) continue;
      let op = 1;
      for (let nd = el; nd && nd.id !== 'stage'; nd = nd.parentElement) { const o = nd.getAttribute('opacity'); if (o != null) op *= +o; }
      if (op < .5) continue;
      const r = el.getBoundingClientRect();
      if (r.height < 16 || r.right <= 0 || r.bottom <= 0 || r.left >= SW || r.top >= SH) continue;
      const s = el.textContent.trim(); if (!s) continue;
      res.push({ id: s, text: s, x0: r.left, y0: r.top, x1: r.right, y1: r.bottom, pass: /^[0-9,.]$/.test(s) });
    }
    return res;
  };
  window.render(0);
  window.READY = true;
}

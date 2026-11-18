// E2 · 120 DAYS — a standing body cut away from the front: the delivery route (lungs ↔ muscle) at the chest,
// the inspection slit (spleen) and the scrap yard (macrophages) in the abdomen, the stamping plant (bone marrow) in the pelvis.
// Red = blood, ochre = iron (and numbers), teal = oxygen.
(() => {
  let K = {};
  const BODY = 'M650 -560C470 -560 380 -430 380 -280C380 -150 450 -60 540 -20L540 40C260 70 60 160 40 400L40 2500C40 2620 110 2690 190 2720L210 3360C220 3440 560 3440 570 3360L600 2800L700 2800L730 3360C740 3440 1080 3440 1090 3360L1110 2720C1190 2690 1260 2620 1260 2500L1260 400C1240 160 1040 70 760 40L760 -20C850 -60 920 -150 920 -280C920 -430 830 -560 650 -560Z';
  const ROUTE = { x: 140, y: 280, w: 1020, h: 480 };
  const SPL = { x: 140, y: 920, w: 1020, h: 420 };
  const SCR = { x: 140, y: 1460, w: 1020, h: 380 };
  const MAR = { x: 140, y: 1980, w: 1020, h: 460 };
  const PRESS = [420, MAR.y + 250];           // stamping press (cell comes out at its foot)
  const SLIT = 650;                           // x of the spleen slit

  function rbc(x, y, k = 1, o = {}) {
    const sx = (o.sx || 1) * k, sy = (o.sy || 1) * k;
    out(`<g transform="translate(${f1(x)} ${f1(y)}) rotate(${f1(o.rot || 0)}) scale(${f1(sx * 100) / 100} ${f1(sy * 100) / 100})">`);
    const d = 'M-40 0C-40 -22 -18 -24 0 -13C18 -24 40 -22 40 0C40 22 18 24 0 13C-18 24 -40 22 -40 0Z';
    shape(d, o.stiff ? C.redD : C.red, 2.6 / Math.max(.6, k));
    out(`<path d="M-30 -8C-26 -16 -16 -16 -10 -11" fill="none" stroke="${C.redL}" stroke-width="4" stroke-linecap="round"/>`);
    if (o.crate) shape(R(-16, -50, 32, 26, 3), o.crate, 2.2);
    out('</g>');
    if (o.ticket) {
      const s = k * .9, tx = x + 10 * k, ty = y - 26 * k;
      line([[tx, ty], [tx, ty - 46 * s]], 2.4);
      const w = (tw(o.ticket, 30, 800, FONT.en) + 24) * s, h = 40 * s;
      shadow(R(tx + 2, ty - 46 * s - h, w, h, 3), 5, 4);
      shape(R(tx + 2, ty - 46 * s - h, w, h, 3), C.cream, 2.4); fillOnly(R(tx + 2, ty - 46 * s - h, 8 * s, h), o.stiff ? C.ink : C.red);
      txt(tx + 2 + 8 * s + (w - 8 * s) / 2, ty - 46 * s - h * .28, o.ticket, 30 * s, { fam: FONT.en, w: 900, anchor: 'middle' });
    }
    if (o.stencil) txt(x, y + 62 * k, o.stencil, 34 * k, { fam: FONT.en, w: 900, anchor: 'middle', fill: C.ink });
  }

  // the hero cell's path
  function hero(t) {
    const born = { x: PRESS[0] + 130, y: PRESS[1] + 10 };
    if (t < K.out) return null;
    if (t < K.up0) { const u = eo(seg(t, K.out, K.out + .8)); return { x: lerp(PRESS[0], born.x, u), y: born.y, k: lerp(.6, 1.4, u) }; }
    if (t < K.job) {   // rides the red vessel up the right side
      const u = eio(seg(t, K.up0, K.job));
      if (u < .25) return { x: lerp(born.x, 1190, u / .25), y: born.y, k: 1.4 };
      return { x: 1190, y: lerp(born.y, ROUTE.y + ROUTE.h - 90, (u - .25) / .75), k: 1.4 };
    }
    if (t < K.but) {   // route: shuttles left <-> right, faster each lap
      const p = (t - K.job) / (K.but - K.job);
      const laps = 3.5, ph = Math.pow(p, 1.6) * laps;
      const f = ph % 1, dir = Math.floor(ph) % 2;
      const x = dir === 0 ? lerp(1040, 260, eio(f)) : lerp(260, 1040, eio(f));
      return { x, y: ROUTE.y + ROUTE.h - 90, k: 1.4, crate: (dir === 0 ? f > .5 : f < .5) ? C.teal : '#9A9CA6' };
    }
    if (t < K.down0) return { x: 260, y: ROUTE.y + ROUTE.h - 90, k: 1.4 };
    if (t < K.arrive) {   // down the left vessel into the spleen, toward the slit
      const u = eio(seg(t, K.down0, K.arrive));
      if (u < .45) return { x: lerp(260, 110, u / .45), y: ROUTE.y + ROUTE.h - 90, k: 1.4 };
      if (u < .8) return { x: 110, y: lerp(ROUTE.y + ROUTE.h - 90, SPL.y + SPL.h - 120, (u - .45) / .35), k: 1.4 };
      return { x: lerp(110, SLIT - 90, (u - .8) / .2), y: SPL.y + SPL.h - 120, k: 1.4 };
    }
    if (t < K.taken) return { x: SLIT - 90 + Math.sin(t * 30) * 2 * pulse(t, K.arrive, .4), y: SPL.y + SPL.h - 120, k: 1.4 };
    if (t < K.taken + .7) { const u = eio(seg(t, K.taken, K.taken + .7)); return { x: lerp(SLIT - 90, 600, u), y: lerp(SPL.y + SPL.h - 120, SCR.y + 170, u), k: 1.4, claw: 1 }; }
    return null;   // taken apart
  }

  function drawWorld(t) {
    bodyWall(BODY);
    // vessels: red loop up the right side, down the left side; ochre iron pipe from the scrap yard to the marrow
    const red = rpoly([[PRESS[0] + 200, PRESS[1] + 10], [1190, PRESS[1] + 10], [1190, ROUTE.y + ROUTE.h - 90]], 40);
    pipe(null, 44, C.red, C.redL, { d: red });
    const redL = rpoly([[200, ROUTE.y + ROUTE.h - 90], [110, ROUTE.y + ROUTE.h - 90], [110, SPL.y + SPL.h - 120], [200, SPL.y + SPL.h - 120]], 40);
    pipe(null, 44, C.red, C.redL, { d: redL });
    const iron = rpoly([[860, SCR.y + SCR.h - 70], [860, MAR.y + 120], [PRESS[0] + 40, MAR.y + 120]], 40);
    pipe(null, 34, C.sun, C.sunL, { d: iron });

    // ---------- chest: the delivery route ----------
    if (inView(ROUTE.x - 60, ROUTE.y - 60, ROUTE.x + ROUTE.w + 60, ROUTE.y + ROUTE.h + 60)) {
      const r = room(ROUTE.x, ROUTE.y, ROUTE.w, ROUTE.h, C.teal);
      belt2([200, ROUTE.y + ROUTE.h - 60], [1100, ROUTE.y + ROUTE.h - 60], 1.1, -t * 5);
      // two docks: OXYGEN (lungs, left) and MUSCLE (right)
      shape(R(190, ROUTE.y + 60, 230, 150, 6), C.tealL, 3); txt(305, ROUTE.y + 150, 'LUNGS', 40, { fam: FONT.en, w: 900, anchor: 'middle' });
      for (let i = 0; i < 3; i++) shape(R(210 + i * 64, ROUTE.y + 220, 46, 40, 3), C.teal, 2.2);
      shape(R(880, ROUTE.y + 60, 230, 150, 6), C.blushL, 3); txt(995, ROUTE.y + 150, 'MUSCLE', 40, { fam: FONT.en, w: 900, anchor: 'middle' });
      for (let i = 0; i < 3; i++) shape(R(900 + i * 64, ROUTE.y + 220, 46, 40, 3), '#9A9CA6', 2.2);
      tag(330, ROUTE.y + 290, 'OXYGEN', '', C.teal, { size: 30 });
      tag(720, ROUTE.y + 290, 'CO2', '', '#9A9CA6', { size: 30 });
      // day counter (time compresses on the dial)
      const day = t < K.job ? 1 : t < K.but ? Math.round(lerp(1, 119, Math.pow(seg(t, K.job, K.but), 1.3))) : t < K.v120 ? 119 : 120;
      shape(R(470, ROUTE.y + 70, 340, 120, 6), C.ink, 3);
      txt(640, ROUTE.y + 160, 'DAY ' + String(day).padStart(3, '0'), 76, { fam: FONT.en, w: 900, anchor: 'middle', fill: day >= 120 ? C.red : C.sun });
      worker(470, r.fl, { s: 1.4, cap: C.teal, front: [lerp(80, 150, pulse(t % 1.2, .2, .5)), 10], back: [30, 0] });
      worker(830, r.fl, { s: 1.4, flip: true, cap: C.red, front: [lerp(80, 150, pulse((t + .6) % 1.2, .2, .5)), 10], back: [30, 0] });
      const [on, pop] = st(t, K.job);
      plaqueN(r.x + 20, ROUTE.y - 30, 'DELIVERY ROUTE', 'BLOOD VESSELS', 2, on, pop, 36);
    }

    // ---------- spleen: the inspection slit ----------
    if (inView(SPL.x - 60, SPL.y - 60, SPL.x + SPL.w + 60, SPL.y + SPL.h + 60)) {
      const r = room(SPL.x, SPL.y, SPL.w, SPL.h, C.red);
      const fy = SPL.y + SPL.h - 120;
      belt2([180, fy + 34], [1110, fy + 34], 1.0, -t * 5);
      // the wall with a narrow slit
      shape(R(SLIT - 22, SPL.y + 16, 44, fy - 70 - SPL.y), C.blush, 3);
      shape(R(SLIT - 22, fy + 22, 44, SPL.y + SPL.h - 16 - fy - 22), C.blush, 3);
      // young bendy cells squeezing through (deform to pass)
      if (t > K.young - .6 && t < K.arrive + .3) for (let i = 0; i < 4; i++) {
        const q = ((t - K.young + .6) * .55 + i / 4) % 1;
        const x = lerp(250, 1060, q), d = Math.abs(x - SLIT);
        const sq = clamp(1 - d / 120);
        rbc(x, fy, 1.1, { sx: 1 - .62 * sq, sy: 1 + .55 * sq });
      }
      // gatekeeper with STOP sign
      const up = ss(seg(t, K.stopped - .1, K.stopped + .08)) * (1 - ss(seg(t, K.taken - .2, K.taken)));
      worker(SLIT + 120, r.fl, { s: 1.5, cap: C.red, front: [lerp(30, 175, up), lerp(0, 10, up)], back: [20, 0],
        prop: h => { if (!h || up < .2) return; line([[h[0], h[1]], [h[0], h[1] - 80]], 4); const sx = h[0], sy = h[1] - 120; let d = ''; for (let i = 0; i < 8; i++) { const a = (i + .5) / 8 * Math.PI * 2; d += (i ? 'L' : 'M') + f1(sx + Math.cos(a) * 46) + ' ' + f1(sy + Math.sin(a) * 46); } shape(d + 'Z', C.red, 3); txt(sx, sy + 11, 'STOP', 30, { fam: FONT.en, w: 900, anchor: 'middle', fill: C.cream }); } });
      const [on, pop] = st(t, K.insp);
      plaqueN(r.x + 20, SPL.y - 30, 'INSPECTION SLIT', 'SPLEEN', 3, on, pop, 36);
    }

    // ---------- scrap yard: macrophages take the old cell apart into colours ----------
    if (inView(SCR.x - 60, SCR.y - 60, SCR.x + SCR.w + 60, SCR.y + SCR.h + 60)) {
      const r = room(SCR.x, SCR.y, SCR.w, SCR.h, C.sun);
      // claw crane on a gantry
      line([[200, SCR.y + 60], [1100, SCR.y + 60]], 8);
      const cx = 600, drop = ss(seg(t, K.taken - .3, K.taken)) * (1 - ss(seg(t, K.taken + .8, K.taken + 1.3)));
      line([[cx, SCR.y + 60], [cx, SCR.y + 90 + drop * 30]], 3);
      shape(R(cx - 40, SCR.y + 90 + drop * 30, 80, 36, 4), C.sun, 2.6);
      // split: iron beads into the ochre hopper (to the iron pipe), the rest into a bin
      const sp = seg(t, K.taken + .7, K.iron);
      if (sp > 0) {
        for (let i = 0; i < 6; i++) { const q = clamp(sp * 1.4 - i * .08); const x = lerp(600, 860, eo(q)), y = lerp(SCR.y + 200, SCR.y + SCR.h - 90, ei(q)) - Math.sin(q * Math.PI) * 60; shape(E(x, y, 13), C.sun, 2.4); }
        for (let i = 0; i < 4; i++) { const q = clamp(sp * 1.4 - i * .1); const x = lerp(600, 330, eo(q)), y = lerp(SCR.y + 200, SCR.y + SCR.h - 110, ei(q)) - Math.sin(q * Math.PI) * 50; shape(R(x - 12, y - 12, 24, 20, 3), C.redD, 2.2); }
      }
      shape(`M800 ${SCR.y + SCR.h - 120}H920L900 ${SCR.y + SCR.h - 40}H820Z`, C.sunL, 3);
      shape(R(270, SCR.y + SCR.h - 130, 130, 90, 4), C.wallS, 3); txt(335, SCR.y + SCR.h - 72, 'WASTE', 28, { fam: FONT.en, w: 900, anchor: 'middle' });
      tag(760, SCR.y + 150, 'IRON', 'BACK TO WORK', C.sun, { size: 30 });
      worker(1020, r.fl, { s: 1.4, flip: true, cap: C.sun, front: [-140 + 20 * Math.sin(t * 3), 0], back: [-40, 0] });
      const [on, pop] = st(t, K.taken);
      plaqueN(r.x + 20, SCR.y - 30, 'SCRAP YARD', 'MACROPHAGES', 4, on, pop, 36);
    }
    // iron beads riding the ochre pipe back to the marrow (follow the colour)
    if (t > K.iron - .2 && t < K.next + .3) for (let i = 0; i < 4; i++) {
      const q = clamp(seg(t, K.iron - .2 + i * .18, K.next - .1 + i * .05));
      if (q <= 0 || q >= 1) continue;
      const L1 = (SCR.y + SCR.h - 70) - (MAR.y + 120), L2 = 860 - (PRESS[0] + 40), u = eio(q) * (L1 + L2);
      const [x, y] = u < L1 ? [860, SCR.y + SCR.h - 70 - u] : [860 - (u - L1), MAR.y + 120];
      shape(E(x, y, 12), C.sun, 2.4);
    }

    // ---------- pelvis: the stamping plant (bone marrow) ----------
    if (inView(MAR.x - 60, MAR.y - 60, MAR.x + MAR.w + 60, MAR.y + MAR.h + 60)) {
      const r = room(MAR.x, MAR.y, MAR.w, MAR.h, C.sun);
      // bone-shaped back wall (the plant sits inside a bone)
      shape('M260 2140C220 2100 230 2050 280 2050C320 2050 330 2090 360 2090H940C970 2090 980 2050 1020 2050C1070 2050 1080 2100 1040 2140C1080 2180 1070 2230 1020 2230C980 2230 970 2190 940 2190H360C330 2190 320 2230 280 2230C230 2230 220 2180 260 2140Z', C.wallD, 2.4, 'opacity=".9"');
      belt2([PRESS[0] - 60, PRESS[1] + 44], [PRESS[0] + 260, PRESS[1] + 44], 1.1, -t * 6);
      // the press stamps (each stamp = a new cell); a steady stream of new cells on the belt
      const hits = [K.out - .1, K.next - .1];
      let dn = 0; for (const h of hits) dn = Math.max(dn, pulse(t, h - .12, .36));
      dn = Math.max(dn, .25 * pulse(t % .5, 0, .2));
      trestle(PRESS[0] - 90, PRESS[1] - 150, PRESS[1] + 30); trestle(PRESS[0] + 90, PRESS[1] - 150, PRESS[1] + 30);
      shape(R(PRESS[0] - 120, PRESS[1] - 250, 240, 70, 6), C.sun, 3);
      shape(R(PRESS[0] - 12, PRESS[1] - 180, 24, 80 + dn * 60, 2), C.wallD, 2.4);
      shape(R(PRESS[0] - 70, PRESS[1] - 100 + dn * 60, 140, 34, 5), C.sunD, 3);
      if (t > K.born - .3) for (let i = 0; i < 5; i++) { const q = ((t * .9 + i / 5) % 1); rbc(lerp(PRESS[0] + 60, PRESS[0] + 280, q), PRESS[1] + 10, .8); }
      // production counter
      const p = seg(t, K.two, K.two + 1.0);
      if (t > K.two - .1) { shadow(R(640, MAR.y + 230, 470, 180, 6), 12, 9, C.wallS); shape(R(640, MAR.y + 230, 470, 180, 6), C.cream, 3); flipboard(660, MAR.y + 246, '2,000,000', '', p, { size: 66, t }); txt(875, MAR.y + 390, 'NEW CELLS EVERY SECOND', 30, { fam: FONT.en, w: 900, anchor: 'middle' }); }
      // the 120-day counter on the press (the hook)
      const pq = seg(t, K.v120a, K.v120a + .6);
      if (t > K.v120a - .1 && t < K.born + .6) { flipboard(PRESS[0] + 150, MAR.y + 40, '120', 'DAYS', pq, { size: 66, t, us: 40 }); }
      const [on, pop] = st(t, K.born);
      const [on2, pop2] = st(t, K.next);
      plaqueN(r.x + 20, MAR.y - 30, 'STAMPING PLANT', 'BONE MARROW', 1, on, Math.max(pop, pop2), 36);
      worker(1050, r.fl, { s: 1.4, flip: true, cap: C.red, front: [-150, 10], back: [-30, 0] });
    }

    // ---------- the hero cell ----------
    const h = hero(t);
    if (h) {
      const stiff = t > K.stiff;
      const day = t < K.job ? 1 : t < K.but ? Math.round(lerp(1, 119, Math.pow(seg(t, K.job, K.but), 1.3))) : t < K.v120 ? 119 : 120;
      rbc(h.x, h.y, h.k, { ticket: 'DAY ' + day, stiff, crate: h.crate, stencil: stiff && t < K.arrive + 2 ? 'STIFF' : '', rot: stiff ? 0 : 3 * Math.sin(t * 5) });
    }
    // the next you (the loop)
    if (t > K.next) { const u = eo(seg(t, K.next, K.next + .8)); rbc(lerp(PRESS[0], PRESS[0] + 130, u), PRESS[1] + 10, lerp(.6, 1.4, u), { ticket: 'DAY 1' }); }
  }

  EPS[2] = {
    id: 'e2_redcell', tail: 1.6,
    setup(at, dur) {
      K = {
        red: at('red'), v120a: at('120'), born: at('born'), two: at('two'), job: at('job'), again: at('again', 1),
        but: at('but'), v120: at('120', 1), stiff: at('stiff'), spleen: at('spleen'), insp: at('inspection'), young: at('young'),
        old: at('old'), stopped: at('stopped'), taken: at('taken'), iron: at('iron'), back: at('back'), next: at('next'), dur,
      };
      K.out = .75; K.up0 = K.two + 1.6; K.down0 = K.spleen - .3; K.arrive = K.old - .1;
      ev(K.out - .1, 'press'); ev(K.out, 'ding'); ev(K.v120a, 'roll', { d: .6 }); ev(K.born, 'ding'); ev(K.two, 'roll', { d: 1.0 });
      ev(K.up0, 'whoosh', { d: K.job - K.up0 }); ev(K.job, 'ding');
      for (let i = 0; i < 6; i++) ev(K.job + .5 + i * (K.but - K.job - .6) / 6, 'clunk');
      ev(K.job, 'tick', { d: K.but - K.job });
      ev(K.stiff, 'clunk'); ev(K.down0, 'whoosh', { d: K.arrive - K.down0 }); ev(K.insp, 'ding');
      ev(K.old + .3, 'stop', { d: K.stopped - K.old - .3 }); ev(K.stopped, 'clunk'); ev(K.stopped, 'bell');
      ev(K.taken - .3, 'whoosh', { d: .6 }); ev(K.taken, 'lever'); ev(K.taken, 'ding');
      for (let i = 0; i < 4; i++) ev(K.iron + i * .2, 'drip');
      ev(K.next - .1, 'press'); ev(K.next, 'ding'); ev(K.next, 'payoff');
    },
    stub(t) { return t < K.born ? 0 : t < K.job ? 1 : t < K.insp ? 2 : t < K.taken ? 3 : t < K.iron ? 4 : 1; },
    fast(t) { return (t > K.up0 + .2 && t < K.job - .1) || (t > K.down0 + .1 && t < K.arrive - .1); },
    camera(t) {
      const open = { x: 560, y: PRESS[1] - 120, z: 1.7 };
      const marW = { x: 640, y: MAR.y + 210, z: 1.02 };
      const routeW = { x: 650, y: ROUTE.y + 250, z: 1.05 };
      const h = hero(t);
      if (t < K.born) return open;
      if (t < K.up0) return mixc(open, marW, eio(seg(t, K.born, K.born + 1.2)));
      if (t < K.job) { const u = eio(seg(t, K.up0, K.job)); return mixc(marW, routeW, u); }
      if (t < K.but) return { ...routeW, z: 1.0 + .03 * seg(t, K.job, K.but) };
      const close = h ? { x: h.x + 40, y: h.y - 60, z: 2.2 } : routeW;
      if (t < K.down0) return mixc(routeW, close, eio(seg(t, K.but, K.but + .6)));
      const splW = { x: 650, y: SPL.y + 230, z: 1.08 };
      if (t < K.arrive) return mixc(close, splW, eio(seg(t, K.down0, K.arrive)));
      if (t < K.taken - .3) return { ...splW, y: splW.y + shake(t, K.stopped, .3, 6) };
      const scrW = { x: 650, y: SCR.y + 200, z: 1.1 };
      if (t < K.iron) return mixc(splW, scrW, eio(seg(t, K.taken - .3, K.taken + .4)));
      const marF = { x: 600, y: MAR.y + 160, z: 1.15 };
      if (t < K.next + .2) return mixc(scrW, marF, eio(seg(t, K.iron, K.next - .2)));
      return mixc(marF, open, eio(seg(t, K.next + .2, K.next + 1.3)));
    },
    world: drawWorld,
  };
})();

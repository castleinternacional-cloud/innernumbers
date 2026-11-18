// E3 · WHY KNUCKLES CRACK — a giant hand (fingers up) cut away: the oil tank (finger joint) inside the index finger,
// the reset clock in the palm; a gantry crane on the paper pulls the finger. Teal = fluid/gas, ochre = numbers.
(() => {
  let K = {};
  const Sx = 2;
  const P = (x, y) => `${x * Sx} ${y * Sx}`;
  const HAND = `M${P(200, 3000)}L${P(70, 2200)}L${P(70, 820)}A${110 * Sx} ${110 * Sx} 0 0 1 ${P(290, 820)}L${P(290, 1180)}L${P(320, 1180)}L${P(320, 490)}A${110 * Sx} ${110 * Sx} 0 0 1 ${P(540, 490)}L${P(540, 1180)}L${P(570, 1180)}L${P(570, 360)}A${110 * Sx} ${110 * Sx} 0 0 1 ${P(790, 360)}L${P(790, 1180)}L${P(820, 1180)}L${P(820, 510)}A${110 * Sx} ${110 * Sx} 0 0 1 ${P(1040, 510)}L${P(1040, 1500)}L${P(1200, 1300)}A${74 * Sx} ${74 * Sx} 0 0 1 ${P(1300, 1400)}L${P(1110, 1900)}L${P(1100, 2200)}L${P(970, 3000)}Z`;
  const TANK = { x: 1690, y: 1440, w: 340, h: 600 };      // index finger joint (world)
  const PALM = { x: 300, y: 2650, w: 1500, h: 620 };
  const TIP = [1860, 1020];                                // index fingertip (world)

  function gap(t) { return lerp(70, 170, eio(seg(t, K.pull, K.pull + .9))) * (1 - eio(seg(t, K.reset + 1.5, K.reset + 2.5))) + 70 * eio(seg(t, K.reset + 1.5, K.reset + 2.5)) * 0; }
  function lift(t) { return lerp(0, 100, eio(seg(t, K.pull, K.pull + .9))) * (1 - eio(seg(t, K.reset + 1.5, K.reset + 2.5))); }

  function bubble(t) {   // 0 = none, beads gathering, then one bubble that slowly shrinks
    if (t < K.gas - .2) return { beads: 0, r: 0 };
    if (t < K.pop) return { beads: seg(t, K.gas - .2, K.pop - .1), r: 0 };
    const r = 70 * (1 - ss(seg(t, K.v20, K.v20 + 3.4)));
    return { beads: 0, r, flash: pulse(t, K.pop, .35) };
  }

  function drawWorld(t) {
    // gantry crane on the paper above the index finger; its hook holds the fingertip
    const L = lift(t);
    const hookY = TIP[1] - 220 - L + (1 - ss(seg(t, .2, .7))) * -160;
    shape(R(1500, 120, 720, 40, 4), C.sun, 3);
    trestle(1540, 160, 600, 40); trestle(2180, 160, 600, 40);
    line([[1540, 600], [2180, 600]], 0);
    shape(R(1820, 160, 80, 60, 4), C.ink, 0);
    line([[1860, 220], [1860, hookY]], 3.4);
    shape(`M${1840} ${hookY}h40v30q0 34 -20 34q-20 0 -20 -20`, C.wallD, 3);
    // the strap around the fingertip
    out(`<g transform="translate(0 ${f1(-L)})">`);
    line([[1860, hookY + 60], [1860, TIP[1] - 10]], 3);
    shape(R(1700, TIP[1] - 30, 320, 40, 8), C.red, 3);
    out('</g>');

    // the hand: the index finger above the joint moves up with the pull (drawn as one wall + a slice)
    bodyWall(HAND);
    // index finger upper segment (above the joint) slides up with the crane
    if (L > .5) {
      fillOnly(R(1640, TANK.y - 40 - L, 440, L + 40), C.ground);
      out(`<path d="M1640 ${f1(TANK.y - 40 - L)}V${TANK.y}M2080 ${f1(TANK.y - 40 - L)}V${TANK.y}" stroke="${C.blush}" stroke-width="56"/>`);
    }

    // ---------- ① the oil tank (finger joint) ----------
    if (inView(TANK.x - 100, TANK.y - 200, TANK.x + TANK.w + 100, TANK.y + TANK.h + 100)) {
      const r = room(TANK.x, TANK.y - L, TANK.w, TANK.h + L, C.teal, { floor: false });
      // two bone ends: upper (moves with the pull) and lower
      const g = 70 + L;
      const cy = TANK.y + TANK.h / 2 - L / 2;
      const topB = cy - g / 2, botB = cy + g / 2;
      // fluid (the gap between the bones, sealed by the capsule)
      shape(R(r.x + 10, topB - 30, r.w - 20, botB - topB + 60, 12), C.tealL, 2.4);
      shape(`M${r.x + 30} ${r.y + 10}H${r.x + r.w - 30}V${topB - 20}Q${r.x + r.w / 2} ${topB + 26} ${r.x + 30} ${topB - 20}Z`, C.cream, 3);
      shape(`M${r.x + 30} ${r.y + r.h - 10}H${r.x + r.w - 30}V${botB + 20}Q${r.x + r.w / 2} ${botB - 26} ${r.x + 30} ${botB + 20}Z`, C.cream, 3);
      // gas: beads gather, then one bubble forms (the pop), then it slowly dissolves
      const b = bubble(t), mx = r.x + r.w / 2;
      if (b.beads > 0) for (let i = 0; i < 12; i++) { const a = i / 12 * Math.PI * 2 + t; const rr = lerp(120, 26, ei(b.beads)); out(`<circle cx="${f1(mx + Math.cos(a) * rr * .9)}" cy="${f1(cy + Math.sin(a) * rr * .3)}" r="${f1(6 + 4 * b.beads)}" fill="${C.cream}" stroke="${C.ink}" stroke-width="${f1(2 * KS)}"/>`); }
      if (b.r > 2) { shape(E(mx, cy, b.r * 1.2, b.r * .55), C.cream, 3); out(`<circle cx="${f1(mx - b.r * .4)}" cy="${f1(cy - b.r * .2)}" r="${f1(b.r * .12)}" fill="${C.tealL}"/>`); }
      if (b.flash > 0) for (let i = 0; i < 10; i++) { const a = i / 10 * Math.PI * 2; line([[mx + Math.cos(a) * 110, cy + Math.sin(a) * 60], [mx + Math.cos(a) * (110 + 90 * b.flash), cy + Math.sin(a) * (60 + 50 * b.flash)]], 5); }
      // pressure gauge
      gauge(r.x + r.w - 60, r.y + 80, 34, t < K.drops ? .7 : lerp(.7, .12, ss(seg(t, K.drops, K.drops + .4))) + .58 * ss(seg(t, K.reset + 1.5, K.reset + 2.5)));
      worker(r.x + 70, botB - 4 + 0, { s: 1.0, cap: C.sun, sit: true, back: [140, 20], front: [160, 10] });
      const [on, pop] = st(t, K.capsule);
      plaqueN(TANK.x - 60, TANK.y - 44 - L, 'OIL TANK', 'FINGER JOINT', 1, on, pop, 30);
    }

    // ---------- ② the reset clock (palm) ----------
    if (inView(PALM.x - 60, PALM.y - 120, PALM.x + PALM.w + 60, PALM.y + PALM.h + 60)) {
      const r = room(PALM.x, PALM.y, PALM.w, PALM.h, C.sun);
      const cx = PALM.x + 330, cy = PALM.y + 300;
      shape(E(cx, cy, 190), C.cream, 4);
      for (let i = 0; i < 12; i++) { const a = i / 12 * Math.PI * 2; line([[cx + Math.cos(a) * 160, cy + Math.sin(a) * 160], [cx + Math.cos(a) * 180, cy + Math.sin(a) * 180]], 5); }
      const spin = ss(seg(t, K.v20, K.reset + .6));
      const am = (-90 + 360 * spin * 1.0) * Math.PI / 180;                // minute hand: one sweep (shown as the 20-minute cycle)
      shape(`M${cx} ${cy}A160 160 0 ${spin > .5 ? 1 : 0} 1 ${f1(cx + Math.cos(am) * 160)} ${f1(cy + Math.sin(am) * 160)}Z`, C.sunL, 0, 'opacity=".8"');
      line([[cx, cy], [cx + Math.cos(am) * 150, cy + Math.sin(am) * 150]], 9);
      line([[cx, cy], [cx + Math.cos(-Math.PI / 3) * 90, cy + Math.sin(-Math.PI / 3) * 90]], 11);
      out(`<circle cx="${cx}" cy="${cy}" r="12" fill="${C.ink}"/>`);
      const p = seg(t, K.v20, K.v20 + .6);
      if (t > K.v20 - .1) { shadow(R(PALM.x + 600, PALM.y + 110, 540, 210, 6), 12, 9, C.wallS); shape(R(PALM.x + 600, PALM.y + 110, 540, 210, 6), C.cream, 3); flipboard(PALM.x + 624, PALM.y + 128, '20', 'MINUTES', p, { size: 88, t, us: 52 }); txt(PALM.x + 870, PALM.y + 300, 'BEFORE IT CAN CRACK AGAIN', 32, { fam: FONT.en, w: 900, anchor: 'middle' }); }
      // workers doze through the reset, wake at the end
      const doze = t > K.v20 && t < K.reset + 1.4;
      worker(PALM.x + 1060, r.fl, { s: 1.6, sit: doze, cap: C.teal, lean: doze ? 18 : 0, front: doze ? [20, 0] : [140, 10], back: [10, 0] });
      if (doze) txt(PALM.x + 1100, r.fl - 130, 'z', 46, { fam: FONT.en, w: 900, fill: C.ink });
      // the safety sign (end)
      const sg = spring(t - K.hurts, 7, .32);
      if (t > K.hurts - .05) {
        const y0 = lerp(PALM.y - 200, PALM.y + 360, clamp(sg, 0, 1.2));
        line([[PALM.x + 700, PALM.y + 14], [PALM.x + 700, y0]], 3); line([[PALM.x + 1040, PALM.y + 14], [PALM.x + 1040, y0]], 3);
        shadow(R(PALM.x + 600, y0, 540, 130, 6), 12, 9); shape(R(PALM.x + 600, y0, 540, 130, 6), C.red, 3.2);
        txt(PALM.x + 870, y0 + 56, 'IF IT HURTS', 52, { fam: FONT.en, w: 900, anchor: 'middle', fill: C.cream });
        txt(PALM.x + 870, y0 + 108, 'SEE A DOCTOR', 44, { fam: FONT.en, w: 900, anchor: 'middle', fill: C.cream });
      }
      const [on, pop] = st(t, K.v20);
      plaqueN(r.x + 20, PALM.y - 30, 'RESET CLOCK', 'GAS DISSOLVES BACK', 2, on, pop, 38);
      // the brand nameplate
      shape(R(PALM.x + 60, r.fl - 70, 320, 56, 4), C.ink, 0);
      txt(PALM.x + 220, r.fl - 30, 'INNER NUMBERS', 36, { fam: FONT.en, w: 900, anchor: 'middle', fill: C.sun, ls: 2 });
    }
  }

  function inner(t) {   // porthole: a doctor's desk — one hand cracked for 60+ years, the other never
    fillOnly(R(0, 0, 1080, 1080), C.paper);
    fillOnly(R(0, 700, 1080, 380), C.wallD); line([[0, 700], [1080, 700]], 3);
    const hand = (x, flip) => {
      out(`<g transform="translate(${x} 700) scale(${flip ? -1 : 1} 1)">`);
      shape('M-90 0L-100 -150L-104 -330A26 26 0 0 1 -52 -330L-50 -190L-40 -380A26 26 0 0 1 12 -380L10 -190L24 -360A26 26 0 0 1 76 -360L60 -170L80 -300A26 26 0 0 1 128 -290L100 -60L80 0Z', C.skin, 3.4);
      out('</g>');
    };
    hand(300, false); hand(780, true);
    // tally boards
    const yrs = Math.round(60 * eo(seg(t, K.sixty - .9, K.sixty + .2)));
    shape(R(150, 90, 300, 190, 8), C.ink, 3); txt(300, 160, 'CRACKED', 34, { fam: FONT.en, w: 900, anchor: 'middle', fill: C.cream });
    txt(300, 250, (t > K.sixty + .2 ? '60+' : String(yrs)) + ' YRS', 70, { fam: FONT.en, w: 900, anchor: 'middle', fill: C.sun });
    shape(R(630, 90, 300, 190, 8), C.ink, 3); txt(780, 160, 'NEVER', 34, { fam: FONT.en, w: 900, anchor: 'middle', fill: C.cream });
    txt(780, 250, '0 YRS', 70, { fam: FONT.en, w: 900, anchor: 'middle', fill: C.cream });
    txt(300, 780, 'LEFT HAND', 40, { fam: FONT.en, w: 900, anchor: 'middle' }); txt(780, 780, 'RIGHT HAND', 40, { fam: FONT.en, w: 900, anchor: 'middle' });
    // stamps: arthritis — none
    for (const [x, at] of [[300, K.neither], [780, K.neither + .45]]) {
      const q = seg(t, at, at + .25); if (q <= 0) continue;
      const s = lerp(1.8, 1, eo(q));
      out(`<g transform="translate(${x} 520) rotate(-12) scale(${f1(s * 100) / 100})" opacity="${f1(Math.min(1, q * 3) * 100) / 100}">`);
      out(`<rect x="-170" y="-58" width="340" height="116" rx="10" fill="none" stroke="${C.teal}" stroke-width="10"/>`);
      txt(0, -6, 'ARTHRITIS', 44, { fam: FONT.en, w: 900, anchor: 'middle', fill: C.teal });
      txt(0, 42, 'NONE', 52, { fam: FONT.en, w: 900, anchor: 'middle', fill: C.teal });
      out('</g>');
    }
  }

  EPS[3] = {
    id: 'e3_knuckles', tail: 1.6,
    setup(at, dur) {
      K = {
        crack: at('crack'), inside: at('inside'), capsule: at('capsule'), fluid: at('fluid'), pull: at('pull'), drops: at('drops'),
        gas: at('gas'), bubble: at('bubble'), pop: at('pop'), sound: at('sound'), v20: at('20'), reset: at('reset'), again: at('again'),
        does: at('does'), doctor: at('doctor'), sixty: at('60'), neither: at('neither'), hurts: at('hurts'), doc2: at('doctor', 1), dur,
      };
      ev(.45, 'clunk'); ev(K.inside - .2, 'whoosh', { d: .9 }); ev(K.capsule, 'ding');
      ev(K.pull, 'lever'); ev(K.pull, 'roll', { d: .9 }); ev(K.drops, 'clunk');
      ev(K.pop - .45, 'stop', { d: .45 }); ev(K.pop, 'pop');
      ev(K.sound + .3, 'whoosh', { d: .9 }); ev(K.v20, 'roll', { d: .6 }); ev(K.v20, 'ding'); ev(K.v20, 'tick', { d: K.reset + .6 - K.v20 });
      ev(K.does + .3, 'iris'); ev(K.sixty - .9, 'roll', { d: 1.1 }); ev(K.neither, 'clunk'); ev(K.neither + .45, 'clunk');
      ev(K.neither + .5, 'payoff'); ev(K.hurts - .5, 'iris'); ev(K.hurts, 'sign'); ev(K.doc2 + .6, 'whoosh', { d: 1.4 });
    },
    stub(t) { return t < K.capsule ? 0 : t < K.v20 ? 1 : t < K.does ? 2 : 0; },
    fast(t) { return t > K.sound + .35 && t < K.v20 - .1; },
    camera(t) {
      const open = { x: 1250, y: 1700, z: .4 };
      const tank = { x: 1860, y: TANK.y + TANK.h / 2 - 40, z: 2.05 };
      const tankPull = { x: 1860, y: TANK.y + TANK.h / 2 - 120, z: 1.9 };
      const palm = { x: PALM.x + 700, y: PALM.y + 330, z: .92 };
      const all = { x: 1250, y: 1700, z: .4 };
      const keys = [[0, open], [K.crack + .3, { x: 1700, y: 1500, z: .62 }, ss], [K.capsule, tank, eio], [K.pull, tank], [K.pull + .9, tankPull, eio], [K.sound + .3, tankPull], [K.v20 - .1, palm, eio], [K.doc2 + .6, palm], [K.doc2 + 2.0, all, eio]];
      const c = camKeys(keys, t);
      c.y += shake(t, K.pop, .35, 10);
      return c;
    },
    world: drawWorld,
    screen(t, cam) { porthole(t, cam, PALM.x + 330, PALM.y + 300, K.does + .3, K.does + .8, K.hurts - .9, K.hurts - .5, inner); },
  };
})();

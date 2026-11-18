// E4 · THE SWEAT OF HUMANITY — a person sitting still on a chair (profile, facing right), cut away:
// the pump wall (sweat glands) in the torso, the year counter in the thigh; then the great pull-back to everyone on Earth.
// Teal = water, ochre = numbers.
(() => {
  let K = {};
  const BODY = 'M550 0C700 0 800 110 800 250L860 290L800 330C790 430 730 490 660 505L680 580C820 620 900 740 900 900L900 1420L1350 1420C1440 1420 1490 1480 1490 1560L1490 2300L1600 2340C1640 2350 1640 2400 1600 2400L1250 2400C1220 2400 1210 2380 1210 2350L1210 1700L520 1700C330 1700 200 1600 200 1400L200 900C200 740 280 630 420 580L440 500C360 470 300 400 300 250C300 110 400 0 550 0Z';
  const TOR = { x: 270, y: 700, w: 560, h: 660 };
  const THI = { x: 930, y: 1450, w: 500, h: 220 };
  const JUG = [760, 2330];
  const PUMP0 = [430, 900];        // the hero pump (opening close-up)

  function pumpUnit(x, y, ph, k = 1) {
    const push = .5 + .5 * Math.sin(ph);
    out(`<g transform="translate(${f1(x)} ${f1(y)}) scale(${k})">`);
    shape(R(-16, -30, 32, 46, 5), C.wallD, 2.4);
    shape(R(-4, -30 - 22 + push * 12, 8, 24, 2), C.ink, 0);
    shape(R(-14, -56 + push * 12, 28, 8, 3), C.sun, 2);
    shape(R(-5, 16, 10, 14, 2), C.teal, 2);
    out('</g>');
  }
  // a tiny seated person icon (for the crowd), centred at its seat, scale k
  function sitter(x, y, k, col = C.blush) {
    fillOnly(E(x - 4 * k, y - 76 * k, 13 * k), col);
    fillOnly(`M${f1(x - 18 * k)} ${f1(y - 58 * k)}h${f1(26 * k)}v${f1(44 * k)}h${f1(34 * k)}v${f1(48 * k)}h${f1(-14 * k)}v${f1(-30 * k)}h${f1(-46 * k)}Z`, col);
    fillOnly(R(x - 30 * k, y - 10 * k, 66 * k, 8 * k), C.sunD);
  }

  function drawWorld(t, cam) {
    const far = ZL < .3;
    // the crowd: copies of the seated person around the hero (only when pulled back)
    if (ZL < .45) {
      const op = 1 - ss(seg(ZL, .2, .42));
      const pools = ss(seg(t, K.enough - .2, K.enough + .9));
      out(`<g opacity="${f1(op * 100) / 100}">`);
      const sp = 2600, n = 16;
      for (let i = -n; i <= n; i++) for (let j = -n; j <= n; j++) {
        if (i === 0 && j === 0) continue;
        const x = 800 + i * sp, y = 1300 + j * sp * 1.15;
        if (!inView(x - 1500, y - 1500, x + 1500, y + 1500)) continue;
        if (pools > .02) {
          const w = lerp(400, 2300, pools), h = lerp(400, 1150, pools);
          shape(R(x - w / 2, y - h / 2, w, h, 40), C.teal, 0);
          if (pools > .5) for (let l = 1; l < 8; l++) out(`<path d="M${f1(x - w / 2 + 60)} ${f1(y - h / 2 + l * h / 8)}H${f1(x + w / 2 - 60)}" stroke="${C.tealL}" stroke-width="${f1(26 * pools)}" stroke-dasharray="80 60"/>`);
        }
        if (pools < .98) sitter(x, y + 600, 26 * (1 - pools), C.blush);
      }
      out('</g>');
    }

    // chair (on the paper, behind the body)
    shape(R(110, 760, 70, 960, 10), C.sunD, 3);
    shape(R(110, 1700, 1180, 60, 10), C.sun, 3);
    line([[200, 1760], [200, 2400]], 14); line([[1150, 1760], [1150, 2400]], 14);
    out(`<path d="M-4000 2400H6000" stroke="${C.ink}" stroke-width="${f1(3 * KS)}"/>`);
    bodyWall(BODY);

    // ---------- title sign over the head ----------
    if (t > K.skin - .05 && !far) {
      const d = spring(t - K.skin, 7, .32), y0 = lerp(-500, -230, clamp(d, 0, 1.2));
      line([[380, -900], [380, y0]], 3); line([[900, -900], [900, y0]], 3);
      shadow(R(240, y0, 820, 120, 6), 12, 9); shape(R(240, y0, 820, 120, 6), C.cream, 3.2);
      txt(650, y0 + 84, 'THE SWEAT OF HUMANITY', 66, { fam: FONT.en, w: 900, anchor: 'middle', ls: 1 });
    }

    // ---------- ① the pump wall (sweat glands) ----------
    if (inView(TOR.x - 60, TOR.y - 60, TOR.x + TOR.w + 60, TOR.y + TOR.h + 60) && !far) {
      const r = room(TOR.x, TOR.y, TOR.w, TOR.h, C.teal);
      // collector pipe along the floor, down through the seat to the jug
      const col = rpoly([[TOR.x + 40, TOR.y + TOR.h - 70], [TOR.x + TOR.w - 30, TOR.y + TOR.h - 70], [760, TOR.y + TOR.h - 70], [760, 2200]], 30);
      pipe(null, 30, C.teal, C.tealL, { d: col });
      // grid of little pumps, each with a drip
      for (let row = 0; row < 4; row++) for (let c = 0; c < 6; c++) {
        const x = TOR.x + 70 + c * 82, y = TOR.y + 150 + row * 120;
        pumpUnit(x, y, t * 5 + row * 1.3 + c * .7, 1.2);
        const q = ((t * .7 + hash(row * 7 + c)) % 1);
        if (t > .2) drop(x, y + 40 + q * 60, 7);
      }
      const p = seg(t, K.two, K.two + 1.0);
      if (t > K.two - .1) { shadow(R(TOR.x + 40, TOR.y + 40, 480, 120, 6), 10, 8, C.wallS); shape(R(TOR.x + 40, TOR.y + 40, 480, 120, 6), C.cream, 3); flipboard(TOR.x + 56, TOR.y + 52, '2,000,000', '', p, { size: 62, t }); }
      const [on, pop] = st(t, K.skin);
      plaqueN(r.x - 10, TOR.y - 34, 'PUMP WALL', 'SWEAT GLANDS', 1, on, pop, 34);
    }
    // ---------- the jug under the chair (sitting still: half a liter a day) ----------
    if (!far) {
      const fill = clamp(seg(t, K.even, K.day + .2) * .9 + seg(t, K.v180, K.v180 + .5) * 0) * (1 - ss(seg(t, K.v180, K.v180 + .7)));
      shape(`M${JUG[0] - 70} ${JUG[1] - 170}H${JUG[0] + 70}L${JUG[0] + 60} ${JUG[1] + 60}H${JUG[0] - 60}Z`, C.wall, 3);
      fillOnly(`M${JUG[0] - 66 + 10 * (1 - fill)} ${JUG[1] + 56 - 220 * fill}H${JUG[0] + 66 - 10 * (1 - fill)}L${JUG[0] + 58} ${JUG[1] + 56}H${JUG[0] - 58}Z`, C.teal);
      shape(`M${JUG[0] - 70} ${JUG[1] - 170}H${JUG[0] + 70}L${JUG[0] + 60} ${JUG[1] + 60}H${JUG[0] - 60}Z`, null, 3);
      for (let k = 1; k < 5; k++) line([[JUG[0] + 30, JUG[1] + 60 - k * 50], [JUG[0] + 56, JUG[1] + 60 - k * 50]], 2);
      if (t > K.even) for (let i = 0; i < 2; i++) { const q = ((t * 1.2 + i / 2) % 1); drop(760, lerp(2210, JUG[1] - 40, q), 9); }
      const p = seg(t, K.half, K.half + .6);
      if (t > K.half - .1) { shadow(R(880, 2050, 430, 150, 6), 10, 8); shape(R(880, 2050, 430, 150, 6), C.cream, 3); flipboard(900, 2066, '0.5', 'L / DAY', p, { size: 70, t, us: 44 }); }
    }
    // ---------- ② the year counter (thigh) ----------
    if (inView(THI.x - 60, THI.y - 60, THI.x + THI.w + 60, THI.y + THI.h + 60) && !far) {
      const r = room(THI.x, THI.y, THI.w, THI.h, C.sun);
      const days = Math.round(365 * ss(seg(t, K.v180 - .4, K.year)));
      shape(R(THI.x + 30, THI.y + 30, 150, 150, 6), C.cream, 3); fillOnly(R(THI.x + 32, THI.y + 32, 146, 36), C.red);
      txt(THI.x + 105, THI.y + 150, String(Math.max(1, days)), 64, { fam: FONT.en, w: 900, anchor: 'middle' });
      txt(THI.x + 105, THI.y + 62, 'DAY', 26, { fam: FONT.en, w: 900, anchor: 'middle', fill: C.cream });
      // barrel filling
      const bf = ss(seg(t, K.v180 - .4, K.year));
      shape(R(THI.x + 300, THI.y + 30, 150, 160, 18), C.wall, 3);
      fillOnly(R(THI.x + 304, THI.y + 186 - 152 * bf, 142, 152 * bf, 14), C.teal);
      shape(R(THI.x + 300, THI.y + 30, 150, 160, 18), null, 3); line([[THI.x + 300, THI.y + 80], [THI.x + 450, THI.y + 80]], 3); line([[THI.x + 300, THI.y + 140], [THI.x + 450, THI.y + 140]], 3);
      const p = seg(t, K.v180, K.v180 + .6);
      if (t > K.v180 - .1) { shadow(R(THI.x + 30, THI.y + THI.h + 40, 460, 150, 6), 10, 8); shape(R(THI.x + 30, THI.y + THI.h + 40, 460, 150, 6), C.cream, 3); flipboard(THI.x + 50, THI.y + THI.h + 56, '180', 'L / YEAR', p, { size: 70, t, us: 44 }); }
      const [on, pop] = st(t, K.v180);
      plaqueN(r.x - 10, THI.y - 34, 'YEAR COUNTER', 'PER PERSON', 2, on, pop, 34);
    }
    // the hero pump close-up drop (opening + loop)
    if (!far) { const q = (t * .9) % 1; drop(PUMP0[0], PUMP0[1] + 40 + q * 60, 7); }
  }

  // hanging boards in the foreground for the world-scale numbers (screen space, they enter on chains)
  function bigBoard(t, at, out_, y, value, unit, n) {
    if (t < at - .05 || t > out_ + .3) return;
    const d = spring(t - at, 7, .32), go = ei(seg(t, out_, out_ + .3));
    const yy = lerp(-300, y, clamp(d, 0, 1.2)) - go * 600;
    const w = 980, x = 50;
    line([[x + 120, -10], [x + 120, yy]], 3); line([[x + w - 120, -10], [x + w - 120, yy]], 3);
    shadow(R(x, yy, w, 230, 8), 14, 10); shape(R(x, yy, w, 230, 8), C.cream, 3.4);
    const fw = flipboard(x + 30, yy + 24, value, '', seg(t, at, at + .9), { size: value.length > 14 ? 74 : 92, t });
    txt(x + w / 2, yy + 205, unit, 40, { fam: FONT.en, w: 900, anchor: 'middle', ls: 1.5 });
    if (n) numOn(x + w - 40, yy + 30, n, 1, pulse(t, at, .35), 26);
  }

  EPS[4] = {
    id: 'e4_sweat', tail: 1.5,
    setup(at, dur) {
      K = {
        sweat: at('sweat'), earth: at('earth'), skin: at('skin'), two: at('2'), glands: at('glands'), even: at('even'), half: at('half'),
        day: at('day'), v180: at('180'), year: at('year'), person: at('person'), now: at('now'), multiply: at('multiply'),
        b82: at('8'), people: at('people'), t15: at('1.5'), every: at('every'), enough: at('enough'), pools: at('pools'), tag: at('tag'), end: at('now', 1), dur,
      };
      ev(.3, 'drip'); ev(1.1, 'drip'); ev(2.0, 'drip'); ev(K.skin, 'sign'); ev(K.skin, 'ding'); ev(K.two, 'roll', { d: 1.0 });
      for (let i = 0; i < 6; i++) ev(K.even + i * .55, 'drip');
      ev(K.half, 'roll', { d: .6 }); ev(K.v180, 'roll', { d: .6 }); ev(K.v180, 'ding'); ev(K.v180 - .4, 'tick', { d: K.year - K.v180 + .4 });
      ev(K.now, 'whoosh', { d: 1.4 }); ev(K.b82, 'roll', { d: .9 }); ev(K.t15 - .3, 'stop', { d: .3 }); ev(K.t15, 'roll', { d: .9 }); ev(K.t15, 'bell');
      ev(K.enough, 'splash'); ev(K.enough + .5, 'roll', { d: .9 }); ev(K.enough + .4, 'payoff'); ev(K.tag + .6, 'whoosh', { d: 1.2 });
    },
    stub(t) { return t < K.skin ? 0 : t < K.v180 ? 1 : t < K.now ? 2 : 3; },
    fast(t) { return t > K.tag + .7 && t < K.tag + 1.8; },
    camera(t) {
      const open = { x: PUMP0[0] + 60, y: PUMP0[1] + 40, z: 2.1 };
      const whole = { x: 820, y: 1170, z: .6 };
      const jug = { x: 860, y: 1950, z: 1.0 };
      const thigh = { x: 1150, y: 1640, z: 1.15 };
      const world = { x: 800, y: 1300, z: .028 };
      const keys = [[0, open], [K.skin - .2, open], [K.skin + .9, whole, eio], [K.even - .1, whole], [K.even + .8, jug, eio], [K.v180 - .4, jug], [K.v180 + .3, thigh, eio], [K.now, thigh],
        [K.now + 2.6, { x: 800, y: 1300, z: .09 }, eio], [K.t15 + .6, world, eio], [K.tag + .6, { ...world, z: .022 }], [K.tag + 1.9, open, eio]];
      return camKeys(keys, t);
    },
    world: drawWorld,
    screen(t, cam) {
      bigBoard(t, K.b82, K.t15 - .25, 140, '8,200,000,000', 'PEOPLE ON EARTH', 3);
      bigBoard(t, K.t15, K.enough - .2, 140, '1,500,000,000,000', 'LITERS OF WATER A YEAR', 3);
      bigBoard(t, K.enough + .3, K.tag + .5, 140, '600,000', 'OLYMPIC SWIMMING POOLS', 3);
    },
  };
})();

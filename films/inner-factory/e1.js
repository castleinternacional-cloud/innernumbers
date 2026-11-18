// E1 · THE MUCUS ESCALATOR — a torso cut away in profile (facing left): intake in the head, junction (throat) at the neck,
// the cilia escalator shaft down the chest, the glue press (goblet cells) in the lungs, the acid drum (stomach) below the diaphragm.
(() => {
  let K = {};
  const BODY = 'M640 0C300 0 170 180 170 330L92 372L170 420C176 520 262 600 330 640L300 720C120 760 40 900 40 1100L40 2900C40 3150 250 3270 650 3270C1050 3270 1260 3150 1260 2900L1260 1100C1260 880 1180 760 980 720L960 640C1080 560 1120 450 1120 330C1120 140 960 0 640 0Z';
  const SHAFT = { x: 560, y: 1080, w: 360, h: 1200 };          // escalator room
  const BX = 740;                                               // belt x
  const PRESS = { x: 740, belt: 2640 };                         // glue press over the belt foot
  const JUN = { x: 300, y: 760, w: 700, h: 300 };               // junction room
  const STO = { x: 100, y: 2840, w: 1100, h: 380 };             // stomach room
  const DRUM = [700, 3030];

  // where the mucus cargo is at time t (world)
  function cargo(t) {
    if (t < K.esc0) return { x: BX, y: PRESS.belt - 14, k: lerp(2.1, 1.5, ss(seg(t, K.lungs, K.lungs + .6))) };
    if (t < K.top) { const u = seg(t, K.esc0, K.top); return { x: BX, y: lerp(PRESS.belt - 14, SHAFT.y + 40, u), k: 1.5 }; }
    if (t < K.swallow) { const u = eio(seg(t, K.top, K.top + .8)); return { x: lerp(BX, 830, u), y: lerp(SHAFT.y + 40, JUN.y + 190, u), k: 1.5 }; }
    if (t < K.land) {   // tipped into the chute, falls down it
      const u = seg(t, K.swallow, K.land);
      const pts = [[830, JUN.y + 190], [620, JUN.y + 250], [220, JUN.y + 270], [190, 1300], [190, 2800], [480, 2900], [DRUM[0], DRUM[1] - 40]];
      const L = []; let acc = 0; for (let i = 1; i < pts.length; i++) { acc += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); L.push(acc); }
      const want = ei(u) * acc; let i = 0; while (i < L.length - 1 && L[i] < want) i++;
      const a = pts[i], b = pts[i + 1], l0 = i ? L[i - 1] : 0, v = (want - l0) / (L[i] - l0);
      return { x: lerp(a[0], b[0], v), y: lerp(a[1], b[1], v), k: 1.5 };
    }
    return { x: DRUM[0], y: DRUM[1] + 20, k: 1.5 * (1 - ss(seg(t, K.land, K.job))) };
  }

  function speck(x, y, kind, s = 1, rot = 0) {
    out(`<g transform="translate(${f1(x)} ${f1(y)}) rotate(${f1(rot)}) scale(${s})">`);
    if (kind === 0) shape('M-9 -2L-3 -9L7 -6L9 3L1 9L-8 6Z', '#8E8A84', 2.2);                                   // dust
    else if (kind === 1) { let d = ''; for (let i = 0; i < 16; i++) { const a = i / 16 * Math.PI * 2, r = i % 2 ? 13 : 8; d += (i ? 'L' : 'M') + f1(Math.cos(a) * r) + ' ' + f1(Math.sin(a) * r); } shape(d + 'Z', C.sun, 2.2); }  // pollen
    else { shape(E(0, 0, 10), C.red, 2.2); for (let i = 0; i < 6; i++) { const a = i / 6 * Math.PI * 2; line([[Math.cos(a) * 10, Math.sin(a) * 10], [Math.cos(a) * 16, Math.sin(a) * 16]], 2.4); } }   // germ
    out('</g>');
  }

  function drawWorld(t, cam) {
    bodyWall(BODY);
    // nose intake: round grille on the face
    shape(E(150, 392, 34), C.teal, 3); shape(E(150, 392, 22), C.ground, 2.4);
    for (let k = -1; k <= 1; k++) line([[150 + k * 10, 374], [150 + k * 10, 410]], 2.2, C.tealL);

    // ---------- head: intake room ----------
    if (inView(220, 120, 1080, 560)) {
      const r = room(250, 150, 740, 360, C.teal);
      // air duct from the grille into the room and down the right side to the lungs
      pipe([[150, 392], [300, 392]], 40, C.teal, C.tealL);
      pipe(rpoly([[880, 470], [880, 600], [1110, 640], [1110, 2440], [1000, 2440]], 40), 40, C.teal, C.tealL, { d: rpoly([[880, 470], [880, 600], [1110, 640], [1110, 2440], [1000, 2440]], 40) });
      // fan
      const fa = t * 260;
      out(`<g transform="translate(360 330)">`); for (let i = 0; i < 4; i++) shape(`M0 0Q30 ${-30} 0 -66Q-18 -30 0 0Z`, C.tealL, 2.4, `transform="rotate(${f1(fa + i * 90)})"`); shape(E(0, 0, 12), C.ink, 0); out('</g>');
      // counter: litres per day
      const p = seg(t, K.v11, K.v11 + 1.0);
      flipboard(470, 230, '11,000', '', p, { size: 70, t });
      txt(470, 370, 'LITERS OF AIR / DAY', 34, { fam: FONT.en, w: 800 });
      // the brand nameplate bolted to the intake room
      shape(R(r.x + 40, r.fl - 74, 300, 58, 4), C.ink, 0);
      txt(r.x + 190, r.fl - 33, 'INNER NUMBERS', 36, { fam: FONT.en, w: 900, anchor: 'middle', fill: C.sun, ls: 2 });
      worker(860, r.fl, { s: 1.5, flip: true, cap: C.sun, back: [-120, 0], front: [-160 + 20 * Math.sin(t * 2), -20] });
      // title sign drops on chains over the intake (an object, not a header)
      const d = spring(t - K.title, 7, .32), y0 = lerp(-260, 40, clamp(d, 0, 1.2));
      if (t > K.title - .05) {
        line([[380, -400], [380, y0]], 3); line([[860, -400], [860, y0]], 3);
        shadow(R(300, y0, 640, 108, 6), 12, 9);
        shape(R(300, y0, 640, 108, 6), C.cream, 3.2);
        txt(620, y0 + 76, 'THE MUCUS ESCALATOR', 62, { fam: FONT.en, w: 900, anchor: 'middle', ls: 1 });
      }
    }
    // air particles streaming in: from the grille, through the room, down the duct (teal = air)
    if (t > K.air0 && t < K.press + 3) for (let i = 0; i < 26; i++) {
      const ph = ((t - K.air0) * .45 + hash(i * 2.3)) % 1;
      const kind = i % 3;
      let x, y;
      if (ph < .25) { const u = ph / .25; x = lerp(60, 880, u); y = 392 + Math.sin(u * 6 + i) * 30; }
      else { const u = (ph - .25) / .75; x = u < .1 ? 880 : 1110; y = u < .1 ? lerp(392, 600, u / .1) : lerp(640, 2440, (u - .1) / .9); }
      if (x > 1000 || x < 900) speck(x, y, kind, 1.1, t * 90 + i * 40);
    }

    // ---------- neck: junction (throat) ----------
    if (inView(JUN.x - 60, JUN.y - 40, JUN.x + JUN.w + 60, JUN.y + JUN.h + 40)) {
      const r = room(JUN.x, JUN.y, JUN.w, JUN.h, C.sun);
      // the down-chute (oesophagus) starts at the left
      pipe(rpoly([[620, JUN.y + 250], [220, JUN.y + 270], [190, 1300], [190, 2800], [480, 2900]], 50), 64, C.blushD, C.blushL, { d: rpoly([[620, JUN.y + 250], [220, JUN.y + 270], [190, 1300], [190, 2800], [480, 2900]], 50) });
      // tipping hopper at the top of the escalator
      const tip = ss(seg(t, K.swallow, K.swallow + .35)) * (1 - ss(seg(t, K.swallow + 1.2, K.swallow + 1.8)));
      out(`<g transform="rotate(${f1(-38 * tip)} 760 ${JUN.y + 230})">`);
      shape(`M720 ${JUN.y + 140}L900 ${JUN.y + 140}L880 ${JUN.y + 236}L740 ${JUN.y + 236}Z`, C.wallD, 3);
      out('</g>');
      // lever + worker
      const pull = ss(seg(t, K.swallow - .1, K.swallow + .15));
      out(`<g transform="translate(560 ${r.fl}) rotate(${f1(lerp(30, -30, pull))})">`); shape(R(-5, -120, 10, 120, 3), C.ink, 0); shape(E(0, -124, 13), C.red, 2.4); out('</g>');
      worker(500, r.fl, { s: 1.5, cap: C.red, front: [lerp(130, 150, pull), lerp(-10, 30, pull)], back: [40, 10] });
      const [on, pop] = st(t, K.swallow);
      plaqueN(r.x + 10, JUN.y - 30, 'JUNCTION', 'THROAT', 3, on, pop, 38);
      // "running now" lamp (ending)
      const live = t > K.now && Math.floor(t * 3) % 2;
      shape(E(940, JUN.y + 70, 18), live ? C.red : C.redD, 2.6);
    }

    // ---------- chest: the escalator shaft (cilia) ----------
    if (inView(SHAFT.x - 120, SHAFT.y - 40, SHAFT.x + SHAFT.w + 120, SHAFT.y + SHAFT.h + 40)) {
      room(SHAFT.x, SHAFT.y, SHAFT.w, SHAFT.h, C.teal, { floor: false });
      belt2([BX, SHAFT.y + SHAFT.h - 20], [BX, SHAFT.y + 30], 1.1, -t * 6);
      // cilia: rows of oars on both walls, beating in a travelling wave (metachronal)
      if (ZL > .25) for (let y = SHAFT.y + 50; y < SHAFT.y + SHAFT.h - 30; y += 34) for (const side of [-1, 1]) {
        const x0 = side < 0 ? SHAFT.x + 16 : SHAFT.x + SHAFT.w - 16;
        const a = Math.sin(t * 2 * Math.PI * 2.2 + y * .045) * 0.9;
        const L = 70;
        const tipx = x0 - side * Math.cos(a) * L * .9, tipy = y - Math.sin(Math.abs(a)) * L * .55 - 8;
        out(`<path d="M${f1(x0)} ${f1(y)}Q${f1((x0 + tipx) / 2)} ${f1(y - 6)} ${f1(tipx)} ${f1(tipy)}" fill="none" stroke="${C.ink}" stroke-width="${f1(7 * KS)}" stroke-linecap="round"/>`);
        out(`<path d="M${f1(x0)} ${f1(y)}Q${f1((x0 + tipx) / 2)} ${f1(y - 6)} ${f1(tipx)} ${f1(tipy)}" fill="none" stroke="${C.tealL}" stroke-width="${f1(3.5 * KS)}" stroke-linecap="round"/>`);
      }
      const [on, pop] = st(t, K.esc0);
      plaqueN(SHAFT.x - 60, SHAFT.y + SHAFT.h - 160, 'HAIR ESCALATOR', 'CILIA', 2, on, pop, 36);
      // the two counters: boards bolted left of the shaft, revealed as the voice says them
      const board = (y, val, label, p) => {
        const x = 262; shadow(R(x, y, 290, 190, 6), 12, 9, C.groundD); shape(R(x, y, 290, 190, 6), C.cream, 3);
        flipboard(x + 22, y + 18, val, '', p, { size: 72, t });
        txt(x + 145, y + 168, label, 32, { fam: FONT.en, w: 900, anchor: 'middle', ls: 1 });
      };
      if (t > K.v200 - .2) board(K.b200y, '200', 'HAIRS PER CELL', seg(t, K.v200, K.v200 + .7));
      if (t > K.v20 - .2) board(K.b20y, '20', 'BEATS PER SECOND', seg(t, K.v20, K.v20 + .6));
    }

    // ---------- lungs: the glue press (goblet cells) ----------
    if (inView(80, 2260, 1260, 2760)) {
      const r = room(260, 2300, 940, 440, C.olive);
      // bellows = lungs, breathing slowly at the left of the room
      const br = .5 + .5 * Math.sin(t * 2.2);
      for (const [x, k] of [[360, 1], [470, .9]]) { const h = 120 + 40 * br * k; shape(R(x - 40, r.fl - h, 80, h, 16), C.blushL, 2.8); for (let yy = r.fl - h + 20; yy < r.fl - 10; yy += 22) line([[x - 34, yy], [x + 34, yy]], 2, C.blushD); }
      // belt feeding the escalator foot
      belt2([560, PRESS.belt], [BX + 20, PRESS.belt], 1.1, -t * 6);
      line([[BX, PRESS.belt], [BX, SHAFT.y + SHAFT.h]], 0);
      // the press: stamps on the beat, drips a sticky sheet
      const hits = [K.press, K.press + 1.0, K.fly, K.fly + 1.0, K.traps];
      let dn = 0; for (const h of hits) dn = Math.max(dn, pulse(t, h - .12, .36));
      const py = 2420 + dn * 120;
      trestle(PRESS.x - 120, 2460, r.fl); trestle(PRESS.x + 120, 2460, r.fl);
      shape(R(PRESS.x - 150, 2360, 300, 70, 6), C.olive, 3);
      shape(R(PRESS.x - 14, 2430, 28, py - 2430, 2), C.wallD, 2.4);
      shape(R(PRESS.x - 90, py, 180, 40, 6), C.oliveD, 3);
      if (t > K.press) for (let i = 0; i < 3; i++) { const q = ((t - K.press) * .8 + i / 3) % 1; drop(PRESS.x - 60 + i * 60, py + 52 + q * 70, 9, C.olive, C.oliveL); }
      // dust falling out of the duct onto the sticky sheet
      if (t > K.press - 1) for (let i = 0; i < 6; i++) { const q = ((t * .55 + i / 6) % 1); speck(lerp(1000, 820 - i * 18, q), lerp(2440, PRESS.belt - 30, q), i % 3, 1.1, t * 120 + i * 50); }
      const [on, pop] = st(t, K.press);
      plaqueN(r.x + 30, 2270, 'GLUE PRESS', 'GOBLET CELLS', 1, on, pop, 38);
      worker(1040, r.fl, { s: 1.5, flip: true, cap: C.teal, back: [-40, 0], front: [-120, -30] });
      // the opening gag: a worker holds up a sign next to the blob
      if (t < K.so + .3) {
        const flipq = ss(seg(t, K.lungs - .25, K.lungs + .1));
        worker(640, PRESS.belt - 12, { s: 1.4, cap: C.sun, front: [170, 10], back: [150, 30],
          prop: h => { if (!h) return; const w = 150, hh = 70, sx = h[0] - w / 2, sy = h[1] - 96; line([[h[0], h[1]], [h[0], sy + hh]], 4); shape(R(sx, sy, w, hh, 4), C.cream, 3); txt(h[0], sy + 50, flipq < .5 ? 'SNOT?' : 'LUNG MUCUS', flipq < .5 ? 46 : 30, { fam: FONT.en, w: 900, anchor: 'middle', fill: flipq < .5 ? C.ink : C.oliveD }); } });
      }
    }

    // ---------- diaphragm + stomach (acid drum) ----------
    slab(80, 2770, 1140, 44);
    if (inView(STO.x - 40, STO.y - 40, STO.x + STO.w + 40, STO.y + STO.h + 40)) {
      const r = room(STO.x, STO.y, STO.w, STO.h, C.red);
      const spin = t > K.land ? (t - K.land) * 420 : 0;
      trestle(DRUM[0] - 110, DRUM[1] + 40, r.fl); trestle(DRUM[0] + 110, DRUM[1] + 40, r.fl);
      shape(E(DRUM[0], DRUM[1], 120), C.cream, 3.4);
      out(`<g transform="rotate(${f1(spin)} ${DRUM[0]} ${DRUM[1]})">`); for (let i = 0; i < 6; i++) shape(R(DRUM[0] - 8, DRUM[1] - 112, 16, 60, 4), C.red, 2.2, `transform="rotate(${i * 60} ${DRUM[0]} ${DRUM[1]})"`); out('</g>');
      shape(E(DRUM[0], DRUM[1], 34), C.wallD, 2.6);
      // acid rain from a sprinkler when the cargo lands
      if (t > K.land) for (let i = 0; i < 7; i++) { const q = ((t - K.land) * 1.4 + i / 7) % 1; drop(DRUM[0] - 150 + i * 50, lerp(STO.y + 70, DRUM[1] - 110, q), 8, C.red, C.redL); }
      gauge(1000, r.y + 90, 40, ss(seg(t, K.land, K.job)));
      if (t > K.job) { shape(R(940, r.y + 150, 120, 50, 4), C.ink, 0); txt(1000, r.y + 186, 'DONE', 36, { fam: FONT.en, w: 900, anchor: 'middle', fill: C.sun }); }
      const [on, pop] = st(t, K.land);
      plaqueN(r.x + 30, STO.y - 30, 'ACID DRUM', 'STOMACH', 4, on, pop, 38);
      worker(330, r.fl, { s: 1.5, cap: C.red, front: [lerp(60, 160, pulse(t, K.job - .2, .6)), 0], back: [20, 0] });
    }

    // ---------- the cargo ----------
    const cg = cargo(t);
    if (cg.k > .05) {
      blob(cg.x, cg.y, cg.k, t * 6);
      speck(cg.x - 10 * cg.k, cg.y - 18 * cg.k, 0, .7 * cg.k / 1.5, 20); speck(cg.x + 14 * cg.k, cg.y - 12 * cg.k, 1, .6 * cg.k / 1.5, 0);
    }
  }

  function inner(t) {   // porthole: the outside air, full of dust, pollen and germs flying at us
    fillOnly(R(0, 0, 1080, 1080), C.paper);
    shape(E(760, 300, 110), C.sunL, 0);
    for (const [x, w, h] of [[60, 180, 300], [260, 140, 420], [430, 220, 250], [700, 180, 330], [900, 160, 400]]) { fillOnly(R(x, 820 - h, w, h), C.paperD); for (let yy = 820 - h + 30; yy < 800; yy += 60) for (let xx = x + 22; xx < x + w - 30; xx += 52) fillOnly(R(xx, yy, 22, 30), C.wallS); }
    fillOnly(R(0, 820, 1080, 260), C.wallD); line([[0, 820], [1080, 820]], 3);
    for (let i = 0; i < 40; i++) {
      const ph = ((t - K.pov0) * .6 + hash(i * 1.7)) % 1;
      const s = lerp(.4, 3.2, ph * ph);
      const x = 540 + (hash(i * 3.3) - .5) * 1400 * ph, y = 540 + (hash(i * 5.1) - .5) * 1400 * ph;
      speck(x, y, i % 3, s, t * 60 + i * 30);
    }
  }

  EPS[1] = {
    id: 'e1_mucus', tail: 1.4,
    setup(at, dur) {
      K = {
        snot: at('snot'), lungs: at('lungs'), every: at('every'), v11: at('11'), dust: at('dust'), so: at('so'),
        press: at('sticky'), fly: at('fly'), traps: at('traps'), esc0: at('escalator'), v200: at('200'), v20: at('20'),
        throat: at('throat'), andThen: at('and', 1), swallow: at('swallow'), acid: at('acid'), job: at('job'), now: at("you're"), dur,
      };
      K.title = K.every - .05; K.air0 = K.every - .2;
      K.top = K.throat + .3;                        // cargo reaches the top of the shaft
      K.land = K.acid;                              // lands in the drum on "acid"
      K.pov0 = K.dust - 1.0; K.pov1 = K.so - .05;
      // board heights: placed where the camera will be when each number is said
      const yAt = tt => lerp(PRESS.belt - 14, SHAFT.y + 40, seg(tt, K.esc0, K.top));
      K.b200y = yAt(K.v200) - 300; K.b20y = yAt(K.v20) - 300;
      ev(0, 'belt'); ev(K.lungs - .2, 'flip'); ev(K.title, 'sign');
      ev(K.v11, 'roll', { d: 1.0 }); ev(K.pov0, 'iris'); ev(K.pov1, 'iris');
      ev(K.so + .05, 'whoosh', { d: 1.2 });
      for (const h of [K.press, K.press + 1.0, K.fly, K.fly + 1.0, K.traps]) ev(h, 'press');
      ev(K.press, 'ding'); ev(K.esc0, 'ding'); ev(K.v200, 'roll', { d: .7 }); ev(K.v20, 'roll', { d: .6 });
      ev(K.andThen, 'stop', { d: K.swallow - K.andThen }); ev(K.swallow, 'lever'); ev(K.swallow, 'ding');
      ev(K.swallow + .4, 'whoosh', { d: K.land - K.swallow - .4 }); ev(K.land, 'splash'); ev(K.land, 'ding'); ev(K.job, 'bell');
      ev(K.now, 'whoosh', { d: 1.6 });
      EPS[1].K = K;
    },
    stub(t) { return t < K.press ? 0 : t < K.esc0 ? 1 : t < K.swallow ? 2 : t < K.land ? 3 : 4; },
    fast(t) { return (t > K.lungs + .55 && t < K.every - .05) || (t > K.so && t < K.press - .15) || (t > K.swallow + .4 && t < K.land - .1); },
    camera(t) {
      const cg = cargo(t);
      const blobC = { x: BX - 60, y: PRESS.belt - 110, z: 2.25 };
      const lungsW = { x: 700, y: 2470, z: .98 };
      const head = { x: 620, y: 330, z: 1.32 };
      const press = { x: 760, y: 2490, z: 1.32 };
      const keys = [[0, blobC], [.6, blobC], [K.lungs + .5, lungsW, eio], [K.every - .05, head, eio], [K.so, { ...head, z: 1.38 }, ss], [K.press - .15, press, eio]];
      if (t < K.esc0) return camKeys(keys, t);
      if (t < K.top) { const c = { x: BX - 50, y: cg.y - 180, z: 1.32 }; const u = ss(seg(t, K.esc0, K.esc0 + .6)); return mixc(press, c, u); }
      const jun = { x: 640, y: JUN.y + 180, z: 1.3 };
      const top = { x: BX - 50, y: SHAFT.y + 40 - 180, z: 1.32 };
      if (t < K.swallow + .4) return mixc(top, jun, eio(seg(t, K.top, K.top + .9)));
      const sto = { x: 640, y: STO.y + 200, z: 1.22 };
      if (t < K.land) { const c = { x: lerp(jun.x, 400, ss(seg(t, K.swallow + .4, K.land))), y: Math.max(jun.y, Math.min(cg.y, sto.y)), z: 1.26 }; return c; }
      const all = { x: 650, y: 1640, z: .5 };
      if (t < K.now) return { ...sto, x: lerp(400, sto.x, ss(seg(t, K.land, K.land + .5))) };
      return mixc(sto, all, eio(seg(t, K.now, K.now + 1.8)));
    },
    world: drawWorld,
    screen(t, cam) { porthole(t, cam, 150, 392, K.pov0, K.pov0 + .45, K.pov1 - .4, K.pov1, inner); },
  };
})();

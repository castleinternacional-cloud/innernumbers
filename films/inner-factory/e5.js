// E5 · YOUR BONES SOUND THE ALARM — a standing body cut away from the front: the alarm desk (amygdala) in the head,
// the brake lever + heart pump in the chest, the pump station (adrenal glands) at the waist, the bone factory (osteoblasts)
// inside the thigh. Red = blood/alarm, ochre = osteocalcin (and numbers), teal = air.
(() => {
  let K = {};
  const BODY = 'M650 -760C430 -760 320 -620 320 -420C320 -260 400 -140 520 -100L530 40C260 70 60 160 40 400L40 2500C40 2620 110 2690 190 2720L210 3760C220 3840 560 3840 570 3760L600 2800L700 2800L730 3760C740 3840 1080 3840 1090 3760L1110 2720C1190 2690 1260 2620 1260 2500L1260 400C1240 160 1040 70 770 40L780 -100C900 -140 980 -260 980 -420C980 -620 870 -760 650 -760Z';
  const HEAD = { x: 400, y: -640, w: 500, h: 460 };
  const CHEST = { x: 140, y: 200, w: 1020, h: 560 };
  const ADR = { x: 140, y: 1000, w: 1020, h: 420 };
  const BONE = { x: 240, y: 2860, w: 300, h: 700 };
  const EYE = [520, -470];

  function caps(x, y, k = 1) { out(`<g transform="translate(${f1(x)} ${f1(y)}) scale(${k})">`); shape(R(-22, -12, 44, 24, 12), C.sun, 2.4); fillOnly(R(-14, -8, 10, 6, 3), C.sunL); out('</g>'); }

  function drawWorld(t) {
    const run = t > K.brakes ? 1 : 0;
    bodyWall(BODY);
    // the red nerve wire from the alarm desk down to the pump station (the old story)
    const wire = rpoly([[820, HEAD.y + HEAD.h - 60], [820, 60], [1120, 120], [1120, ADR.y + 120], [980, ADR.y + 120]], 30);
    out(`<path d="${wire}" fill="none" stroke="${C.ink}" stroke-width="${f1(14 * KS)}" stroke-linejoin="round"/>`);
    const live = t > K.danger - .1;
    out(`<path d="${wire}" fill="none" stroke="${live ? C.red : C.redD}" stroke-width="${f1(8 * KS)}" stroke-linejoin="round" ${live ? `stroke-dasharray="26 18" stroke-dashoffset="${f1(-t * 160)}"` : ''}/>`);
    // the blood pipe from the thigh up to the chest (ochre capsules ride it)
    const blood = rpoly([[BONE.x + BONE.w - 40, BONE.y + 120], [640, BONE.y + 120], [640, CHEST.y + CHEST.h - 120], [700, CHEST.y + CHEST.h - 120]], 40);
    pipe(null, 46, C.red, C.redL, { d: blood });

    // ---------- head: ① alarm desk (amygdala) ----------
    if (inView(HEAD.x - 120, HEAD.y - 160, HEAD.x + HEAD.w + 120, HEAD.y + HEAD.h + 60)) {
      const r = room(HEAD.x, HEAD.y, HEAD.w, HEAD.h, C.teal);
      shape(E(EYE[0], EYE[1], 40), C.sun, 3); shape(E(EYE[0], EYE[1], 29), C.tealL, 2.4);
      // alarm desk + big red button
      shape(R(620, r.fl - 120, 240, 120, 6), C.wallD, 3);
      const slap = pulse(t, K.danger - .15, .35);
      shape(E(740, r.fl - 130 + slap * 8, 30), C.red, 3);
      const flash = live && Math.floor(t * 4) % 2;
      // siren lamp on top of the head (outside, on the wall)
      shape(R(615, -800, 70, 40, 8), flash ? C.red : C.redD, 3);
      if (flash) for (let i = 0; i < 5; i++) { const a = -Math.PI / 2 + (i - 2) * .45; line([[650 + Math.cos(a) * 60, -790 + Math.sin(a) * 60], [650 + Math.cos(a) * 110, -790 + Math.sin(a) * 110]], 6); }
      worker(600, r.fl, { s: 1.4, cap: C.red, front: [lerp(110, 160, slap), lerp(10, 60, slap)], back: [40, 0] });
      const [on, pop] = st(t, K.danger);
      plaqueN(r.x - 30, HEAD.y - 36, 'ALARM DESK', 'AMYGDALA', 1, on, pop, 32);
    }

    // ---------- chest: ④ brake lever + heart pump + lung bellows ----------
    if (inView(CHEST.x - 60, CHEST.y - 60, CHEST.x + CHEST.w + 60, CHEST.y + CHEST.h + 60)) {
      const r = room(CHEST.x, CHEST.y, CHEST.w, CHEST.h, C.red);
      const rate = run ? 3.2 : 1.1;
      const beat = .5 + .5 * Math.sin(t * Math.PI * 2 * rate);
      // heart pump
      shape(`M520 ${CHEST.y + 230}C520 ${CHEST.y + 150} 640 ${CHEST.y + 150} 640 ${CHEST.y + 220}C640 ${CHEST.y + 150} 760 ${CHEST.y + 150} 760 ${CHEST.y + 230}C760 ${CHEST.y + 320} 640 ${CHEST.y + 380} 640 ${CHEST.y + 410}C640 ${CHEST.y + 380} 520 ${CHEST.y + 320} 520 ${CHEST.y + 230}Z`, C.red, 3.4, `transform="translate(640 ${CHEST.y + 280}) scale(${f1((1 + .07 * beat) * 100) / 100}) translate(-640 ${-(CHEST.y + 280)})"`);
      gauge(820, CHEST.y + 120, 40, run ? .9 : .35);
      txt(820, CHEST.y + 190, run ? 'FAST' : 'CALM', 28, { fam: FONT.en, w: 900, anchor: 'middle' });
      // lung bellows
      for (const x of [250, 1030]) { const h = 150 + 50 * (.5 + .5 * Math.sin(t * Math.PI * 2 * (run ? 1.6 : .5))); shape(R(x - 60, r.fl - h, 120, h, 18), C.tealL, 2.8); for (let yy = r.fl - h + 20; yy < r.fl - 10; yy += 24) line([[x - 52, yy], [x + 52, yy]], 2, C.teal); }
      // the brake: a big lever holding a brake shoe on the pump's flywheel; knocked off by a capsule
      const off = ss(seg(t, K.brakes - .05, K.brakes + .25));
      const fw = 380, fwy = CHEST.y + 420;
      out(`<g transform="rotate(${f1(t * (run ? 600 : 120))} ${fw} ${fwy})">`); shape(E(fw, fwy, 60), C.wallD, 3); line([[fw - 56, fwy], [fw + 56, fwy]], 4); out('</g>');
      out(`<g transform="rotate(${f1(lerp(0, -55, off))} 470 ${fwy + 90})">`); shape(R(466, fwy - 30, 14, 120, 4), C.ink, 0); shape(R(440, fwy - 34, 40, 30, 4), C.red, 2.4); out('</g>');
      tag(820, CHEST.y + 250, 'BRAKE', 'CALM-DOWN NERVES', C.red, { size: 28 });
      const [on, pop] = st(t, K.brakes);
      plaqueN(r.x + 20, CHEST.y - 34, 'BRAKE LEVER', 'PARASYMPATHETIC', 4, on, pop, 34);
      worker(960, r.fl, { s: 1.4, flip: true, cap: C.sun, front: [run ? 170 : 120, run ? 40 : 0], back: [run ? 150 : 30, 0] });
    }

    // ---------- waist: ② pump station (adrenal glands) — the old story ----------
    if (inView(ADR.x - 60, ADR.y - 60, ADR.x + ADR.w + 60, ADR.y + ADR.h + 60)) {
      const r = room(ADR.x, ADR.y, ADR.w, ADR.h, C.sun);
      const offA = t > K.rodents - .1;
      const ph = offA ? 0 : t * 6;
      for (const x of [420, 720]) {
        const p = .5 + .5 * Math.sin(ph + x);
        shape(R(x - 70, r.fl - 200, 140, 200, 8), offA ? C.wallS : C.blushL, 3);
        shape(R(x - 10, r.fl - 260 - p * 30 * (offA ? 0 : 1), 20, 80, 3), C.ink, 0);
        shape(R(x - 50, r.fl - 280 - p * 30 * (offA ? 0 : 1), 100, 24, 4), C.sunD, 2.4);
      }
      if (!offA && t > K.adrenal) for (let i = 0; i < 4; i++) { const q = ((t * 1.2 + i / 4) % 1); drop(lerp(780, 1000, q), lerp(ADR.y + 200, ADR.y + 140, q), 10, C.red, C.redL); }
      // switch: thrown off when the rodent study is mentioned
      const sw = ss(seg(t, K.rodents - .1, K.rodents + .15));
      shape(R(900, ADR.y + 60, 120, 140, 6), C.wallD, 3);
      out(`<g transform="rotate(${f1(lerp(-30, 30, sw))} 960 ${ADR.y + 150})">`); shape(R(955, ADR.y + 80, 10, 70, 3), C.ink, 0); out('</g>');
      txt(960, ADR.y + 230, sw > .5 ? 'OFF' : 'ON', 32, { fam: FONT.en, w: 900, anchor: 'middle', fill: sw > .5 ? C.red : C.teal });
      // a rodent trots across the floor (the study animals), still startled by the alarm
      if (t > K.rodents - .2 && t < K.so + .8) { const q = seg(t, K.rodents - .2, K.so + .8); const mx = lerp(200, 1120, q), my = r.fl; const hop = Math.abs(Math.sin(q * 30)) * 14; shape(E(mx, my - 22 - hop, 34, 20), '#8E8A84', 2.6); shape(E(mx + 32, my - 34 - hop, 14), '#8E8A84', 2.4); line([[mx - 34, my - 20 - hop], [mx - 70, my - 40 - hop]], 3); out(`<circle cx="${f1(mx + 38)}" cy="${f1(my - 38 - hop)}" r="3" fill="${C.ink}"/>`); }
      // 2019 calendar board
      if (t > K.y2019 - .1) { const p = seg(t, K.y2019, K.y2019 + .6); shadow(R(200, ADR.y + 50, 300, 130, 6), 10, 8, C.wallS); shape(R(200, ADR.y + 50, 300, 130, 6), C.cream, 3); flipboard(220, ADR.y + 64, '2019', '', p, { size: 72, t }); }
      // the empty hook: the missing piece
      const sw2 = Math.sin(t * 3) * 12 * ss(seg(t, K.missing - .3, K.missing));
      if (t > K.missing - .4 && t < K.bone + .3) { line([[640, ADR.y + 14], [640 + sw2, ADR.y + 150]], 3); shape(`M${630 + sw2} ${ADR.y + 150}h20v24q0 30 -18 30q-18 0 -18 -16`, C.wallD, 3); txt(700 + sw2, ADR.y + 210, '?', 90, { fam: FONT.en, w: 900, fill: C.red }); }
      const [on, pop] = st(t, K.adrenal);
      plaqueN(r.x + 20, ADR.y - 34, 'PUMP STATION', 'ADRENAL GLANDS', 2, on, pop, 34);
      if (t > K.story - .2 && t < K.but + 1) { shape(R(r.x + 560, ADR.y - 34, 300, 50, 4), C.ink, 0); txt(r.x + 710, ADR.y + 2, 'THE OLD STORY', 32, { fam: FONT.en, w: 900, anchor: 'middle', fill: C.cream, ls: 1 }); }
    }

    // ---------- thigh: ③ bone factory (osteoblasts) ----------
    if (inView(BONE.x - 120, BONE.y - 80, BONE.x + BONE.w + 300, BONE.y + BONE.h + 80)) {
      const r = room(BONE.x, BONE.y, BONE.w, BONE.h, C.sun);
      // the bone itself as the back wall
      shape(`M${BONE.x + 80} ${BONE.y + 40}C${BONE.x + 40} ${BONE.y + 20} ${BONE.x + 40} ${BONE.y + 90} ${BONE.x + 90} ${BONE.y + 100}V${BONE.y + BONE.h - 100}C${BONE.x + 40} ${BONE.y + BONE.h - 90} ${BONE.x + 40} ${BONE.y + BONE.h - 20} ${BONE.x + 80} ${BONE.y + BONE.h - 40}H${BONE.x + 220}C${BONE.x + 260} ${BONE.y + BONE.h - 20} ${BONE.x + 260} ${BONE.y + BONE.h - 90} ${BONE.x + 210} ${BONE.y + BONE.h - 100}V${BONE.y + 100}C${BONE.x + 260} ${BONE.y + 90} ${BONE.x + 260} ${BONE.y + 20} ${BONE.x + 220} ${BONE.y + 40}Z`, C.wallD, 2.6);
      // stacked presses stamp capsules into the pipe
      for (let k = 0; k < 3; k++) {
        const y = BONE.y + 200 + k * 160;
        const hit = t > K.release ? pulse((t - K.release + k * .17) % .5, 0, .25) : 0;
        shape(R(BONE.x + 40, y - 40, 120, 40, 5), C.sun, 2.6);
        shape(R(BONE.x + 90, y, 20, 20 + hit * 30, 2), C.ink, 0);
        if (t > K.release) caps(BONE.x + 200 + ((t * 2 + k * .3) % 1) * 60, y + 30, .9);
      }
      const [on, pop] = st(t, K.bone);
      plaqueN(r.x - 40, BONE.y - 36, 'BONE FACTORY', 'OSTEOBLASTS', 3, on, pop, 32);
      if (t > K.hormone - .1) tag(BONE.x + BONE.w + 40, BONE.y + 60, 'OSTEOCALCIN', 'A BONE HORMONE', C.sun, { size: 30 });
      worker(BONE.x + 230, r.fl, { s: 1.3, flip: true, cap: C.red, front: [-140, 10], back: [-30, 0] });
    }
    // capsules riding the blood pipe up to the chest (follow the colour)
    if (t > K.release) for (let i = 0; i < 6; i++) {
      const q = ((t - K.release) * .45 + i / 6) % 1;
      const L1 = (640 - (BONE.x + BONE.w - 40)), L2 = (BONE.y + 120) - (CHEST.y + CHEST.h - 120), u = q * (L1 + L2);
      const [x, y] = u < L1 ? [BONE.x + BONE.w - 40 + u, BONE.y + 120] : [640, BONE.y + 120 - (u - L1)];
      caps(x, y, 1.0);
    }
    // leg pistons (the body runs once the brake is off)
    for (const lx of [390, 910]) {
      const p = run ? .5 + .5 * Math.sin(t * 12 + lx) : .5;
      shape(R(lx - 30, 3400 - 120 + p * 80, 60, 200, 6), C.wallD, 3);
      shape(R(lx - 12, 3300, 24, 120 + p * 80, 3), C.ink, 0);
    }
    // the skeleton glows (ending)
    const gl = ss(seg(t, K.skeleton - .2, K.skeleton + .8));
    if (gl > .02) {
      out(`<g opacity="${f1(gl * 100) / 100}">`);
      const bone = (pts, w) => { gline(pts, w + 12, C.ink); gline(pts, w, C.sun); };
      bone([[650, -40], [650, 2400]], 34);
      for (let k = 0; k < 6; k++) { const y = 260 + k * 100; bone([[650, y], [300, y + 60]], 18); bone([[650, y], [1000, y + 60]], 18); }
      bone([[380, 2440], [920, 2440]], 40);
      bone([[420, 2460], [390, 3700]], 40); bone([[880, 2460], [910, 3700]], 40);
      bone([[300, 120], [1000, 120]], 26);
      out('</g>');
    }
  }

  function inner(t) {   // porthole: a car swerving straight at us
    fillOnly(R(0, 0, 1080, 1080), C.paper);
    fillOnly(R(0, 640, 1080, 440), C.wallD); line([[0, 640], [1080, 640]], 3);
    for (let i = 0; i < 6; i++) fillOnly(R(i * 200 - ((t * 400) % 200), 840, 110, 16), C.cream);
    const q = clamp(t / 2.2), s = lerp(.5, 1.7, q * q), x = 540 + Math.sin(t * 5) * 40 * (1 - q);
    out(`<g transform="translate(${f1(x)} 760) scale(${f1(s * 100) / 100})">`);
    shape(R(-220, -170, 440, 150, 30), C.teal, 4); shape(R(-160, -250, 320, 100, 30), C.tealL, 4);
    shape(E(-130, -20, 50), C.ink, 0); shape(E(130, -20, 50), C.ink, 0);
    shape(E(-150, -110, 26), C.sunL, 3); shape(E(150, -110, 26), C.sunL, 3);
    out('</g>');
    if (Math.floor(t * 6) % 2) for (let i = 0; i < 6; i++) { const a = i / 6 * Math.PI * 2; line([[540 + Math.cos(a) * 380, 420 + Math.sin(a) * 300], [540 + Math.cos(a) * 470, 420 + Math.sin(a) * 370]], 8, C.red); }
  }

  EPS[5] = {
    id: 'e5_bones', tail: 1.6,
    setup(at, dur) {
      K = {
        bones: at('bones'), reason: at('reason'), danger: at('danger'), decades: at('decades'), story: at('story'), threat: at('threat'),
        adrenal: at('adrenal'), adrenaline: at('adrenaline'), flee: at('flee'), but: at('but'), y2019: at('2019'), strange: at('strange'),
        rodents: at('rodents'), so: at('so'), missing: at('missing'), bone: at('bone'), release: at('release'), hormone: at('hormone'),
        osteo: at('osteocalcin'), brakes: at('breaks'), skeleton: at('skeleton'), alarm: at('alarm'), dur,
      };
      K.pov1 = K.reason - .1;
      ev(0, 'alarm', { d: 1.0 }); ev(K.pov1, 'iris'); ev(K.danger, 'clunk'); ev(K.danger, 'ding'); ev(K.danger, 'alarm', { d: .8 });
      ev(K.decades, 'whoosh', { d: 1.4 }); ev(K.adrenal, 'ding');
      for (let i = 0; i < 6; i++) ev(K.adrenal + i * .5, 'pump');
      ev(K.y2019, 'roll', { d: .6 }); ev(K.rodents, 'lever'); ev(K.rodents + .5, 'alarm', { d: .8 });
      ev(K.missing + .2, 'stop', { d: K.bone - K.missing - .2 }); ev(K.bone - .3, 'whoosh', { d: .5 }); ev(K.bone, 'press'); ev(K.bone, 'ding');
      for (let i = 0; i < 8; i++) ev(K.release + i * .5, 'press');
      ev(K.brakes, 'lever'); ev(K.brakes, 'ding'); ev(K.brakes + .1, 'heart'); ev(K.brakes + .5, 'heart'); ev(K.brakes + .9, 'heart');
      ev(K.skeleton - .2, 'whoosh', { d: 1.6 }); ev(K.skeleton, 'payoff'); ev(K.alarm, 'alarm', { d: 1.0 });
    },
    stub(t) { return t < K.danger ? 0 : t < K.adrenal ? 1 : t < K.bone ? 2 : t < K.brakes ? 3 : 4; },
    fast(t) { return (t > K.decades + .1 && t < K.story + .3) || (t > K.bone - .35 && t < K.bone + .05) || (t > K.osteo + .9 && t < K.brakes - .1); },
    camera(t) {
      const head = { x: 650, y: HEAD.y + 230, z: 1.6 };
      const adr = { x: 650, y: ADR.y + 220, z: 1.02 };
      const bone = { x: 470, y: BONE.y + 330, z: 1.5 };
      const chest = { x: 650, y: CHEST.y + 300, z: 1.0 };
      const all = { x: 650, y: 1500, z: .4 };
      const keys = [[0, head], [K.decades, head], [K.story + .3, adr, eio], [K.bone - .35, adr], [K.bone, bone, eio], [K.osteo + .9, bone], [K.brakes - .1, chest, eio], [K.skeleton - .2, chest], [K.skeleton + 1.4, all, eio]];
      const c = camKeys(keys, t);
      c.y += shake(t, K.bone, .3, 8) + shake(t, K.brakes, .3, 6);
      return c;
    },
    world: drawWorld,
    screen(t, cam) { porthole(t, cam, EYE[0], EYE[1], -1, -.5, K.pov1 - .4, K.pov1, inner); },
  };
})();

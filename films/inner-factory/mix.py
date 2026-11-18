"""Inner Factory · score + foley + voice mix for one episode.
usage: $LIB/.venv/bin/python mix.py <ep_id> <events.json> <out.wav>
Score: a production-line march at 120 BPM (bar = 2 s) in F major. A base of pizzicato bass + woodblock; every station
that lights ('ding' event) adds a voice (bassoon, clarinet, flute, then glockenspiel+xylophone on the payoff).
'stop' events stop the band dead. Foley is procedural (core/audio/sfx.py) on the event frames.
"""
import sys, os, json
import numpy as np, soundfile as sf
LIB = os.environ.get('LIB', os.path.expanduser('~/lemo-opuscar'))
sys.path.insert(0, LIB)
from core.audio import sampler as S
from core.audio import sfx as X
SR = X.SR

ep, evf, outp = sys.argv[1], sys.argv[2], sys.argv[3]
HERE = os.path.dirname(os.path.abspath(__file__))
E = json.load(open(evf)); DUR = E['dur']; EV = E['ev']
N = int(DUR * SR) + SR
S.seed(7)

# ---------------- score ----------------
BEAT = .5
stops = [(e['t'], e['t'] + e.get('d', .6)) for e in EV if e['type'] == 'stop']
in_stop = lambda t: any(a - .02 <= t < b for a, b in stops)
dings = sorted(e['t'] for e in EV if e['type'] == 'ding')
payoff = next((e['t'] for e in EV if e['type'] in ('payoff',)), dings[-1] if dings else DUR - 3)
def level(t):   # how many station voices are playing at t
    return sum(1 for d in dings if d <= t)
PROG = [('F2', 'C3', ['A3', 'C4']), ('C2', 'G2', ['G3', 'E4']), ('A#1', 'F2', ['D4', 'F4']), ('C2', 'G2', ['E4', 'G4'])]
MEL = ['C5', 'A4', 'F4', 'A4', 'C5', 'D5', 'C5', None, 'A#4', 'G4', 'E4', 'G4', 'A#4', 'C5', 'A#4', None]   # 2 bars of 8ths, repeated
ev = []
nb = int(DUR / BEAT) + 1
for b in range(nb):
    t = b * BEAT
    if t > DUR - .6: break
    bar, beat = divmod(b, 4)
    root, fifth, ch = PROG[bar % 4]
    lv = level(t)
    if in_stop(t): continue
    # base
    if beat in (0, 2): ev.append((t, 'contrabass_pizz', root if beat == 0 else fifth, .45, .62, -.1))
    if beat in (1, 3): ev.append((t, 'woodblock', None, None, .28, .35))
    if beat == 0: ev.append((t, 'bass_drum', None, None, .22, 0))
    # station voices
    if lv >= 1:   # bassoon 8ths ostinato
        for k, p in enumerate([root, fifth]):
            tt = t + k * BEAT / 2
            if not in_stop(tt): ev.append((tt, 'bassoon_stac', S.name(S.midi(p) + 12), .22, .42, -.3))
    if lv >= 2 and beat in (1, 3):   # clarinet off-beat chord stabs
        for p in ch: ev.append((t + BEAT / 2, 'clarinet_stac', p, .2, .34, .3))
    if lv >= 3:   # flute melody
        for k in range(2):
            p = MEL[(b * 2 + k) % len(MEL)]
            tt = t + k * BEAT / 2
            if p and not in_stop(tt): ev.append((tt, 'flute_stac', p, .22, .36, .15))
    if t >= payoff - .01:   # payoff: glock + xylophone double the tune
        for k in range(2):
            p = MEL[(b * 2 + k) % len(MEL)]
            tt = t + k * BEAT / 2
            if p and not in_stop(tt): ev.append((tt, 'glockenspiel', S.name(S.midi(p) + 12), .3, .32, -.15))
music = S.render(ev, dur=N / SR, master=False)
music = music[:N] if len(music) >= N else np.pad(music, ((0, N - len(music)), (0, 0)))
# hard stop envelope (band stops dead), 20 ms ramps
g = np.ones(N)
for a, b in stops:
    i0, i1 = int(a * SR), int(b * SR); r = int(.02 * SR)
    g[i0:i1] = 0; g[max(0, i0 - r):i0] *= np.linspace(1, 0, min(r, i0)); g[i1:i1 + r] *= np.linspace(0, 1, len(g[i1:i1 + r]))
music *= g[:, None]
# end fade
fade = int(.8 * SR); music[N - fade:] *= np.linspace(1, 0, fade)[:, None]
music = S.room(music, size=.35, mix=.14)

# ---------------- foley ----------------
fx = np.zeros((N, 2))
def A(x, t, gain=1.0, pan=0.0):
    if t < 0 or t >= N / SR: return
    X.add(fx, x.astype(np.float64), t, gain, pan)
glock = lambda p, v=.55: S.note('glockenspiel', p, 1.2, vel=v)
for e in EV:
    t, ty, d = e['t'], e['type'], e.get('d', .5)
    if ty == 'press': A(X.thump(.9, 60), t, .55); A(X.clack(.8), t + .01, .35, .1)
    elif ty == 'ding': A(glock('C6' if level(t + .01) % 2 else 'G5'), t, .45, .2)
    elif ty == 'sign':
        for k in range(6): A(X.click(1.4 + k * .1, .6), t - .3 + k * .05, .25, -.2)
        A(X.thump(.8, 90), t + .02, .45); A(X.clack(.9), t + .25, .25)
    elif ty == 'roll':
        for k in range(int(d * 20)): A(X.click(2.2, .5), t + k / 20, .14, .25)
        A(X.clack(1.0), t + d, .35, .25)
    elif ty == 'flip': A(X.clack(1.3), t, .3)
    elif ty == 'iris': A(X.whoosh(.35, .7), t, .3)
    elif ty == 'whoosh': A(X.whoosh(min(1.4, max(.3, d)), 1.0), t, .45)
    elif ty == 'lever': A(X.clack(.7), t, .5); A(X.creak(.8), t + .05, .3)
    elif ty == 'splash':
        x = X.lp(X.noise(.6), 1800) * X.env_exp(.6, .12); A(X.norm(x, .8), t, .5)
    elif ty == 'bell': A(X.ding(1.0), t, .45); A(glock('F6', .7), t, .4)
    elif ty == 'pop': A(X.pop(1.0), t, .9); A(X.thump(1.0, 55), t, .5)
    elif ty == 'tick':
        for k in range(int(d * 8)): A(X.click(1.0, .5), t + k / 8, .18, -.3)
    elif ty == 'alarm':
        for k in range(int(d / .25)): A(X.ding(.9), t + k * .25, .32)
    elif ty == 'belt':
        for k in range(int(d * 6)): A(X.click(.7, .4), t + k / 6, .08, .3)
    elif ty == 'pump':
        x = X.lp(X.noise(.25), 600) * X.env_exp(.25, .07); A(X.norm(x, .7), t, .35, -.2)
    elif ty == 'clunk': A(X.thump(.9, 80), t, .5); A(X.clack(.6), t, .3)
    elif ty == 'drip': A(X.pop(.6), t, .3, .2)
    elif ty == 'heart': A(X.heartbeat(1.0), t, .5)
# room tone
tone = X.lp(X.noise(N / SR), 300) * .012
fx[:len(tone)] += np.stack([tone, tone[::-1]], 1)[:N]

# ---------------- voice ----------------
v, vsr = sf.read(os.path.join(HERE, 'voice', f'{ep}.wav'), dtype='float64')
if v.ndim > 1: v = v.mean(1)
import soxr
v = soxr.resample(v, vsr, SR)
v = X.norm(v, .9)
v = X.compress(v, thr=.22, ratio=3.2)
vb = np.zeros(N); vb[:min(N, len(v))] = v[:N]
# duck + carve: music -10 dB-ish while the voice speaks, 300 Hz–4 kHz carved
env = np.abs(vb); win = int(.12 * SR)
env = np.convolve(env, np.ones(win) / win, 'same'); env = np.clip(env / (env.max() + 1e-9) * 6, 0, 1)
hold = np.maximum.accumulate(env[::-1])[::-1] * 0 + env
duck = 1 - .72 * hold
carve = X.bp(music[:, 0], 300, 4000), X.bp(music[:, 1], 300, 4000)
m2 = np.stack([music[:, 0] - .55 * carve[0] * hold, music[:, 1] - .55 * carve[1] * hold], 1) * duck[:, None]

def rms(x): return np.sqrt(np.mean(x ** 2) + 1e-12)
vm = rms(vb[vb != 0]) if np.any(vb) else .1
m2 *= (vm / (rms(m2) + 1e-9)) * 10 ** (-13 / 20)
mix = m2 + fx * .8 + np.stack([vb, vb], 1)
mix = np.stack([X.limit(mix[:, 0], .95), X.limit(mix[:, 1], .95)], 1)
sf.write(outp, mix.astype(np.float32), SR)
print('mix', outp, round(N / SR, 2), 's; events', len(EV), '; score notes', len(ev))

"""Acting: turns the dialogue timeline + lip-sync + a gesture cue sheet into per-drawing channel dicts
for HOST and GUEST. Everything a performance needs to feel alive:
  - lip sync (viseme + openness) while speaking; a resting smile otherwise
  - IK-posed gestures with anticipation, arc travel and overshoot; speech-beat hand bobs
  - blinks (incl. blinks on big moves), saccades (look at the other person / the camera / props)
  - nods + head tilts driven by vocal emphasis, brows lifting on stress and on questions
  - listening behaviour: nods, reactions on cue
  - breathing, weight sway, and spring physics on the antennae
Precomputed in one sequential pass (springs need history) -> list of dicts per drawing (12/s).
"""
import json
import math
import numpy as np

DPS = 12
L_GUEST = (92.0, 92.0); SH_GUEST = {-1: (-60.0, -324.0), 1: (60.0, -324.0)}
L_HOST = (100.0, 96.0); SH_HOST = {-1: (-74.0, -370.0), 1: (74.0, -370.0)}

# arm entry: (wrist_x, wrist_y, hand_pose, hand_angle_offset)  — local coords (feet origin, y down)
GUEST_G = {
    "lap":       dict(L=(-14, -198, "flat", -10), R=(14, -198, "flat", 10)),
    "wag":       dict(L=(-14, -198, "flat", -10), R=(124, -478, "point", -78), osc=("R", 16, 0, 3.2), brow=0.3, brow_ang=-0.2, smile=0.15),
    "pinch":     dict(L=(-14, -198, "flat", -10), R=(104, -470, "pinch", -58), lid=0.62, smile=0.5, brow_ang=-0.35, tilt=-5, px=0.1),
    "paper":     dict(L=(-96, -300, "hold", 10), R=(96, -300, "hold", -10), prop="paper", px=-0.1),
    "paper_out": dict(L=(-236, -330, "hold", 30), R=(-96, -338, "hold", -20), prop="paper", lean=-4, brow=0.4, smile=0.5),
    "shrug":     dict(L=(-196, -326, "flat", -150), R=(196, -326, "flat", 150), brow=0.7, smile=-0.05, tilt=7, dy=10, lid=0.45),
    "temple":    dict(L=(-14, -198, "flat", -10), R=(184, -652, "point", -122), osc=("R", 0, 7, 4.0), px=0.65, py=-0.75, lid=0.25, brow=0.3, tilt=4),
    "open_arms": dict(L=(-214, -440, "spread", -120), R=(214, -440, "spread", 120), brow=0.75, smile=0.65, pupil=1.15, tilt=-3),
    "explain":   dict(L=(-14, -198, "flat", -10), R=(172, -336, "open", -60), beat="R"),
    "explain2":  dict(L=(-172, -340, "open", 60), R=(14, -198, "flat", 10), beat="L"),
    "count":     dict(L=(-14, -198, "flat", -10), R=(130, -410, "peace", -82), beat="R"),
    "jar":       dict(L=(-70, -206, "hold", 40), R=(70, -206, "hold", -40), prop="jar"),
    "jar_point": dict(L=(-70, -206, "hold", 40), R=(96, -640, "point", -96), prop="jar", brow=0.6, py=-0.3),
    "point_up":  dict(L=(-14, -198, "flat", -10), R=(96, -660, "point", -96), brow=0.6, py=-0.5),
    "hands_head": dict(L=(-112, -700, "spread", -60), R=(112, -700, "spread", 60), brow=1.0, pupil=0.75, smile=-0.3),
    "hold_box":  dict(L=(-86, -330, "hold", 20), R=(86, -330, "hold", -20), prop="box", py=0.4, smile=0.4),
    "peek":      dict(L=(-120, -300, "fist", 0), R=(120, -300, "fist", 0), py=-0.2, brow=0.5),
}
HOST_G = {
    "desk":      dict(L=(-96, -252, "flat", -8), R=(96, -252, "flat", 8)),
    "ask":       dict(L=(-96, -252, "flat", -8), R=(204, -336, "open", -78), beat="R", lean=3, brow=0.4),
    "lean_in":   dict(L=(-44, -300, "fist", 40), R=(44, -300, "fist", -40), lean=8, dy=12, brow=0.5),
    "card":      dict(L=(-96, -252, "flat", -8), R=(160, -470, "hold", -40), prop="card", px=0.4, smile=0.5),
    "read":      dict(L=(-96, -396, "hold", 20), R=(96, -396, "hold", -20), prop="card2", py=0.5),
    "point_up":  dict(L=(-96, -252, "flat", -8), R=(118, -736, "point", -96), brow=0.7, py=-0.6),
    "spread":    dict(L=(-236, -446, "spread", -120), R=(236, -446, "spread", 120), brow=0.6, smile=0.6),
    "chin":      dict(L=(-96, -252, "flat", -8), R=(70, -444, "fist", -60), tilt=8, px=0.5, py=-0.6, brow_ang=0.3),
    "wave":      dict(L=(-96, -252, "flat", -8), R=(214, -540, "open", -96), osc=("R", 18, 0, 3.0), smile=0.7),
}

# Absolute hand directions per gesture (L, R): fingers point this way on screen, whatever the elbow does.
HAND_ABS = {
    "GUEST": {"lap": (17, 163), "wag": (17, 262), "pinch": (17, 258), "shrug": (195, 345), "temple": (17, 190),
              "open_arms": (235, 305), "explain": (17, 330), "explain2": (210, 163), "count": (17, 280),
              "jar_point": (85, 266), "point_up": (17, 268), "hands_head": (300, 240), "heart": (8, 172),
              "somber": (17, 163), "two": (17, 278), "dot": (17, 266), "one": (17, 268), "paper_out": (195, 197)},
    "HOST": {"desk": (39, 141), "ask": (39, 335), "card": (39, 320), "point_up": (39, 268), "spread": (215, 325),
             "chin": (39, 268), "wave": (39, 275), "self": (39, 225), "panic": (245, 295), "welcome": (200, 340),
             "to_audience": (39, 20), "lean_in": (37, 143)},
}

# (line id, fraction of line, actor, gesture) — when a gesture starts. Listener reactions use the
# same table (the actor need not be the speaker).
CUES = [
    ("H01", 0.10, "HOST", "ask"), ("H01", 0.95, "HOST", "desk"),
    ("G01", 0.02, "GUEST", "wag"), ("G01", 0.52, "GUEST", "pinch"), ("G01", 0.99, "GUEST", "lap"),
    ("H02", 0.05, "HOST", "lean_in"), ("H02", 0.97, "HOST", "desk"),
    ("G02", 0.04, "GUEST", "paper"), ("G02", 0.24, "GUEST", "paper_out"), ("G02", 0.70, "GUEST", "shrug"), ("G02", 0.97, "GUEST", "lap"),
    ("H03", 0.0, "HOST", "card"), ("H03", 0.98, "HOST", "desk"),
    ("G03", 0.03, "GUEST", "temple"), ("G03", 0.36, "GUEST", "open_arms"), ("G03", 0.74, "GUEST", "explain"), ("G03", 0.99, "GUEST", "lap"),
    ("H04", 0.06, "HOST", "spread"), ("H04", 0.26, "HOST", "point_up"), ("H04", 0.62, "HOST", "chin"), ("H04", 0.97, "HOST", "desk"),
    ("H05", 0.04, "HOST", "ask"), ("H05", 0.50, "HOST", "chin"), ("H05", 0.80, "HOST", "spread"), ("H05", 0.99, "HOST", "desk"),
    ("H06", 0.02, "HOST", "read"), ("H07", 0.80, "HOST", "spread"), ("H07", 0.99, "HOST", "desk"),
    ("G05", 0.0, "GUEST", "jar"), ("G05", 0.62, "GUEST", "jar_point"), ("G05", 0.99, "GUEST", "lap"),
    ("G06", 0.02, "GUEST", "explain2"), ("G06", 0.55, "GUEST", "hold_box"),
    ("G07", 0.0, "GUEST", "hold_box"), ("G07", 0.92, "GUEST", "lap"),
    ("G08", 0.0, "GUEST", "explain"), ("G08", 0.62, "GUEST", "hands_head"),
    ("G09", 0.0, "GUEST", "shrug"), ("G09", 0.6, "GUEST", "explain2"), ("G09", 0.98, "GUEST", "lap"),
]
REACT = [  # listener face reactions: (line, frac_start, frac_end, actor, dict)
    ("G01", 0.55, 1.0, "HOST", dict(pupil=1.25, brow=0.5)),
    ("G02", 0.75, 1.0, "HOST", dict(brow_ang=0.5, brow=0.2, smile=0.0)),
    ("H03", 0.25, 1.0, "GUEST", dict(smile=0.75, blush=1.6, lid=0.5)),
    ("G03", 0.4, 0.9, "HOST", dict(face="normal", pupil=1.2, brow=0.4)),
    ("H07", 0.82, 1.0, "HOST", dict(face="heart")),
    ("H05", 0.88, 1.0, "HOST", dict(glitch=1.0)),
]


def _ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def _antic_overshoot(x, a=0.08, o=1.18):
    """Anticipation dip then overshoot settle: maps 0..1 -> ~0..1 (with -a then >1)."""
    if x <= 0: return 0.0
    if x >= 1: return 1.0
    if x < 0.18:
        return -a * math.sin(x / 0.18 * math.pi)
    u = (x - 0.18) / 0.82
    c1 = o * 1.70158
    c3 = c1 + 1
    return 1 + c3 * (u - 1) ** 3 + c1 * (u - 1) ** 2


def _move(x, o=0.06, A=0.05):
    """Gesture spacing: ease into a small anticipation, a smooth main move to a slight overshoot, then a settle.
    Continuous in value and slope everywhere."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    if x < 0.14:
        return -A * math.sin(0.5 * math.pi * x / 0.14)
    u = (x - 0.14) / 0.86
    if u < 0.75:
        v = u / 0.75
        return -A + (1 + o + A) * v * v * (3 - 2 * v)
    v = (u - 0.75) / 0.25
    return 1 + o * (1 - v * v * (3 - 2 * v))


def ik(S, T, l1, l2, side, sgn=None):
    """Two-bone IK. Of the two elbow solutions take the natural one — elbow low and out from the body
    (down for a hand raised at the side, out for a hand in the lap, up only when the hand goes overhead) —
    unless a bend sign is forced (keeps one gesture's elbow from flipping while its hand bobs or waves).
    Returns (shoulder_deg, elbow_deg, sgn)."""
    dx, dy = T[0] - S[0], T[1] - S[1]
    d = min(max(math.hypot(dx, dy), 14.0), l1 + l2 - 0.5)
    th = math.atan2(dy, dx)
    a = math.acos(max(-1.0, min(1.0, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))))
    b = math.acos(max(-1.0, min(1.0, (l1 * l1 + l2 * l2 - d * d) / (2 * l1 * l2))))
    if sgn is None:
        def score(sg):
            r = th + sg * a
            return math.sin(r) + 0.8 * side * math.cos(r)        # elbow y (down) + outward x
        sgn = 1.0 if score(1.0) >= score(-1.0) else -1.0
    return math.degrees(th + sgn * a), math.degrees(-sgn * (math.pi - b)), sgn


def _wrap(a, side):
    """Shoulder angles live on the arc that never swings through the chest: left arm [0,360), right (-180,180]."""
    if side < 0:
        return a % 360.0
    return (a + 180.0) % 360.0 - 180.0


def _adiff(a, b):
    return (b - a + 180.0) % 360.0 - 180.0


class Track:
    def __init__(self, actor, tl, lips, seed):
        self.actor = actor
        self.lines = [l for l in tl["lines"]]
        self.my = [l for l in self.lines if l["spk"] == actor]
        self.lips = lips
        self.rng = np.random.default_rng(seed)
        self.G = HOST_G if actor == "HOST" else GUEST_G
        self.SH = SH_HOST if actor == "HOST" else SH_GUEST
        self.LL = L_HOST if actor == "HOST" else L_GUEST
        L = {l["id"]: l for l in self.lines}
        self.cues = sorted([(L[i]["t0"] + (L[i]["t1"] - L[i]["t0"]) * f, g) for i, f, a, g in CUES if a == actor])
        self.react = [(L[i]["t0"] + (L[i]["t1"] - L[i]["t0"]) * f0, L[i]["t0"] + (L[i]["t1"] - L[i]["t0"]) * f1, d) for i, f0, f1, a, d in REACT if a == actor]
        dur = tl["duration"]
        self.blinks = []
        t = 0.6 + self.rng.random()
        while t < dur:
            self.blinks.append(t)
            if self.rng.random() < 0.15:
                self.blinks.append(t + 0.28)
            t += self.rng.uniform(2.0, 4.6)
        for tc, g in self.cues:
            if self.rng.random() < 0.55:
                self.blinks.append(tc + 0.04)
        self.blinks.sort()
        self.sacc = []
        t = 0.0
        while t < dur:
            self.sacc.append((t, self.rng.uniform(-0.18, 0.18), self.rng.uniform(-0.12, 0.12), self.rng.random()))
            t += self.rng.uniform(0.7, 2.2)
        self.nods = []
        t = 1.0
        while t < dur:
            self.nods.append(t)
            t += self.rng.uniform(2.8, 5.5)
        self.sp = dict(L=np.zeros(2), Lv=np.zeros(2), R=np.zeros(2), Rv=np.zeros(2))
        self.cur_g, self.start, self.tc, self.dur, self.last, self.last_pose, self.start_pose = None, None, 0.0, 0.38, None, None, None
        self.prev_head = None

    def speaking(self, t):
        for l in self.my:
            if l["t0"] <= t < l["t1"]:
                return l
        return None

    def other_speaking(self, t):
        for l in self.lines:
            if l["spk"] != self.actor and l["t0"] <= t < l["t1"]:
                return l
        return None

    def gesture_at(self, t):
        prev, cur, tc = INITIAL.get(self.actor, "lap" if self.actor == "GUEST" else "desk"), None, -99.0
        cur = prev
        for tg, g in self.cues:
            if tg <= t:
                prev, cur, tc = cur, g, tg
        return prev, cur, tc

    def _pose(self, gname, t, beat=None, emph=0.0):
        """Joint angles for a gesture's pose at time t (osc + speech-beat bobs re-solved with the gesture's own bend)."""
        g = self.G[gname]
        out = {}
        for side, key in ((-1, "L"), (1, "R")):
            x0, y0, pose, ho = g[key]
            _, _, sgn = ik(self.SH[side], (x0, y0), self.LL[0], self.LL[1], side)
            x, y = x0, y0
            wob = 0.0
            if "osc" in g and g["osc"][0] == key:
                _, ax, ay, f = g["osc"]
                ph = math.sin(t * f * 2 * math.pi)
                x += ax * ph; y += ay * ph
                wob = 12.0 * ph
            if beat == key:
                y -= 26 * emph; x += 8 * emph * side
            sh, el, _ = ik(self.SH[side], (x, y), self.LL[0], self.LL[1], side, sgn)
            tab = HAND_ABS.get(self.actor, {}).get(gname)
            if tab is not None:
                hand_abs = tab[0 if side < 0 else 1] + wob
            else:                                            # untabled gesture: keep its authored offset on the old bend
                osh, oel, _ = ik(self.SH[side], (x0, y0), self.LL[0], self.LL[1], side, 1.0 if side < 0 else -1.0)
                hand_abs = osh + oel + ho
            out[key] = (_wrap(sh, side), el, hand_abs, pose)
        return out

    def _wrists(self, gname, t):
        g = self.G[gname]
        out = {}
        for side, key in ((-1, "L"), (1, "R")):
            x, y, pose, ho = g[key]
            if "osc" in g and g["osc"][0] == key:
                _, ax, ay, f = g["osc"]
                x += ax * math.sin(t * f * 2 * math.pi)
                y += ay * math.sin(t * f * 2 * math.pi)
            out[key] = [x, y, pose, ho]
        return out

    def frame(self, t):
        P = {}
        ln = self.speaking(t)
        prev, cur, tc = self.gesture_at(t)
        u = (t - tc) / 0.38
        k = _antic_overshoot(u)
        gA, gB = self.G[prev], self.G[cur]
        wa, wb = self._wrists(prev, t), self._wrists(cur, t)
        emph = 0.0
        if ln is not None:
            lp = self.lips[ln["id"]]
            fi = int((t - ln["t0"]) * 24)
            fi = min(max(fi, 0), lp["n"] - 1)
            P["vis"] = lp["vis"][fi]
            P["mo"] = float(lp["open"][fi]) * 1.0
            emph = float(np.mean(lp["emph"][max(0, fi - 2): fi + 3]))
        else:
            P["vis"] = "X"; P["mo"] = 0.0
        pB = self._pose(cur, t, beat=gB.get("beat") if ln is not None else None, emph=emph)
        if cur != self.cur_g:                                 # a new gesture: move from wherever the arms ARE right now
            self.start = self.last if self.last is not None else {kk: pB[kk][:3] for kk in ("L", "R")}
            self.start_pose = self.last_pose if self.last_pose is not None else {kk: pB[kk][3] for kk in ("L", "R")}
            self.cur_g, self.tc = cur, tc
            dmax = max(max(abs(pB[kk][0] - self.start[kk][0]), abs(pB[kk][1] - self.start[kk][1]),
                           abs(_adiff(self.start[kk][2], pB[kk][2])) * 0.5) for kk in ("L", "R"))
            self.dur = min(max(0.30 + dmax / 330.0, 0.36), 0.9)  # big swings take longer: no joint leaps between drawings
        mu = (t - self.tc) / self.dur
        mk = _move(mu)
        u = mu
        last, last_pose = {}, {}
        for side, key in ((-1, "L"), (1, "R")):
            sha, ela, hda = self.start[key]; shb, elb, hdb, pb = pB[key]
            sh = sha + (shb - sha) * mk                       # wrapped arcs: the arm swings out, never through the chest
            el = ela + (elb - ela) * mk
            if ela * elb > 0:                                 # same bend both ends: fold a little more mid-swing
                el += math.copysign(8.0, elb) * math.sin(min(max(mu, 0), 1) * math.pi)
            hand = hda + _adiff(hda, hdb) * min(max(mk, 0), 1.06)
            pre = "a" + key
            P[pre + "_sh"] = sh; P[pre + "_el"] = el
            P[pre + "_hand"] = hand - (sh + el)
            P[pre + "_pose"] = pb if mu > 0.45 else self.start_pose[key]
            last[key] = (sh, el, hand); last_pose[key] = P[pre + "_pose"]
        self.last, self.last_pose = last, last_pose
        P["prop"] = gB.get("prop") if u > 0.3 else gA.get("prop")
        P["prop_k"] = min(max(u, 0), 1) if gB.get("prop") else 1.0

        def mixv(key, base):
            a = gA.get(key, base); b = gB.get(key, base)
            return a + (b - a) * _ease(u * 1.3)
        lid = mixv("lid", 0.32); smile = mixv("smile", 0.3 if self.actor == "GUEST" else 0.35)
        brow = mixv("brow", 0.0); brow_ang = mixv("brow_ang", 0.0); tilt = mixv("tilt", 0.0)
        lean = mixv("lean", 0.0); dy = mixv("dy", 0.0); pupil = mixv("pupil", 1.0)
        gpx = gB.get("px"); gpy = gB.get("py")
        # gaze
        other = -1 if self.actor == "GUEST" else 1
        st = [s for s in self.sacc if s[0] <= t][-1]
        if ln is not None:
            base = (other * 0.62, 0.0) if st[3] < 0.62 else (0.0, 0.05)
        else:
            base = (other * 0.66, 0.05)
        px, py = base[0] + st[1], base[1] + st[2]
        if gpx is not None and u > 0.2:
            px = gpx + st[1] * 0.4
        if gpy is not None and u > 0.2:
            py = gpy + st[2] * 0.4
        # blinks
        bl = 0.0
        for b in self.blinks:
            d = t - b
            if -0.05 <= d <= 0.17:
                bl = max(bl, 1 - abs(d - 0.05) / 0.11)
        bl = min(1.0, bl * 1.4)
        # head: emphasis nods + tilt, listening nods, idle noise
        nod = 9 * emph
        if ln is None and self.other_speaking(t) is not None:
            for nt in self.nods:
                d = t - nt
                if 0 <= d < 0.9:
                    nod += 7 * math.sin(d / 0.9 * 2 * math.pi * 2) ** 2
        n1 = math.sin(t * 0.73 + (1.3 if self.actor == "HOST" else 0)) * 2.2 + math.sin(t * 1.9) * 0.8
        tilt_total = tilt + n1 + (4 * emph * (1 if int(t * 0.8) % 2 else -1))
        if ln is not None and ln["text"].rstrip().endswith("?") and t > ln["t0"] + (ln["t1"] - ln["t0"]) * 0.65:
            brow += 0.5; tilt_total += 3
        brow += 0.55 * emph
        P.update(lid=lid, smile=smile, browL=brow, browR=brow, brow_ang=brow_ang, head_tilt=tilt_total, head_dy=dy + nod,
                 lean=lean + math.sin(t * 0.41) * 1.2, px=float(np.clip(px, -1, 1)), py=float(np.clip(py, -1, 1)), pupil=pupil,
                 blinkL=bl, blinkR=bl, breath=t * 0.27, squash=1.0 + 0.025 * emph, blush=1.0, face="normal", glitch=0.0)
        if self.actor == "HOST" and (abs(math.sin(t * 7.3)) > 0.995):
            P["glitch"] = 0.35
        for r0, r1, d in self.react:
            if r0 <= t < r1:
                for kk, vv in d.items():
                    if kk in ("brow",):
                        P["browL"] += vv; P["browR"] += vv
                    else:
                        P[kk] = vv
        # antenna springs (driven by head motion)
        head = np.array([P["head_tilt"] * 4.0 + P["lean"] * 6.0, P["head_dy"] * 2.0])
        if self.prev_head is None:
            self.prev_head = head.copy(); self.prev_v = np.zeros(2)
        v = (head - self.prev_head) * DPS
        acc = (v - self.prev_v) * DPS
        self.prev_head = head.copy(); self.prev_v = v
        dt = 1.0 / DPS
        for key, ph in (("L", 0.0), ("R", 1.7)):
            x, xv = self.sp[key], self.sp[key + "v"]
            idle = np.array([math.sin(t * 1.3 + ph) * 3.0, math.sin(t * 2.1 + ph) * 2.0])
            force = -60.0 * (x - idle) - 6.5 * xv - acc * 0.012
            xv = xv + force * dt
            x = x + xv * dt
            x = np.clip(x, -40, 40)
            self.sp[key], self.sp[key + "v"] = x, xv
        P["antL"] = (float(self.sp["L"][0]), float(self.sp["L"][1]))
        P["antR"] = (float(self.sp["R"][0]), float(self.sp["R"][1]))
        return P


INITIAL = {}


def load_cues(path):
    """Per-episode cue sheet: {"cues": [[line, frac, actor, gesture], ...], "react": [[line, f0, f1, actor, {...}], ...],
    "gestures": {"HOST": {name: {...}}, "GUEST": {...}}} — replaces the episode-1 tables."""
    global CUES, REACT, INITIAL
    d = json.load(open(path))
    INITIAL = dict(d.get("initial", {}))
    CUES = [tuple(c) for c in d.get("cues", [])]
    REACT = [tuple(r) for r in d.get("react", [])]
    for actor, table in d.get("gestures", {}).items():
        (HOST_G if actor == "HOST" else GUEST_G).update(table)
    for actor, tab in d.get("hand_abs", {}).items():
        HAND_ABS.setdefault(actor, {}).update({k: tuple(v) for k, v in tab.items()})


def precompute(tl_path, lips_path, out_path, cues_path=None):
    if cues_path:
        load_cues(cues_path)
    tl = json.load(open(tl_path)); lips = json.load(open(lips_path))
    n = int(math.ceil(tl["duration"] * DPS)) + 1
    tracks = {"HOST": Track("HOST", tl, lips, 11), "GUEST": Track("GUEST", tl, lips, 23)}
    frames = []
    for d in range(n):
        t = d / DPS
        frames.append({k: tr.frame(t) for k, tr in tracks.items()})
    json.dump(frames, open(out_path, "w"))
    return frames


if __name__ == "__main__":
    import sys
    fr = precompute(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
    print("drawings", len(fr))
    for d in (80, 130, 220, 400):
        g = fr[d]["GUEST"]; h = fr[d]["HOST"]
        print(d, "G", g["vis"], round(g["mo"], 2), g["aR_pose"], round(g["aR_sh"]), round(g["aR_el"]), "| H", h["vis"], h["aR_pose"])


# DON'T MELT
# JIN2 · @jin_22ee · 2026    Free to use for personal projects, see LICENSE.txt.
#
# run:   pip install -r requirements.txt
#        python snowman.py
# keys:  Space pause · R restart · S screenshot · Esc quit

import sys
import time
from pathlib import Path

import pygame
import numpy as np

TAU = np.pi * 2
LOOP = 22.0                  # seconds
VOX = 0.05                   # one voxel
POOLS = ["1il!;:", "rtfjcvxz=+", "aeoun0{}[]<>", "08B$#&%Q"]
CHARS = " .,:~+*^01|/\\-_#" + "".join(POOLS)
AT = {c: i for i, c in enumerate(CHARS)}
FILL = np.array([[AT[p[k % len(p)]] for k in range(12)] for p in POOLS])

SNOW, HOLE, STICK, FLAKE, PUDDLE, CHUNK = 0, 1, 2, 3, 5, 6


def smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


# face: eyes, smile and buttons are black squares

# (column, row) on the front of each block, counted from the bottom-left voxel
EYES = {(2, 5), (5, 4)}                       # head: 8 x 8, left eye a little higher
SMILE = {(1, 3), (2, 2), (3, 1), (4, 1), (5, 2), (6, 2)}      # smile
BUTTONS_MID = {(4, 7), (4, 5), (4, 3)}        # middle: 10 x 10
BUTTONS_LOW = {(5, 9), (5, 7), (5, 5)}        # bottom: 12 x 12


def block(center, n, mark=(), per=None):
    # six faces of an n x n x n voxel block as points; marked front voxels become holes
    per = per or n * 3
    h = n * VOX / 2
    g = (np.arange(per) + 0.5) / per * 2 * h - h
    u, v = [a.ravel() for a in np.meshgrid(g, g)]
    P, N, F = [], [], []
    for axis in range(3):
        for sign in (-1, 1):
            p = np.zeros((len(u), 3))
            p[:, axis] = sign * h
            p[:, (axis + 1) % 3], p[:, (axis + 2) % 3] = u, v
            nn = np.zeros((len(u), 3))
            nn[:, axis] = sign
            P.append(p), N.append(nn), F.append(np.full(len(u), axis * 2 + (sign > 0)))
    p, n_, f = np.concatenate(P), np.concatenate(N), np.concatenate(F)
    vox = np.clip(((p + h) / VOX).astype(int), 0, n - 1)
    hole = (f == 5) & np.array([(a, b) in mark for a, b in zip(vox[:, 0], vox[:, 1])])
    return p + center, n_, f, vox, hole


FACE_SQUARES = []                             # eyes, smile, buttons: 4 corners each


def build_snowman():
    P, N, PART, TAG, VID = [], [], [], [], []
    for b, (y, n, mark) in enumerate(((0.30, 12, BUTTONS_LOW), (0.85, 10, BUTTONS_MID),
                                      (1.30, 8, EYES | SMILE))):        # each tier smaller
        p, nn, f, vox, hole = block(np.array([0, y, 0]), n, mark)
        P.append(p), N.append(nn), PART.append(b * 10 + f), TAG.append(np.full(len(p), SNOW))
        h = n * VOX / 2                                       # face squares are exact, not from points
        for cx, cy in mark:
            x0, y0 = -h + cx * VOX, y - h + cy * VOX
            FACE_SQUARES.append([[x0, y0, h], [x0 + VOX, y0, h], [x0 + VOX, y0 + VOX, h], [x0, y0 + VOX, h]])
        VID.append(b * 1000 + vox[:, 0] * 100 + vox[:, 1] * 10 + vox[:, 2])
    return [np.concatenate(a) for a in (P, N, PART, TAG, VID)]


BODY_P, BODY_N, BODY_PART, BODY_TAG, BODY_VID = build_snowman()
FACE_SQUARES = np.array(FACE_SQUARES)          # (squares, 4 corners, xyz)


_FACE = {}


def face_cells(t, cols, rows, aspect, F):
    # letter cells covered by a black face square, computed once and cached
    key = (cols, rows, round(aspect, 6), F)
    if key not in _FACE:
        _FACE[key] = _face_cells(cols, rows, aspect, F)
    return _FACE[key]


def _face_cells(cols, rows, aspect, F):
    sq = FACE_SQUARES.reshape(-1, 3)
    x, y, z = look(sq, 0.0)
    sx = (0.5 + x / z * F * 0.5) * cols
    sy = (0.5 - y / z * F * 0.5 * aspect) * rows
    q = np.stack([sx, sy], 1).reshape(-1, 4, 2)
    mask = np.zeros((rows, cols), bool)
    cell = aspect * rows / cols                         # letter cell width / height
    wide = np.median(np.abs(q[:, 1, 0] - q[:, 0, 0]))   # one face pixel, in letter cells
    w = max(2, int(round(wide * 1.3)))                  # every square the same size
    h = max(1, int(round(w * cell)))                    # and square on screen
    for quad in q:
        cx, cy = quad.mean(0)
        c0, r0 = int(round(cx - w / 2)), int(round(cy - h / 2))
        mask[max(r0, 0):max(r0 + h, 0), max(c0, 0):max(c0 + w, 0)] = True
    return mask


# which voxels fall off, and when

THUDS = [9.6, 11.4, 11.7, 13.5, 15.0, 15.2, 16.8, 18.1, 18.4, 19.6, 20.6, 20.8]


def plan_thuds():
    vids, idx = np.unique(BODY_VID, return_inverse=True)
    center = np.array([BODY_P[idx == i].mean(0) for i in range(len(vids))])
    r = np.random.default_rng(3)
    face = (center[:, 2] > 0.17) & (np.abs(center[:, 0]) < 0.2)     # his face and buttons stay
    free = ~face
    when = np.full(len(vids), np.inf)
    for i, t in enumerate(THUDS):
        # top edges first, left and right taking turns
        side = 1 if i % 2 == 0 else -1
        score = center[:, 1] % 0.48 + side * center[:, 0] * 0.8 + r.random(len(vids)) * 0.35
        seed = np.argmax(np.where(free, score, -9))
        near = free & (np.linalg.norm(center - center[seed], axis=1) < 0.09 + r.random() * 0.04)
        when[near], free[near] = t, False
    return idx, center, when


VIDX, V_CENTER, V_WHEN = plan_thuds()
V_RAND = np.random.default_rng(9).random((len(V_CENTER), 3))   # per-piece bounce


def melted(t):
    return np.searchsorted(THUDS, t) / len(THUDS)


# snowfall

FLAKES = np.random.default_rng(5).random((420, 4))


def snowfall(t):
    f = FLAKES
    x = f[:, 0] * 5 - 2.5 + 0.12 * np.sin(t * 0.8 + f[:, 3] * TAU)
    y = (f[:, 1] * 3.2 - t * (0.14 + 0.18 * f[:, 2])) % 3.2
    z = f[:, 2] * 4.5 - 3.0
    return np.stack([x, y, z], 1), 0.3 + 0.7 * f[:, 2]       # nearer flakes brighter


# arms: two sticks with a small twitch

TWITCH = [3.9, 4.3, 6.2, 10.4, 14.1, 17.5, 21.0]


def arms(t):
    twitch = sum(np.exp(-((t - c) / 0.12) ** 2) for c in TWITCH)
    droop = 0.10 * melted(t)
    sag = 1 - 0.06 * melted(t)
    left = (np.array([-.25, .84 * sag, 0]), np.array([-.56, (.64 - droop) * sag, .04]))     # left arm
    right = (np.array([.25, .98 * sag, 0]), np.array([.52, (.58 + .08 * twitch - droop) * sag, .04]))  # right arm
    pts = []
    for a, b in (left, right):
        u = np.linspace(0, 1, 220)[:, None]
        line = a + u * (b - a)
        pts += [line, line + [0, .012, 0]]            # two strands for a thicker stick
    return np.concatenate(pts)


# scene

def pose(p, t):
    # sag while melting: shorter, wider at the base
    m = melted(t)
    q = p.copy()
    spread = 1 + 0.10 * m * np.clip(1 - q[:, 1] / 0.4, 0, 1)
    q[:, 0] *= spread
    q[:, 2] *= spread
    return q


def gather(p, t, seed):
    # build-in from the bottom; 1 in 10 points flies in, the rest fade in
    r = np.random.default_rng(seed).random((len(p), 3))
    k = smooth((t - 0.2 - p[:, 1] * 1.1 - r[:, 0] * 0.6) / 0.9)
    away = np.stack([np.cos(r[:, 1] * TAU), r[:, 2], np.sin(r[:, 1] * TAU)], 1) * 0.7
    return p + away * (1 - k)[:, None] ** 2, k, (np.arange(len(p)) % 10) == 0


def scene(t):
    rest = pose(BODY_P, t)
    body, k, flyer = gather(rest, t, 1)

    # falling chunks: gravity, two bounces, skid, then melt into the puddle
    G = 9.8
    dt = np.maximum(t - V_WHEN[VIDX], 0)
    gone = t >= V_WHEN[VIDX]
    rv = V_RAND[VIDX]
    y0 = np.maximum(rest[:, 1], 0.01)
    land = np.sqrt(2 * y0 / G)
    fall = np.minimum(dt, land)
    drift = np.sign(rest[:, 0:1] + 1e-6) * [0.08, 0, 0] + [0, 0, 0.04]
    p = rest + drift * fall[:, None]
    p[:, 1] = rest[:, 1] - 0.5 * G * fall ** 2

    tb = np.maximum(dt - land, 0)                              # time since landing
    h1 = 0.06 + 0.07 * rv[:, 0]                                # first bounce height
    d1 = 2 * np.sqrt(2 * h1 / G)
    d2 = d1 * 0.55
    hop = np.where(tb < d1, 4 * h1 * (tb / d1) * (1 - tb / d1),
                   np.where(tb < d1 + d2, 4 * h1 * 0.3 * ((tb - d1) / d2) * (1 - (tb - d1) / d2), 0))
    ang = rv[:, 1] * TAU
    skid = (0.10 + 0.22 * rv[:, 2]) * (1 - np.exp(-tb * 3.5))  # skid with friction
    p[:, 0] += np.where(tb > 0, np.cos(ang) * skid, 0)
    p[:, 2] += np.where(tb > 0, np.sin(ang) * skid, 0)
    p[:, 1] = np.where(tb > 0, 0.02 + hop, p[:, 1])
    still = tb > d1 + d2
    melt_in = smooth((tb - d1 - d2) / 1.2)
    p[:, 1] = np.where(still, 0.02 * (1 - melt_in) + 0.004, p[:, 1])
    landed = gone & still & (melt_in > 0.5)                    # turned to water
    body = np.where(gone[:, None], p, body)

    light = np.array([-.45, .7, .55]) / np.linalg.norm([-.45, .7, .55])
    shade = 0.25 + 0.75 * np.clip(BODY_N @ light, 0, 1)
    tag = np.where(gone, np.where(landed, PUDDLE, CHUNK), BODY_TAG)
    part = np.where(gone | (k < 0.95), -2, BODY_PART)
    shade = np.where(k < 0.95, np.where(flyer, shade * (0.3 + 0.7 * k), 0), shade)

    A = arms(t)
    S, s_shade = snowfall(t)
    shown = smooth((t - 1.8) / 1.0)
    P = np.concatenate([body, A, S])
    shade = np.concatenate([shade, np.full(len(A), .85 * shown), s_shade * smooth(t / 2)])
    tag = np.concatenate([tag, np.full(len(A), STICK), np.full(len(S), FLAKE)])
    part = np.concatenate([part, np.full(len(A), 70), np.full(len(S), -1)])
    info = {"melt": float(melted(t)), "temp": -6.0 + 9.0 * smooth((t - 8) / 14)}
    return P, shade, tag, part, info


# fixed camera

def look(P, t):
    yaw, pitch, dist, ty = 0.42, 0.14, 3.46741, 0.84
    target = np.array([0, ty, 0])
    eye = target + dist * np.array([np.sin(yaw) * np.cos(pitch), np.sin(pitch), np.cos(yaw) * np.cos(pitch)])
    fwd = (target - eye) / np.linalg.norm(target - eye)
    right = np.cross(fwd, [0, 1.0, 0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    rel = P - eye
    return rel @ right, rel @ up, rel @ fwd


def outline_letter(gx, gy):
    ax, ay = np.abs(gx), np.abs(gy)
    c = np.where(ax > 2 * ay, AT["|"], np.where(ay > 2 * ax, np.where(gy > 0, AT["_"], AT["-"]),
                 np.where(gx * gy > 0, AT["/"], AT["\\"])))
    return np.where((ax + ay) == 0, AT["+"], c)


def frame(t, cols, rows, aspect, zoom=1.0):
    # project points to the letter grid
    P, shade, T, K, info = scene(t)
    x, y, z = look(P, t)
    z = z - 0.006 * (T == HOLE)               # face holes win their cell
    F = 3.25 * zoom
    sx = (0.5 + x / z * F * 0.5) * cols
    sy = (0.5 - y / z * F * 0.5 * aspect) * rows
    order = np.argsort(-z)                    # painter's order
    sx, sy, z, shade, T, K = sx[order], sy[order], z[order], shade[order], T[order], K[order]
    ix, iy = sx.astype(int), sy.astype(int)
    ok = (ix >= 0) & (ix < cols) & (iy >= 0) & (iy < rows)

    part = np.full((rows, cols), -1)
    depth = np.full((rows, cols), 99.0)
    lum = np.zeros((rows, cols))
    tag = np.zeros((rows, cols), int)
    b = ok & (K >= 0) & (shade > 0)
    part[iy[b], ix[b]], depth[iy[b], ix[b]] = K[b], z[b]
    lum[iy[b], ix[b]], tag[iy[b], ix[b]] = shade[b], T[b]
    body = part >= 0

    pp = np.pad(part, 1, constant_values=-1)
    pd = np.pad(depth, 1, constant_values=99)
    edge = np.zeros_like(body)
    gx = np.zeros((rows, cols))
    gy = np.zeros((rows, cols))
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == dy == 0:
                continue
            nb = pp[1 + dy:rows + 1 + dy, 1 + dx:cols + 1 + dx]
            nz = pd[1 + dy:rows + 1 + dy, 1 + dx:cols + 1 + dx]
            out = body & ((nb < 0) | ((nb != part) & (nz > depth + 0.02)))
            gx += dx * out
            gy += dy * out
            if dx == 0 or dy == 0:
                edge |= out

    r, c = np.mgrid[0:rows, 0:cols]
    h = (r * 7919 + c * 104729) % 9973
    level = np.clip((lum * 4).astype(int), 0, 3)
    inside = FILL[level, (h + (t * 5 + h % 11).astype(int)) % 12]
    face_front = part == 25                                              # front of the head
    inside = np.where(face_front, FILL[3, h % 12], inside)        # dense letters on the face
    char = np.where(body, np.where(edge, outline_letter(gx, gy), inside), 0)
    lum = np.where(body, np.where(edge, 0.80 + 0.20 * lum, 0.30 + 0.42 * lum), 0)
    lum = np.where(face_front & ~edge, 0.62, lum)
    hole = body & face_cells(t, cols, rows, aspect, F)
    char, lum = np.where(hole, 0, char), np.where(hole, 0, lum)
    hp = np.pad(hole, 1)
    ring = body & ~hole & (hp[:-2, 1:-1] | hp[2:, 1:-1] | hp[1:-1, :-2] | hp[1:-1, 2:])
    lum = np.where(ring, 1.0, lum)                                       # bright rim around face holes

    # chunks, puddle and snowflakes, occluded by the body
    fx = ok & (K < 0) & (shade > 0.03)
    hidden = body[iy[fx], ix[fx]] & (depth[iy[fx], ix[fx]] < z[fx])
    fi, fj, fs, ft = (a[fx][~hidden] for a in (iy, ix, shade, T))
    bits = FILL[2, (fi * 31 + fj * 17 + int(t * 12)) % 12]
    flake = np.where(fs > 0.75, AT["*"], np.where(fs > 0.5, AT["+"], AT["."]))
    letter = np.select([ft == PUDDLE, ft == FLAKE], [AT["~"], flake], bits)
    char[fi, fj], lum[fi, fj], tag[fi, fj] = letter, np.where(ft == PUDDLE, 0.6, fs), ft
    return char, lum, tag, info, int(body.sum())


# window

TITLE = "DON'T MELT · JIN2"
SIGN = "@jin_22ee · 2026"
CW, CH, FONT_PX = 9, 14, 15
W, H = 1080, 960
TRAIL = 0.4
TAG_COLOR = [[226, 236, 255], [96, 112, 150], [176, 126, 86], [206, 222, 255], [118, 132, 168],
             [150, 178, 236], [236, 242, 255]]
COLS, ROWS = W // CW, H // CH
ASPECT = (COLS * CW) / (ROWS * CH)
COLOR = np.array(TAG_COLOR, np.float32) / 255
DIM, PINK = (120, 112, 128), (255, 122, 182)


def glyphs():
    font = pygame.font.SysFont("consolas,menlo,dejavusansmono,couriernew,monospace", FONT_PX)
    atlas = []
    for ch in CHARS:
        s = pygame.Surface((CW, CH))
        g = font.render(ch, True, (255, 255, 255))
        s.blit(g, ((CW - g.get_width()) // 2, (CH - g.get_height()) // 2))
        atlas.append(pygame.surfarray.array3d(s)[:, :, 0].T.astype(np.float32) / 255)
    return np.stack(atlas)


class Canvas:
    # glyph mask x colour x brightness, over a fading copy of the previous frame

    def __init__(self, atlas):
        self.atlas = (atlas * 255).astype(np.uint8)
        self.shape = pygame.Surface((COLS * CW, ROWS * CH))
        self.trail = pygame.Surface((W, H))
        self.fade = (int(TRAIL * 255),) * 3

    def reset(self):
        self.trail.fill((0, 0, 0))

    def draw(self, t):
        char, lum, tag, info, count = frame(t, COLS, ROWS, ASPECT)
        mask = self.atlas[char.T].transpose(0, 3, 1, 2).reshape(COLS * CW, ROWS * CH)
        pygame.surfarray.blit_array(self.shape, np.repeat(mask[..., None], 3, 2))
        col = (COLOR[np.clip(tag, 0, len(COLOR) - 1)] * np.clip(lum, 0, 1)[..., None] * 255).astype(np.uint8)
        tint = pygame.transform.scale(pygame.surfarray.make_surface(col.transpose(1, 0, 2)), self.shape.get_size())
        self.shape.blit(tint, (0, 0), special_flags=pygame.BLEND_MULT)
        self.trail.fill(self.fade, special_flags=pygame.BLEND_MULT)
        self.trail.blit(self.shape, (0, 0), special_flags=pygame.BLEND_MAX)
        return self.trail, info, count


def blur(surf, k, radius):
    small = pygame.transform.smoothscale(surf, (W // k, H // k))
    if hasattr(pygame.transform, "gaussian_blur"):
        small = pygame.transform.gaussian_blur(small, max(1, radius // k))
    return pygame.transform.smoothscale(small, (W, H))


def glow_layer(surf, amount):
    layer = surf.copy()
    layer.fill((int(255 * amount),) * 3, special_flags=pygame.BLEND_MULT)
    return layer


def HUD(info):
    return f"temp {info['temp']:+05.1f}°C   melted {info['melt'] * 100:3.0f}%"


def window_size():
    # shrink to fit small or scaled screens
    info = pygame.display.Info()
    k = 1.0
    if info.current_w > 0 and info.current_h > 0:
        k = min(1.0, 0.85 * info.current_h / H, 0.95 * info.current_w / W)
    return int(W * k), int(H * k)


def main():
    pygame.init()
    size = window_size()
    window = pygame.display.set_mode(size)
    pygame.display.set_caption(TITLE)
    screen = pygame.Surface((W, H))
    small = pygame.font.SysFont("consolas,menlo,dejavusansmono,couriernew,monospace", 17)
    canvas, clock = Canvas(glyphs()), pygame.time.Clock()
    t, paused = 0.0, False
    art, info, count = canvas.draw(t)
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                pygame.quit()
                return
            if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                paused = not paused
            if e.type == pygame.KEYDOWN and e.key == pygame.K_r:
                t = 0.0
                canvas.reset()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_s:
                pygame.image.save(screen, str(Path(__file__).with_name(f"snowman_{int(time.time())}.png")))
        dt = clock.tick(30) / 1000
        if not paused:
            t += min(dt, 1 / 15)
            if t > LOOP:
                t = 0.0
                canvas.reset()
            art, info, count = canvas.draw(t)
        screen.fill((0, 0, 0))
        screen.blit(art, (0, 0))
        screen.blit(glow_layer(blur(art, 4, 5), 0.75), (0, 0), special_flags=pygame.BLEND_ADD)
        screen.blit(glow_layer(blur(art, 8, 22), 0.45), (0, 0), special_flags=pygame.BLEND_ADD)
        y = H - 70
        screen.blit(small.render(SIGN, True, (120, 112, 128)), (64, y - 26))
        screen.blit(small.render(HUD(info), True, DIM), (64, y))
        screen.blit(small.render(f"letters {count:05,d}", True, DIM), (64, y + 26))
        tt = small.render(f"{'●' if int(t * 2) % 2 == 0 else ' '} t {t:05.2f}s", True, PINK)
        screen.blit(tt, (W - 64 - tt.get_width(), 30))
        window.blit(screen if size == (W, H) else pygame.transform.smoothscale(screen, size), (0, 0))
        pygame.display.flip()


if __name__ == "__main__":
    sys.exit(main())

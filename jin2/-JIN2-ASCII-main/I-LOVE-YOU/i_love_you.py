# I LOVE YOU
# JIN2 · @jin_22ee · 2026    Free to use for personal projects, see LICENSE.txt.
#
# run:   pip install -r requirements.txt
#        python i_love_you.py
# keys:  Space pause · R restart · S screenshot · Esc quit

import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import pygame

LOOP, BUILD = 20.0, 3.0
TRAIL = 0.35
HERE = Path(__file__).parent
PHRASES = json.loads((HERE / "sprites" / "phrases.json").read_text(encoding="utf-8"))


def trim(a):
    # cut the empty margin around each phrase so they can sit close together
    ys, xs = np.nonzero(a > 0.05)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


SPRITES = [trim(cv2.imread(str(HERE / "sprites" / f"{i:02d}.png"), cv2.IMREAD_UNCHANGED)[:, :, 3].astype(np.float32) / 255)
           for i in range(len(PHRASES))]
RTL = {"Arabic", "Hebrew", "Persian", "Pashto", "Urdu", "Yiddish", "Uyghur"}
N = len(PHRASES)

W, H = 1080, 960
CX, CY = 540, 480                 # centre of the heart on screen
WIDTH = 840                       # heart width in pixels
TEXT_PX = 19                      # text height
PITCH = 21                        # one row of text every this many pixels
GAP = 14                          # space between phrases in a row
TURN = 10.0                       # seconds for one full turn to the right
WALL = 22                         # half the thickness of the heart's side, in pixels
DOME = 70                         # how much the faces bulge out beyond the side

# right half of the outline (x, y as fractions of the width), top dip to bottom tip
HALF = [(0.0, -0.3575), (0.0301, -0.3662), (0.0563, -0.3844), (0.0825, -0.4024), (0.109, -0.4199),
        (0.1373, -0.4328), (0.1671, -0.4422), (0.1981, -0.4489), (0.231, -0.4507), (0.264, -0.4489),
        (0.2947, -0.4418), (0.3236, -0.43), (0.349, -0.41), (0.3738, -0.3887), (0.3993, -0.3687),
        (0.4241, -0.3474), (0.4442, -0.322), (0.4604, -0.295), (0.4741, -0.267), (0.4852, -0.2379),
        (0.4928, -0.2073), (0.4964, -0.1751), (0.4982, -0.1421), (0.4969, -0.109), (0.4928, -0.077),
        (0.4857, -0.0462), (0.4767, -0.0162), (0.465, 0.0126), (0.4513, 0.0406), (0.4351, 0.0676),
        (0.4176, 0.0941), (0.3988, 0.12), (0.3788, 0.1454), (0.3562, 0.1698), (0.3319, 0.1923),
        (0.3075, 0.2149), (0.2826, 0.2362), (0.2577, 0.2575), (0.2329, 0.2788), (0.208, 0.3001),
        (0.1831, 0.3214), (0.1577, 0.3414), (0.1323, 0.3614), (0.1069, 0.3815), (0.0809, 0.4002),
        (0.0548, 0.4185), (0.028, 0.4352), (0.0, 0.4489)]


def outline():
    # mirror the half and fill
    right = np.array(HALF) * WIDTH
    left = right[::-1] * [-1, 1]
    pts = np.concatenate([right, left]) + [CX, CY]
    m = np.zeros((H, W), np.uint8)
    cv2.fillPoly(m, [np.round(pts * 4).astype(np.int32)], 255, lineType=cv2.LINE_AA, shift=2)
    return m > 127


INSIDE = outline()
DIST = cv2.distanceTransform(INSIDE.astype(np.uint8), cv2.DIST_L2, 5)
RAD = 1 - DIST / DIST.max()                # 0 in the middle, 1 on the edge
MASK = INSIDE.astype(np.float32)


_CACHE = {}


def sprite(idx, k):
    key = (idx, round(k * 200))
    if key not in _CACHE:
        a = SPRITES[idx]
        _CACHE[key] = cv2.resize(a, (max(1, round(a.shape[1] * k)), max(1, round(a.shape[0] * k))),
                                 interpolation=cv2.INTER_AREA)
    return _CACHE[key]


def stamp(img, idx, x, y, k, shown):
    # one phrase, centred on (x, y); only the typed part is visible
    a = sprite(idx, k)
    h, w = a.shape
    if shown < 1:
        cut = int(w * shown)
        a = a.copy()
        if PHRASES[idx][0] in RTL:
            a[:, :w - cut] = 0
        else:
            a[:, cut:] = 0
    x0, y0 = int(x - w / 2), int(y - h / 2)
    cx0, cy0, cx1, cy1 = max(x0, 0), max(y0, 0), min(x0 + w, W), min(y0 + h, H)
    if cx1 <= cx0 or cy1 <= cy0:
        return
    p = a[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0]
    img[cy0:cy1, cx0:cx1] = np.maximum(img[cy0:cy1, cx0:cx1], p)


def smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


# depth: flat sides, bulging faces, a raised rim just inside the edge
lip = np.exp(-((DIST - 14) / 5.0) ** 2) * 10 - np.exp(-((DIST - 34) / 7.0) ** 2) * 7
Z = (WALL + DOME * np.sqrt(np.clip(1 - RAD ** 2, 0, 1)) + lip) * INSIDE
Z = cv2.GaussianBlur(Z.astype(np.float32), (0, 0), 2.0) * INSIDE
ZX, ZY = np.gradient(Z, axis=1), np.gradient(Z, axis=0)

# chrome environment: sky, horizon band, floor
SKY = np.array([255, 240, 248]) / 255
BAND = np.array([78, 36, 70]) / 255
FLOOR = np.array([246, 168, 210]) / 255


def chrome(ry, rx):
    # reflected environment colour from the reflection vector
    sky = smooth((ry - 0.12) / 0.3)
    floor = smooth((-ry - 0.05) / 0.4)
    c = BAND[None] * (1 - sky - floor)[:, None] + SKY[None] * sky[:, None] + FLOOR[None] * floor[:, None]
    streak = np.exp(-((rx + 0.35) / 0.08) ** 2) * smooth((ry + 0.1) / 0.3)      # side highlight
    return c + streak[:, None] * 0.5


# pixel rows inside the heart, split into runs
RUNS = []
for y in range(H):
    cols = np.nonzero(MASK[y] > 0)[0]
    if len(cols):
        for run in np.split(cols, np.nonzero(np.diff(cols) > 1)[0] + 1):
            RUNS.append((y, run))


def fit_row(xl, xr, first, k):
    # justify phrases to fill [xl, xr] exactly
    span = xr - xl
    picks, used, j = [], 0.0, first
    for _ in range(40):
        for tries in range(12):                    # look for a shorter one if it does not fit
            idx = (j + tries * 5) % N
            w = SPRITES[idx].shape[1] * k
            if used + w + (GAP if picks else 0) <= span:
                break
        else:
            break
        used += w + (GAP if picks else 0)
        picks.append((idx, w))
        j = idx + 7
    if not picks:
        return []
    gap = (span - sum(w for _, w in picks)) / max(len(picks) - 1, 1)
    out, x = [], xl if len(picks) > 1 else xl + (span - picks[0][1]) / 2
    for idx, w in picks:
        out.append((idx, x, w))
        x += w + gap
    return out


LAYOUT = {0: [], 1: []}
_k = TEXT_PX / SPRITES[0].shape[0]
for r, y in enumerate(range(int(CY - 0.47 * WIDTH), int(CY + 0.46 * WIDTH), PITCH)):
    band = RAD[max(y - TEXT_PX // 2, 0):min(y + TEXT_PX // 2, H - 1)].max(0)    # full text height must fit
    cols = np.nonzero(band < 0.985)[0]
    if len(cols) < 20:
        continue
    for run in np.split(cols, np.nonzero(np.diff(cols) > 1)[0] + 1):
        if len(run) < 20:
            continue
        for side in (0, 1):
            for j, (idx, x, w) in enumerate(fit_row(run[0], run[-1], r * 13 + side * 29 + int(run[0]), _k)):
                LAYOUT[side].append((r, j, idx, x, w, y))


def texture(t, side):
    # text sheet for one face (side 0 = front, 1 = back), typed in during BUILD
    layer = np.zeros((H, W), np.float32)
    count = 0
    for r, j, idx, x, w, y in LAYOUT[side]:
        start = 0.1 + ((r * 7919 + j * 104729 + side * 31) % 997) / 997 * (BUILD - 0.6)
        shown = smooth((t - start) / 0.3)
        if shown > 0:
            stamp(layer, idx, x + w / 2, y, _k, shown)
            count += 1
    return layer, count


WD = 2 * WALL + 8                         # side wall texture width
SIDE_ROWS = sorted({y for _, _, _, _, _, y in LAYOUT[0]})


def side_texture(t):
    # text for the side walls (end 0 = left, 1 = right)
    tex = np.zeros((2, H, WD), np.float32)
    count = 0
    for end in (0, 1):
        for r, y in enumerate(SIDE_ROWS):
            for tries in range(N):
                idx = (r * 17 + end * 41 + tries * 3) % N
                ks = min(_k, (WD - 6) / SPRITES[idx].shape[1])
                if ks >= _k * 0.55:                   # allow some shrinking to fit
                    break
            start = 0.1 + ((r * 6007 + end * 911) % 997) / 997 * (BUILD - 0.6)
            shown = smooth((t - start) / 0.3)
            if shown > 0:
                a_ = sprite(idx, ks)
                hh, ww = a_.shape
                x0, y0 = int(WD / 2 - ww / 2), int(y - hh / 2)
                if 0 <= y0 and y0 + hh <= H and x0 >= 0:
                    tex[end, y0:y0 + hh, x0:x0 + ww] = np.maximum(tex[end, y0:y0 + hh, x0:x0 + ww], a_)
                    count += 1
    return tex, count


def render(t):
    # text-mapped heart rotating about the vertical axis
    front, n1 = texture(t, 0)
    back, n2 = texture(t, 1)
    side, n3 = side_texture(t)
    th = 2 * np.pi * t / TURN
    c, s = np.cos(th), np.sin(th)
    out = np.zeros((H, W, 3), np.float32)
    for y, run in RUNS:
        x = run.astype(np.float32) - CX
        z, zx, zy = Z[y, run], ZX[y, run], ZY[y, run]
        norm = np.sqrt(zx * zx + zy * zy + 1)
        # front and back faces
        X = np.concatenate([x, x])
        D = np.concatenate([z, -z])
        tex = np.concatenate([front[y, run], back[y, (2 * CX - run).clip(0, W - 1)]])
        nx = np.concatenate([-zx, zx]) / np.concatenate([norm, norm])
        ny = np.concatenate([zy, zy]) / np.concatenate([norm, norm])
        nz = np.concatenate([1 / norm, -1 / norm])
        # side walls at both ends of the run
        for end, xe in ((0, run[0]), (1, run[-1])):
            ze = max(float(Z[y, xe]), WALL * 0.8)
            zs = np.arange(-ze, ze, 0.7, dtype=np.float32)
            u = ((ze - zs) if end == 0 else (zs + ze)) / (2 * ze) * (WD - 1)
            X = np.concatenate([X, np.full(len(zs), xe - CX, np.float32)])
            D = np.concatenate([D, zs])
            tex = np.concatenate([tex, side[end, y, u.astype(int)]])
            nx = np.concatenate([nx, np.full(len(zs), -1.0 if end == 0 else 1.0)])
            ny = np.concatenate([ny, np.full(len(zs), 0.12)])
            nz = np.concatenate([nz, np.zeros(len(zs))])
        sx = X * c + D * s + CX                      # screen x
        depth = -X * s + D * c                       # towards the viewer
        nxr, nzr = nx * c + nz * s, -nx * s + nz * c # rotated normal
        ry, rx = 2 * nzr * ny, 2 * nzr * nxr         # reflection vector
        ry = np.where(nz == 0, 0.25, ry)             # walls: fixed softer light
        col_ = chrome(ry, rx)
        rim = np.clip(1 - np.abs(nzr), 0, 1)
        val = col_ * (tex * (0.95 + 0.8 * rim))[:, None]
        cols = np.round(sx).astype(int)
        ok = (cols >= 0) & (cols < W) & (nzr > -0.05)
        order = np.argsort(depth[ok])                # painter's order
        out[y, cols[ok][order]] = val[ok][order]
    return out, {"languages": N, "phrases": n1 + n2 + n3}, n1 + n2 + n3


# window

TITLE = "I LOVE YOU · JIN2"
SIGN = "@jin_22ee · 2026"
DIM, PINK = (120, 112, 128), (255, 122, 182)


def to_surface(img):
    return pygame.surfarray.make_surface((np.clip(img, 0, 1) * 255).astype(np.uint8).transpose(1, 0, 2))


def glow(img, k, radius, amount):
    small = cv2.resize(img, (W // k, H // k), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), max(1, radius / k))
    return cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR) * amount


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
    small = pygame.font.SysFont("consolas,menlo,dejavusansmono,couriernew,monospace", 17)
    clock = pygame.time.Clock()
    t, paused, trail, info, count = 0.0, False, None, {}, 0
    screen = pygame.Surface((W, H))
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                pygame.quit()
                return
            if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                paused = not paused
            if e.type == pygame.KEYDOWN and e.key == pygame.K_r:
                t, trail = 0.0, None
            if e.type == pygame.KEYDOWN and e.key == pygame.K_s:
                pygame.image.save(screen, str(Path(__file__).with_name(f"i_love_you_{int(time.time())}.png")))
        dt = clock.tick(30) / 1000
        if not paused or trail is None:
            if not paused:
                t += min(dt, 1 / 15)
            if t > LOOP:
                t -= LOOP
            img, info, count = render(t)
            trail = img if trail is None else np.maximum(trail * TRAIL, img)
        shown = trail + glow(trail, 4, 5, 0.75) + glow(trail, 8, 22, 0.45)
        screen.blit(to_surface(shown), (0, 0))
        y = H - 70
        screen.blit(small.render(SIGN, True, DIM), (64, y - 26))
        screen.blit(small.render(f"languages {info.get('languages', N)}   phrases {info.get('phrases', 0)}", True, DIM), (64, y))
        screen.blit(small.render(f"letters {count:05,d}", True, DIM), (64, y + 26))
        tt = small.render(f"{'●' if int(t * 2) % 2 == 0 else ' '} t {t:05.2f}s", True, PINK)
        screen.blit(tt, (W - 64 - tt.get_width(), 30))
        window.blit(screen if size == (W, H) else pygame.transform.smoothscale(screen, size), (0, 0))
        pygame.display.flip()


if __name__ == "__main__":
    sys.exit(main())

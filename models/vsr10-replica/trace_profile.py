"""Trace the stock's side outline from reference.png into stock_profile.json.

The photo is a level left-side view with crisp edges on a white background,
so every edge is located to sub-pixel precision where the brightness crosses
the midpoint between the background (~252) and the black stock (~45).

Scale: muzzle (px 12.9) to butt pad heel (px 884.4) = 1075 mm, the VSR-10's
published overall length. Model coordinates: X from the butt pad heel (0)
toward the muzzle, Z up from the bore axis.
"""
import json
import numpy as np
from PIL import Image

MUZZLE_PX, BUTT_PX, BORE_ROW = 12.9, 884.4, 145
S = 1075 / (BUTT_PX - MUZZLE_PX)
T = 150                         # edge threshold (brightness)

FOREND_FRONT_PX = 318.0         # vertical front face of the forend
STOCK_TOP_ROW = 148             # seam between barrel/receiver and stock
RECEIVER_REAR_PX = 605          # receiver ends here; the cocking piece hides
WRIST_PX = 628                  # the stock top until this column
FROM_BELOW_PX = 700             # behind the grip, find the bottom edge from below
LAST_PX = 880                   # columns past this are behind the toe of the pad face
# Attachments that hang below the stock: bridge the stock's own edge across them.
BRIDGES = [(337, 395),          # accessory rail and bipod post
           (579, 630),          # trigger guard and trigger
           (824, 836)]          # sling swivel

img = np.asarray(Image.open("reference.png").convert("L")).astype(float)


def X(px): return (BUTT_PX - px) * S
def Z(row): return (BORE_ROW - row) * S


def edge(col, row, step):
    """Walk from `row` by `step` until the brightness crosses T; sub-pixel row."""
    inside = img[row, col] < T
    while (img[row + step, col] < T) == inside:
        row += step
    a, b = img[row, col], img[row + step, col]
    return row + step * (a - T) / (a - b)


def whittaker(y, lam):
    """Penalised least-squares smoother (second differences)."""
    d = np.diff(np.eye(len(y)), 2, axis=0)
    return np.linalg.solve(np.eye(len(y)) + lam * d.T @ d, y)


cols = np.arange(int(FOREND_FRONT_PX) + 1, LAST_PX + 1)

# Top edge: visible behind the cocking piece; the action/forend seam before it.
top = np.full(len(cols), float(STOCK_TOP_ROW))
seen = cols >= WRIST_PX
top[seen] = [edge(c, 120, +1) for c in cols[seen]]
hidden = (cols >= RECEIVER_REAR_PX) & ~seen       # behind the cocking piece
top[hidden] = np.interp(cols[hidden], [RECEIVER_REAR_PX, WRIST_PX], [STOCK_TOP_ROW, top[seen][0]])

# Bottom edge: from inside the stock (so the trigger guard's open loop stops
# the scan), and from below behind the grip.
bottom = np.array([edge(c, int(t) + 4 if c >= WRIST_PX else 165, +1) if c < FROM_BELOW_PX
                   else edge(c, img.shape[0] - 30, -1) for c, t in zip(cols, top)])
for c0, c1 in BRIDGES:
    span = (cols >= c0) & (cols <= c1)
    bottom[span] = np.interp(cols[span], [c0, c1], [bottom[cols == c0][0], bottom[cols == c1][0]])

top, bottom = whittaker(top, 30), whittaker(bottom, 30)

# Butt pad face: how far forward of the heel it sits at each height.
face = []
for row in range(166, 251, 2):
    c = img.shape[1] - 6
    while img[row, c] > T:
        c -= 1
    col = c + (img[row, c + 1] - T) / (img[row, c + 1] - img[row, c])
    face.append((round(Z(row), 2), round(X(col), 2)))

# Both edges run from the butt toward the forend tip (ascending X).
profile = {
    "scale_mm_per_px": S,
    "front_x": round(X(FOREND_FRONT_PX), 2),
    "top": [(round(X(c), 2), round(Z(r), 2)) for c, r in zip(cols, top)][::-1],
    "bottom": [(round(X(c), 2), round(Z(r), 2)) for c, r in zip(cols, bottom)][::-1],
    "butt_face": face[::-1],          # (Z, X offset), ascending Z
}
json.dump(profile, open("stock_profile.json", "w"))
print(f"{len(cols)} columns, X {profile['top'][0][0]}..{profile['top'][-1][0]} mm, "
      f"forend front at X {profile['front_x']} mm")

"""Trace the stock's side outline from reference.png into stock_profile.json.

The photo is a level left-side view. Scale: muzzle tip (px 13) to butt pad
(px 884) = 1075 mm, the VSR-10's published overall length.
Model coordinates: X from the butt (0) toward the muzzle, Z up from the bore.
"""
import json
import numpy as np
from PIL import Image

MUZZLE_PX, BUTT_PX, BORE_ROW = 13, 884, 145
S = 1075 / (BUTT_PX - MUZZLE_PX)
STOCK_TOP_ROW = 148          # seam between receiver/barrel and stock (from the photo)
FOREND_FRONT_PX = 318
WRIST_PX = 628               # stock outline is fully visible behind this column

img = np.asarray(Image.open("reference.png").convert("RGB")).astype(int)
dark = img.min(axis=2) < 200

def X(px): return (BUTT_PX - px) * S
def Z(row): return (BORE_ROW - row) * S

def bottom_edge(col, start):
    row = start
    while row < img.shape[0] - 1 and dark[row + 1, col]:
        row += 1
    return row

def top_edge(col):
    row = 185
    while row > 0 and dark[row - 1, col]:
        row -= 1
    return row

cols = range(FOREND_FRONT_PX, BUTT_PX)
# Start each downward search just inside the stock: the wrist sits lower
# than the forend, so a fixed start row would begin in the background there.
bottom = np.array([bottom_edge(c, top_edge(c) + 3 if c >= WRIST_PX else 165) for c in cols], float)
# Remove attachments hanging below the stock (bipod stud, trigger guard,
# sling swivel) by clamping spikes to a running median.
med = np.array([np.median(bottom[max(0, i - 8):i + 9]) for i in range(len(bottom))])
bottom = np.where(bottom > med + 2, med, bottom)
# Smooth 1-px jitter.
bottom = np.convolve(np.pad(bottom, 7, mode="edge"), np.ones(15) / 15, mode="valid")

top = np.array([top_edge(c) if c >= WRIST_PX else STOCK_TOP_ROW for c in cols], float)
top = np.convolve(np.pad(top, 2, mode="edge"), np.ones(5) / 5, mode="valid")

# Butt pad: the last few columns are washed out by highlights; square it off
# using the pad's measured top/bottom.
pad = [i for i, c in enumerate(cols) if c >= BUTT_PX - 6]
top[pad] = top[pad[0] - 1]
bottom[pad] = bottom[pad[0] - 1]

step = 2
upper = [(round(X(c), 2), round(Z(t), 2)) for c, t in zip(cols, top)][::step]
lower = [(round(X(c), 2), round(Z(b), 2)) for c, b in zip(cols, bottom)][::step]
# Both edges run from the butt plate (X = 0) to the forend tip.
upper = [(0.0, upper[-1][1])] + upper[::-1]
lower = [(0.0, lower[-1][1])] + lower[::-1]
json.dump({"scale_mm_per_px": S, "top": upper, "bottom": lower}, open("stock_profile.json", "w"))
print(f"{len(upper)} top + {len(lower)} bottom points, X 0..{upper[-1][0]:.0f} mm")

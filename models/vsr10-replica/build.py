"""1:1 one-piece display replica of a VSR-10 style bolt-action airsoft rifle
with a sporter stock (see reference.png).

The stock's side outline is traced from the photo (trace_profile.py ->
stock_profile.json) and scaled to the VSR-10's published overall length of
1075 mm. The stock is a smooth loft of cross-sections along that outline;
its widths come from typical sporter-stock measurements, since the photo is
a single side view. The metal parts are CAD solids, joined to the stock with
a mesh union into one watertight body.

Solid prop: no internal mechanism, blocked muzzle. Units: mm.
Axes: X = length (butt at 0, muzzle at +X), Z = up (bore axis at Z=0),
Y = width (shooter's right side is -Y).

Run:  python3 trace_profile.py && python3 build.py   ->  vsr10_replica.stl
"""
import json
import math

import manifold3d as mf
import numpy as np
import trimesh
from build123d import *

OVERALL = 1075

# ================================================================ stock
profile = json.load(open("stock_profile.json"))
TOP, BOTTOM = np.array(profile["top"]), np.array(profile["bottom"])
FRONT_X = profile["front_x"]

# Cross-section shape along the stock as (x, value) keyframes, eased between:
# butt | comb nose and grip | wrist | action | forend.
#   wt, rt  half-width and height of the rounded top (crown)
#   wm, tm  widest half-width and where it sits (0 = bottom, 1 = top)
#   wb, rb  half-width and height of the rounded bottom
#   pt, pb  squareness of the top and bottom rounding (2 = elliptical)
SHAPE = {
    "wt": [(0, 12.5), (200, 13.0), (250, 13.0), (295, 13.5), (335, 19.5), (700, 19.5)],
    "rt": [(0, 18.0), (200, 18.0), (250, 14.0), (295, 11.0), (335, 4.5), (700, 4.5)],
    "wm": [(0, 20.5), (185, 20.5), (240, 17.5), (270, 16.0), (300, 16.5), (335, 20.0),
           (520, 20.0), (700, 19.5)],
    "tm": [(0, 0.36), (185, 0.42), (250, 0.55), (300, 0.60), (335, 0.62), (700, 0.62)],
    "wb": [(0, 15.5), (185, 15.5), (240, 15.0), (300, 15.0), (335, 16.5), (520, 16.5),
           (700, 15.0)],
    "rb": [(0, 11.0), (240, 11.0), (300, 11.0), (335, 12.0), (700, 13.0)],
    "pt": [(0, 2.0), (250, 2.0), (295, 2.2), (335, 5.0), (700, 5.0)],
    "pb": [(0, 2.3), (185, 2.3), (240, 2.2), (700, 2.2)],
}

M = 72                  # points per half section, top centre to bottom centre
STEP = 2.0              # spacing of sections along the stock
R_HEEL = 7.0            # heel corner radius seen from the side
R_EDGE = 3.5            # rounding where the pad face meets its sides
PAD = 21.0              # recoil pad thickness
PAD_PROUD = 0.4         # pad stands this much proud of the stock
GROOVE_W, GROOVE_D = 1.2, 0.8   # parting line between pad and stock
DOME = 1.5              # bulge of the pad face
NOSE = 16.0             # length of the forend tip's rounding seen from above
NOSE_CORNER = (15.0, 10.0)      # forend tip's bottom corner seen from the side: length, height

_T = (1 - np.cos(np.linspace(0, np.pi, 1500))) / 2    # 0..1, dense near both ends


def eased(keys, x):
    xs, vs = zip(*keys)
    x = min(max(x, xs[0]), xs[-1])
    i = int(max(0, min(np.searchsorted(xs, x) - 1, len(xs) - 2)))
    u = (x - xs[i]) / (xs[i + 1] - xs[i])
    return vs[i] + (vs[i + 1] - vs[i]) * u * u * (3 - 2 * u)


def outline(x):
    """Traced top and bottom edge of the stock at x, with a rounded heel."""
    z_top = np.interp(x, TOP[:, 0], TOP[:, 1])
    z_bot = np.interp(x, BOTTOM[:, 0], BOTTOM[:, 1])
    if x < R_HEEL:
        z_top -= R_HEEL - math.sqrt(R_HEEL ** 2 - (R_HEEL - x) ** 2)
    # The tip's bottom corner turns up to meet the vertical front face tangentially.
    corner_x = FRONT_X - NOSE_CORNER[0]
    if x > corner_x:
        u = min((x - corner_x) / NOSE_CORNER[0], 1.0)
        z_bot = np.interp(corner_x, BOTTOM[:, 0], BOTTOM[:, 1]) + NOSE_CORNER[1] * (1 - math.sqrt(1 - u * u))
    return z_top, z_bot


def section(x, inset=0.0):
    """Closed cross-section at x as (y, z) arrays, shrunk by `inset` all round."""
    p = {k: eased(v, x) for k, v in SHAPE.items()}
    z_top, z_bot = outline(x)
    z_top, z_bot = z_top - inset, z_bot + inset
    wt, wm, wb, tm = p["wt"] - inset, p["wm"] - inset, p["wb"] - inset, p["tm"]
    h = z_top - z_bot
    ct, cb = max(p["rt"] - inset, 1.0) / h, max(p["rb"] - inset, 1.0) / h
    t = _T
    width = np.where(t >= tm, wm - (wm - wt) * ((t - tm) / (1 - tm)) ** 2,
                     wm - (wm - wb) * ((tm - t) / tm) ** 2)
    rounding = np.ones_like(t)
    up, dn = t > 1 - ct, t < cb
    rounding[up] = np.clip(1 - ((t[up] - 1 + ct) / ct) ** p["pt"], 0, 1) ** (1 / p["pt"])
    rounding[dn] = np.clip(1 - ((cb - t[dn]) / cb) ** p["pb"], 0, 1) ** (1 / p["pb"])
    # Right half from top centre down to bottom centre, evenly spaced by arc length.
    y, z = (width * rounding)[::-1], (z_bot + h * t)[::-1]
    s = np.concatenate([[0], np.cumsum(np.hypot(np.diff(y), np.diff(z)))])
    even = np.linspace(0, s[-1], M)
    hy, hz = np.interp(even, s, y), np.interp(even, s, z)
    hy[0] = hy[-1] = 0.0
    return np.concatenate([hy, -hy[-2:0:-1]]), np.concatenate([hz, hz[-2:0:-1]])


def pad_lean(z):
    """How far forward of the heel the pad face sits at height z (fitted to the photo)."""
    u = np.clip((-28 - z) / 54, 0, 1)
    return 3.8 * u * u * (3 - 2 * u) + 0.4 * np.clip((-82 - z) / 48, 0, 1)


def lean_weight(x):
    """The whole pad leans with its face; the stock behind it takes up the difference."""
    u = np.clip((x - PAD - 2) / 30, 0, 1)
    return 1 - u * u * (3 - 2 * u)


def loft(start, rings, end):
    """Watertight mesh through closed rings of equal size, capped by two points."""
    n = len(rings[0])
    verts = np.vstack([start, *rings, end])
    i = np.arange(n)
    j = (i + 1) % n
    faces = [np.column_stack([np.zeros(n, int), 1 + j, 1 + i])]
    for k in range(len(rings) - 1):
        a, b = 1 + k * n, 1 + (k + 1) * n
        faces += [np.column_stack([a + i, a + j, b + j]), np.column_stack([a + i, b + j, b + i])]
    last, tip = 1 + (len(rings) - 1) * n, len(verts) - 1
    faces.append(np.column_stack([last + i, last + j, np.full(n, tip)]))
    mesh = trimesh.Trimesh(verts, np.vstack(faces), process=False)
    if mesh.volume < 0:
        mesh.invert()
    return mesh


def build_stock():
    groove0, groove1 = PAD, PAD + GROOVE_W
    stations = []                                          # (x, inset, plan scale)
    for a in np.linspace(0, math.pi / 2, 10):              # rounded edge of the pad face
        stations.append((R_EDGE * (1 - math.cos(a)), R_EDGE * (1 - math.sin(a)) - PAD_PROUD, 1.0))
    for x in np.arange(R_EDGE + STEP, FRONT_X - NOSE, STEP):
        if groove0 - 0.6 < x < groove1 + 0.6:
            continue
        stations.append((x, -PAD_PROUD if x < groove0 else 0.0, 1.0))
    stations += [(groove0 - 0.05, -PAD_PROUD, 1.0), (groove0, GROOVE_D, 1.0),
                 (groove1, GROOVE_D, 1.0), (groove1 + 0.05, 0.0, 1.0)]
    for u in (1 - np.cos(np.linspace(0, math.pi / 2, 14))) ** 0.5 * 0.9999:  # forend tip
        stations.append((FRONT_X - NOSE * (1 - u), 0.0, (1 - u ** 2.2) ** (1 / 2.2)))
    stations.sort(key=lambda s: s[0])

    rings = []
    for x, inset, plan in stations:
        y, z = section(x, inset)
        rings.append(np.column_stack([np.full_like(y, x), y * plan, z]))

    # Slightly domed pad face: shrink the face outline toward its centre.
    face = rings[0]
    zc = (face[:, 2].max() + face[:, 2].min()) / 2
    dome = []
    for k in (0.8, 0.6, 0.4, 0.2):
        dome.append(np.column_stack([np.full(len(face), -DOME * (1 - k * k)),
                                     face[:, 1] * k, zc + (face[:, 2] - zc) * k]))
    tip = rings[-1]
    mesh = loft(np.array([[-DOME, 0.0, zc]]), dome[::-1] + rings,
                np.array([[FRONT_X, 0.0, tip[:, 2].mean()]]))
    v = mesh.vertices
    v[:, 0] += pad_lean(v[:, 2]) * lean_weight(v[:, 0])
    return trimesh.Trimesh(v, mesh.faces, process=False)


# ================================================================ metal parts
def belly(x):
    return float(np.interp(x, BOTTOM[:, 0], BOTTOM[:, 1]))


R_RCV, Z_RCV = 13.5, -2.5
X_RCV0, X_RCV1 = 344, 500            # receiver rear (px 605) to front
receiver = Pos((X_RCV0 + X_RCV1) / 2, 0, Z_RCV) * Rot(0, 90, 0) * Cylinder(R_RCV, X_RCV1 - X_RCV0)
receiver = fillet(receiver.edges(), 2)
receiver -= Pos(425, -R_RCV, 2) * Box(60, 7, 13)                 # ejection port (right side)

# Bolt cocking piece behind the receiver (px 605-625 in the photo)
cocking = Pos(331, 0, Z_RCV + 1) * Rot(0, 90, 0) * Cylinder(7.5, 26)
cocking = fillet(cocking.edges().group_by(Axis.X)[0], 2)
cocking -= Pos(336, 0, Z_RCV + 1) * Rot(0, 90, 0) * (Cylinder(8, 1.2) - Cylinder(6.8, 1.2))

# Scope rail on the receiver (px 490-590)
rail_x0, rail_x1 = 363, 486
rail = Pos((rail_x0 + rail_x1) / 2, 0, 14) * Box(rail_x1 - rail_x0, 15, 7)
x = rail_x0 + 6
while x < rail_x1 - 3:
    rail -= Pos(x, 0, 16.5) * Box(5.3, 18, 2.5)
    x += 10

# Bolt handle on the right side: stem angled down, ball knob
stem = Pos(352, -R_RCV + 2, Z_RCV) * Rot(30, 0, 0) * Rot(90, 0, 0) \
    * Cylinder(4.5, 36, align=(Align.CENTER, Align.CENTER, Align.MIN))
knob = Pos(352, -R_RCV - 29, Z_RCV - 18) * Sphere(8.5)

# Trigger guard: thin round loop (X 317-371, Z -51..-83 in the photo)
loop = Pos(345, -66) * Ellipse(26, 17) - Pos(345, -66) * Ellipse(22, 13)   # sketch (x, z)
guard = extrude(Plane.XZ * loop, amount=4, both=True)
guard &= Pos(345, 0, -80) * Box(80, 20, 70)                        # top sinks into the stock

# Curved trigger blade built from short straight segments
trigger = Part()
blade = [(341, -50), (338, -56), (336, -62), (338, -68), (343, -73)]
for (xa, za), (xb, zb) in zip(blade, blade[1:]):
    angle = -math.degrees(math.atan2(zb - za, xb - xa))
    length = math.hypot(xb - xa, zb - za) + 2.4
    trigger += Pos((xa + xb) / 2, 0, (za + zb) / 2) * Rot(0, angle, 0) * Box(length, 5, 2.4)

# Barrel
barrel = Pos(X_RCV1 - 10, 0, 0) * Rot(0, 90, 0) \
    * Cylinder(11.2, OVERALL - X_RCV1 + 10, align=(Align.CENTER, Align.CENTER, Align.MIN))
barrel = fillet(barrel.edges().group_by(Axis.X)[-1], 1)
barrel -= Pos(OVERALL - 10, 0, 0) * Rot(0, 90, 0) * (Cylinder(12, 0.8) - Cylinder(10.6, 0.8))  # orange tip line
barrel -= Pos(OVERALL - 2, 0, 0) * Rot(0, 90, 0) * Cylinder(5, 5)                              # recessed muzzle

# Accessory rail (X 603-675) following the forend's belly, with a folding
# bipod post at its front end; rear sling swivel under the butt.
fx0, fx1 = 603, 675
tilt = math.degrees(math.atan2(belly(fx1) - belly(fx0), fx1 - fx0))
fore_rail = Box(fx1 - fx0, 14, 8)                                  # top 2.5 mm into the belly
for i in range(7):
    fore_rail -= Pos(-30 + i * 10, 0, -3.5) * Box(5.3, 18, 2.5)
fore_rail = Pos((fx0 + fx1) / 2, 0, (belly(fx0) + belly(fx1)) / 2 - 1.5) * Rot(0, -tilt, 0) * fore_rail
post_top = belly(676) - 6
bipod = Pos(676, 0, post_top + 2) * Box(9, 10, 6)                  # hinge block
bipod += Pos(676, 0, post_top) * Cylinder(3, post_top + 63, align=(Align.CENTER, Align.CENTER, Align.MAX))
bipod += Pos(676, 0, -64) * fillet(Cylinder(4.5, 3).edges(), 1)    # foot
swivel = Pos(66, 0, -120) * Cylinder(4, 10, align=(Align.CENTER, Align.CENTER, Align.MAX))
swivel += Pos(66, 0, -128) * Box(10, 9, 4)
swivel += Pos(66, 0, -139) * Rot(90, 0, 0) * Torus(8, 1.8)

parts = [receiver, cocking, rail, stem, knob, guard, trigger, barrel, fore_rail, bipod, swivel]


# ================================================================ assemble
def to_manifold(mesh):
    solid = mf.Manifold(mf.Mesh(vert_properties=np.ascontiguousarray(mesh.vertices, np.float32),
                                tri_verts=np.ascontiguousarray(mesh.faces, np.uint32)))
    if solid.status() != mf.Error.NoError:
        raise RuntimeError(f"mesh is not a closed manifold: {solid.status()}")
    return solid


def tessellated(part):
    verts, tris = part.tessellate(0.03, 0.15)
    mesh = trimesh.Trimesh([(v.X, v.Y, v.Z) for v in verts], tris)   # merges shared vertices
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.remove_unreferenced_vertices()
    trimesh.repair.fix_normals(mesh)
    if not mesh.is_watertight:
        trimesh.repair.fill_holes(mesh)
    return mesh


stock = build_stock()
print(f"stock: {len(stock.faces)} faces, watertight={stock.is_watertight}")
rifle = mf.Manifold.batch_boolean([to_manifold(stock)] + [to_manifold(tessellated(p)) for p in parts],
                                  mf.OpType.Add)
out = rifle.to_mesh()
mesh = trimesh.Trimesh(np.asarray(out.vert_properties)[:, :3], np.asarray(out.tri_verts))
print("bounding box (mm):", mesh.extents.round(1), "bodies:", len(mesh.split(only_watertight=False)))
mesh.export("vsr10_replica.stl")
print("wrote vsr10_replica.stl")

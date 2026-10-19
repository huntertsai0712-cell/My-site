"""1:1 one-piece display replica of a VSR-10 style bolt-action airsoft rifle
with a sporter stock (see reference.png).

Proportions were traced from the reference photo's silhouette and scaled to
the VSR-10's published overall length of 1075 mm (1.234 mm per pixel).
Solid prop: no internal mechanism, blocked muzzle. Units: mm.
Axes: X = length (butt at 0, muzzle at +X), Z = up (bore axis at Z=0),
Y = width (shooter's right side is -Y).

Run:  python3 build.py   ->  vsr10_replica.stl
"""
from build123d import *

OVERALL = 1075
STOCK_W = 44
GRIP_W = 32

# ---------------------------------------------------------------- stock
# Side profile traced from the photo, (x, z). Top edge from butt to forend
# tip, then the bottom edge back from the tip to the butt.
top = [
    (0, -20), (100, -18), (232, -17), (242, -22), (256, -28),   # comb, drop to wrist
    (270, -27), (286, -23), (300, -18), (316, -10),             # wrist up to action
    (490, -7), (700, -4),                                       # bed under barrel
]
bottom = [
    (706, -10), (704, -26), (692, -36), (600, -40), (500, -43),  # forend tip, belly
    (440, -46), (380, -49), (330, -51), (305, -55),              # down to trigger area
    (295, -60), (284, -69), (270, -85), (262, -97), (252, -105), # grip front
    (238, -105), (224, -100), (214, -93), (206, -88),            # grip base and back
    (195, -89), (150, -101), (100, -115), (50, -130),            # butt underline
    (20, -136), (6, -135), (0, -128),
]
side = Polygon(*(top + bottom), align=None)
# Round every corner of the outline (convex first, then concave).
side = offset(offset(side, -5, kind=Kind.ARC), 5, kind=Kind.ARC)
side = offset(offset(side, 6, kind=Kind.ARC), -6, kind=Kind.ARC)
stock = extrude(Plane.XZ * side, amount=STOCK_W / 2, both=True)
stock = fillet(stock.faces().filter_by(Axis.Y).edges(), 9)   # rounded sporter section

# Slim the pistol grip with rounded cutters on both sides.
grip_cut = fillet(Box(120, 30, 100).edges(), 12)
for s in (1, -1):
    stock -= Pos(250, s * (GRIP_W / 2 + 15), -112) * grip_cut

# Butt pad parting line
stock -= Pos(14, 0, -78) * Box(1.2, STOCK_W + 2, 140)

# ---------------------------------------------------------------- action
R_RCV, Z_RCV = 14.5, -1.5
X_RCV0, X_RCV1 = 318, 490
receiver = Pos((X_RCV0 + X_RCV1) / 2, 0, Z_RCV) * Rot(0, 90, 0) * Cylinder(R_RCV, X_RCV1 - X_RCV0)
receiver = fillet(receiver.edges(), 2.5)
receiver -= Pos(420, -R_RCV, 3) * Box(60, 8, 14)              # ejection port (right side)
shroud = Pos(308, 0, Z_RCV) * Rot(0, 90, 0) * Cone(9, 12.5, 11, align=(Align.CENTER, Align.CENTER, Align.MIN))

# Short scope rail on the receiver
rail_x0, rail_x1 = 363, 474
rail = Pos((rail_x0 + rail_x1) / 2, 0, 14) * Box(rail_x1 - rail_x0, 15, 7)
x = rail_x0 + 6
while x < rail_x1 - 3:
    rail -= Pos(x, 0, 16.5) * Box(5.3, 18, 2.5)
    x += 10

# Bolt handle on the right side: stem angled down, ball knob
stem = Pos(326, -R_RCV + 2, Z_RCV) * Rot(30, 0, 0) * Rot(90, 0, 0) \
    * Cylinder(4.5, 38, align=(Align.CENTER, Align.CENTER, Align.MIN))
knob = Pos(326, -R_RCV - 31, Z_RCV - 19) * Sphere(9)

# Trigger guard loop (X 323-369, down to Z -83 in the photo) and trigger
guard = Pos(345, 0, -66) * fillet(Box(44, 8, 34).edges().filter_by(Axis.Y), 15)
guard -= Pos(345, 0, -68) * fillet(Box(35, 10, 26).edges().filter_by(Axis.Y), 12)
trigger = Pos(348, 0, -62) * Rot(0, -12, 0) * fillet(Box(5, 6, 20).edges().filter_by(Axis.Z), 2)

# ---------------------------------------------------------------- barrel
barrel = Pos(X_RCV1 - 10, 0, 0) * Rot(0, 90, 0) \
    * Cone(12.5, 11, OVERALL - X_RCV1 + 10, align=(Align.CENTER, Align.CENTER, Align.MIN))
barrel -= Pos(OVERALL - 11, 0, 0) * Rot(0, 90, 0) * (Cylinder(12, 1) - Cylinder(10.4, 1))  # tip ring line
barrel -= Pos(OVERALL - 1.5, 0, 0) * Rot(0, 90, 0) * Cylinder(5, 4)                         # recessed muzzle

# Accessory rail with bipod stud under the forend, rear sling swivel
fore_rail = Pos(640, 0, -43) * Box(86, 15, 8)
for i in range(8):
    fore_rail -= Pos(604 + i * 10, 0, -46) * Box(5.3, 18, 2.5)
bipod_stud = Pos(671, 0, -47) * Cylinder(4, 18, align=(Align.CENTER, Align.CENTER, Align.MAX))
bipod_stud += Pos(671, 0, -64) * Cylinder(6, 3)
swivel_stud = Pos(67, 0, -122) * Cylinder(4, 14, align=(Align.CENTER, Align.CENTER, Align.MAX))
swivel_ring = Pos(67, 0, -141) * Rot(90, 0, 0) * Torus(8, 1.8)

# ---------------------------------------------------------------- assemble
rifle = stock + receiver + shroud + rail + stem + knob + guard + trigger \
    + barrel + fore_rail + bipod_stud + swivel_stud + swivel_ring

print("bounding box (mm):", rifle.bounding_box().size)
export_stl(rifle, "vsr10_replica.stl", tolerance=0.05, angular_tolerance=0.15)
print("wrote vsr10_replica.stl")

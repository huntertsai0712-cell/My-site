# VSR-10 style rifle display replica (1:1, one piece)

Full-size, solid display prop of a VSR-10 style bolt-action airsoft rifle with
a sporter stock. It is a single solid body with no working parts and a
blocked muzzle.

The side profile was traced from the silhouette in `reference.png` and scaled
to the VSR-10's published overall length of 1075 mm (1.234 mm per pixel).
`comparison.png` shows the photo, the model rendered at the same scale, and
the two overlaid.

![comparison](comparison.png)
![preview](preview.png)

| | |
|---|---|
| Overall length | 1075 mm |
| Height | 168 mm (including sling swivel and bipod stud) |
| Width | 44 mm stock (77 mm including bolt knob) |
| Solid volume | ~2.06 L (about 2.6 kg of PLA at 100 % infill; roughly 0.8–1 kg at 15 % infill with 3 walls) |

## Files

- `vsr10_replica.stl` – the printable model (watertight, checked with `stl-check`)
- `build.py` – parametric source (build123d); run `python3 build.py`
- `reference.png`, `comparison.png`, `preview.png`

## Limits

- The photo is a single side view, so the widths (stock 44 mm, grip 32 mm)
  are typical values, not measured.
- At 1075 mm long it exceeds almost every consumer printer bed; as one piece
  it needs a large-format printer or a print service.

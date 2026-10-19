# VSR-10 style rifle display replica (1:1, one piece)

Full-size, solid display prop of a VSR-10 style bolt-action airsoft rifle with
a sporter stock. It is a single solid body with no working parts and a
blocked muzzle.

The stock's full side outline is traced pixel by pixel from `reference.png`
(`trace_profile.py` -> `stock_profile.json`, simplified to within 0.4 mm) and
scaled to the VSR-10's published overall length of 1075 mm (1.234 mm per
pixel). The stock is then shaped in 3D: 9 mm rounded edges, narrowing through
the wrist and pistol grip, and a separate butt pad.
`comparison.png` shows the photo, the model rendered at the same scale, and
the two overlaid.

![comparison](comparison.png)
![preview](preview.png)

| | |
|---|---|
| Overall length | 1075 mm |
| Height | 166 mm (including sling swivel and bipod stud) |
| Width | 42 mm butt, 31 mm wrist/grip, 40 mm forend (72 mm including bolt knob) |
| Solid volume | ~1.91 L (about 2.4 kg of PLA at 100 % infill; roughly 0.8–1 kg at 15 % infill with 3 walls) |

## Files

- `vsr10_replica.stl` – the printable model (one watertight solid, checked with `stl-check`)
- `trace_profile.py` – traces the stock outline from the photo into `stock_profile.json`
- `build.py` – parametric source (build123d); run `python3 trace_profile.py && python3 build.py`
- `reference.png`, `comparison.png`, `preview.png`

## Limits

- The photo is a single side view, so widths are typical sporter-stock
  values, not measured, and the hidden right side (bolt handle, ejection
  port) follows the standard VSR-10 layout.
- At 1075 mm long it exceeds almost every consumer printer bed; as one piece
  it needs a large-format printer or a print service.

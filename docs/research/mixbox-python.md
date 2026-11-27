# Mixbox from Python: package, API, licence, ratios

Research for #4 (part of #1). Question: how do we use Mixbox from Python for M1
to predict `mixes`-mode colours (SPEC §5): install, API for N-part ratios,
latent-space details, LUT size, licence obligations for a public
non-commercial repo, and accuracy caveats.

Sources (all first-party unless noted):

- **[repo]** Official repo `scrtwpns/mixbox`, branch `master`, last commit
  `a1bdb75` (2022-12-17): https://github.com/scrtwpns/mixbox
- **[py]** `python/mixbox.py` and `python/README.md` in that repo.
- **[lic]** `LICENSE` in that repo (preamble + full CC BY-NC 4.0 text).
- **[pypi]** PyPI project `pymixbox`: https://pypi.org/project/pymixbox/ and
  its JSON API `https://pypi.org/pypi/pymixbox/json`.
- **[paper]** Šárka Sochorová, Ondřej Jamriška. *Practical Pigment Mixing for
  Digital Painting.* ACM Trans. Graph. 40(6), Article 234, Dec 2021.
  https://doi.org/10.1145/3478513.3480549 (author PDF:
  https://scrtwpns.com/mixbox.pdf)
- **[issues]** Upstream issue tracker, https://github.com/scrtwpns/mixbox/issues
  (users and maintainers, not authoritative, cited only for observed behaviour).
- **[exp]** Our own checks: `pymixbox==2.0.0` run under CPython 3.14.
- **[proto]** `prototype/variants.py` and `prototype/Dockerfile` on the
  `prototype` branch.

## TL;DR

- `pip install pymixbox` (2.0.0, the only real release, 2022-09-20). Import name
  is `mixbox`. Pure Python, one file, no dependencies (stdlib `zlib` and
  `base64`). Wheel is 123 KB. [pypi][py]
- Two colours: `mixbox.lerp(rgb_a, rgb_b, t)` with 8-bit sRGB tuples. For
  `wa` parts A plus `wb` parts B, use `t = wb / (wa + wb)`. N colours: convert
  each to a 7-float latent with `rgb_to_latent`, take the weighted average,
  then `latent_to_rgb`. [py][paper eq. 14]
- Licence: **CC BY-NC 4.0**, with the note "Copyright (c) 2022, Secret
  Weapons". Fine for a public, free, non-commercial repo. Duties: attribute,
  link the licence, keep the notice when we redistribute it, and no commercial
  use. Depend on it through pip; do not vendor it. [lic][py]
- Accuracy: plausible K–M mixing through **4 fixed idealised acrylic
  primaries** (Phthalo Blue, Quinacridone Magenta, Hansa Yellow, Titanium
  White). It does **not** know real tinting strength, so "parts" are only
  approximate. Treat predicted mixes as a guide, to be checked against
  swatches. [paper §3, §5]

## 1. Package and install

| Fact | Value | Source |
|---|---|---|
| PyPI name | `pymixbox` | [pypi], [repo README] |
| Import name | `mixbox` (top-level module `mixbox.py`) | wheel `top_level.txt` |
| Latest version | 2.0.0, uploaded 2022-09-20. Earlier 0.0.1–0.0.5 were pre-releases | [pypi] |
| Wheel | `pymixbox-2.0.0-py2.py3-none-any.whl`, 123 258 B, universal | [pypi] |
| Dependencies | none (no `Requires-Dist`). Uses stdlib `zlib`, `base64` | wheel METADATA, [py] |
| PyPI licence field | `CC-BY-NC-4.0`. The wheel ships `pymixbox-2.0.0.dist-info/LICENSE` | wheel |
| Wheel vs repo | `mixbox.py` in the wheel is byte-identical to `python/mixbox.py` on `master` (same SHA-256) | [exp] |
| Maintenance | No code change since 2022. Issues go unanswered, e.g. the licence question #15 | [repo], [issues] |

The prototype already installs it this way (`pip install ... pymixbox` in
`prototype/Dockerfile`). [proto]

Pin it in our dependencies: `pymixbox==2.0.0`.

## 2. API

The public functions in `mixbox.py` (header: "MIXBOX 2.0 (c) 2022 Secret
Weapons", authors Sarka Sochorova and Ondrej Jamriska). [py]

| Function | In → out |
|---|---|
| `lerp(c1, c2, t)` | 8-bit sRGB `(r,g,b)` or `(r,g,b,a)` ints → 8-bit tuple (alpha is lerped linearly) |
| `lerp_float(c1, c2, t)` | float sRGB 0–1 → float sRGB |
| `lerp_linear_float(c1, c2, t)` | linear-light float RGB → linear float |
| `rgb_to_latent(rgb)` / `float_rgb_to_latent` / `linear_float_rgb_to_latent` | → 7-tuple latent |
| `latent_to_rgb(z)` / `latent_to_float_rgb` / `latent_to_linear_float_rgb` | 7-tuple latent → colour, clamped to [0,1] |
| `LATENT_SIZE` | `7` |

`t` is the fraction of the **second** colour: `t=0` → `c1`, `t=1` → `c2`. Its
body is `latent_to_rgb((1-t)*z1 + t*z2)`. [py]

### Ratios in parts

Two tubes, `wa` parts A + `wb` parts B:

```python
import mixbox

def mix2(rgb_a, rgb_b, wa, wb):
    return mixbox.lerp(rgb_a, rgb_b, wb / (wa + wb))
```

N tubes with integer parts. This is the official "Mixing Multiple Colors"
recipe, normalised, and matches the paper's weighted mean
`G(Σ wᵢ F(RGBᵢ) / Σ wᵢ)`. [py README][paper eq. 14 ff.]

```python
def mix_parts(rgbs, parts):
    total = sum(parts)
    zs = [mixbox.rgb_to_latent(c) for c in rgbs]
    z = [sum(p / total * zi[k] for p, zi in zip(parts, zs))
         for k in range(mixbox.LATENT_SIZE)]
    return mixbox.latent_to_rgb(z)
```

Checks [exp]:

- `mix_parts([a, b], [wa, wb])` gives exactly the same result as
  `lerp(a, b, wb/(wa+wb))` for 1:1, 2:1, 3:1, 1:2 and 1:3.
- `lerp(a, b, 0) == a` and `lerp(a, b, 1) == b`.
- `latent_to_rgb(rgb_to_latent(c)) == c` for 2 000 random 8-bit colours.
- Sample, Amsterdam chart approximations from the prototype: Primary Yellow
  `#F5C800` + Ultramarine `#22308F`, 1:1 → `(76,132,53)`, a green. Burnt
  Sienna `#7B4800` + Titanium White `#F4F3EE`, 2:1 → `(175,116,71)`.

**Mix all the colours in one step.** Do not chain `lerp` calls (A+B, then the
result + C). Each trip back through RGB rounds the value and loses residual
information, so chained mixing gives a different colour from the one-step
latent average. This was reported upstream (#11) and the reporter confirmed
the fix. [issues]

## 3. Latent space and LUT

- Latent = 7 floats: **4 pigment concentrations** (they sum to 1) + **3 RGB
  residuals**. The residual is `RGB − mix(unmix(RGB))`: the light that the
  pigments cannot reproduce, carried along linearly. With it, any sRGB colour
  round-trips. [paper §3; py `float_rgb_to_latent`]
- Mixing = a linear combination in latent space. Decoding evaluates a
  polynomial fit of the K–M mix of the 4 primaries, adds the mixed residual,
  and clamps. [py `latent_to_rgb`, `_eval_polynomial`]
- Primaries: Golden acrylic **PB15:4 (Phthalo Blue), PY73 (Hansa Yellow),
  PR122 (Quinacridone Magenta), PW6 (Titanium White)**, with K/S data from the
  Artist Paint Spectral Database (Berns 2016). In practice they are replaced by
  "surrogate" pigments whose mixtures stay inside sRGB (the P*-vs-Q* difference
  histogram peaks around ΔE00 1). [paper §3, §4.3]
- LUT size:
  - The paper describes two 256³ tables (96 MB in memory, 7 MB as PNG). [paper]
  - The Python port is much smaller: a base64 + raw-deflate blob inside
    `mixbox.py` (about 159 KB file). It decompresses into a 790 785-byte
    `bytearray`, a **64³ grid** of 3 concentrations with trilinear lookup, plus
    the polynomial decoder. [py; exp]
  - Import takes about 0.14 s and about 3 MB peak memory. One `lerp` takes
    about 6 µs. No external asset files. [exp]
  - Our whole candidate set (14 tubes → 91 pairs × 5 ratios = 455 mixes) costs
    a few ms. No caching needed.

## 4. Licence and attribution (public, non-commercial repo)

What the licence says [lic][py]:

- "Mixbox is licensed for non-commercial use under the CC BY-NC 4.0 license",
  plus "Copyright (c) 2022, Secret Weapons. All rights reserved." For a
  commercial licence, contact the email address in the upstream README.
- §2(a)(1): we may reproduce and share it, and produce and share Adapted
  Material, **for NonCommercial purposes only**. §1(i): "not primarily intended
  for or directed towards commercial advantage or monetary compensation".
- §3(a) attribution, **when we Share the Licensed Material** (including
  modified): keep the creator identification, the copyright notice, a
  reference to the licence and to the warranty disclaimer, and a link to the
  material. Say whether we modified it. A link to a page that holds this
  information is acceptable (§3(a)(2)).
- §2(b)(2): no patent or trademark rights. §2(a)(6): no implied endorsement.
- §6(a): breaking the terms ends the licence automatically. It comes back if we
  fix the breach within 30 days.

What this means for us:

1. **Depend, don't vendor.** We list `pymixbox==2.0.0` as a dependency and do
   not copy `mixbox.py` into the repo. Then the repo itself does not
   redistribute the material. pip brings the licence file along in
   `dist-info`. If we ever publish a Docker image, it does contain Mixbox, and
   the dist-info `LICENSE` stays inside the image.
2. **Attribute anyway** (cheap and in the spirit of §3). Put this in the README
   and NOTICE, and in the "about" text of the viewer and PDF:
   > Mix prediction uses **Mixbox** by Šárka Sochorová and Ondřej Jamriška,
   > © 2022 Secret Weapons (https://github.com/scrtwpns/mixbox), licensed under
   > CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/). Provided
   > as-is, without warranty. Not affiliated with or endorsed by Secret Weapons.
   > Paper: https://doi.org/10.1145/3478513.3480549
3. **No commercial use** of the running product: no paid hosting, no ads, no
   selling the generated templates or PDFs as a service. Anyone who forks the
   repo for commercial use needs their own Mixbox licence. The README should
   say so.
4. **Our own code licence.** The repo has no licence file yet. Whatever we pick
   (e.g. MIT) covers only our code. The README must say clearly that the
   Mixbox dependency stays CC BY-NC and is not relicensed. CC itself advises
   against CC licences for software, and upstream #15 (GPL compatibility) has
   no answer. So a copyleft or open-source *combined* licence cannot
   relicense Mixbox. [issues] *This is a reading of the licence text, not
   legal advice.*
5. Output colours. RGB values computed with Mixbox, such as swatches in a PDF,
   are not Mixbox code. Producing them is "use", which the licence does not
   restrict beyond NC. Section 8(a) says the licence does not restrict uses
   that need no permission.

## 5. Accuracy caveats

1. **Fixed 4-pigment basis.** Every input colour, including our tube hexes, is
   re-read as a mix of Phthalo Blue, Quinacridone Magenta, Hansa Yellow and
   White, plus a residual. The paper says each primary's "characteristic
   properties will get baked in". A warm blue such as Ultramarine therefore
   mixes with a cool phthalo bias. The basis cannot be changed without
   rebuilding the LUT, and no tool to do that is published (upstream #13).
   [paper §5 "Choice of Primary Pigments"; issues]
2. **Parts ≠ real paint quantities.** `t` weights *latent concentrations*
   derived from the colour's RGB only. Real tubes differ in **tinting
   strength**: a little phthalo overwhelms a lot of ochre. Mixbox cannot model
   that, because two tubes with the same hex behave identically. So
   "2× Burnt Sienna + 1× White" is a plausible colour, not a measured one.
   *(This is our inference from the RGB-in/RGB-out design. The paper does not
   discuss tinting strength.)*
3. **Inputs are approximate.** Tube colours are chart approximations (SPEC §5),
   so the errors add up. Calibration from photographed swatches (SPEC §5) is
   the real fix. Ideally calibrate the *mixes* too, not only the tubes.
4. **Opaque, homogeneous mixing only.** No glazing or translucent layers, which
   is fine for paint-by-numbers. [paper §5]
5. **Medium.** The K/S data are glossy acrylics, so saturation may be
   overestimated for duller media. That matches our default Amsterdam
   *acrylic* set well. [paper §3 "Choice of Primary Pigments"]
6. **Residual-heavy colours.** For colours far outside the pigment gamut
   (very saturated sRGB), the behaviour is "plausible" rather than physical.
   [paper §4.2]
7. **White.** One user reports tints lighter than expected (#14). Pyrrole Red
   + White mixes toward pink (`#C3192C` + `#F4F3EE` 1:1 → `(235,100,150)`
   [exp]). Real red tints do go pink, but the size of the shift is not
   validated. [issues; exp]
8. Upstream is effectively unmaintained (no releases since 2022), but the
   module is tiny, pure Python and stable. Low risk for M1.

## 6. How the prototype uses it [proto]

```python
RATIOS = [(1, 1), (2, 1), (1, 2), (3, 1), (1, 3)]
def mix(a, b, wa, wb):
    t = wb / (wa + wb)
    out = mixbox.lerp(tuple(int(v * 255) for v in a), tuple(int(v * 255) for v in b), t)
    return np.array(out, float) / 255
```

- Correct `t` convention. All pairs `i < j` of 14 tubes × 5 ordered ratios →
  455 mixes + 14 tubes = 469 candidates.
- `int(v*255)` after `/255` happens to round-trip every 8-bit value exactly
  [exp]. Still, `round()` or `lerp_float` would be more robust for colours that
  do not come from a hex.
- For M1, keep tube colours as 8-bit sRGB hex and call `mixbox.lerp` (or
  `mix_parts`) directly. No float round-trip is needed.

## 7. Consequences for the paint set schema (#8)

- Store each tube colour as **8-bit sRGB hex**. That is Mixbox's native input.
  Leave room for a later **calibrated** value, measured from swatches, that
  overrides the chart value.
- Express a recipe as **integer parts per tube**, e.g.
  `[{tube: burnt-sienna, parts: 2}, {tube: titanium-white, parts: 1}]`.
  Compute the colour in one latent step with the normalised weights. This
  works for 2 tubes now and extends to 3+ without schema change. Never chain
  pairwise mixes.
- SPEC's "1:1, 2:1, 3:1" means both orders for each unordered pair, so 5
  distinct ratios per pair. Canonicalise recipes (sort by parts, then by tube)
  so that 1:2 A:B and 2:1 B:A are one candidate.
- Mixed colours are derived, never stored as truth, so they need no schema
  field. A per-mix calibrated override could be added later.
- The attribution and NC notice should appear wherever recipes are shown (the
  viewer's about text and the PDF palette page footer).

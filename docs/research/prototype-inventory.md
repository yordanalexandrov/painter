# Prototype inventory: what carries over into M1

Research for #2. Source: the `prototype` branch, commit `72576b2`
(`prototype/variants.py`, `refine_llm.py`, `stylize_gemini.py`, `viewer.html`,
`Dockerfile`). Line references are to `prototype/variants.py` unless stated.
Model facts come from the upstream repositories linked in §3.

Timings were measured by rebuilding the prototype `Dockerfile` and running the
pipeline on scikit-image's public `astronaut` sample (512 px, upscaled to the
1200 px working size), CPU only. The prototype's own test images are not used
here.

## 1. Verdict per component

| Component | Prototype status | M1 decision |
|---|---|---|
| Pre-process (resize + bilateral) | works | **carry over** as is |
| Importance map (YuNet + U²-Net-p) | works | **carry over**, with fixes (§2.2) |
| Palette selection (greedy facility location) | works | **carry over** |
| Mixbox candidate set | works | **carry over** (licence §3.3) |
| Contrast preservation | works | **carry over**, tidy up |
| Felzenszwalb segmentation (2-level) | works | **carry over**; drop the `raw_fine_experiment` hack |
| Region merging | partly: no region budget | **rewrite**: add budget-driven merge (SPEC §4.4) |
| Line layer | partly | **carry over**, then re-merge the fragments it creates |
| Vectorisation (per-region blurred iso-contours) | partly: no shared boundaries | **rewrite** (SPEC §4 step 7) |
| Label placement | partly: numbers too small | **carry over** the placement; **rewrite** the size rule (#12) |
| SVG + viewer HTML | works as a demo | **rewrite** (M3: Vite/TS), keep the interaction design |
| Metrics (ΔE, counts) | works | **carry over**, switch to ΔE2000 |
| LLM refine (`refine_llm.py`, `apply_refine`) | works for palette | **defer to M5**; keep schema and `apply_refine` |
| Gemini stylisation (`stylize_gemini.py`) | works | **defer to M2**; keep polling pattern |
| `Dockerfile` | works | **rewrite**: pin versions and model URLs |

## 2. Components in detail

### 2.1 Pre-process (works → carry over)
- Long side resized to `WORK_SIDE = 1200` px (cubic up, area down), then
  `cv2.bilateralFilter(img, 7, 30, 5)` twice (lines 425–429).
- The unsmoothed image is also kept (`RAW`, a global) for the line layer and
  stroke colours. In M1 pass it explicitly; no module globals.
- Physical scale: `mm_per_px = CANVAS_MM / max(h, w)`, with `CANVAS_MM = 500`
  hard-coded (40×50 cm): 0.417 mm/px. M1 must derive it from the canvas setting.
- Cost: 0.27 s.

### 2.2 Importance map (works → carry over with fixes)
`importance = max(face_mask, 0.75 × saliency)`, values 0–1 (lines 117–120).

Faces (`faces`, lines 93–104):
- `cv2.FaceDetectorYN` on the whole 1200 px image, `score_threshold=0.6`.
- Each box becomes a filled ellipse with semi-axes 0.65·w × 0.8·h, blurred
  with σ = long side / 150, multiplied by 1.3 and clipped to 1.
- Cost: 0.04 s.

Saliency (`saliency`, lines 107–114):
- U²-Net-p ONNX via onnxruntime CPU. Input resized to 320×320, ImageNet mean/std,
  NCHW. Uses the first output (fused map), min-max normalised, resized back.
- Cost: 0.11 s including session creation.

Measured total ≈ 0.15 s, not "a few seconds" as SPEC §4.2 says.

Failure modes / fixes for M1:
- **Large faces are missed.** The YuNet README says the model "can detect
  faces of pixels between around 10x10 to 300x300". A close-up portrait at
  1200 px has a face well over 300 px. Fix: also run detection on a
  downscaled copy (e.g. long side 320–640) and merge boxes.
- **Saliency is always stretched to 0–1** by the min-max normalisation, so an
  image with no clear subject still gets a "main subject". Consider skipping
  the stretch when `max` is low.
- **OpenCV 5 vs fixed-shape model.** The unpinned `pip install` gave
  `opencv-python-headless 5.1.0.95`. Detection still worked (one face found,
  with a "new graph engine" warning), but the README says the 2023mar model has a
  fixed input shape and that OpenCV 5's ONNX Runtime engine needs the new
  dynamic-shape `face_detection_yunet_2026may.onnx`. In M1, pin OpenCV and pick
  the matching model file.
- An ONNX session is created on every call. Create it once per process.
- The importance range becomes [-1, 1] once `apply_refine` adds `simplify`
  boxes (negative = simplify). Keep that convention if M5 reuses it.

### 2.3 Palette selection (works → carry over)
`pick_palette`, lines 173–191; called at 321–330.
- Candidates: 13 tubes + every pair of tubes at ratios 1:1, 2:1, 1:2, 3:1, 1:3
  (that is SPEC's 1:1/2:1/3:1 in both orders) = 13 + 78×5 = **403** candidates
  in `mixes` mode, 13 in `tubes` mode.
- 20 000 random pixels (seed 0) from the smoothed CIELAB image, weights
  `1 + 4 × clip(importance, 0, 1)`.
- Weighted greedy facility location (minimise Σ w·min distance), then one swap
  pass. `palette_must_include` colours (LLM) are forced in first.
- If `n ≥ candidates` every candidate is used (this is the `tubes` cap).
- Palette numbered light to dark (sort by L*).
- Distances are plain Euclidean Lab (ΔE76). Cost 0.66 s (403-column distance
  matrix).
- The prototype tube list has **13 tubes, no skin-tone tube**. SPEC §5's 14th
  tube was never tested. Colours and codes are marked "APPROXIMATE, unverified"
  in the source.

### 2.4 Mixbox (works → carry over)
- `mixbox.lerp(rgb_a, rgb_b, t)` with 0–255 integer tuples, `t = wb/(wa+wb)`
  (lines 70–73). Package `pymixbox` 2.0.0.
- Only pairwise mixes are predicted. Licence: §3.3.

### 2.5 Contrast preservation (works → carry over)
`assign_colours`, lines 194–219.
- Each segment gets its nearest palette colour. Then segments are visited in
  order of `contrast × (1 + importance)`. A segment is recoloured when all of
  these hold: its ΔE to the border-weighted mean of its neighbours is
  ≥ `PROTECT_DE = 14`, it got the same colour as its *dominant* neighbour
  (longest shared border), and its own mean differs from that neighbour's mean
  by ≥ 14 ΔE. It then takes the nearest *other* palette colour, provided that
  colour is within (distance to the shared colour + 25) ΔE.
- On the test image: 28–30 segments protected.
- Limitations: only the dominant neighbour is checked, and the 25 ΔE slack is
  arbitrary. Both are fine for M1 and can be tuned later.

### 2.6 Felzenszwalb segmentation (works → carry over)
Lines 332–340.
- Base: `felzenszwalb(smoothed, scale, sigma=0.5, min_size=max(hard_px, 4))`.
  `hard_px` = 2 mm² ≈ 11.5 px.
- Fine zone (`importance > 0.6`): a second run with `scale/4`, `sigma=0.3`,
  `min_size=3`, pasted over the base, then relabelled.
- Scale per difficulty (`VARIANTS`, lines 47–52):

| Variant | Colours | Felzenszwalb scale | Min area bg (mm²) | Vector blur σ |
|---|---|---|---|---|
| Easy (A) | 12 | 220 | 40 | 1.4 |
| Medium (B) | 18 | 140 | 18 | 1.2 |
| Hard (C) | 24 | 90 | 8 | 1.0 |
| Tubes only (D) | 13 | 140 | 18 | 1.2 |

- Drop `raw_fine_experiment` (fine pass on the unsmoothed image). The source
  comment says: "more noise, eyes not better".
- Felzenszwalb takes most of the ≈ 3 s per variant that is not accounted for
  by the other steps.

### 2.7 Region merging (partly → rewrite)
`merge_small`, lines 222–247.
- Works on the palette-index raster: connected components are recomputed each
  pass, so neighbours with the same colour fuse automatically.
- Size limit per component:
  `min_px × (1 − 0.85·clip(imp,0,1)) × (1 + 3·clip(−imp,0,1))`. High-contrast
  components (> 14 ΔE, not marked simplify) are capped at 2 × hard minimum.
  The floor is 2 mm².
- A small component joins the neighbour whose palette colour is closest to the
  component's mean colour (the SPEC §4.3 rule). Smallest first.
- At most 10 passes. On the test image all 10 ran, so the loop had not
  converged.
- **There is no region budget.** Result: 5 900–8 700 regions on a simple test
  image (Medium/Hard). SPEC's budget (Medium ≈ 1 500) needs a new merge stage
  that orders candidates by low importance and low contrast and stops at the
  budget. This is the main new algorithmic work in M1.
- Repeating patterns are not handled (SPEC §4.4).
- Cost 1.6 s; `seg_stats` and `adjacency` are recomputed on every pass.

### 2.8 Line layer (partly → carry over and finish)
`line_layer` / `apply_line_layer`, lines 280–312.
- Morphological black-hat on unsmoothed L*, elliptical kernel ≈ 2.5 mm
  (odd, ≥ 5 px).
- Threshold: black-hat > 14 (importance > 0.4) or > 26 (elsewhere), and
  L* < 55. Then a 2×2 open.
- Components kept if ≥ 3 mm² (important) or ≥ 12 mm² (elsewhere).
- The core is dilated by radius ≈ 0.5 mm, giving a stroke about 1 mm wide.
  Colour = nearest palette colour to the mean of the *core* pixels.
- Overlaid **after** merging, so lines are never merged away. 129 line
  components on the test image. Region count drops slightly (lines join
  fragments).
- Failure modes:
  - The overlay cuts existing regions and leaves **new slivers that are never
    re-merged**, so some regions end up unpaintable and unlabelable. M1: run a
    constrained re-merge after the overlay that never absorbs line pixels.
  - Line colour is snapped to the palette, so a dark stroke can pick a
    mid-tone when the palette has no dark colour.
  - SPEC §11 says it is "still not clean". It is the only classic way the
    prototype found to bring face outlines back.

### 2.9 Vectorisation (partly → rewrite)
`vectorise`, lines 250–277.
- Each connected region is traced **independently**: pad by 4 px, Gaussian blur
  of the binary mask with σ from the variant (1.0–1.4), `find_contours` at
  0.5, `approxPolyDP` with ε = 0.3 px. All contours go into one `<path>`
  (outer and holes).
- Failure modes:
  - **No shared boundaries.** Neighbouring paths have slight gaps and overlaps.
    The SVG hides this by giving each path a stroke in its own fill colour
    (`stroke-width .6` in colour mode). In outline mode every border is drawn
    twice, once per side. SPEC §4 step 7 requires shared boundaries, so this
    is a rewrite. A likely route is tracing the label-map boundary graph once
    (edges between pixel corners, junctions as nodes), simplifying each edge
    once, and building every region from those shared edges.
  - Holes depend on contour winding with the default `nonzero` fill rule. This
    was not verified. An enclosing region painted after its island can cover
    it.
- Size: 0.6–0.8 MB of SVG for 6 000–8 700 regions. Cost 0.5 s.

### 2.10 Label placement (partly → keep placement, rewrite sizing)
Lines 273–276.
- Position: maximum of `cv2.distanceTransform` on the region mask (centre of
  the largest inscribed circle, a pixel-grid pole of inaccessibility). Keep it.
- Size: `font_size = clip(1.1 × inscribed_radius, 2.2, 18)` px. At
  0.417 mm/px the floor is ≈ 0.9 mm text height, which cannot be read on
  paper. Labels can also overflow regions that are long and thin.
- The 2 mm² hard minimum region (≈ 1.6 mm diameter disc) cannot hold any
  legible number. See §4 (#12).

### 2.11 SVG + viewer (works as demo → rewrite in M3)
- The SVG is built directly as strings: `viewBox` in working-resolution px,
  `<g class="regions">` with `path.r[data-c][fill][stroke]` and
  `<g class="labels">` with `<text data-c font-size>`. There is no
  intermediate model.
- `viewer.html`: a single page with the variants JSON, original and importance
  heat-map embedded as base64; `@panzoom/panzoom@4.5.1` from unpkg
  (`maxScale: 60`). Modes: outline / colour (optional numbers) / original /
  importance. Other features: an opacity slider for the original underlay,
  click a palette entry to highlight its regions, hover tooltip (number +
  recipe), ←/→ variant switcher with `?variant=` in the URL, and an image bar
  from `images.json`. The UI strings are Bulgarian.
- Carry over the interaction set, which matches SPEC §6. Rewrite as Vite/TS
  fed from the canonical model (#7) instead of baked-in HTML.

### 2.12 Metrics (works → carry over)
- Mean ΔE76 over all pixels and over pixels with importance > 0.5. Also
  counts: colours, regions, tubes used, protected segments, line components,
  SVG size.
- Test image: Medium 9.5 ΔE, Hard 8.9 ΔE.
- M1: use ΔE2000 for user-facing numbers, keep these counts, and store them in
  the model.

### 2.13 Not in M1 (keep for later milestones)
- `refine_llm.py` (M5): Claude `claude-opus-5-5`, JSON-schema output
  (`regions[{label, box[x0,y0,x1,y1] in 0–1, action preserve_detail|simplify,
  strength, reason}]`, `palette_must_include[{near_hex, reason}]`, `notes`),
  at most 8 regions. Input: original | result side by side with a 10×10 grid
  (`grid`, lines 401–411). `apply_refine` (lines 123–138) maps boxes to
  importance (blurred rectangle, σ = long side / 200). The refusal case is
  handled with an exit.
- `stylize_gemini.py` (M2): model `gemini-nano-banana-2.1`. Uses
  `client.interactions.create(background=True)` and polls every 4 s with a
  180 s timeout, because a blocking call hangs on `RESOURCE_EXHAUSTED`. Output
  is a 2K JPEG. Any status other than `completed` is treated as failure. M2
  needs to tell refusals apart from errors to drive the `exact` fallback.

### 2.14 Dockerfile (rewrite)
- `python:3.13-slim`, unpinned `pip install numpy opencv-python-headless
  scikit-image pooch onnxruntime pymixbox google-genai anthropic`. Versions
  resolved in this test: numpy 2.5.5, opencv 5.1.0.95, onnxruntime 1.32.0,
  scikit-image 0.26.0, scipy 1.18.1, pymixbox 2.0.0.
- Models are fetched with `ADD` from a **moving** URL (`raw/main/...`) and are
  not checksummed. M1: pin to a commit and verify a SHA-256 (§3).

## 3. Models and libraries: sources, licences, sizes

### 3.1 YuNet (face detection)
- Repo: [opencv/opencv_zoo `models/face_detection_yunet`](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet).
  The README says: "All files in this directory are licensed under MIT
  License" (LICENSE: © 2020 Shiqi Yu). The repo as a whole is Apache-2.0.
- Files: `face_detection_yunet_2023mar.onnx` (used, fixed input shape,
  232 589 bytes), `_int8`, `_int8bq`, and `face_detection_yunet_2026may.onnx`
  (added 2026-05-22: dynamic input shape for OpenCV 5.x's ONNX Runtime engine).
  The files are Git LFS (the tree shows 131-byte pointers; `raw/` serves the
  real file).
- Pinned URL for the 2023mar file (last commit `f12e127`):
  `https://github.com/opencv/opencv_zoo/raw/f12e12798e8314f7c074a6656816c048dcc95b7a/models/face_detection_yunet/face_detection_yunet_2023mar.onnx`
- Valid range: faces of about 10–300 px (README). WIDER Face AP
  0.884/0.866/0.750 (easy/medium/hard).
- Paper: Wu, Peng, Yu, "YuNet: A tiny millisecond-level face detector",
  *Machine Intelligence Research* 20(5), 2023.

### 3.2 U²-Net / U²-Net-p (saliency)
- Upstream: [xuebinqin/U-2-Net](https://github.com/xuebinqin/U-2-Net),
  Apache-2.0. The weights are published only as PyTorch `.pth` on Google Drive
  / Baidu: `u2net.pth` 176.3 MB, `u2netp.pth` 4.7 MB (README).
- ONNX used: the [rembg](https://github.com/danielgatis/rembg) (MIT) release
  `v0.0.0` asset `u2netp.onnx`, **4 574 861 bytes**,
  `https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx`.
  The full `u2net.onnx` in the same release is 175 997 641 bytes.
  This is a third-party conversion of the Apache-2.0 weights.
- Licence obligations: we download at build time and do not redistribute in
  the repo, so nothing needs vendoring. If a built image is ever published,
  include the Apache-2.0 licence text for the weights.
- u2netp was enough in the prototype: 0.11 s, and the full model is 38× larger.
  Keep u2netp for M1.

### 3.3 Mixbox
- [scrtwpns/mixbox](https://github.com/scrtwpns/mixbox): "licensed for
  non-commercial use under the CC BY-NC 4.0 license". Commercial use needs a
  licence from the authors. The PyPI package is `pymixbox`.
- Compatible with SPEC's personal, non-commercial scope. CC BY requires
  attribution, so credit Mixbox in the UI or README.

## 4. Impact on other tickets

- **#7 canonical model.** The prototype has no model: the SVG is produced
  straight from the label raster. What it implies:
  - The natural core is the **label raster** (palette index per pixel at
    working resolution) plus `mm_per_px`. Shared-boundary vectors, labels and
    metrics are derived from it.
  - The line layer is not a separate entity once applied, because it is burnt
    into the raster. Keep its mask if the viewer should show it.
  - Prototype coordinates are px at 1200 px working resolution, with
    0.417 mm/px hard-coded. A model in px plus an explicit `mm_per_px` matches
    the code. Physical sizes (min areas, line width, kernel) are already
    computed in mm and converted to px.
  - Palette entries need: number, hex, Lab, recipe (tubes + parts), share of
    area.
- **#12 tiny-region labels.** The prototype's numbers fall to ≈ 0.9 mm
  (2.2 px), and its 2 mm² hard minimum region cannot hold any legible number.
  So "minimum size = a number fits" is not just a label rule: it raises the
  hard minimum well above 2 mm². For example, a 2.5 mm number needs an
  inscribed circle of roughly 3 mm diameter (≈ 7 mm²). That conflicts with the
  "detail 2 mm²" column in SPEC §4.4. Either the detail minimum rises, or
  important areas need leader-line labels. The line layer also creates slivers
  that cannot be labelled (§2.8).
- **Region budget (SPEC §4.4)**: none exists in the prototype. Budget-driven
  merging is new M1 work, not a port.
- **SPEC corrections** (for the map owner): the importance map costs ≈ 0.15 s,
  not "a few seconds". The tested tube set had 13 tubes, without the skin-tone
  tube. YuNet's 300 px face limit is a known gap.

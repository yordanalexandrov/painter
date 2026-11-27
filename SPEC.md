# Painter — paint-by-numbers generator

Upload a picture, get a printable paint-by-numbers template, a palette built
from a real paint set (with simple mixing recipes), and an interactive browser
viewer.

Personal, self-hosted project in a public repo. Nothing deployment-specific or
personal (hostnames, IPs, tailnet names, paths, emails, API keys, photos) is
committed: secrets and host settings live in `.env` (git-ignored), only
`.env.example` is in the repo.

The decisions below were validated with a throwaway prototype (see §11).

## 1. User flow

1. Upload an image.
2. Choose the **source mode** (§3), **difficulty** and, optionally, advanced settings.
3. In AI mode: review the **stylised preview** next to the original, then
   accept it, regenerate it, or fall back to the original photo.
4. Generate → interactive viewer opens.
5. Inspect, adjust, regenerate; download the PDF.
6. Projects are saved and listed for later.

## 2. Settings

| Setting | Values | Notes |
|---|---|---|
| Source mode | `ai` (default) / `exact` | §3 |
| Difficulty | Easy / Medium / Hard | Sets colours, region budget and minimum region size (§4.4) |
| Number of colours | e.g. 8–36 | Overrides difficulty |
| Region budget | max number of regions | Overrides difficulty |
| Minimum region size | mm² at print size | Background value; important areas go lower (§4.2) |
| Paint mode | `tubes` / `mixes` | §5 |
| Paint set | YAML file from `paints/` | Default: Amsterdam Standard basic set |
| Canvas size | e.g. 30×40, 40×50 cm, custom | Physical size of the finished painting |
| Print paper | A4 (default) | Canvas is tiled across sheets (§6) |

## 3. Source mode

### `ai` — generative stylisation (default)
- The image is first redrawn by an image model as a **flat-colour illustration
  with clear outlines** (about 20 flat colours, no texture), keeping the
  composition; then the normal pipeline runs on that.
- Model: Gemini image editing (`gemini-nano-banana-2.1`) through the Gemini API
  (key in `.env`). About 25 s per image.
- Prototype result on a pastel painting: half the regions (8 100 → 4 100),
  colour error 13 → 8 ΔE, and the eyes, mouth and small figures survive.
  Classic processing could not achieve this.
- Known behaviour:
  - It is an **interpretation**: it can reframe slightly, change a pose detail
    (e.g. an invented pointing finger), or redraw backgrounds. Hence the
    mandatory preview step with *Regenerate* / *Use original*.
  - The prompt insists on identical framing and no added or removed content;
    the LLM reviewer (§4.6) flags invented details.
  - It **refuses some images** (in the prototype: a photo of a public figure;
    ordinary portraits and a baby photo were fine). On refusal or error, fall
    back to `exact` automatically and say so.
- Calls run in the background with polling and a timeout: a blocking call hangs
  silently on quota errors.

### `exact` — classic pipeline on the original
For when the interpretation is not wanted, or the image model refuses.
Uses the full pipeline below including the line layer (§4.5).

## 4. Pipeline

1. **Pre-process:** resize to a working resolution matched to the canvas
   (prototype: 1200 px long side), edge-preserving smoothing (bilateral).
2. **Importance map** (§4.2).
3. **Palette selection** (§4.3).
4. **Segmentation:** edge-aware over-segmentation (Felzenszwalb), finer in
   important areas; each segment gets the nearest palette colour, then
   **contrast preservation** (§4.3).
5. **Region cleanup:** merge regions below their size limit (§4.4) until the
   region budget is met.
6. **Line layer** (`exact` mode, optional in `ai` mode) (§4.5).
7. **Vectorise:** trace **shared boundaries** so neighbours have no gaps or
   overlaps (prototype: blurred-mask iso-contours); simplify.
8. **Labels:** a number at each region's pole of inaccessibility, font fitted
   to the region (§10: tiny regions).
9. **Model:** one canonical result (regions, palette, recipes, labels) feeds
   both the viewer and the PDF.

### 4.2 Importance map
- Faces (YuNet face detector) + main subject (U²-Net saliency), CPU only, a
  few seconds per image.
- Important areas: lower minimum region size, finer segmentation, more weight
  in palette selection.
- The LLM reviewer can add *preserve* / *simplify* boxes (§4.6).

### 4.3 Colour rules
- Palette = N colours chosen **from the achievable set** (tubes, or tubes +
  allowed mixes), by weighted greedy facility location in CIELAB, with
  important pixels weighted higher.
- **Contrast preservation:** if a segment clearly differs from its neighbour
  but both map to the same palette colour, the segment gets the nearest
  *different* palette colour instead of disappearing. "No exact colour" is
  never a reason to merge a detail away.
- When merging, a small region joins the neighbour **with the most similar
  colour**, not the largest neighbour.

### 4.4 Difficulty and region budget
Difficulty = (colours, **region budget**, minimum region size). Size limits
alone left 4 000–13 000 regions in the prototype, which is too many.
Regions are merged in order of least importance and lowest contrast until the
budget is met. Starting values for 40×50 cm (to tune):

| | Colours | Region budget | Min. region (background / detail) |
|---|---|---|---|
| Easy | 12 | ~500 | 40 / 4 mm² |
| Medium | 18 | ~1 500 | 18 / 2 mm² |
| Hard | 24 | ~3 000 | 8 / 2 mm² |

Repeating patterns (shirt print, speaker grilles) produce dozens of tiny
regions; they are merged into the base colour or turned into one region.

### 4.5 Line layer
Thin dark strokes (eyes, outlines of heads and hands) cannot survive
region-based processing. They are detected separately (morphological
black-hat on lightness, stricter outside important areas), widened to a
paintable width of about 1 mm, coloured from the stroke core, and overlaid
after merging so they are never merged away. In the prototype this was the
only classic technique that brought the outline of the face back.

### 4.6 LLM reviewer (Claude API)
- Input: original and result side by side with a 0.0–1.0 grid.
- Output (JSON schema): regions to `preserve_detail` / `simplify` (boxes +
  strength), `palette_must_include` colours, notes.
- Works well for the **palette** (it restored missing sky colours in the
  prototype) and for spotting problems. It can only steer parameters, so it
  cannot rescue fine lines on its own.
- Also used to compare the AI-stylised image with the original and flag
  invented or moved content.
- Model: `claude-opus-5-5`, structured outputs, at most 1–2 review rounds.

## 5. Paints and mixing

- Paint sets are YAML files: brand, name, code, approximate colour. Colours
  are approximations of the manufacturers' charts; later calibration from
  photographed swatches can correct them.
- **Default set: Amsterdam Standard Series, 14 tubes.** Titanium White,
  Lamp Black, Primary Yellow, Yellow Ochre, Pyrrole Red, Primary Magenta,
  Permanent Blue Violet, Ultramarine, Primary Cyan, Permanent Green Light,
  Burnt Sienna, Burnt Umber, Raw Umber, plus a **skin-tone tube** (e.g.
  Naples Yellow Light). Without it, skin in portraits comes out pink, because
  two-tube mixes cannot make a warm skin tone. Codes are to be verified against
  the official chart.
- **`tubes` mode:** every palette colour is one tube. The colour count is
  capped at the tube count. Show the colour error clearly (prototype: ~23 ΔE
  versus ~13 with mixes).
- **`mixes` mode:** a palette colour is a single tube or a **simple mix**:
  at most **2 tubes**, ratios **1:1, 2:1, 3:1** (in parts). Mixed colours are
  predicted with **Mixbox** (pigment model; CC BY-NC licence, fine for this
  personal non-commercial project). Mixes halved the colour error in every
  prototype image, while needing *fewer* tubes.
- The palette shows, for every number: swatch, recipe
  (`#7 = 2× Burnt Sienna + 1× Titanium White`), tube codes, share of area.
- The preview shows the colours you will actually get.

## 6. Output

### Browser viewer
- SVG with zoom/pan (`@panzoom/panzoom`; 10 000 paths and 1–2 MB SVG stay
  smooth).
- Modes: **outline**, **coloured**, **original**, **importance** (debug), with
  an opacity slider to overlay the original.
- Click a palette entry → highlight all its regions. Hover a region → number,
  paint, recipe.
- Image/project bar at the top; variant switcher to compare settings.
- PDF download.

### PDF
- Outline template at canvas size, **tiled over A4 sheets** with overlap,
  alignment marks and sheet indices (`B2`).
- Overview page of the whole template, scaled down.
- Palette page: number, swatch, recipe, tube codes, shopping list.
- Coloured preview page.

## 7. Architecture

```
pipeline/   pure Python: image + params → model   (OpenCV, scikit-image,
            onnxruntime, Mixbox)
ai/         Gemini stylisation, Claude reviewer
api/        FastAPI: upload, generate, projects, SVG/PDF export
web/        Vite + vanilla TypeScript: viewer, palette, settings
paints/     paint set YAML files
models/     downloaded ONNX models (YuNet, U²-Net), not committed
```

- Generation runs as a background job with status polling (classic: about
  3 s per variant; AI stylisation about 25 s).
- Projects (input, stylised image, parameters, result) are stored on a volume.

## 8. Deployment

- Docker Compose on the home server (CPU only, no GPU needed: heavy image
  generation is done by the external API).
- Reached only over Tailscale (`tailscale serve` for HTTPS in the tailnet).
- `.env`: `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, host settings.

## 9. Milestones

1. **Pipeline core:** `exact` mode end to end (importance, palette, contrast
   preservation, region budget, line layer, vectorise, labels) → SVG + PDF.
2. **AI mode:** Gemini stylisation with fallback + preview step.
3. **Web app:** upload, settings, preview, viewer, projects.
4. **Deployment:** Docker Compose + Tailscale.
5. **LLM reviewer:** palette fixes, invented-detail check, variant choice.
6. **Later:** paint calibration, more paint sets, paint quantity estimates,
   manual importance brush.

## 10. Open points (with current recommendation)

- **Region budget values:** start from §4.4 and tune on real prints.
- **Numbers in tiny regions:** prefer never creating unlabelable regions
  (minimum size = a number fits); in important areas allow a number outside
  the region with a leader line.
- **Manual importance brush** in the viewer ("important here" / "simplify
  here") as a cheap correction when the detectors miss. Later milestone.
- **Paint quantity estimate** per colour (ml, from area). Later milestone.
- Exact Amsterdam tube list, codes and the skin-tone tube choice.
- Gemini pricing per image (not in the docs we read; check in AI Studio).

## 11. Prototype findings (summary)

| Iteration | What | Verdict |
|---|---|---|
| v1 | k-means-style palette + pixel majority filter + size merge | Works, but faces lose detail |
| v2 | importance map, contrast preservation, Felzenszwalb, Mixbox, violet tube | Faces better; too many regions |
| v3 | LLM refine boxes (preserve / simplify, palette) | Palette fixed; fine lines not |
| v4 | line layer | Head and hand outlines back; still not clean |
| AI | Gemini flat-colour stylisation → pipeline | Big improvement: clear details, half the regions |

The prototype code lives on the `prototype` branch, not on `main`.

"""PROTOTYPE v2 — throwaway. Not production code.

Question: does the paint-by-numbers idea from SPEC.md produce usable results?
v3 adds an LLM review loop: an LLM looks at original | result and returns refine
instructions (regions to preserve / simplify, colours to include) — see refine_llm.py.
v2 tested two fixes from user feedback on v1:
  1. importance-aware detail (faces + main subject keep detail, background is simplified);
  2. contrast preservation: a segment that differs from its neighbour keeps a
     *similar but different* palette colour instead of being merged away.

Usage (inside the prototype container):
    python prototype/variants.py <image-path | astronaut | chelsea | coffee> [out-name] [--refine refine.json]
"""
import argparse
import base64
import html
import json
import sys
from pathlib import Path

import cv2
import mixbox
import numpy as np
import onnxruntime as ort
from scipy import ndimage
from skimage import color, data, measure, segmentation

# --- Paint set: Amsterdam Standard (codes and colours APPROXIMATE, unverified) ---
TUBES = [
    ("Titanium White", "105", "#F4F3EE"),
    ("Lamp Black", "702", "#1E1E1E"),
    ("Primary Yellow", "275", "#F5C800"),
    ("Yellow Ochre", "227", "#C9922E"),
    ("Pyrrole Red", "315", "#C3192C"),
    ("Primary Magenta", "369", "#B0185E"),
    ("Permanent Blue Violet", "568", "#4A3B8F"),
    ("Ultramarine", "504", "#22308F"),
    ("Primary Cyan", "572", "#0079B8"),
    ("Permanent Green Light", "618", "#4FA33F"),
    ("Burnt Sienna", "411", "#8C3B1E"),
    ("Burnt Umber", "409", "#4B2B1B"),
    ("Raw Umber", "408", "#5E4A35"),
]
RATIOS = [(1, 1), (2, 1), (1, 2), (3, 1), (1, 3)]

# key: label, mode, colours, segment scale, min area mm², edge blur
VARIANTS = {
    "A": ("Лесно · смеси · 12 цвята", "mixes", 12, 220, 40, 1.4),
    "B": ("Средно · смеси · 18 цвята", "mixes", 18, 140, 18, 1.2),
    "C": ("Трудно · смеси · 24 цвята", "mixes", 24, 90, 8, 1.0),
    "D": ("Средно · само туби · 13 цвята", "tubes", 13, 140, 18, 1.2),
}
WORK_SIDE = 1200
CANVAS_MM = 500             # long side of the assumed 40×50 cm canvas
HARD_MIN_MM2 = 2.0          # nothing smaller than this is paintable
PROTECT_DE = 14.0           # segments that differ this much from neighbours are "details"
IMPORTANCE_SHRINK = 0.85
RAW = {}  # unsmoothed working image (prototype shortcut)    # min area multiplier goes down to 1-0.85 in important areas


# ---------- colour helpers ----------
def hex2rgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float) / 255


def rgb2hex(c):
    return "#%02X%02X%02X" % tuple(int(round(v * 255)) for v in np.clip(c, 0, 1))


def mix(a, b, wa, wb):
    t = wb / (wa + wb)
    out = mixbox.lerp(tuple(int(v * 255) for v in a), tuple(int(v * 255) for v in b), t)
    return np.array(out, float) / 255


def candidates(mode):
    out = [(hex2rgb(h), f"{n} ({c})", [n]) for n, c, h in TUBES]
    if mode == "mixes":
        for i in range(len(TUBES)):
            for j in range(i + 1, len(TUBES)):
                (ni, _, hi), (nj, _, hj) = TUBES[i], TUBES[j]
                for wa, wb in RATIOS:
                    out.append((mix(hex2rgb(hi), hex2rgb(hj), wa, wb),
                                f"{wa} ч. {ni} + {wb} ч. {nj}", [ni, nj]))
    return out


def lab(rgb):
    return color.rgb2lab(np.asarray(rgb, float).reshape(-1, 1, 3)).reshape(-1, 3)


# ---------- importance map ----------
def faces(bgr):
    h, w = bgr.shape[:2]
    det = cv2.FaceDetectorYN.create("/models/yunet.onnx", "", (w, h), score_threshold=0.6)
    det.setInputSize((w, h))
    _, found = det.detect(bgr)
    mask = np.zeros((h, w), np.float32)
    boxes = [] if found is None else found[:, :4]
    for x, y, bw, bh in boxes:
        cv2.ellipse(mask, (int(x + bw / 2), int(y + bh / 2)), (int(bw * 0.65), int(bh * 0.8)), 0, 0, 360, 1, -1)
    if len(boxes):
        mask = cv2.GaussianBlur(mask, (0, 0), max(h, w) / 150)
    return np.clip(mask * 1.3, 0, 1), len(boxes)


def saliency(rgb):
    sess = ort.InferenceSession("/models/u2netp.onnx", providers=["CPUExecutionProvider"])
    x = cv2.resize(rgb, (320, 320), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    x = x.transpose(2, 0, 1)[None].astype(np.float32)
    out = sess.run(None, {sess.get_inputs()[0].name: x})[0][0, 0]
    out = (out - out.min()) / (out.max() - out.min() + 1e-6)
    return cv2.resize(out, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_LINEAR)


def importance(rgb):
    face, n_faces = faces(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    sal = saliency(rgb)
    return np.maximum(face, 0.75 * sal), n_faces


def apply_refine(imp, refine):
    """Refine regions: preserve_detail raises importance to `strength`;
    simplify pushes it negative (bigger minimum region there). Range [-1, 1]."""
    h, w = imp.shape
    imp = imp.copy()
    for r in refine.get("regions", []):
        x0, y0, x1, y1 = r["box"]
        m = np.zeros((h, w), np.float32)
        cv2.rectangle(m, (int(x0 * w), int(y0 * h)), (int(x1 * w), int(y1 * h)), 1, -1)
        m = cv2.GaussianBlur(m, (0, 0), max(h, w) / 200)
        st = float(r.get("strength", 1.0))
        if r["action"] == "preserve_detail":
            imp = np.maximum(imp, st * m)
        else:
            imp = np.where(m > 0.5, np.minimum(imp, -st * m), imp)
    return imp


# ---------- segment graph helpers ----------
def adjacency(seg):
    """Pairs (i<j) of touching segments and their shared border length."""
    u = np.concatenate([seg[:, :-1].ravel(), seg[:-1].ravel()])
    v = np.concatenate([seg[:, 1:].ravel(), seg[1:].ravel()])
    m = u != v
    lo, hi = np.minimum(u[m], v[m]), np.maximum(u[m], v[m])
    n = int(seg.max()) + 1
    keys, counts = np.unique(lo.astype(np.int64) * n + hi, return_counts=True)
    return keys // n, keys % n, counts


def seg_stats(seg, lab_img, imp):
    n = int(seg.max()) + 1
    flat = seg.ravel()
    area = np.bincount(flat, minlength=n).astype(float)
    mean = np.stack([np.bincount(flat, lab_img[..., c].ravel(), n) for c in range(3)], 1) / np.maximum(area, 1)[:, None]
    imp_mean = np.bincount(flat, imp.ravel(), n) / np.maximum(area, 1)
    return area, mean, imp_mean


def neighbour_contrast(n, a, b, w, mean):
    """ΔE between a segment's mean and the border-weighted mean of its neighbours."""
    acc = np.zeros((n, 3))
    wsum = np.zeros(n)
    np.add.at(acc, a, mean[b] * w[:, None]); np.add.at(wsum, a, w)
    np.add.at(acc, b, mean[a] * w[:, None]); np.add.at(wsum, b, w)
    nb = acc / np.maximum(wsum, 1)[:, None]
    return np.linalg.norm(mean - nb, axis=1)


# ---------- pipeline steps ----------
def pick_palette(pix_lab, weights, cand_lab, n, forced=()):
    """Weighted greedy facility location + one swap pass: choose n achievable colours.
    `forced` candidate indices are always kept (from LLM `must_include`)."""
    d = np.linalg.norm(pix_lab[:, None, :] - cand_lab[None, :, :], axis=2).astype(np.float32)
    if n >= d.shape[1]:
        return list(range(d.shape[1]))
    w = weights.astype(np.float32)[:, None]
    forced = list(dict.fromkeys(forced))[:n]
    chosen = list(forced)
    cur = d[:, chosen].min(1) if chosen else np.full(d.shape[0], np.inf, np.float32)
    for _ in range(n - len(chosen)):
        k = int(np.argmin((np.minimum(cur[:, None], d) * w).sum(0)))
        chosen.append(k)
        cur = np.minimum(cur, d[:, k])
    for idx in range(len(forced), len(chosen)):
        others = [c for i, c in enumerate(chosen) if i != idx]
        base = d[:, others].min(1)
        chosen[idx] = int(np.argmin((np.minimum(base[:, None], d) * w).sum(0)))
    return sorted(set(chosen))


def assign_colours(seg, mean, imp_mean, pal_lab):
    """Nearest palette colour per segment, then contrast preservation."""
    n = len(mean)
    dist = np.linalg.norm(mean[:, None] - pal_lab[None], axis=2)
    col = dist.argmin(1)
    a, b, w = adjacency(seg)
    contrast = neighbour_contrast(n, a, b, w, mean)
    # dominant neighbour of each segment (longest shared border)
    best_w = np.zeros(n); dom = np.full(n, -1)
    for x, y in ((a, b), (b, a)):
        order = np.argsort(w)  # later (longer) borders overwrite earlier
        for i, j, ww in zip(x[order], y[order], w[order]):
            if ww >= best_w[i]:
                best_w[i], dom[i] = ww, j
    changed = 0
    for i in np.argsort(-(contrast * (1 + imp_mean))):
        j = dom[i]
        if j < 0 or contrast[i] < PROTECT_DE or col[i] != col[j]:
            continue
        if np.linalg.norm(mean[i] - mean[j]) < PROTECT_DE:
            continue
        alt = dist[i].copy(); alt[col[j]] = np.inf
        k = int(alt.argmin())
        if alt[k] < np.linalg.norm(mean[i] - pal_lab[col[j]]) + 25:  # "similar enough" replacement
            col[i] = k; changed += 1
    return col, changed


def merge_small(labels, lab_img, imp, pal_lab, min_px, hard_px):
    """Merge regions below their (importance- and contrast-aware) size limit into the
    neighbour whose palette colour is closest to the region's own colour."""
    for _ in range(10):
        comp = measure.label(labels + 1, connectivity=1, background=0) - 1
        area, mean, imp_mean = seg_stats(comp, lab_img, imp)
        a, b, w = adjacency(comp)
        contrast = neighbour_contrast(len(area), a, b, w, mean)
        limit = min_px * (1 - IMPORTANCE_SHRINK * np.clip(imp_mean, 0, 1)) * (1 + 3 * np.clip(-imp_mean, 0, 1))
        limit = np.where((contrast > PROTECT_DE) & (imp_mean > -0.2), np.minimum(limit, hard_px * 2), limit)
        limit = np.maximum(limit, hard_px)
        small = np.flatnonzero(area < limit)
        if len(small) == 0:
            break
        slices = ndimage.find_objects(comp + 1)
        for cid in small[np.argsort(area[small])]:
            sl = slices[cid]
            r0, r1 = max(sl[0].start - 1, 0), sl[0].stop + 1
            c0, c1 = max(sl[1].start - 1, 0), sl[1].stop + 1
            m = comp[r0:r1, c0:c1] == cid
            ring = cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) & ~m
            neigh = np.unique(labels[r0:r1, c0:c1][ring])
            if neigh.size:
                target = neigh[np.argmin(np.linalg.norm(pal_lab[neigh] - mean[cid], axis=1))]
                labels[r0:r1, c0:c1][m] = target
    return labels


def vectorise(labels, sigma):
    comp = measure.label(labels + 1, connectivity=1, background=0)
    slices = ndimage.find_objects(comp)
    paths, texts = [], []
    pad = 4
    for cid, sl in enumerate(slices, start=1):
        if sl is None:
            continue
        r0, c0 = sl[0].start, sl[1].start
        mm = comp[sl] == cid
        m = np.pad(mm.astype(np.float32), pad)
        k = int(labels[sl][mm][0])
        blurred = cv2.GaussianBlur(m, (0, 0), sigma)
        d = []
        for cnt in measure.find_contours(blurred, 0.5):
            pts = cv2.approxPolyDP(cnt[:, ::-1].astype(np.float32), 0.3, True).reshape(-1, 2)
            if len(pts) < 3:
                continue
            pts = pts + [c0 - pad, r0 - pad]
            d.append("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z")
        if not d:
            continue
        paths.append((k, "".join(d)))
        dist = cv2.distanceTransform((m > 0).astype(np.uint8), cv2.DIST_L2, 5)
        y, x = np.unravel_index(dist.argmax(), dist.shape)
        fs = float(np.clip(dist.max() * 1.1, 2.2, 18))
        texts.append((k, x + c0 - pad, y + r0 - pad, fs))
    return paths, texts, len(slices)


def line_layer(imp, mm_per_px):
    """Thin dark strokes (eyes, outlines) as a mask, made at least ~1 mm wide."""
    L = RAW["lab"][..., 0].astype(np.float32)
    k = max(5, int(round(2.5 / mm_per_px)) | 1)                     # ~2.5 mm structuring element
    bh = cv2.morphologyEx(L, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    thr = np.where(imp > 0.4, 14.0, 26.0)                            # easier to keep lines in important zones
    m = ((bh > thr) & (L < 55)).astype(np.uint8)                     # only genuinely dark strokes
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    n, comp, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    min_area = np.where(imp > 0.4, 3.0, 12.0) / mm_per_px ** 2        # mm² → px, stricter outside
    keep = np.zeros(n, bool)
    for i in range(1, n):
        ys, xs = np.nonzero(comp[stats[i, 1]:stats[i, 1] + stats[i, 3], stats[i, 0]:stats[i, 0] + stats[i, 2]] == i)
        y, x = ys[0] + stats[i, 1], xs[0] + stats[i, 0]
        keep[i] = stats[i, cv2.CC_STAT_AREA] >= min_area[y, x]
    core = keep[comp].astype(np.uint8)
    width = max(1, int(round(0.5 / mm_per_px)))                       # grow to ≥ ~1 mm paintable width
    m = cv2.dilate(core, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * width + 1, 2 * width + 1)))
    return m.astype(bool), core.astype(bool)


def apply_line_layer(labels, imp, pal_lab, mm_per_px):
    """Overlay line components after merging, so they are never merged away.
    Each line component gets the palette colour nearest to its own mean colour."""
    m, core = line_layer(imp, mm_per_px)
    n, comp = cv2.connectedComponents(m.astype(np.uint8), connectivity=8)
    flat = np.where(core, comp, 0).ravel()          # colour from the stroke core, not the widened rim
    cnt = np.bincount(flat, minlength=n)
    mean = np.stack([np.bincount(flat, RAW["lab"][..., c].ravel(), n) for c in range(3)], 1) / np.maximum(cnt, 1)[:, None]
    col = np.linalg.norm(mean[:, None] - pal_lab[None], axis=2).argmin(1)
    labels = labels.copy()
    labels[m] = col[comp[m]]
    return labels, n - 1


def run_variant(smooth_rgb, smooth_lab, imp, spec, refine=None, lines=False):
    name, mode, n, scale, min_mm2, sigma = spec
    h, w = smooth_lab.shape[:2]
    mm_per_px = CANVAS_MM / max(h, w)
    min_px, hard_px = min_mm2 / mm_per_px ** 2, HARD_MIN_MM2 / mm_per_px ** 2

    cands = candidates(mode)
    cand_lab = lab([c[0] for c in cands])
    flat = smooth_lab.reshape(-1, 3)
    rng = np.random.default_rng(0)
    idx = rng.choice(len(flat), 20000, replace=False)
    forced = [int(np.argmin(np.linalg.norm(cand_lab - lab([hex2rgb(c["near_hex"])])[0], axis=1)))
              for c in (refine or {}).get("palette_must_include", [])]
    chosen = pick_palette(flat[idx], 1 + 4 * np.clip(imp.ravel()[idx], 0, 1), cand_lab, n, forced)
    chosen.sort(key=lambda i: -cand_lab[i, 0])  # number from light to dark
    pal_lab = cand_lab[chosen]

    seg = segmentation.felzenszwalb(smooth_rgb, scale=scale, sigma=0.5, min_size=max(int(hard_px), 4))
    fine_zone = imp > 0.6
    if fine_zone.any():  # finer segmentation where detail matters, on the UNSMOOTHED image
        hack = RAW.get("raw_fine_experiment", False)  # v3 experiment: more noise, eyes not better
        raw = RAW["rgb"] if hack else smooth_rgb
        fine = segmentation.felzenszwalb(raw, scale=scale / (8 if hack else 4), sigma=0.2 if hack else 0.3,
                                         min_size=3)
        seg = np.where(fine_zone, fine + seg.max() + 1, seg)
        seg = measure.label(seg + 1, connectivity=1, background=0) - 1
    seg_lab = np.where((imp > 0.6)[..., None], RAW["lab"], smooth_lab) if RAW.get("raw_fine_experiment") else smooth_lab
    _, mean, imp_mean = seg_stats(seg, seg_lab, imp)
    col, protected = assign_colours(seg, mean, imp_mean, pal_lab)
    labels = col[seg]
    labels = merge_small(labels, seg_lab, imp, pal_lab, min_px, hard_px)
    n_lines = 0
    if lines:
        labels, n_lines = apply_line_layer(labels, imp, pal_lab, mm_per_px)

    fidelity = float(np.linalg.norm(flat - pal_lab[labels.ravel()], axis=1).mean())
    imp_mask = imp.ravel() > 0.5
    review = pal_lab[labels]
    fidelity_imp = float(np.linalg.norm(flat[imp_mask] - pal_lab[labels.ravel()[imp_mask]], axis=1).mean()) if imp_mask.any() else 0

    paths, texts, n_regions = vectorise(labels, sigma)
    share = np.bincount(labels.ravel(), minlength=len(chosen)) / labels.size
    palette = []
    for i, ci in enumerate(chosen):
        rgb, recipe, tubes = cands[ci]
        palette.append({"n": i + 1, "hex": rgb2hex(rgb), "recipe": recipe, "tubes": tubes,
                        "share": round(float(share[i]) * 100, 1)})
    hexes = [p["hex"] for p in palette]

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">',
           '<g class="regions">']
    svg += [f'<path class="r" data-c="{k}" fill="{hexes[k]}" stroke="{hexes[k]}" d="{d}"/>' for k, d in paths]
    svg.append('</g><g class="labels">')
    svg += [f'<text data-c="{k}" x="{x:.1f}" y="{y:.1f}" font-size="{fs:.1f}">{k + 1}</text>' for k, x, y, fs in texts]
    svg.append("</g></svg>")

    used_tubes = sorted({t for p in palette for t in p["tubes"]})
    review_rgb = (np.clip(color.lab2rgb(review), 0, 1) * 255).astype(np.uint8)
    return {
        "name": name, "palette": palette, "svg": "".join(svg), "review_rgb": review_rgb,
        "stats": {
            "Цветове": len(palette),
            "Полета": n_regions,
            "Нужни туби": len(used_tubes),
            "Мин. поле (фон / детайл)": f"{min_mm2:g} / {HARD_MIN_MM2:g} mm²",
            "Запазени детайли (контраст)": protected,
            "Линии (слой)": n_lines if lines else "—",
            "ΔE цяло / важни зони": f"{fidelity:.1f} / {fidelity_imp:.1f}",
            "SVG размер": f"{sum(len(s) for s in svg) / 1e6:.1f} MB",
        },
        "tubes": used_tubes,
    }


def load(arg):
    if arg in ("astronaut", "chelsea", "coffee"):
        return getattr(data, arg)()[..., :3]
    bgr = cv2.imread(arg, cv2.IMREAD_COLOR)
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def b64(img_rgb, ext=".jpg"):
    ok, buf = cv2.imencode(ext, cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])
    return f"data:image/{ext[1:].replace('jpg', 'jpeg')};base64," + base64.b64encode(buf.tobytes()).decode()


def grid(img):
    """Draw a 10×10 coordinate grid (0.0–1.0) so an LLM can give boxes."""
    out = img.copy()
    h, w = out.shape[:2]
    for i in range(1, 10):
        x, y = int(w * i / 10), int(h * i / 10)
        cv2.line(out, (x, 0), (x, h), (0, 255, 255), 1)
        cv2.line(out, (0, y), (w, y), (0, 255, 255), 1)
        cv2.putText(out, f"{i / 10:.1f}", (x + 2, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
        cv2.putText(out, f"{i / 10:.1f}", (2, y - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", nargs="?", default="astronaut")
    ap.add_argument("name", nargs="?")
    ap.add_argument("--refine", help="refine JSON from an LLM review")
    ap.add_argument("--plan", choices=["difficulty", "lines"], default="difficulty")
    args = ap.parse_args()
    out_name = args.name or Path(args.src).stem
    refine = json.loads(Path(args.refine).read_text()) if args.refine else None

    img = load(args.src)
    s = WORK_SIDE / max(img.shape[:2])
    img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC if s > 1 else cv2.INTER_AREA)
    smooth = img
    for _ in range(2):
        smooth = cv2.bilateralFilter(smooth, 7, 30, 5)
    smooth_lab = color.rgb2lab(smooth / 255.0)
    RAW["rgb"], RAW["lab"] = img, color.rgb2lab(img / 255.0)
    imp, n_faces = importance(img)
    print(f"faces: {n_faces}", flush=True)

    imp_ref = apply_refine(imp, refine) if refine else imp
    if args.plan == "lines":  # approach comparison: baseline / line layer / line layer + LLM refine
        plan = [("A", VARIANTS["B"], set()), ("B", VARIANTS["B"], {"lines"}),
                ("C", VARIANTS["B"], {"lines", "refine"} if refine else {"lines"}), ("D", VARIANTS["C"], {"lines"})]
        suffix = "-v4"
    elif refine:  # compare each difficulty without / with the LLM refine
        plan = [("A", VARIANTS["B"], set()), ("B", VARIANTS["B"], {"refine"}),
                ("C", VARIANTS["C"], set()), ("D", VARIANTS["C"], {"refine"})]
        suffix = "-v3"
    else:
        plan = [(k, v, set()) for k, v in VARIANTS.items()]
        suffix = "-v2"

    variants = []
    review_dir = Path(__file__).parent / "out" / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    for key, spec, opts in plan:
        print(f"variant {key} …", flush=True)
        use_ref = "refine" in opts
        v = run_variant(smooth, smooth_lab, imp_ref if use_ref else imp, spec, refine if use_ref else None,
                        lines="lines" in opts)
        v["key"] = key
        if "lines" in opts:
            v["name"] += " · линии"
        if use_ref:
            v["name"] += " · LLM refine"
        rev = np.concatenate([grid(img), np.full((img.shape[0], 8, 3), 255, np.uint8), grid(v.pop("review_rgb"))], 1)
        cv2.imwrite(str(review_dir / f"{out_name}{suffix}-{key}.png"), cv2.cvtColor(rev, cv2.COLOR_RGB2BGR))
        v["stats"] = {"Открити лица": n_faces, **v["stats"]}
        variants.append(v)

    heat_src = imp_ref if refine else imp
    heat = cv2.applyColorMap(((np.clip(heat_src, -1, 1) + 1) * 127.5).astype(np.uint8), cv2.COLORMAP_INFERNO)
    heat = cv2.cvtColor(heat, cv2.COLOR_BGR2RGB)
    for r in (refine or {}).get("regions", []):
        x0, y0, x1, y1 = r["box"]
        h, w = heat.shape[:2]
        c = (0, 255, 120) if r["action"] == "preserve_detail" else (120, 160, 255)
        cv2.rectangle(heat, (int(x0 * w), int(y0 * h)), (int(x1 * w), int(y1 * h)), c, 2)
        cv2.putText(heat, r.get("label", r["action"])[:40], (int(x0 * w) + 4, int(y0 * h) + 16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 1)
    page = (Path(__file__).parent / "viewer.html").read_text()
    page = page.replace("__TITLE__", html.escape(out_name))
    page = page.replace("__ORIGINAL__", b64(img))
    page = page.replace("__IMPORTANCE__", b64(heat))
    page = page.replace("__SIZE__", json.dumps([img.shape[1], img.shape[0]]))
    page = page.replace("__VARIANTS__", json.dumps(variants, ensure_ascii=False).replace("</", "<\\/"))
    out = Path(__file__).parent / "out" / f"{out_name}{suffix}.html"
    out.write_text(page)
    pages = sorted(f.name for f in out.parent.glob("*.html"))
    rank = lambda f: ({"-v4": 0, "-v3": 1, "-v2": 2}.get(f[-8:-5], 3), f)
    (out.parent / "images.json").write_text(json.dumps(sorted(pages, key=rank)))
    print("wrote", out)


if __name__ == "__main__":
    main()

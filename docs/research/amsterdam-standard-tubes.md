# Amsterdam Standard Series: tube list, codes and colours

Research for issue #3 (part of map #1, feeds #8, the paint set YAML schema).
Context: SPEC §5 names a 14-tube default set and says the codes still need
checking against the official chart.

## Answer in short

- All 13 named tubes exist in the Amsterdam Standard Series acrylic range under
  the names SPEC §5 uses. Their codes are in the table below.
- Recommended skin-tone tube: **292 Naples Yellow Red Light**, not 222 Naples
  Yellow Light. The runner-up is 289 Titanium Buff Light, and 224 Naples Yellow
  Red is the deeper option Royal Talens puts in its own portrait set.
- None of these colour values were measured from paint. There are two
  manufacturer sources: the hex code on each royaltalens.com product page, and
  swatches sampled from the printed colour chart PDF. They often disagree by a
  lot. Use the product-page hex as the default and keep the chart value as a
  cross-check.

## Sources

| # | Source | Trust | What it gives |
|---|---|---|---|
| S1 | Royal Talens, *color chart Amsterdam Standard Series* (1-page PDF, QuarkXPress, created 2017-03-23), mirrored by a reseller at `webareal.sk/fotky40801/fotov/_ps_258amsterdam-standard-series-eng.pdf` | Manufacturer document, older range (73 colours) | Code, name, pigments, opacity, lightfastness, printed CMYK swatch |
| S2 | royaltalens.com product pages, e.g. `royaltalens.com/en/catalog/amsterdam-standard-series-acrylic/standard-series-acrylic-tube-120-ml-<name>-<code>` and `royaltalens.com/products/amsterdam-standard-series-acrylic-tube-120-ml` | Manufacturer, current | Per-colour "Hex colour code", opacity, lightfastness |
| S3 | royaltalens.com set pages (`/products/amsterdam-standard-series-acrylic-paint-*-set-*`) | Manufacturer, current | Contents of the sets |
| S4 | Google Monk Skin Tone scale (skintone.google) | Published reference scale | 10 skin reference colours for the skin-tube check |

**Access caveat:** royaltalens.com returned HTTP 429 to every direct fetch
during this research. The S2/S3 values were read from the search engine's index
of those pages, not from a live page load. Each value was attributed to its
royaltalens.com URL, and the index flagged some scraped pages as having jumbled
layouts. Re-check the hex values in a browser before treating them as final.

## The 14 tubes

Code, name, pigments, opacity and lightfastness come from S1. **Site hex** is
S2. **Chart hex** is the median pixel of the S1 swatch, rendered by Ghostscript
at 150 dpi with its default CMYK→sRGB conversion.

Opacity (S1): 1 = transparent, 2 = semi-transparent, 3 = semi-opaque, 4 = opaque.
Lightfastness `+++` = at least 100 years under museum conditions (ASTM D4303).

| Code | Name (official) | Pigments | Opacity | LF | Site hex (S2) | Chart hex (S1) |
|---|---|---|---|---|---|---|
| 105 | Titanium White | PW6 | 4 | +++ | `#FFFFFF` | `#FFFFFF` |
| 702 | Lamp Black | PBk7 | 4 | +++ | `#2E2D2C` | `#332E30` |
| 275 | Primary Yellow | PY3/PY74 | 3 | ++ | `#FFED00` | `#FFF200` |
| 227 | Yellow Ochre | PY42 | 4 | +++ | `#C49720` | `#CF9626` |
| 315 | Pyrrole Red | PR254 | 3 | +++ | `#BC0615` | `#E31F26` |
| 369 | Primary Magenta | PV19 | 1 | +++ | `#B7024F` | `#D91C5C` |
| 568 | Permanent Blue Violet | PV23/PV19 | 2 | +++ | `#50267F` | `#5C2D91` |
| 504 | Ultramarine | PB29 | 1 | +++ | `#344290` | `#244EA2` |
| 572 | Primary Cyan | PB15/PW6 | 2 | +++ | `#0077C0` | `#00A2D2` |
| 618 | Permanent Green Light | PG7/PY74 | 3 | +++ | `#448E42` | `#009A4B` |
| 411 | Burnt Sienna | PR101 | 2 | +++ | `#892220` | `#B1322F` |
| 409 | Burnt Umber | PR101/PBk11 | 2 | +++ | `#513B30` | `#5F433A` |
| 408 | Raw Umber | PY42/PBk11 | 2 | +++ | `#5A471B` | `#494343` |
| 292 | Naples Yellow Red Light (skin) | PW6/PY42/PR101 | 4 | +++ | `#F5E1CE` | `#FEDCC6` |

Notes on the table:

- **Only Primary Yellow 275 is rated `++`** (25 to 100 years). The other 13
  tubes are `+++`.
- **Opacity matters for the hex.** For the transparent and semi-transparent
  tubes (369, 504, 568, 572, 411, 408, 409), a single hex depends heavily on
  how thick the paint is. The site hex values for these are dark and look like
  masstone. The chart swatches are lighter and look like a print rendition.
- **The chart is a print approximation.** Its CMYK conversion pushes Primary
  Yellow and Transparent Yellow to the process-yellow limit (`#FFF200`). It
  gives Raw Umber as a neutral grey (`#494343`), while the site value
  `#5A471B` is the expected greenish-brown. It also prints Burnt Sienna as a
  textured red.
- **568 pigments:** S1 says PV23/PV19. One indexed site listing gives PV19
  only. Trust S1 unless a current product page says otherwise.
- **The range has grown since S1.** The current site lists a 90 × 20 ml
  "all colors" set (art. 17820490), and other pages mention 102 colours. All
  14 codes above still have current product pages (S2).

## Sets Royal Talens sells (Standard Series, from S3)

| Set | Contents |
|---|---|
| General selection 6 × 20 ml | 105, 275, 315, 504, 619 Perm. Green Deep, 735 Oxide Black |
| Primary 6 × 20 ml | 105, 275, 369, 572, 409, 735 |
| Primary 5 × 120 ml | 105, 275, 369, 572, 735 |
| Classroom 6 × 120 ml | 105, 275, 369, 572, 675 Phthalo Green, 735 |
| Portrait 6 × 20 ml (art. 17820502), also sold as 6 × 120 ml | 105, **224 Naples Yellow Red**, 344 Caput Mortuum Violet, 227, 408, 409 |
| General selection 12 × 20 ml (art. 17820412) | 105, 275, 269 Azo Yellow Medium, 311 Vermilion, 315, 568, 504, 572, 619, 227, 409, 735. The colour list is from a retailer (Dick Blick); the official page was cut off in the index. |
| Others | Landscape 12, Pastel 12, Urban landscape 12, Grey 12, Metallic 6, Pearl 6, General selection 48 / 72, All colors 90, Value packs 12 / 18 × 120 ml, Mixing 5 × 120 ml |

**No Royal Talens set matches the SPEC 14-tube list.** The closest is the
general selection 12, which shares 8 tubes with it. The 14 tubes have to be
bought one by one, or as the 12-set plus single tubes.

**Black:** every Royal Talens basic set uses **735 Oxide Black** (PBk11), not
702 Lamp Black (PBk7). Both work. If the default set should be easy to buy,
consider using 735 instead of 702 (open question for #1, not decided here).

## Skin-tone tube

**Recommendation: 292 Naples Yellow Red Light** (PW6/PY42/PR101, opaque,
`+++`, site hex `#F5E1CE`). It is a ready-made warm, light peach.

**Check (tubes mode only):** I took the 13 base tubes plus one candidate, using
the site hex values. For each of the 10 Monk Skin Tone colours (S4), I found
the nearest single tube by CIEDE2000.

| Candidate | Mean ΔE00 (all 10) | Mean ΔE00 (MST 1–5, light) | Per tone MST1…10 |
|---|---|---|---|
| none (13 tubes) | 10.1 | 11.5 | 6 8 12 15 17 15 14 4 6 4 |
| 222 Naples Yellow Light `#FFFCE5` | 8.9 | 9.1 | 6 8 6 9 16 15 14 4 6 4 |
| 223 Naples Yellow Deep `#F5D769` | 9.9 | 11.0 | 6 8 12 15 14 15 14 4 6 4 |
| **292 Naples Yellow Red Light `#F5E1CE`** | **7.5** | **6.3** | 6 4 5 6 11 15 14 4 6 4 |
| 289 Titanium Buff Light `#F1E8DE` | 7.5 | 6.2 | 1 1 6 9 14 15 14 4 6 4 |
| 224 Naples Yellow Red `#FBAF85` | 9.8 | 10.8 | 6 8 12 15 13 15 14 4 6 4 |
| 316 Venetian Rose `#D78387` | 10.1 | 11.5 | (no gain) |

With the chart hex values instead, the ranking is the same: 289 at 7.4, then
292 and 222 tied at 8.5.

Why 292 and not 289 or 222:

- **289 Titanium Buff Light** ties on the mean, but almost all of its gain is
  at MST 1–2, which are near white. Titanium White already covers those.
  **292** is better from MST 2 to MST 5 (4/5/6/11 against 1/6/9/14), which is
  where most portrait skin sits.
- **222 Naples Yellow Light** (the SPEC example) is nearly white with a slight
  yellow cast. It helps only MST 3.
- **224 Naples Yellow Red** is Royal Talens' own portrait-set choice. It is a
  deeper, more saturated tube, made to be lightened with white. As a single
  tube it barely helps. In `mixes` mode, mixes such as 224 + 105 or 224 + 227
  may do well, and possibly better than 292. **This was not checked:** running
  Mixbox was outside what this research could do. Run the same check with
  every allowed 2-tube mix (1:1, 2:1, 3:1) through Mixbox before deciding.
  The candidates are 292 and 224.

**Gap:** no candidate covers mid-to-dark skin (MST 6–7, about 14 to 15 ΔE00
in tubes mode). With the chart values, 234 Raw Sienna lowered those two tones
to about 10 and 7. If `tubes` mode must handle darker skin, a 15th tube such as
Raw Sienna, or a second skin tube, would be needed.

## Caveats

1. **No values are measured.** The site hex values are manufacturer screen
   values, and nothing says how they were made. The chart values are a print
   rendition put through a generic CMYK profile. Both are approximations.
   SPEC §5 already plans to calibrate later from photographed swatches.
2. The site hex values were read from search-index snippets, because the site
   rate-limited direct fetches. Check them in a browser before release.
3. The skin check uses one reference scale (Monk Skin Tone, 10 tones). It uses
   nearest-tube ΔE00 only, and models no mixing.
4. S1 dates from 2017. Codes and pigments for these 14 tubes look the same in
   the current product pages, but individual pigment changes since then cannot
   be ruled out.

## Effects on #8 (paint set YAML schema)

- Store the code as a **string** (`"105"`). The colour number is the identity
  within a series, and the same numbers are reused across Royal Talens lines.
- Allow **more than one colour value per tube, each with a source**. For
  example, `hex` plus `colour_source: site | chart | measured`, or a list of
  `{hex, source}`, so later calibration can sit next to the manufacturer
  values. Lab can be computed from these values and does not need storing.
- Include optional **`opacity` (1–4)**, **`lightfastness`** and
  **`pigments`** (a list). Opacity is useful for warning that a transparent
  tube's single hex is unreliable.
- Set level: brand (`Royal Talens`), line (`Amsterdam Standard Series`),
  medium (`acrylic`).

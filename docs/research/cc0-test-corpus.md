# CC0 test corpus for pipeline metrics

Research for #5. Question: which 6–10 freely licensed images form a public test
corpus for M1 metrics and regressions, covering a single portrait, a group, a
small child, a pet, a landscape with sky, an interior or still life, a painting
and a high-texture scene?

## Answer

Ten images from Wikimedia Commons, all tagged **CC0 1.0** on their file pages.
No identifiable public figures. Fetch them with a script and pin each one by
SHA-1. Do not commit them (see [Recommendation](#recommendation-fetch-dont-commit)).

## Shortlist

All licences were checked on 2026-11-27 against the file page's wikitext
(`action=raw`) and the Commons API (`extmetadata.LicenseShortName`). Resolution
is the size of the original upload.

| # | Category | Title (Commons file page) | Licence proof | Resolution | Why it stresses the pipeline |
|---|---|---|---|---|---|
| 1 | Portrait, easy baseline | [Gray-haired man portrait (Unsplash).jpg](https://commons.wikimedia.org/wiki/File:Gray-haired_man_portrait_(Unsplash).jpg) | `{{Unsplash}}` → CC0; Unsplash ID dated 2016-08-25 | 5760×3840, 9.7 MB | One clear face on a plain grey gradient. Thin glasses frames and grey hair on grey. Checks face-detail survival with no clutter, and banding on a smooth background. |
| 2 | Portrait, detailed face | [Karen Elder (Unsplash).jpg](https://commons.wikimedia.org/wiki/File:Karen_Elder_(Unsplash).jpg) | `{{Unsplash}}` → CC0; dated 2017-03-06 | 3648×5472, 7.7 MB | Deep wrinkles, wispy white hair and a saturated red shirt against a blurred background. Tests whether eyes and mouth survive while the wrinkles are simplified, and whether the region budget holds on a face full of texture. Portrait orientation. |
| 3 | Group of people | [Three friends by train tracks (Unsplash).jpg](https://commons.wikimedia.org/wiki/File:Three_friends_by_train_tracks_(Unsplash).jpg) | `{{Unsplash}}` → CC0; dated 2017-03-25 | 5472×3648, 10.5 MB | Three medium-sized faces, a patterned blanket and grain elevators against a white sky. Tests detecting several faces and splitting the importance budget between them, plus light-on-light contrast (white buildings, white sky). |
| 4 | Small child | [Baby (Unsplash).jpg](https://commons.wikimedia.org/wiki/File:Baby_(Unsplash).jpg) | `{{Unsplash}}` → CC0; dated 2017-03-17 | 5117×3411, 8.4 MB | Close-up of a sleeping newborn held in adult hands. Soft skin with little contrast, closed eyes, small fingers, a dark background and a knitted blanket. Close to the prototype's baby photo. |
| 5 | Pet / animal | [Relaxed tabby cat (Unsplash).jpg](https://commons.wikimedia.org/wiki/File:Relaxed_tabby_cat_(Unsplash).jpg) | `{{Unsplash}}` → CC0; dated 2016-06-22 | 4272×2848, 4.4 MB | Striped fur on a white fluffy blanket. Lots of texture with little colour variety; the cat's face is not a human face, so YuNet should not fire, and saliency has to carry the importance map. |
| 6 | Landscape with sky | [Kayaks on a mountain lake (Unsplash).jpg](https://commons.wikimedia.org/wiki/File:Kayaks_on_a_mountain_lake_(Unsplash).jpg) | `{{Unsplash}}` → CC0; dated 2016-09-21 | 4804×3182, 9.5 MB | Blue sky gradient, cumulus clouds, snow, dark conifers and turquoise water, with tiny kayaks as small details. Tests sky banding vs region budget, and whether tiny high-contrast objects survive merging. |
| 7 | Interior | [Blue white kitchen interior (Unsplash).jpg](https://commons.wikimedia.org/wiki/File:Blue_white_kitchen_interior_(Unsplash).jpg) | `{{Unsplash}}` → CC0; dated 2017-05-22 (see note) | 4896×3264, 6.8 MB | Straight lines, cabinet doors, pendant lamps, bar stools and window light. Tests clean vectorisation of geometry, many similar whites, and thin structures (lamp cords, stool legs). |
| 8 | Painting | [The Daughters of Catulle Mendès (Renoir, 1888), Met](https://commons.wikimedia.org/wiki/File:The_Daughters_of_Catulle_Mend%C3%A8s,_Huguette_(1871%E2%80%931964),_Claudine_(1876%E2%80%931937),_and_Helyonne_(1879%E2%80%931955).jpg) | `{{cc-zero}}`; Met Open Access object [438014](https://www.metmuseum.org/art/collection/search/438014) reports `isPublicDomain: true` | 3011×3722, 2.3 MB | Pastel Impressionist painting with three small faces, a violin, a piano and a patterned dress. Close to the prototype's pastel painting; tests brushwork texture, small faces in a painting, and the `ai` stylisation path. |
| 9 | High texture | [Lavender meadow (Unsplash).jpg](https://commons.wikimedia.org/wiki/File:Lavender_meadow_(Unsplash).jpg) | `{{Unsplash}}` → CC0; dated 2016-07-16 | 5472×3648, 13.4 MB | Thousands of small purple spikes over green, with shallow depth of field. Worst case for the region budget and for unlabelable regions; there is no face and little salient subject. |
| 10 | Tiny figures / crowd | [Holiday on a wet beach (Unsplash).jpg](https://commons.wikimedia.org/wiki/File:Holiday_on_a_wet_beach_(Unsplash).jpg) | `{{Unsplash}}` → CC0; dated 2017-04-29 | 3888×2592, 1.8 MB | Aerial view of a beach with dozens of tiny people and towels, plus a turquoise water gradient. Tests whether small details survive when they are too small for face detection, and whether contrast preservation keeps them apart from the sand. |

Alternates if one is rejected:
- [Still Life with Fruit, Glassware, and a Wanli Bowl (Willem Kalf), Met](https://commons.wikimedia.org/wiki/File:Still_Life_with_Fruit,_Glassware,_and_a_Wanli_Bowl_MET_DP145932.jpg): `{{cc-zero}}`, 3251×3697. A very dark still life, useful as a low-key case.
- [Adventurers taking a break (Unsplash).jpg](https://commons.wikimedia.org/wiki/File:Adventurers_taking_a_break_(Unsplash).jpg): CC0, 4158×2723. Small figures in mist on rocks.
- [Woman holding cat (Unsplash).jpg](https://commons.wikimedia.org/wiki/File:Woman_holding_cat_(Unsplash).jpg): CC0, 5184×3456. A face and a pet in one frame.

### Licence notes

- **Unsplash imports.** The Commons template
  [`{{Unsplash}}`](https://commons.wikimedia.org/wiki/Template:Unsplash)
  transcludes `{{Cc-zero}}` and says the image "was published prior to
  5 June 2017 under the Creative Commons CC0 1.0 Universal Public Domain
  Dedication". On 5 June 2017 Unsplash replaced CC0 with its own licence. The
  template documentation says files published after 4 June 2017 do not qualify.
  Every Unsplash pick has a publication date before that cutoff. Most dates
  come from the Unsplash image ID, which is a millisecond Unix timestamp
  (e.g. `photo-1489791505242-…` = 2017-03-17), and are backed by Wayback
  snapshots linked on the file page.
- **Kitchen (#7).** This file page has no image ID or Wayback snapshot older
  than June 2017. Its proof is the `date=2017-05-22` field and the
  `April 2017 in Utah` category. It is also the only pick whose page is not in
  `Images from Unsplash (review needed)`. The evidence is good but weaker than
  for the others. If in doubt, use the Kalf still life instead.
- **"Review needed".** Several Unsplash files are still in the Commons
  licence-review queue. That is a Commons process flag, not a licence dispute,
  and the publication dates above meet the template's rule.
- **People in photos.** CC0 covers copyright only. Personality and model rights
  are not covered, and Commons does not record model releases for these
  imports. That is fine for test inputs and CI artefacts. Do not use the
  photos of people (#1–4, #10) in project marketing.
- **Public figures.** None. #8 depicts private 19th-century children, so the
  Gemini refusal seen in the prototype should not apply. Still record the
  result when M2 runs.

## Recommendation: fetch, don't commit

Fetch the images with a script. Do not commit them.

1. `SPEC.md` already says no photos are committed to the public repo. Eight of
   the ten picks are photos.
2. The originals total about 75 MB. Committing them would bloat every clone,
   and the pipeline only needs 1200 px anyway.
3. Pinning by SHA-1 makes the inputs reproducible. If someone uploads a new
   version of a Commons file, the SHA-1 check fails loudly instead of silently
   changing the metrics.

Shape of the script:
- A manifest file in the repo (e.g. `tests/corpus/manifest.yaml`) with, per
  image: `id`, `category`, Commons `title`, file-page URL, original URL,
  `sha1`, licence, and expected face count (filled in by running YuNet once
  and reviewing the result by hand).
- The fetch script downloads each original from `upload.wikimedia.org` with a
  descriptive `User-Agent` (Wikimedia asks for one), checks the SHA-1, and
  downscales locally to the working resolution with a fixed resampler. Do not
  use Commons thumbnails for this: Commons regenerates them, so their bytes
  are not stable.
- CI caches the downloaded originals, keyed on the manifest hash.

Fallback: CC0 also allows committing small derivatives (e.g. 1200 px long
side, about 0.3–0.5 MB each, about 4 MB in total). Do this only if the network
fetch proves flaky in CI, and only after revisiting the `SPEC.md` "no photos"
rule.

Pinned originals (SHA-1 from the Commons API, `iiprop=sha1`):

| # | SHA-1 | Original URL |
|---|---|---|
| 1 | `d62d9e01cd0c2c8320735a0746f8c6301f1dc965` | https://upload.wikimedia.org/wikipedia/commons/b/bf/Gray-haired_man_portrait_%28Unsplash%29.jpg |
| 2 | `b5405c73265b30e054f609de0ec686845bdcc806` | https://upload.wikimedia.org/wikipedia/commons/f/f8/Karen_Elder_%28Unsplash%29.jpg |
| 3 | `95eb81b07a835f7ab1b40acf0cf3ce7940ecbc1a` | https://upload.wikimedia.org/wikipedia/commons/d/d4/Three_friends_by_train_tracks_%28Unsplash%29.jpg |
| 4 | `2aa52dd51d541c006850762d0316e778c446e5e5` | https://upload.wikimedia.org/wikipedia/commons/6/66/Baby_%28Unsplash%29.jpg |
| 5 | `8bf8ce338c30d898db27e6ee912d1e2ec004040c` | https://upload.wikimedia.org/wikipedia/commons/a/a6/Relaxed_tabby_cat_%28Unsplash%29.jpg |
| 6 | `648326d15883ad98e06db3109bd9e91c19cb41ce` | https://upload.wikimedia.org/wikipedia/commons/0/0f/Kayaks_on_a_mountain_lake_%28Unsplash%29.jpg |
| 7 | `f8a4cee912512a1c6d651da869a03508d88081f2` | https://upload.wikimedia.org/wikipedia/commons/2/26/Blue_white_kitchen_interior_%28Unsplash%29.jpg |
| 8 | `d4f7ba3f01a6e955c4a81eaabf5a6630cec99dd1` | https://upload.wikimedia.org/wikipedia/commons/e/eb/The_Daughters_of_Catulle_Mend%C3%A8s%2C_Huguette_%281871%E2%80%931964%29%2C_Claudine_%281876%E2%80%931937%29%2C_and_Helyonne_%281879%E2%80%931955%29.jpg |
| 9 | `b02c88e471adc8b2c2ffed306de71055c1b3db42` | https://upload.wikimedia.org/wikipedia/commons/6/61/Lavender_meadow_%28Unsplash%29.jpg |
| 10 | `165ec9bfb3039f1e9c63b3de3b6a31abbd874ca9` | https://upload.wikimedia.org/wikipedia/commons/b/b4/Holiday_on_a_wet_beach_%28Unsplash%29.jpg |

## Notes for #9 (metrics and thresholds)

- **No ground truth.** None of these images comes with segmentation masks or
  face boxes. Metrics must be reference-free (region count vs budget, ΔE to
  the source, unlabelable share, gaps and overlaps), or compare against a
  baseline run that a human has approved. Face-detail survival needs expected
  face boxes, which have to be created once (YuNet plus a manual check) and
  stored in the manifest.
- **Expected faces differ a lot.** Roughly: #1 1, #2 1, #3 3, #4 1, #8 3 (small,
  painted), #5/#6/#7/#9 0, #10 many but probably below YuNet's minimum size.
  The face metric should skip images with no expected faces and not count 0/0
  as a pass.
- **One threshold will not fit all.** #9 (lavender) and #10 (beach) will hit
  the region budget and have the highest share of unlabelable regions. #1 and
  #6 should pass easily. Consider per-image or per-category thresholds, or
  treat the hard images as tracked regressions (no worse than the baseline)
  rather than as absolute pass/fail.
- **Sky and gradient banding** (#1 background, #6 sky, #10 water) is not
  captured by mean ΔE. It may need its own check, e.g. the number of regions
  in low-saliency smooth areas.
- **Painting (#8)** is the natural `ai`-mode regression image, matching the
  prototype's pastel-painting result.
- Because everything is CC0, CI can publish its SVG and PDF outputs as public
  artefacts with no licence concern.

## Sources

- Commons file pages and wikitext (`?action=raw`) for each file listed above.
- Commons API `action=query&prop=imageinfo&iiprop=size|sha1|url|extmetadata`.
- [Template:Unsplash](https://commons.wikimedia.org/wiki/Template:Unsplash) and its `/doc` subpage (CC0 cutoff of 5 June 2017).
- [Met Collection API object 438014](https://collectionapi.metmuseum.org/public/collection/v1/objects/438014) (`isPublicDomain: true`).
- [CC0 1.0 legal code](https://creativecommons.org/publicdomain/zero/1.0/).

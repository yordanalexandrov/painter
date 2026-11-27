"""PROTOTYPE — throwaway. LLM review step for the paint-by-numbers pipeline.

Sends the review image (original | result, with a 0.0–1.0 grid) to Claude and
gets back refine instructions as JSON, in the schema variants.py --refine reads.

Usage (needs ANTHROPIC_API_KEY or another Anthropic credential):
    pip install anthropic
    python prototype/refine_llm.py prototype/out/review/museum-v2-B.png > prototype/input/museum-refine.json
"""
import base64
import json
import sys

import anthropic

SCHEMA = {
    "type": "object",
    "properties": {
        "regions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "box": {"type": "array", "items": {"type": "number"},
                            "description": "[x0, y0, x1, y1] in 0.0–1.0 image coordinates"},
                    "action": {"type": "string", "enum": ["preserve_detail", "simplify"]},
                    "strength": {"type": "number", "description": "0.0–1.0"},
                    "reason": {"type": "string"},
                },
                "required": ["label", "box", "action", "strength", "reason"],
                "additionalProperties": False,
            },
        },
        "palette_must_include": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"near_hex": {"type": "string"}, "reason": {"type": "string"}},
                "required": ["near_hex", "reason"],
                "additionalProperties": False,
            },
        },
        "notes": {"type": "string"},
    },
    "required": ["regions", "palette_must_include", "notes"],
    "additionalProperties": False,
}

PROMPT = """The image shows two panels side by side. Left: the original picture. Right: a
paint-by-numbers version of it, reduced to a fixed palette of mixable acrylic colours.
Both panels have the same 0.0–1.0 coordinate grid.

Review the right panel the way a person who will paint it would. Find:
- details that make the picture recognisable but got lost or blurred (faces, eyes,
  hands, small figures, outlines) -> action "preserve_detail";
- areas broken into many tiny fragments that add work but not meaning (texture,
  hatching, noise) -> action "simplify";
- colours that are clearly missing from the palette -> palette_must_include.

Give boxes in the grid coordinates of ONE panel (0.0–1.0, not the combined image).
Return at most 8 regions, most important first. Keep reasons to one sentence."""


def main():
    path = sys.argv[1]
    data = base64.standard_b64encode(open(path, "rb").read()).decode()
    client = anthropic.Anthropic()
    response = client.beta.messages.create(
        model="claude-opus-5-5",
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        output_config={"effort": "high", "format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": data}},
                {"type": "text", "text": PROMPT},
            ],
        }],
    )
    if response.stop_reason == "refusal":
        sys.exit(f"refused: {response.stop_details}")
    text = next(b.text for b in response.content if b.type == "text")
    print(json.dumps(json.loads(text), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

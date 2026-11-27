"""PROTOTYPE — throwaway. Generative pre-processing with Gemini (Nano Banana 2.1).

Turns a photo / painting into a flat-colour illustration with clear outlines,
so the paint-by-numbers pipeline gets clean shapes (like the tree example).

Usage (inside the prototype container, with GEMINI_API_KEY from .env):
    python prototype/stylize_gemini.py prototype/input/museum.jpg prototype/input/museum-flat.jpg
"""
import base64
import mimetypes
import sys
import time

from google import genai

MODEL = "gemini-nano-banana-2.1"

PROMPT = """Redraw this exact image as a flat-colour illustration that will be used as a
paint-by-numbers template.

Keep the composition, framing, proportions and every subject exactly where they are.
- Use about 20 flat colours, no gradients, no texture, no brush or pastel strokes.
- Merge small texture into larger, clean shapes.
- Keep the details that make the picture recognisable: eyes, mouth, nose, hands,
  small figures, and the outline of the main subject. Draw them as clear, dark,
  slightly thickened shapes so they survive at print size.
- Do not add, remove or move anything. No text, no signature, no frame."""


def main():
    src, dst = sys.argv[1], sys.argv[2]
    mime = mimetypes.guess_type(src)[0] or "image/jpeg"
    data = base64.b64encode(open(src, "rb").read()).decode("utf-8")
    client = genai.Client()  # reads GEMINI_API_KEY
    # background + polling: a blocking call silently hangs on quota errors (RESOURCE_EXHAUSTED)
    created = client.interactions.create(
        model=MODEL,
        background=True,
        input=[
            {"type": "image", "mime_type": mime, "data": data},
            {"type": "text", "text": PROMPT},
        ],
        response_format={"type": "image", "mime_type": "image/jpeg", "image_size": "2K"},
    )
    deadline = time.time() + 180
    interaction = created
    while interaction.status == "in_progress" and time.time() < deadline:
        time.sleep(4)
        interaction = client.interactions.get(created.id)
    if interaction.status != "completed":
        sys.exit(f"{MODEL}: {interaction.status} {getattr(interaction, 'errors', None)}")
    with open(dst, "wb") as f:
        f.write(base64.b64decode(interaction.output_image.data))
    print("wrote", dst)


if __name__ == "__main__":
    main()

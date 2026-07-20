import json

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

WANTED = {
    "analytics": 0xE95B,
    "reports": 0xE95D,
    "marketplace": 0xE95F,
    "invoices": 0xE960,
    "apiConnection": 0xE95C,
    "widgets": 0xE96C,
    "subscribe": 0xE96B,
    "sign": 0xE96A,
    "management": 0xE964,
    "mail": 0xE963,
    "bankCards": 0xE95E,
    "settings": 0xE92E,
    "logout": 0xE961,
}

font = TTFont("icomoon.ttf")
cmap = font.getBestCmap()
glyphs = font.getGlyphSet()
upem = font["head"].unitsPerEm

out = {}
for name, cp in WANTED.items():
    glyph_name = cmap.get(cp)
    if glyph_name is None:
        out[name] = None
        continue
    pen = SVGPathPen(glyphs)
    glyphs[glyph_name].draw(pen)
    out[name] = {"path": pen.getCommands(), "advance": glyphs[glyph_name].width}

print(json.dumps({"upem": upem, "glyphs": out}, indent=2)[:400])
with open("glyphs.json", "w", encoding="utf-8") as f:
    json.dump({"upem": upem, "glyphs": out}, f)

print("\nresolved:", sum(1 for v in out.values() if v), "of", len(WANTED))
print("missing:", [k for k, v in out.items() if not v])

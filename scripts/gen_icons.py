import json
from pathlib import Path

data = json.load(open("glyphs.json", encoding="utf-8"))
upem = data["upem"]
glyphs = data["glyphs"]

# Icon fonts point y upward from a baseline, so flip and shift into the viewbox.
ascent = 832

lines = [
    "// Generated from the icomoon glyph set epoint uses.",
    "// Regenerate with scripts/gen_icons.py.",
    "",
    f"export const ICON_VIEW_BOX = '0 0 {upem} {upem}'",
    "",
    "export const ICON_PATHS = {",
]

for name, glyph in glyphs.items():
    path = glyph["path"].replace("'", "\\'")
    lines.append(f"  {name}: '{path}',")

lines += [
    "} as const",
    "",
    "export type IconName = keyof typeof ICON_PATHS",
    "",
    f"export const ICON_TRANSFORM = 'translate(0, {ascent}) scale(1, -1)'",
    "",
]

out = Path("icons.generated.ts")
out.write_text("\n".join(lines), encoding="utf-8")
print("wrote", out, out.stat().st_size, "bytes")

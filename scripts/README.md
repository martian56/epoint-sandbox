# scripts

`extract_glyphs.py` pulls the sidebar icon glyphs out of the icomoon font the epoint dashboard
uses and writes `glyphs.json`. `gen_icons.py` turns that into
`apps/web/src/components/icons/paths.ts`.

Both are one-off tools. Run them only if the icon set needs refreshing:

```bash
curl -s "https://epoint.az/fonts/icomoon/fonts/icomoon.ttf" -o icomoon.ttf
uv run --with fonttools python extract_glyphs.py
uv run --with fonttools python gen_icons.py
```

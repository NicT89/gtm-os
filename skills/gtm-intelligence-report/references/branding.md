# Branding and layout

Defaults are the Launch99 identity; any engagement can override them in `config.json` (`palette`, `fonts`, `assets.logo`).

| Token | Default | Use |
|---|---|---|
| primary | #F56A00 | accents, section kickers, INFERRED label |
| dark | #132b4a | headers, cover block, KNOWN label |
| accent | #31b7b9 | cover decoration, secondary chart series |
| ink | #0B2545 | body text |
| tints | #FDEBDD, #E8EDF3, #E3F5F5, #F4F6F9 | callouts, zebra rows, tiles |
| danger | #c81414 | UNVERIFIED label |
| link | #166cd4 | URLs |

Fonts: headings Poppins (Regular, Medium, Bold), UI and tables Inter, body PT Sans. Provide TTF paths in `config.json`; missing files fall back to built-in PDF fonts so the build never fails on a font. Convert woff to ttf with fontTools if needed.

Logo: a transparent or white-background PNG on the cover top left, referenced from `assets.logo`. Do not commit logo or font binaries to the plugin repo.

Layout rules that fixed real defects: use `CondPageBreak` (about 3.2 inch) instead of hard page breaks; give headings `keepWithNext`; keep evidence screenshots at about 62 percent of text width and at most 2.55 inch tall; embed JPEG q82 not PNG; escape `$` in chart labels; keep chart text short enough to fit before rendering.

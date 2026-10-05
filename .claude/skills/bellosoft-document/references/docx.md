# Bellosoft in Word (.docx)

Read this before building a `.docx`. Use the `docx` skill to do the actual file
writing; this file only says what the Bellosoft design becomes in Word.

## Tell the user first

A Word version is a **re-creation, not the same document**. Say so before you
start, in one sentence — do not let them discover it. What does not carry over:

- The `<doc-page>` engine. Word paginates its own way; page breaks will fall
  elsewhere.
- The wordmark as a running header renders, but as an embedded image in a Word
  header, not the data URL — extract it once (see below) and reuse the PNG.
- Hairline CSS borders. Word's thinnest rule is heavier than a 1px CSS border at
  print resolution.
- `text-wrap: balance` on headings, the 62ch measure, `orphans/widows`
  behaviour, and `break-inside: avoid` on the callout and stat panel. Word has
  approximate equivalents (keep-with-next, keep-lines-together); use them.
- Montserrat ExtraLight if the recipient does not have Montserrat installed —
  Word substitutes and the ultralight display headings, the single most
  recognisable thing about the design, collapse to a generic sans.

If the recipient does not need to edit the file, recommend PDF instead. Build
the `.docx` anyway if they still want it.

## Page

A4 for PT, A4 or Letter for EN following the recipient. Margins 0.85in all
round, matching the template's `margin="0.85in"`.

## Colours

| Token | Hex | Used for |
|---|---|---|
| `--ink-900` | `14191C` | headings, table header text, emphasis in body, stat values |
| `--ink-700` | `31383D` | body text |
| `--slate-400` | `889FAC` | eyebrow, bullet glyphs, step numbers, quote rule |
| `--stone-400` | `A9ABAE` | captions, header tagline, footer |
| `--paper-200` | `ECECEC` | stat panel fill |
| `--border-default` | `DCDDDE` | hairlines, table body rules, callout border |

No other colours. Word's automatic table styles introduce their own — start from
a plain table and set borders explicitly.

## Type

CSS px × 0.75 = Word pt. Font is Montserrat throughout; the "weight 200" faces
are the **Montserrat ExtraLight** family name in Word, not a lightened weight of
Montserrat.

| Block | Word paragraph style |
|---|---|
| Eyebrow | 9pt, semibold, all caps, expanded spacing ~1.6pt, `stone-400`/`slate-400`, 15pt space after |
| h1 | Montserrat ExtraLight 36pt, line 1.08, `ink-900`, 18pt after. One italic phrase. |
| Lead paragraph | 14pt, `ink-700`, line 1.55, 30pt after |
| Meta strip | 4-column borderless table, single top and bottom hairline; label 7.5pt caps semibold `stone-400`, value 10.5pt `ink-900` |
| h2 | Montserrat ExtraLight 22.5pt, `ink-900`, 12pt after, keep-with-next |
| h3 | 10.5pt semibold all caps, expanded ~1pt, `ink-900`, 10pt after, keep-with-next |
| Body | 12pt, line 1.65, `ink-700`, 13pt after, widow/orphan control on |
| Bullets | 12pt, `·` glyph in `slate-400`, 16.5pt hanging indent, 7.5pt between items |
| Stat panel | 3-column table, `paper-200` cell shading, no borders, 21pt cell padding; value Montserrat ExtraLight 30pt `ink-900`, caption 7.5pt caps semibold `stone-400` |
| Table | header row 7.5pt caps semibold `ink-900` over a `ink-900` bottom rule; body 10.5pt with `border-default` bottom rules; header row set to repeat |
| Note callout | single-cell table, `border-default` box, 18pt/21pt padding, "NOTE"/"NOTA" caption in `slate-400` |
| Quote | 16.5pt Montserrat ExtraLight `ink-900`, 18pt left indent, 2pt `slate-400` left border; attribution 7.5pt caps `stone-400` |
| Next steps | numbered `01` `02` `03` in 8pt semibold `slate-400`, 33pt hanging indent, text 12pt |
| Signature | 2-column borderless table; label 7.5pt caps `stone-400`, 30pt gap, then an `ink-900` top rule over 10pt "Name · Role · Date" |

## Header and footer

**Word header** (all languages): wordmark image 18px tall (≈13.5pt) left,
tagline right — 7pt semibold caps expanded, `stone-400` — over a
`border-default` bottom rule.
- EN: "Technology connects"
- PT: "A tecnologia conecta"

**Word footer** (all languages): left side is "Bellosoft Limited · [city], [country] · bellosoft.com", right side is the confidentiality label — 7pt `stone-400`, over a top rule.
- EN: Watford, England | "Confidential"
- PT: Watford, Inglaterra | "Confidencial"

## Extracting the wordmark

The PNG lives as a base64 data URL on the `<img>` in the header of either
template. Pull the substring after `base64,` up to the closing quote and decode
it to a file once:

```bash
python -c "import base64,re,sys;h=open(sys.argv[1],encoding='utf-8').read();d=re.search(r'base64,([^\"]+)',h).group(1);open('bellosoft-wordmark.png','wb').write(base64.b64decode(d))" assets/template-en.html
```

Same asset in both templates. Keep it out of the skill folder unless it is
needed again — do not commit a second copy of something the templates already
carry.

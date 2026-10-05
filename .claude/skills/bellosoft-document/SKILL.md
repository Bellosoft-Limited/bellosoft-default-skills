---
name: bellosoft-document
description: Use whenever the user wants a client-facing Bellosoft document — a proposal, quote, statement of work, report, memo, letter, brief, contract summary or any deliverable that goes out under the Bellosoft name, in English or Portuguese, as HTML, PDF or Word. Also use when the user mentions the Bellosoft template, Bellosoft branding, or asks to "put this on Bellosoft letterhead".
---

# Bellosoft document

Two locale templates carry the Bellosoft house design: Montserrat, ultralight
display headings, uppercase letterspaced eyebrows, hairline rules, the wordmark
in a running header, a signature block at the end. Building a document means
**filling a template in**, never designing one.

- `assets/template-en.html` — English, British English, £
- `assets/template-pt.html` — Portuguese, PT-BR, R$

Each is one standalone file: Google Fonts link, colour tokens in `:root`, the
`<doc-page>` paged-document engine inlined, and the wordmark embedded as a data
URL. Nothing else is needed to print it.

## Workflow

### 1. Pick the locale

Write in the language the user is using:

- **EN** — English, British spelling, £ currency
- **PT** — Portuguese (Brazilian), R$ currency

If the audience is genuinely ambiguous (e.g. a Brazilian client of a UK
entity), ask which locale to use. Never machine-translate one locale's file from
the other; if both are needed, fill each template independently from the source
facts.

### 2. Ask the output format

**Always ask, every time.** Do not assume:

> HTML, PDF, or Word (.docx)?

- **HTML** — the true path. Fill the template, hand over the `.html`. The user
  opens it and prints to PDF; the inlined engine owns the geometry.
- **PDF** — Render the HTML to PDF using headless Chrome/Edge (see **Rendering
  PDF** section below). You provide both files.
- **DOCX** — a re-creation, not the same document. Read `references/docx.md`
  before starting and tell the user what does not carry over.

### 3. Gather the facts

Never invent a figure, date, price, reference number or client name. Ask for
anything missing, or leave the template's placeholder visibly in place and say
which ones you left.

### 4. Build

Copy the locale's template to the output filename, then edit **only** the content
inside the final `<div>` of `<doc-page>` — plus the footer's confidentiality
label if the user wants a different one. Replace the specimen text with real
content and **delete every block you do not need**.

Read `references/house-style.md` before writing any prose.

## Blocks

The specimen document inside each template is the block reference. There are
thirteen available block types; delete unused ones, **never invent new ones**:

1. Eyebrow (uppercase letterspaced accent label)
2. h1 (main title)
3. Lead paragraph
4. Four-column meta strip
5. h2 (section heading)
6. h3 (subsection heading)
7. Body paragraph
8. Bullet list
9. Three-up stat panel
10. Table with `<thead>`
11. Bordered note callout
12. Quote
13. Numbered next steps
14. Signature block

Repeat a block as often as needed (many h2 sections, several tables). Keep them
in the template's order unless the document's logic demands otherwise.

## Hard rules

- Keep the running header and footer, and the signature block at the end.
- Inline styles only, copied from the specimen, using the existing `var(--*)`
  tokens. **No new colours**, no stylesheet, no classes.
- **Never write an `@page` rule** or hard-code paper dimensions. The engine owns
  all print geometry.
- Never touch anything above `<body>` — the `<style>` block, the engine script,
  the font link. Never re-encode or replace the wordmark data URL.
- Sentence case throughout. UPPERCASE only for eyebrows and captions. No emoji.

## Rendering PDF

Build the HTML first and keep it — the user gets both files.

Use headless Chrome or Edge for print-to-PDF rendering. On Windows, Edge is
always present:

```bash
"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" --headless --disable-gpu --no-pdf-header-footer --print-to-pdf="out.pdf" "file:///absolute/path/out.html"
```

Wait a moment for the webfont to load and the custom `<doc-page>` element to
render. If no headless browser is available (some sandboxes), say so plainly and
hand over the HTML with print instructions rather than substituting a degraded
renderer.

## Verify before delivering

Do not claim it works. Open the HTML in a browser and look at it: the wordmark
renders, Montserrat loaded (headings are visibly ultralight, not bold), no
placeholder text survives, no block is half-deleted, tables have their header
row. For PDF, confirm the file is non-empty and has the pages you expect.

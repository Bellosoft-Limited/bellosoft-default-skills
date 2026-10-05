# Bellosoft house style

Read before writing any prose into a template.

## Voice

We are Bellosoft; the reader is you. Short declaratives. No preamble — the lead
paragraph states what the document is and what the reader should do with it,
starting from the first word.

State value by naming what a thing is not. "Not a rebuild — the existing data
stays where it is" carries more than "seamless and robust". Adjectives are not
evidence.

Claims carry numbers where numbers exist, and the numbers are specific enough to
be checked. "14 days to first prototype" beats "rapidly". If you cannot name the
number, do not make the claim.

## Headline

The h1 is two sentences, both in sentence case, both ending in a full stop:
a plain title, then exactly **one** italicised phrase carrying the promise.

> Fiscal classification, rebuilt. *One motor, every competence.*

One italic phrase. Not zero, not two. Nothing else in the document is
italicised.

## Case and punctuation

- Sentence case everywhere: headings, table headers' underlying words, list
  items, captions.
- UPPERCASE is reserved for eyebrows and captions — the small letterspaced
  labels. The template already applies it via `text-transform`, so type those in
  sentence case too and let the CSS do it.
- No emoji. No exclamation marks.
- Bullets are one line each where possible; add a qualifying clause only when
  the detail genuinely matters.

## Measure and length

Body copy sits on a 62-character measure (`max-width:62ch` — already in the
specimen, keep it). Quotes sit at 58ch. Respect them; they are why the page
reads well.

Prefer three bullets to seven. Prefer one tight table to three loose ones. A
document that fits its argument in two pages is stronger than one padded to
four.

## Locale

### English — `template-en.html`

British English: organisation, recognise, programme, analyse, licence (noun) /
license (verb), whilst is archaic — use while. Currency £, thousands separated
with a comma: £48,000. Dates written long: 6th August 2026.

### Portuguese — `template-pt.html`

PT-BR. Currency R$, Brazilian convention: R$ 48.000,00 — full stop for
thousands, comma for decimals, space after R$. Dates written long: 6 de agosto
de 2026.

**Never machine-translate one locale from the other.** If both versions are
needed, write each from the source facts. A translated headline loses the
italic-phrase rhythm, and translated currency is a real commercial error.

## Numbers in the stat panel

Three stats, no more, no fewer — the panel is a three-column grid and two stats
leave a visible hole. Each value is short enough to read at 40px: `50+`, `14d`,
`Zero`, `R$ 2,4M`. The caption beneath says what it counts.

## Tables

Every table gets a `<thead>`. Long tables repeat their header across printed
pages only if the header is in a `<thead>` — this is not cosmetic.

Numeric columns are right-aligned, text columns left. Keep the specimen's
`break-inside:avoid` on each `<tr>`.

## Signature block

Stays at the end, always. Left is "For Bellosoft Limited" / "Pela Bellosoft
Limited"; right is the client. If a document genuinely needs no countersignature
— an internal report, say — replace the right-hand column's label rather than
deleting the block and leaving a lopsided grid.

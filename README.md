# indrajala-datasets-herodotus-rawlinson

Herodotus' *Histories* in George Rawlinson's translation, all nine books, cleaned to ASCII plain
text for character-level language modelling, for use by
[`indrajala-ml`](https://github.com/davidbarkhuizen/indrajala-ml) and other consumers that want a
pinned, checksum-verified source rather than a manually-supplied local copy.

This repo holds a *reproducible cleaned text*: the source is Wikisource's transcription, pinned to
one revision of each book, and `clean.py` rebuilds `data/herodotus-rawlinson.txt` from it byte for
byte (`python3 clean.py --check`).

## contents

```
clean.py                                  - fetches the pinned source revisions, verifies, cleans
metadata.json                             - repo-level metadata (provenance, revisions, file list)
data/
  herodotus-rawlinson.txt                 - 1,496,601 characters, 1,856 paragraphs
  herodotus-rawlinson.txt.metadata.json   - checksum, counts, vocabulary
```

## the cleaning

- Markup removed: comments, templates (the header, and with it each book's heading; anchors),
  `span`, `div` and `poem` tags, line breaks, italics, interlanguage links, and three images with
  their captions that Wikisource's editors added. A wiki link becomes its text.
- Chapter numbers removed (the source numbers some books' chapters and not others).
- A paragraph per line, verse included: books 1-6 are hard-wrapped in the source and their verse
  mostly untagged, so verse can't be told from wrapped prose there; one rule keeps the books
  alike. Paragraphs are separated by a blank line, the books by two blank lines.
- ASCII: accents stripped (Europe for Europé), ligatures spelled out (Phoenicians for
  Phœnicians), dashes as `-` and `--`, quotes straight. 76 distinct characters remain: letters,
  digits, space, newline and `!"'(),-./:;?`.

This translation's Wikisource text has no footnotes, so there are none here.

## quick start

```python
text = open("data/herodotus-rawlinson.txt", encoding="ascii").read()
vocabulary = sorted(set(text))
```

There is no train/test split: consumers make their own (`indrajala-ml` holds out the last 10%).

## provenance

Herodotus wrote in the 5th century BC; George Rawlinson's translation was first published in
1858-60 (he died in 1902), and Wikisource's text is the 1910 edition: all public domain. The
transcription is Wikisource's ([The History of Herodotus
(Rawlinson)](https://en.wikisource.org/wiki/The_History_of_Herodotus_(Rawlinson))), whose pages
are published under CC BY-SA 4.0; the cleaned text keeps only the public-domain words, not the
editors' links, images or markup. `metadata.json` lists each book's revision and the checksum of
its raw wikitext, which `clean.py` verifies.

## versioning

Consumers should pin to a specific tag or commit, not `main` - see `metadata.json`'s `version`
field for this repo's own packaging version.

## license

This repo's own packaging (this README, `clean.py`, `metadata.json`, directory layout) is
MIT-licensed - see `LICENSE`. The text itself is in the public domain; see "provenance" above.

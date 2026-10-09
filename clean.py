"""
Rebuilds data/herodotus-rawlinson.txt from Wikisource: George Rawlinson's translation of
Herodotus' Histories (the 1910 text), its nine books fetched as wikitext at pinned revisions,
checksum-verified, and cleaned:

- the markup removed: comments, the header template (and with it each book's heading), anchors,
  spans, divs, poem tags, line breaks, italics, interlanguage links, and three images with their
  captions (added on Wikisource, not Rawlinson's); a wiki link becomes its text;
- the chapter numbers that start some paragraphs dropped;
- each paragraph on one line, verse included (books 1-6 are hard-wrapped at the source, verse
  mostly untagged, and 7-9 are not wrapped); paragraphs separated by a blank line, books by two;
- normalized to ASCII: accents stripped, ligatures spelled out (ae, oe), dashes as - and --,
  curly quotes straight. Any other non-ASCII character is an error, not a silent change.

    python3 clean.py            # fetch, verify, clean, write data/herodotus-rawlinson.txt
    python3 clean.py --check    # the same, then compare with the committed file, byte for byte

Python 3.10+, standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import unicodedata
import urllib.request

TITLE = "The_History_of_Herodotus_(Rawlinson)/Book_{book}"
URL = "https://en.wikisource.org/w/index.php?title={title}&oldid={revision}&action=raw"
OUT = "data/herodotus-rawlinson.txt"

# book: (Wikisource revision id, sha256 of its raw wikitext)
SOURCES: dict[int, tuple[int, str]] = {
    1: (10761576, "a4b3226181f13aabb2e26b2a5228700e3d7139ea9afa295900f201b071b18718"),
    2: (7044570, "926a234666db3dd04bcca8dba94c8c1cbef73b2cfb64f71809439720df3be9ed"),
    3: (15467572, "1c5b18f3c8358e4d84686f4f959d2b2e1b9542b06ffe9e8e45be6963509cb90c"),
    4: (6064815, "7109432bfe6c58b5b0bd48ef735c2a9dc384b1937bc0ae52f21ff51c78e3667d"),
    5: (6173895, "2fec868ad1b3a36344747e115563e98f66d7fa6bf11cb48a22074be89264d111"),
    6: (6173902, "bca3a58a4a979cf48ca8b3d3a3ebc9eb3f46a2799c01a2782adfd9daa8df4ebf"),
    7: (9417761, "a38fe73d2fd9646ed7addc918b2886fe9e5af038a0945734d099855ff14c7c36"),
    8: (9417744, "2d8fe6ecfe881e1595b702393fd1d5f81305fd47d28c8452f16c671f52a2aea8"),
    9: (6173924, "a0959d761cbfc7c74e5e441f19ff963c1020ee59096bd6a97416b304b46396b5"),
}

# characters NFKD doesn't reduce to ASCII
SPELLED = {"æ": "ae", "Æ": "AE", "œ": "oe", "Œ": "OE", "—": "--", "–": "-", "‘": "'", "’": "'", "“": '"', "”": '"'}


def fetch(book: int) -> str:
    revision, expected = SOURCES[book]
    url = URL.format(title=TITLE.format(book=book), revision=revision)
    request = urllib.request.Request(url, headers={"User-Agent": "indrajala-datasets-herodotus-rawlinson/clean.py"})
    with urllib.request.urlopen(request) as response:
        raw = response.read()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected:
        sys.exit(f"book {book}: revision {revision}'s sha256 is {actual}, expected {expected}")
    return raw.decode("utf-8")


def strip_markup(wikitext: str) -> str:
    text = re.sub(r"<!--.*?-->", "", wikitext, flags=re.S)
    text = re.sub(r"\{\{header.*?\n\}\}", "", text, flags=re.S)
    text = re.sub(r"\{\{(?:DEFAULTSORT|[Aa]nchor)[^}]*\}\}", "", text)
    if "{{" in text:
        raise ValueError(f"an unhandled template: {text[text.index('{{') :][:80]!r}")
    text = re.sub(r"\[\[(?:File|Image):[^\]]*\]\]", "", text)  # images and their captions, added on Wikisource
    text = re.sub(r"\[\[[a-z]{2,3}:[^\]]*\]\]", "", text)  # interlanguage links
    text = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", text)  # a link as its text
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"</?(?:span|div)\b[^>]*>", "", text)
    text = re.sub(r"'{2,3}", "", text)
    leftover = re.search(r".{0,40}[<>\[\]].{0,40}", re.sub(r"</?poem>", "", text))
    if leftover:
        raise ValueError(f"unhandled markup (poem tags aside): {leftover.group()!r}")
    return text


def paragraphs(text: str) -> list[str]:
    """Each paragraph on one line, verse included: books 1-6 are hard-wrapped at the source and their
    verse is mostly untagged, so it can't be told from wrapped prose; one rule keeps the books alike."""
    out: list[str] = []
    for paragraph in re.split(r"\n\s*\n", re.sub(r"</?poem>", "\n\n", text)):
        line = " ".join(paragraph.split())
        line = re.sub(r"^\d+\.\s+", "", line)  # a chapter number
        if line:
            out.append(line)
    return out


def to_ascii(text: str) -> str:
    text = "".join(SPELLED.get(c, c) for c in text)
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    bad = sorted({c for c in text if ord(c) > 127})
    if bad:
        raise ValueError(f"characters with no ASCII form here: {bad}")
    return text


def clean() -> str:
    books = ["\n\n".join(paragraphs(strip_markup(fetch(book)))) for book in SOURCES]
    return to_ascii("\n\n\n".join(books)) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="compare with the committed file instead of writing it")
    args = parser.parse_args()
    text = clean().encode("ascii")
    if args.check:
        with open(OUT, "rb") as f:
            same = f.read() == text
        print("reproduced exactly" if same else "differs from the committed file")
        sys.exit(0 if same else 1)
    with open(OUT, "wb") as f:
        f.write(text)
    print(f"wrote {OUT}: {len(text)} bytes, sha256 {hashlib.sha256(text).hexdigest()}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3.11
"""
Reconstruct edition-specific Book of Mormon text from the BYU-ODH OpenScripture
word-aligned TSV dataset (~/bible-in-bom/text/openscripture), and build a
1830-vs-1920 (and 1830-vs-current) variant register.

Source data: text/openscripture/book-of-mormon/*.tsv
Columns: Citation, wID, 1830, 1837, 1840, 1841, 1879, 1920, 1981, 2013
- Citation is already the MODERN verse reference (constant across editions).
- wID: integer = head word; N.NN = subword/punctuation attached to head N.
- '⌴' = literal space token. '∅' = word absent in this edition (skip).

Output:
  text/bom-1830.json     { "1 Nephi 1:1": "I, Nephi, ...", ... }
  text/bom-1920.json     same shape, 1920 Salt Lake City edition wording
  text/bom-current.json  same shape, prefers 2013 col, falls back to 1981
  data/variants.json     [{citation, wid, editions: {1830:"white", 1920:"white", ...}}, ...]
                         one entry per word-position where 1830 differs from 1920
                         OR 1830 differs from current — this is the raw variant
                         register the adjudication stage reads from.

Does NOT touch the published site's text — this is the internal reconstruction
step (Plan v1 step 1). License note: OpenScripture's dataset carries no
declared license (checked 2026-09-05). This script's OUTPUT is used for
internal verification and to derive the variant register; before publishing
any RUNNING TEXT on the public site, cross-check `text/bom-1830.json` against
an independently-sourced PD transcription (Wikisource 1830) and resolve the
OpenScripture licensing question. See PLAN.md and NOW.md.
"""
import csv
import json
import re
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "text" / "openscripture" / "book-of-mormon"
OUT_DIR = ROOT / "text"
DATA_DIR = ROOT / "data"

EDITIONS = ["1830", "1837", "1840", "1841", "1879", "1920", "1981", "2013"]
NULL = "∅"   # U+2205 EMPTY SET — word absent in this edition
SPACE = "⌴"  # U+2334 APL FUNCTIONAL SYMBOL QUAD — literal space token


def wid_key(w: str):
    # "12" -> (12, 0) ; "12.01" -> (12, 1) ; sorts head before its subwords.
    # One row in Alma.tsv (37:24, wID "2,01") uses a comma typo for the
    # decimal point — normalize rather than special-case it.
    w = w.replace(",", ".")
    if "." in w:
        head, sub = w.split(".", 1)
        return (int(head), int(sub))
    return (int(w), 0)


def build_edition_text(rows, edition_idx):
    """rows: list of (wid, [edition values]), already sorted by wid_key."""
    out = []
    for _wid, vals in rows:
        tok = vals[edition_idx]
        if tok == NULL:
            continue
        if tok == SPACE:
            out.append(" ")
        else:
            out.append(tok)
    text = "".join(out)
    # collapse accidental double spaces, trim
    text = re.sub(r" {2,}", " ", text).strip()
    return text


def main():
    tsvs = sorted(SRC_DIR.glob("*.tsv"))
    if not tsvs:
        print(f"no TSVs found under {SRC_DIR}", file=sys.stderr)
        sys.exit(1)

    per_edition_text = {ed: {} for ed in EDITIONS}
    variants = []

    for tsv_path in tsvs:
        with open(tsv_path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
            header = next(reader)
            assert header[0] == "Citation" and header[1] == "wID", f"unexpected header in {tsv_path}: {header}"
            ed_cols = header[2:]
            assert ed_cols == EDITIONS, f"unexpected edition columns in {tsv_path}: {ed_cols}"

            by_citation = defaultdict(list)
            for row in reader:
                if not row or not row[0]:
                    continue
                citation = row[0]
                wid = row[1]
                vals = row[2:2 + len(EDITIONS)]
                by_citation[citation].append((wid_key(wid), wid, vals))

        for citation, entries in by_citation.items():
            entries.sort(key=lambda e: e[0])
            rows = [(wid, vals) for (_key, wid, vals) in entries]

            for i, ed in enumerate(EDITIONS):
                text = build_edition_text(rows, i)
                if text:
                    per_edition_text[ed][citation] = text

            # variant register: 1830 vs 1920, word-position by word-position
            i1830, i1920, i2013, i1981 = (EDITIONS.index(e) for e in ("1830", "1920", "2013", "1981"))
            for wid, vals in rows:
                v1830 = vals[i1830]
                v1920 = vals[i1920]
                vcur = vals[i2013] if vals[i2013] != NULL else vals[i1981]
                if v1830 in (SPACE, NULL) and v1920 in (SPACE, NULL) and vcur in (SPACE, NULL):
                    continue
                differs_1920 = v1830 != v1920
                differs_current = v1830 != vcur
                if differs_1920 or differs_current:
                    variants.append({
                        "citation": citation,
                        "wid": wid,
                        "1830": None if v1830 == NULL else v1830,
                        "1920": None if v1920 == NULL else v1920,
                        "current": None if vcur == NULL else vcur,
                        "diff1830v1920": differs_1920,
                        "diff1830vCurrent": differs_current,
                    })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for ed, fname in [("1830", "bom-1830.json"), ("1920", "bom-1920.json")]:
        with open(OUT_DIR / fname, "w", encoding="utf-8") as f:
            json.dump(per_edition_text[ed], f, ensure_ascii=False, indent=1)
        print(f"wrote {OUT_DIR / fname}: {len(per_edition_text[ed])} verses")

    current = {}
    for citation in per_edition_text["2013"]:
        current[citation] = per_edition_text["2013"][citation]
    for citation, text in per_edition_text["1981"].items():
        current.setdefault(citation, text)
    with open(OUT_DIR / "bom-current.json", "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=1)
    print(f"wrote {OUT_DIR / 'bom-current.json'}: {len(current)} verses")

    with open(DATA_DIR / "variants.json", "w", encoding="utf-8") as f:
        json.dump(variants, f, ensure_ascii=False, indent=1)
    print(f"wrote {DATA_DIR / 'variants.json'}: {len(variants)} word-level variant rows (1830 vs 1920/current)")


if __name__ == "__main__":
    main()

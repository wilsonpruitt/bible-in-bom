#!/usr/bin/env python3.11
"""
Build a Brass `Book` JSON file (lib/types.ts shape) for one Book of Mormon
book from the reconstructed 1830 text (text/bom-1830.json). One pericope per
verse for now, with an empty `links` array — this is Plan v1 §8 step 2:
"reader renders 1 Nephi text with zero links." Chapter grouping/pericope
merging happens later, during adjudication.

Usage: python3.11 tools/build-book-data.py "1 Nephi" 1-nephi
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    if len(sys.argv) != 3:
        print("usage: build-book-data.py <Book Name> <slug>", file=sys.stderr)
        sys.exit(1)
    book_name, slug = sys.argv[1], sys.argv[2]

    bom = json.load(open(ROOT / "text" / "bom-1830.json", encoding="utf-8"))
    prefix = f"{book_name} "
    verses = {k[len(prefix):]: v for k, v in bom.items() if k.startswith(prefix)}
    if not verses:
        print(f"no verses found for {book_name!r} — check the name matches text/bom-1830.json keys", file=sys.stderr)
        sys.exit(1)

    def sort_key(ref):
        ch, v = ref.split(":")
        return (int(ch), int(v))

    pericopes = []
    for ref in sorted(verses, key=sort_key):
        ch_str, v_str = ref.split(":")
        pericopes.append({
            "id": ref,
            "ch": int(ch_str),
            "ref": ref,
            "text": verses[ref],
            "links": [],
        })

    book = {
        "slug": slug,
        "name": book_name,
        "subtitle": None,
        "translation": "1830 first edition (modern versification)",
        "pericopes": pericopes,
    }
    book = {k: v for k, v in book.items() if v is not None}

    out = ROOT / "data" / f"{slug}.json"
    out.write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {out}: {len(pericopes)} pericopes, {len(set(p['ch'] for p in pericopes))} chapters")


if __name__ == "__main__":
    main()

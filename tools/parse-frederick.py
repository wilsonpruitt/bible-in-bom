#!/usr/bin/env python3.11
"""
Index the biblical passages Nicholas J. Frederick discusses alongside each
Book of Mormon verse — the scholarship stream (PLAN.md §4.4), second source.

Input:  text/frederick-raw.txt — plain text via `pdftotext -layout`, GITIGNORED.
        *The Bible, Mormon Scripture, and the Rhetoric of Allusivity* (Fairleigh
        Dickinson, 2016) is a purchased, copyrighted monograph. What this script
        keeps is a fact index — which Book of Mormon verse is discussed near
        which biblical verse — the same kind of object as a concordance. Do NOT
        extend it to copy Frederick's sentences into tracked output.

Output: data/frederick-refs.json
        { "1 Nephi 13:27": { "near": ["John 1:5", ...], "window": 900 }, ... }

METHOD, AND ITS LIMIT. Frederick has no cross-reference apparatus: he is not
Hardy, and this is not an appendix of proposed intertexts. He is arguing about
the Gospel of John, and he quotes Book of Mormon verses as evidence in those
arguments. So co-occurrence in a window means "these are discussed together",
NOT "Frederick derives this Book of Mormon verse from this biblical verse."
Anything written into a `bibliography` field from this index must therefore say
what he actually does — see CONVENTIONS §6's hard limit. The window is
deliberately narrow for that reason.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "text" / "frederick-raw.txt"
OUT = ROOT / "data" / "frederick-refs.json"
WINDOW = 1500  # characters either side; roughly one argument, tuned so that the
              # 1 Nephi 13:26-14:17 cluster and its John 1:5 discussion — which
              # a human has read and verified as one continuous argument — are
              # captured. Widening further starts joining unrelated paragraphs.

BOILER = re.compile(
    r"^\s*(Copyright © 2016\.|Frederick, J\.\. The Bible,|ProQuest Ebook Central|Created from nottingham)")

BOM = ("1 Nephi|2 Nephi|Jacob|Enos|Jarom|Omni|Words of Mormon|Mosiah|Alma|Helaman"
       "|3 Nephi|4 Nephi|Mormon|Ether|Moroni")
BIBLE = ("Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|1 Samuel|2 Samuel"
         "|1 Kings|2 Kings|1 Chronicles|2 Chronicles|Ezra|Nehemiah|Esther|Job|Psalm|Psalms"
         "|Proverbs|Ecclesiastes|Isaiah|Jeremiah|Lamentations|Ezekiel|Daniel|Hosea|Joel|Amos"
         "|Obadiah|Jonah|Micah|Nahum|Habakkuk|Zephaniah|Haggai|Zechariah|Malachi"
         "|Matthew|Mark|Luke|John|Acts|Romans|1 Corinthians|2 Corinthians|Galatians|Ephesians"
         "|Philippians|Colossians|1 Thessalonians|2 Thessalonians|1 Timothy|2 Timothy|Titus"
         "|Philemon|Hebrews|James|1 Peter|2 Peter|1 John|2 John|3 John|Jude|Revelation")


def main() -> None:
    if not RAW.exists():
        sys.exit(f"{RAW} not found. Run:\n  pdftotext -layout '<the PDF>' {RAW}")
    lines = [l for l in RAW.read_text().split("\n") if not BOILER.match(l)]
    flat = re.sub(r"-\n\s*", "", "\n".join(lines))   # repair end-of-line hyphenation
    flat = re.sub(r"\s+", " ", flat)

    # "Jacob" and "Mormon" name both a Book of Mormon book and other things;
    # requiring a chapter:verse after the name is what keeps them honest.
    bom_hits = [(m.group(0), m.start()) for m in re.finditer(rf"\b({BOM}) \d+:\d+", flat)]
    bib_hits = [(m.group(0), m.start()) for m in re.finditer(rf"\b({BIBLE}) \d+:\d+", flat)]

    index: dict[str, set] = {}
    for ref, pos in bom_hits:
        near = {b for b, p in bib_hits if abs(p - pos) <= WINDOW}
        index.setdefault(ref, set()).update(near)

    out = {k: {"near": sorted(v), "window": WINDOW}
           for k, v in sorted(index.items()) if v}
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")

    print(f"{len(bom_hits)} Book of Mormon citations, {len(bib_hits)} biblical citations.")
    print(f"{len(out)} Book of Mormon verses have a biblical citation within {WINDOW} chars.")
    print(f"wrote {OUT.relative_to(ROOT)}")
    n1 = {k: v for k, v in out.items() if k.startswith("1 Nephi ")}
    print(f"\n1 Nephi: {len(n1)} verse(s) — the pilot's whole overlap with this book.")
    for k, v in n1.items():
        print(f"   {k}: {', '.join(v['near'])}")


if __name__ == "__main__":
    main()

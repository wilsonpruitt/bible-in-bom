#!/usr/bin/env python3.11
"""
Collate a Book of Mormon Isaiah block against the KJV, verse by verse.

PLAN.md §5 requires that 1 Nephi 20-21 be collated against KJV Isaiah 48-49
"and each departure is recorded as a variant row, not treated as two quotation
blocks". This produces those rows mechanically so that the adjudicator argues
about the departures rather than hunting for them.

The alignment is by verse number: 1 Nephi 20:N against Isaiah 48:N. That
alignment is an assumption, not a fact, and the tool reports any verse where
the word-overlap falls below a floor so a human can check whether the
versification has slipped.

Usage:
  python3.11 tools/collate-isaiah.py 1-nephi 20 Isaiah 48
  python3.11 tools/collate-isaiah.py 1-nephi 21 Isaiah 49 --json data/isaiah-variants.json
"""
import argparse, difflib, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORD = re.compile(r"[A-Za-z’']+")


def words(s: str) -> list[str]:
    return WORD.findall(s)


def norm(w: str) -> str:
    return w.lower().replace("’", "'")


def collate(bom_text: str, kjv_text: str):
    """Word-level diff. Returns (ops, overlap) where ops are the departures."""
    a, b = words(kjv_text), words(bom_text)
    sm = difflib.SequenceMatcher(a=[norm(w) for w in a], b=[norm(w) for w in b])
    ops = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        ops.append({
            "kind": {"replace": "replace", "delete": "omit", "insert": "add"}[tag],
            "kjv": " ".join(a[i1:i2]),
            "bom": " ".join(b[j1:j2]),
            "at": i1,
        })
    return ops, sm.ratio()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug"); ap.add_argument("chapter", type=int)
    ap.add_argument("book"); ap.add_argument("kjv_chapter", type=int)
    ap.add_argument("--json", help="write the variant rows here")
    ap.add_argument("--floor", type=float, default=0.55,
                    help="flag verses whose word overlap falls below this")
    args = ap.parse_args()

    book = json.loads((ROOT / "data" / f"{args.slug}.json").read_text())
    kjv = json.loads((ROOT / "text" / "kjv.json").read_text())
    per = {p["ref"]: p["text"] for p in book["pericopes"] if p["ch"] == args.chapter}

    rows, flagged = [], []
    print(f"# {book['name']} {args.chapter} collated against {args.book} {args.kjv_chapter}\n")
    print(f"Running text: {book['translation']}. KJV: Project Gutenberg #10 (see text/SOURCES.md).")
    print("Word-level departures only; punctuation and capitalization are ignored.\n")
    for ref in sorted(per, key=lambda r: int(r.split(":")[1])):
        v = int(ref.split(":")[1])
        kref = f"{args.book} {args.kjv_chapter}:{v}"
        ktext = kjv.get(kref)
        if ktext is None:
            print(f"### {ref}  — NO KJV COUNTERPART at {kref}\n")
            flagged.append((ref, kref, 0.0))
            continue
        ops, ratio = collate(per[ref], ktext)
        mark = "  ⚠ LOW OVERLAP" if ratio < args.floor else ""
        print(f"### {ref} ~ {kref}   (overlap {ratio:.2f}, {len(ops)} departure(s)){mark}")
        if ratio < args.floor:
            flagged.append((ref, kref, ratio))
        for op in ops:
            if op["kind"] == "replace":
                print(f"- KJV `{op['kjv']}` → BoM `{op['bom']}`")
            elif op["kind"] == "omit":
                print(f"- KJV `{op['kjv']}` → BoM (omitted)")
            else:
                print(f"- BoM adds `{op['bom']}`")
            rows.append({"bomRef": f"{book['name']} {ref}", "kjvRef": kref, **op})
        print()

    print(f"\n---\n\n{len(rows)} departures across {len(per)} verses.")
    if flagged:
        print(f"\n⚠ {len(flagged)} verse(s) below the {args.floor} overlap floor — "
              "check the versification assumption before trusting these rows:")
        for ref, kref, r in flagged:
            print(f"  - {ref} ~ {kref} ({r:.2f})")

    if args.json:
        Path(args.json).write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
        print(f"\nwrote {args.json}", file=sys.stderr)


if __name__ == "__main__":
    main()

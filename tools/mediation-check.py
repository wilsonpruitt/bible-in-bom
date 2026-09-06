#!/usr/bin/env python3.11
"""
Decide `mediation` mechanically where the KJV lets you.

The 1 Nephi pilot's principal result was sixteen OT-via-NT rows, and every one
was found the same way: an Old Testament verse and its own New Testament
quotation are worded DIFFERENTLY in the King James Bible, so whichever form
the Book of Mormon has tells you which page it was reading. 2:22 turns on
`ruler` against `prince`; 15:18 on `kindreds` against `nations`; 19:11 on
`vapour` against `pillars`; 17:46 on `smooth` against `plain`.

That is a diff, and it should not be done by eye. Give this tool the Book of
Mormon verse and two or more candidate sources; it diffs the candidates
against each other, and for each point of divergence reports which candidate's
wording the Book of Mormon actually has.

Usage:
  python3.11 tools/mediation-check.py "1 Nephi 22:20" "Deuteronomy 18:15" "Acts 3:22"
  python3.11 tools/mediation-check.py "1 Nephi 2:22" "Exodus 2:14" "Acts 7:27" "Acts 7:35"
  python3.11 tools/mediation-check.py --text "1-nephi" "1 Nephi 15:18" "Genesis 22:18" "Acts 3:25"

It reports evidence, never a verdict: a divergence the Book of Mormon matches
on one side is a fact, and whether that settles the mediation is the
adjudicator's call (CONVENTIONS §7).
"""
import argparse, difflib, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORD = re.compile(r"[A-Za-z’']+")


def words(s): return WORD.findall(s)
def norm(w):  return w.lower().replace("’", "'")


def common_words(kjv, top=120) -> set[str]:
    """
    The most frequent word TYPES in the KJV, derived rather than hand-listed.

    A single-word divergence is only a test if the word is distinctive. "Will"
    or "the" appearing in the Book of Mormon verse proves nothing, because it
    is there for its own reasons — this produced a false "decisive" on the
    pilot's flagship verse (22:20) the first time the tool was run.
    """
    from collections import Counter
    c = Counter(norm(w) for t in kjv.values() for w in words(t))
    return {w for w, _ in c.most_common(top)}


def bom_verse(ref: str) -> str | None:
    for f in ("bom-1830.json",):
        d = json.loads((ROOT / "text" / f).read_text())
        if ref in d:
            return d[ref]
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("bom_ref", help='e.g. "1 Nephi 22:20"')
    ap.add_argument("sources", nargs="+", help="two or more KJV refs to compare")
    ap.add_argument("--text", help="unused; accepted for symmetry with other tools")
    args = ap.parse_args()
    if len(args.sources) < 2:
        sys.exit("give at least two candidate sources to compare")

    kjv = json.loads((ROOT / "text" / "kjv.json").read_text())
    bom = bom_verse(args.bom_ref)
    if bom is None:
        sys.exit(f"{args.bom_ref} not found in text/bom-1830.json")
    missing = [s for s in args.sources if s not in kjv]
    if missing:
        sys.exit(f"not in text/kjv.json: {', '.join(missing)}")

    stop = common_words(kjv)
    bom_norm = set(map(norm, words(bom)))
    bom_flat = " ".join(map(norm, words(bom)))

    print(f"\n{args.bom_ref} (1830)")
    print(f"  {bom}\n")
    for s in args.sources:
        print(f"{s}\n  {kjv[s]}\n")

    print("=" * 72)
    print("DIVERGENCES BETWEEN THE CANDIDATES, and which form the Book of Mormon has")
    print("=" * 72)

    base, *rest = args.sources
    decisive = []
    for other in rest:
        a, b = words(kjv[base]), words(kjv[other])
        sm = difflib.SequenceMatcher(a=[norm(w) for w in a], b=[norm(w) for w in b])
        print(f"\n--- {base}  vs  {other} ---")
        any_op = False
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            any_op = True
            av, bv = " ".join(a[i1:i2]) or "(nothing)", " ".join(b[j1:j2]) or "(nothing)"
            an = " ".join(norm(w) for w in a[i1:i2])
            bn = " ".join(norm(w) for w in b[j1:j2])
            def informative(span: str) -> bool:
                toks = span.split()
                return bool(toks) and any(t not in stop for t in toks)

            in_a = bool(an) and an in bom_flat and informative(an)
            in_b = bool(bn) and bn in bom_flat and informative(bn)
            # A single differing word is the cleanest kind of test.
            # A single differing word is the cleanest kind of test — but only if the
            # word is distinctive enough that its presence means something.
            if not in_a and not in_b and (i2 - i1) == 1 and (j2 - j1) == 1:
                if an not in stop and bn not in stop:
                    in_a, in_b = an in bom_norm, bn in bom_norm
            if in_a and not in_b:
                verdict, mark = f"BoM has {base}'s form", "  ◀── DECISIVE"
                decisive.append((base, av, other, bv))
            elif in_b and not in_a:
                verdict, mark = f"BoM has {other}'s form", "  ◀── DECISIVE"
                decisive.append((other, bv, base, av))
            elif in_a and in_b:
                verdict, mark = "both present in the BoM verse — not a test", ""
            else:
                verdict, mark = "neither — the BoM reads otherwise here", ""
            print(f"  {base:>22} “{av}”")
            print(f"  {other:>22} “{bv}”")
            print(f"  {'':>22} {verdict}{mark}\n")
        if not any_op:
            print("  identical wording — no test available here")

    print("=" * 72)
    if decisive:
        winners = {}
        for src, form, loser, lform in decisive:
            winners.setdefault(src, []).append((form, loser, lform))
        for src, rows in winners.items():
            print(f"\n{len(rows)} decisive point(s) favour {src}:")
            for form, loser, lform in rows:
                print(f"   • BoM has “{form}” ({src}), not “{lform}” ({loser})")
        if len(winners) > 1:
            print("\n⚠ Divergences point BOTH ways. That is a real finding and not a bug —")
            print("  the verse may be a composite. Say so in the note rather than picking one.")
    else:
        print("\nNo decisive divergence. The candidates do not differ at any point the")
        print("Book of Mormon reproduces, so this verse cannot settle its own mediation;")
        print("record mediation as 'uncertain' or argue it from elsewhere (CONVENTIONS §7).")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3.11
"""
PLAN.md §7.2: "Every Hardy appendix row for 1 Nephi is either a Link or a
reasoned exclusion." This checks it.

A Hardy row is accounted for when the source it names appears — as a Link's
source, composite, or recurrenceRefs entry, or as an exclusion — at the verse
Hardy attaches it to OR within one verse of it. The tolerance is deliberate:
Hardy hangs a cross-reference on the verse where the allusion is clearest to a
reader, and this catalogue hangs a Link where the verbal evidence is strongest;
those are not always the same verse, and a link on the neighbouring verse
plainly accounts for the row. Anything further apart is reported as a gap.

Book-and-chapter matching is used for the source, since Hardy cites ranges
("Exodus 14:21-29") where a Link cites a verse.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def bookchap(ref: str):
    m = re.match(r"^(.*?)(\d+):", ref)
    return (m.group(1).strip(), m.group(2)) if m else (ref, "")


def main(slug=None, name=None, tolerance=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("slug", nargs="?", default=slug or "1-nephi")
    ap.add_argument("--name", default=name)
    ap.add_argument("--tolerance", type=int, default=tolerance if tolerance is not None else 1,
                    help="how many verses a Link may sit from the verse Hardy keys the row to")
    args = ap.parse_args()
    slug, tolerance = args.slug, args.tolerance
    name = args.name or json.loads((ROOT / "data" / f"{slug}.json").read_text())["name"]
    hardy = json.loads((ROOT / "data" / "hardy-refs.json").read_text())
    book = json.loads((ROOT / "data" / f"{slug}.json").read_text())
    exc = json.loads((ROOT / "data" / "exclusions.json").read_text())["exclusions"]

    at = {}
    for p in book["pericopes"]:
        s = set()
        for l in p["links"]:
            s.add(l["source"])
            s.update(l.get("composite") or [])
            s.update(l.get("recurrenceRefs") or [])
        at.setdefault(p["ref"], set()).update(s)
    for e in exc:
        r = e["bomRef"].replace(name + " ", "")
        at.setdefault(r, set()).add(e["source"])

    total = covered = 0
    gaps = []
    for ref, refs in sorted(hardy.items()):
        if not ref.startswith(name + " "):
            continue
        v = ref.replace(name + " ", "")
        ch, vs = v.split(":")
        window = set()
        for d in range(-tolerance, tolerance + 1):
            window |= at.get(f"{ch}:{int(vs)+d}", set())
        wbc = {bookchap(x) for x in window}
        for r in refs:
            total += 1
            if r in window or bookchap(r) in wbc:
                covered += 1
            else:
                gaps.append((ref, r))

    print(f"Hardy rows for {name}: {total}")
    print(f"  accounted for (±{tolerance} verse): {covered}")
    print(f"  gaps: {len(gaps)}")
    for g in gaps:
        print(f"   - {g[0]} -> {g[1]}")
    return 1 if gaps else 0


if __name__ == "__main__":
    sys.exit(main())

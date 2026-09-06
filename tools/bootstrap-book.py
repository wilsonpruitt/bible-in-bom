#!/usr/bin/env python3.11
"""
Take a Book of Mormon book from nothing to ready-to-adjudicate.

Builds the data file from the 1830 text, generates machine candidates, creates
the work directory, and reports what a chapter pass will face. Everything it
does is already possible by hand; the point is that a book should not be
half-set-up when agents start on it.

Usage: python3.11 tools/bootstrap-book.py "2 Nephi" 2-nephi
       python3.11 tools/bootstrap-book.py --list
"""
import argparse, json, re, subprocess, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(*cmd, allow_fail=False):
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    r = subprocess.run([sys.executable, *[str(c) for c in cmd]],
                       capture_output=True, text=True, cwd=ROOT)
    if r.returncode and not allow_fail:
        print(r.stdout); print(r.stderr, file=sys.stderr)
        sys.exit(f"failed: {' '.join(str(c) for c in cmd)}")
    return r.stdout


def books():
    bom = json.loads((ROOT / "text" / "bom-1830.json").read_text())
    return Counter(re.sub(r" \d+:\d+$", "", k) for k in bom)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("name", nargs="?")
    ap.add_argument("slug", nargs="?")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--skip-candidates", action="store_true",
                    help="the candidate run is the slow step; skip it if it is already done")
    args = ap.parse_args()

    if args.list or not (args.name and args.slug):
        done = {p.stem for p in (ROOT / "data").glob("*.json")}
        print(f"{'book':20} {'verses':>7}  {'status':>12}")
        for name, n in books().items():
            slug = name.lower().replace(" ", "-")
            print(f"{name:20} {n:7}  {'built' if slug in done else 'not built':>12}")
        if args.list:
            return
        sys.exit("\ngive a book name and a slug")

    name, slug = args.name, args.slug
    if name not in books():
        sys.exit(f"{name!r} is not a book in text/bom-1830.json — see --list")

    print(f"\n1. data/{slug}.json")
    run(ROOT / "tools" / "build-book-data.py", name, slug)

    work = ROOT / "work" / slug
    work.mkdir(parents=True, exist_ok=True)
    print(f"2. work/{slug}/")

    if args.skip_candidates or (work / "candidates.jsonl").exists():
        print("3. candidates — already present, skipping")
    else:
        print("3. candidates (slow — n-gram and fuzzy over the whole KJV)")
        run(ROOT / "tools" / "find-candidates.py", slug, name)

    book = json.loads((ROOT / "data" / f"{slug}.json").read_text())
    per_ch = Counter(p["ch"] for p in book["pericopes"])
    words = sum(len(p["text"].split()) for p in book["pericopes"])
    hardy = json.loads((ROOT / "data" / "hardy-refs.json").read_text())
    fred = json.loads((ROOT / "data" / "frederick-refs.json").read_text())
    h = sum(len(v) for k, v in hardy.items() if k.startswith(name + " "))
    f = sum(1 for k in fred if k.startswith(name + " "))

    print(f"\n{name}: {len(per_ch)} chapters, {len(book['pericopes'])} verses, {words:,} words")
    print(f"  Hardy rows to account for: {h}   (PLAN §7.2)")
    print(f"  Frederick verses touched:  {f}")
    print("  chapters by verse count:",
          ", ".join(f"{c}({n})" for c, n in sorted(per_ch.items())))
    print("\n4. auditing Hardy's verse attribution for this book")
    print("   (the walker mis-keyed four rows in Jacob and one in 1 Nephi;")
    print("    never dispatch agents against an unaudited apparatus)")
    print(run(ROOT / "tools" / "audit-hardy.py", slug, allow_fail=True).rstrip() or "   (no rows)")

    print(f"\nNext: add `{slug}` to data/books.ts, then dispatch one adjudicator "
          f"per chapter (see ADJUDICATING.md).")


if __name__ == "__main__":
    main()

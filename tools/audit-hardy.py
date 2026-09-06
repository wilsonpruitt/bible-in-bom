#!/usr/bin/env python3.11
"""
Audit the verse attribution of data/hardy-refs.json.

parse-hardy.py walks verses against page-header checkpoints and can mis-key a
footnote when a chapter turns over mid-page, or drift inside a long chapter.
Three such errors were found in Jacob by adjudicating agents, at 4:3, 5:2 and
5:4 — after I had told Wilson the first one was "not systematic" on the
strength of a single instance. This tool exists so that claim never has to be
made from one case again.

METHOD. For each Hardy row (a Book of Mormon verse and the biblical passages
he cross-references there), score the content-word overlap between the biblical
passage and the keyed Book of Mormon verse. Then score it against every other
verse in a window around it. If some other verse scores materially better, the
row is a drift suspect and the tool names the better candidate.

WHAT IT CANNOT DO. Many of Hardy's rows are thematic and correctly carry almost
no shared wording — Genesis 22:1-18 at Jacob 3:5 is the standing example, and
this tool will report it as a low-overlap row with no better candidate, which
is the right answer. A row is only ever a SUSPECT here. Every hit needs a human
to read both verses, and every correction goes into
data/hardy-corrections.json with its evidence (CONVENTIONS §6a).

Usage:
  python3.11 tools/audit-hardy.py                 # every book with a data file
  python3.11 tools/audit-hardy.py jacob --window 80
  python3.11 tools/audit-hardy.py --min-gain 0.10
"""
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORD = re.compile(r"[A-Za-z’']+")

# Content words only: a shared "and the of" tells you nothing about attribution.
STOP = set("""a an the and or but if of in on at to for with by from as is are was were be been
being that this these those which who whom whose it its he she they them their his her him i you
ye thou thee thy thine we us our not no nor so then than there here shall will would should may
might can could do did done have has had unto upon into out up down all any some such other same
when where while because therefore wherefore behold yea now also more most many much every one two
o lord god""".split())


def words(t): return [w.lower().replace("’", "'") for w in WORD.findall(t)]
def content(t): return {w for w in words(t) if w not in STOP and len(w) > 2}


def expand(ref: str, kjv: dict) -> list[str]:
    """'Isaiah 5:1-7' -> the verses that exist; a bare ref -> itself."""
    m = re.match(r"^(.*?)(\d+):(\d+)(?:-(\d+))?$", ref.strip())
    if not m:
        return [ref]
    book, ch, lo, hi = m.group(1).strip(), m.group(2), int(m.group(3)), m.group(4)
    hi = int(hi) if hi else lo
    out = [f"{book} {ch}:{v}" for v in range(lo, hi + 1)]
    return [r for r in out if r in kjv] or ([ref] if ref in kjv else [])


def score(bib_words: set, bom_text: str) -> float:
    """Fraction of the biblical passage's content vocabulary present in the verse."""
    if not bib_words:
        return 0.0
    return len(bib_words & content(bom_text)) / len(bib_words)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--window", type=int, default=80,
                    help="verses either side of the keyed verse to consider")
    ap.add_argument("--min-gain", type=float, default=0.12,
                    help="how much better a rival must score to be reported")
    args = ap.parse_args()

    kjv = json.loads((ROOT / "text" / "kjv.json").read_text())
    bom = json.loads((ROOT / "text" / "bom-1830.json").read_text())
    hardy = json.loads((ROOT / "data" / "hardy-refs.json").read_text())
    corrections = {}
    cpath = ROOT / "data" / "hardy-corrections.json"
    if cpath.exists():
        for m in json.loads(cpath.read_text()).get("moves", []):
            corrections.setdefault(m["to"], []).extend(m["refs"])

    slugs = args.slugs or [p.stem for p in (ROOT / "data").glob("*.json")
                           if (ROOT / "data" / p.name).exists()
                           and "name" in json.loads(p.read_text() or "{}")]
    names = {}
    for s in slugs:
        f = ROOT / "data" / f"{s}.json"
        if f.exists():
            try: names[json.loads(f.read_text())["name"]] = s
            except Exception: pass
    # A slug with no data file used to leave `names` empty, and an empty `names`
    # means "audit everything" — so asking for one un-bootstrapped book silently
    # audited the whole corpus and reported its totals as that book's. Found
    # 2026-09-06 on Mosiah, which reported 35 suspects before it had a data file
    # and 13 after. Same shape as the "0 Hardy rows" trap: a number that looks
    # like an answer.
    if args.slugs and not names:
        sys.exit(f"no data file for {', '.join(args.slugs)} — run tools/bootstrap-book.py first "
                 f"(auditing without one would silently scan every book)")

    # Verse order per book, so a "window" means neighbouring verses.
    order = {}
    for k in bom:
        b, cv = k.rsplit(" ", 1)
        ch, v = cv.split(":")
        order.setdefault(b, []).append((int(ch), int(v), k))
    for b in order:
        order[b].sort()

    # The drift has a signature. Every error found so far keeps the VERSE number
    # and moves the CHAPTER: Jacob 4:3→5:3, 5:2→6:2, 5:6→6:6, 1 Nephi 21:16→20:16.
    # That is what a verse-walker checkpointing on page headers does when it
    # crosses a chapter boundary in the wrong place. Testing it directly is far
    # more reliable than the window scan, which reports coincidences of religious
    # vocabulary as well.
    print("=" * 72)
    print("CHAPTER-SHIFT TEST — same verse number, adjacent chapter")
    print("=" * 72)
    shifts = 0
    for ref, cites in sorted(hardy.items()):
        book = ref.rsplit(" ", 1)[0]
        if names and book not in names or ref not in bom:
            continue
        ch, v = map(int, ref.rsplit(" ", 1)[1].split(":"))
        for cite in cites:
            exp = expand(cite, kjv)
            if not exp:
                continue
            bw = set()
            for e in exp:
                bw |= content(kjv[e])
            here = score(bw, bom[ref])
            for d in (-1, 1):
                alt = f"{book} {ch + d}:{v}"
                if alt not in bom:
                    continue
                there = score(bw, bom[alt])
                if there - here >= args.min_gain:
                    shifts += 1
                    done = cite in corrections.get(ref, [])
                    print(f"  {ref} -> {cite}"
                          f"{'   (already corrected)' if done else ''}")
                    print(f"     {here:.2f} here, {there:.2f} at {alt}")
                    print(f"     {alt}: {bom[alt][:120]}")
    print(f"\n  {shifts} chapter-shift suspect(s).\n")

    print("=" * 72)
    print("WINDOW SCAN — any better-scoring verse nearby")
    print("=" * 72)
    suspects = thematic = clean = 0
    for ref, cites in sorted(hardy.items()):
        book = ref.rsplit(" ", 1)[0]
        if names and book not in names:
            continue
        if ref not in bom:
            print(f"⚠ {ref}: keyed to a verse that does not exist")
            continue
        verses = order[book]
        idx = next(i for i, (_, _, k) in enumerate(verses) if k == ref)
        lo, hi = max(0, idx - args.window), min(len(verses), idx + args.window + 1)

        for cite in cites:
            exp = expand(cite, kjv)
            if not exp:
                continue
            bw = set()
            for e in exp:
                bw |= content(kjv[e])
            here = score(bw, bom[ref])
            best_k, best_s = ref, here
            for _, _, k in verses[lo:hi]:
                sc = score(bw, bom[k])
                if sc > best_s:
                    best_k, best_s = k, sc
            corrected = cite in corrections.get(ref, [])
            if best_k != ref and best_s - here >= args.min_gain:
                suspects += 1
                tag = "  (already corrected here)" if corrected else ""
                print(f"SUSPECT {ref} -> {cite}{tag}")
                print(f"        keyed verse scores {here:.2f}; {best_k} scores {best_s:.2f}")
                print(f"        {best_k}: {bom[best_k][:130]}")
            elif here < 0.10:
                thematic += 1
            else:
                clean += 1

    print(f"\n{suspects} suspect(s), {thematic} low-overlap row(s) with no better candidate "
          f"(likely thematic, not drift), {clean} clean.")
    print("Every suspect needs a human to read both verses before anything moves; "
          "corrections go in data/hardy-corrections.json with their evidence.")
    return 1 if suspects else 0


if __name__ == "__main__":
    sys.exit(main())

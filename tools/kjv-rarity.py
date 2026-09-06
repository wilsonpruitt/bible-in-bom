#!/usr/bin/env python3.11
"""
How rare is a phrase in the King James Bible?

This is the single most-used operation in the 1 Nephi pilot and it was done
ad hoc, one throwaway heredoc at a time. Nearly every strong link in the
catalogue rests on a sentence of the form "X occurs in exactly N KJV verses",
and CONVENTIONS §4 asks for those counts wherever a link matters. An
adjudicator without this tool guesses; with it, every `provenance.other`
claim is checkable in one command.

Usage:
  python3.11 tools/kjv-rarity.py "mist of darkness" "rod of iron"
  python3.11 tools/kjv-rarity.py --regex "blinded .{0,20}eyes"
  python3.11 tools/kjv-rarity.py --file phrases.txt --max-show 5
  python3.11 tools/kjv-rarity.py --json "still small voice"

Matching is case-insensitive and ignores the KJV's curly apostrophes, which
is what bit the pilot at Exodus 3:18 ("three days' journey" fails to match a
straight apostrophe). Whitespace in the query is treated as flexible, so a
phrase spanning a line break in your notes still matches.
"""
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load():
    return json.loads((ROOT / "text" / "kjv.json").read_text())


def norm(s: str) -> str:
    return s.replace("’", "'").replace("‘", "'")


def search(kjv, query: str, as_regex: bool):
    pat = query if as_regex else r"\s+".join(re.escape(w) for w in norm(query).split())
    rx = re.compile(pat, re.I)
    return [(ref, text) for ref, text in kjv.items() if rx.search(norm(text))]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("phrases", nargs="*")
    ap.add_argument("--regex", action="store_true", help="treat each phrase as a regex")
    ap.add_argument("--file", help="read phrases from a file, one per line")
    ap.add_argument("--max-show", type=int, default=12)
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    phrases = list(args.phrases)
    if args.file:
        phrases += [l.strip() for l in Path(args.file).read_text().split("\n") if l.strip()]
    if not phrases:
        sys.exit("give at least one phrase (or --file)")

    kjv = load()
    out = {}
    for q in phrases:
        hits = search(kjv, q, args.regex)
        out[q] = [r for r, _ in hits]
        if args.as_json:
            continue
        n = len(hits)
        verdict = ("A KJV SINGLETON — absolute rarity, the strongest kind of evidence"
                   if n == 1 else
                   f"{n} verses — rare enough to name them in provenance.other" if n <= 4 else
                   f"{n} verses — too common to identify a source on its own" if n <= 20 else
                   f"{n} verses — formulaic; see CONVENTIONS §5")
        print(f"\n“{q}”  →  {n}   {verdict}")
        for ref, text in hits[: args.max_show]:
            print(f"    {ref:22} {text[:150]}")
        if n > args.max_show:
            print(f"    … and {n - args.max_show} more")
    if args.as_json:
        print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

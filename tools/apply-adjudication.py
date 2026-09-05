#!/usr/bin/env python3.11
"""
Merge authored adjudication files into the book's data file.

The judgments live in work/<slug>/adjudicated/ch<NN>.json, one file per chapter,
and are the only hand-written scholarly content in the project. data/<slug>.json
is a BUILD ARTIFACT: its running text comes from the 1830 reconstruction and its
links come from here. Keeping the two apart means the book file can be rebuilt
from the texts at any time without putting a single adjudication at risk.

Running this is idempotent — it replaces the links of every chapter it has a file
for and leaves every other chapter untouched.

Usage:  python3.11 tools/apply-adjudication.py 1-nephi
        python3.11 tools/apply-adjudication.py 1-nephi --check
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED = ("source", "type", "confidence", "text", "note")
# PLAN.md §7.5: every link carries an argument, a route, a KJV-specificity call,
# and either a citation or an explicit admission that it has none.
NEEDS_WHYNOT = ("low", "contested")


def validate(chapter: int, ref: str, link: dict) -> list[str]:
    problems = []
    for field in REQUIRED:
        if not link.get(field):
            problems.append(f"{ref} → {link.get('source', '?')}: missing {field}")
    if link.get("confidence") in NEEDS_WHYNOT and not link.get("whyNot"):
        problems.append(
            f"{ref} → {link['source']}: confidence '{link['confidence']}' requires whyNot"
        )
    if not link.get("mediation"):
        problems.append(f"{ref} → {link['source']}: missing mediation")
    if not link.get("kjvSpecific"):
        problems.append(f"{ref} → {link['source']}: missing kjvSpecific")
    has_citation = bool(link.get("bibliography"))
    if not has_citation and link.get("status") != "novel" and not link.get("citationsPending"):
        problems.append(
            f"{ref} → {link['source']}: no bibliography, so needs status 'novel' "
            "or citationsPending: true"
        )
    return problems


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--check", action="store_true",
                    help="validate only; do not write the book file")
    args = ap.parse_args()

    book_path = ROOT / "data" / f"{args.slug}.json"
    book = json.loads(book_path.read_text())

    adj_dir = ROOT / "work" / args.slug / "adjudicated"
    files = sorted(adj_dir.glob("ch*.json")) if adj_dir.is_dir() else []
    if not files:
        sys.exit(f"no adjudication files in {adj_dir}")

    links_by_ref: dict[str, list] = {}
    problems: list[str] = []
    chapters = []
    for path in files:
        data = json.loads(path.read_text())
        chapters.append(data["chapter"])
        for ref, links in data["links"].items():
            links_by_ref[ref] = links
            for link in links:
                problems.extend(validate(data["chapter"], ref, link))

    if problems:
        print(f"{len(problems)} schema problem(s):", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        sys.exit(1)

    applied = 0
    for per in book["pericopes"]:
        if per["ch"] in chapters:
            per["links"] = links_by_ref.get(per["ref"], [])
            applied += len(per["links"])

    pending = sum(
        1 for links in links_by_ref.values() for l in links if l.get("citationsPending")
    )
    print(
        f"{len(files)} chapter file(s), chapters {chapters}: "
        f"{applied} links across {len(links_by_ref)} verses. "
        f"{pending} awaiting citation."
    )

    if args.check:
        print("--check: book file not written.")
        return

    book_path.write_text(json.dumps(book, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {book_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

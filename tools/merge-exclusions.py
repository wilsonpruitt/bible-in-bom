#!/usr/bin/env python3.11
"""
Merge a book's per-chapter exclusion files into data/exclusions.json.

Agents adjudicating one chapter each cannot append to a shared register — the
last writer wins and the rest of the run is lost. So a chapter pass writes
work/<slug>/exclusions/ch<NN>.json (a JSON array) and this merges them, in
chapter and verse order, after the run.

A row already in the register (same bomRef and source) is left alone rather
than duplicated, so the merge can be re-run safely.

Usage: python3.11 tools/merge-exclusions.py 2-nephi [--check]
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = {"bomRef", "source", "category", "reason"}


def sort_key(e: dict) -> tuple:
    m = re.search(r"(\d+):(\d+)$", e["bomRef"])
    return (int(m.group(1)), int(m.group(2)), e["source"]) if m else (0, 0, e["source"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--check", action="store_true", help="validate and report, write nothing")
    args = ap.parse_args()

    reg_path = ROOT / "data" / "exclusions.json"
    reg = json.loads(reg_path.read_text())
    categories = set(reg["categories"])
    have = {(e["bomRef"], e["source"]) for e in reg["exclusions"]}

    incoming, problems = [], []
    for path in sorted((ROOT / "work" / args.slug / "exclusions").glob("ch*.json")):
        rows = json.loads(path.read_text())
        if not isinstance(rows, list):
            problems.append(f"{path.name}: not a JSON array")
            continue
        for e in rows:
            where = f"{path.name} {e.get('bomRef', '?')} → {e.get('source', '?')}"
            missing = REQUIRED - set(e)
            if missing:
                problems.append(f"{where}: missing {sorted(missing)}")
            elif e["category"] not in categories:
                problems.append(f"{where}: category {e['category']!r} is not one of {sorted(categories)}")
            elif (e["bomRef"], e["source"]) in have:
                continue      # already registered; a re-run, not a conflict
            else:
                have.add((e["bomRef"], e["source"]))
                incoming.append(e)

    for p in problems:
        print(f"  ERROR {p}")
    print(f"{len(incoming)} new exclusion(s) from {args.slug}, {len(problems)} error(s)")
    if problems or args.check:
        print("nothing written." if problems else "--check: nothing written.")
        raise SystemExit(1 if problems else 0)

    reg["exclusions"].extend(sorted(incoming, key=sort_key))
    reg_path.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote data/exclusions.json — {len(reg['exclusions'])} rows in the register")


if __name__ == "__main__":
    main()

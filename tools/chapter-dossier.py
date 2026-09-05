#!/usr/bin/env python3.11
"""
Assemble the per-chapter adjudication dossier described in PLAN.md §5: the
Book of Mormon chapter in 1830 wording, with substantive 1830-vs-1920 variants
flagged inline, followed by the machine candidates for that chapter ranked by
n-gram rarity and grouped under the verse they belong to.

This is the packet a human (or an Opus agent) reads in order to write Links and
exclusions. It decides nothing itself; it only puts the evidence in one place.

Usage:  python3.11 tools/chapter-dossier.py 1-nephi 1
        python3.11 tools/chapter-dossier.py 1-nephi 1 --top 60
Output: stdout (redirect to work/<slug>/dossier-ch<N>.md)
"""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# A variant row is only worth an adjudicator's attention when the WORD changed.
# The 1830-to-1920 diff is dominated by punctuation and capitalization added by
# later editors, which never bears on whether a phrase depends on the KJV.
PUNCT_ONLY = re.compile(r"^[^\w]*$")


def substantive(row: dict) -> bool:
    a = (row.get("1830") or "").strip()
    b = (row.get("1920") or "").strip()
    if PUNCT_ONLY.match(a) and PUNCT_ONLY.match(b):
        return False
    return a.lower() != b.lower()


def chapter_of(citation: str) -> int | None:
    try:
        return int(citation.split()[-1].split(":")[0])
    except (ValueError, IndexError):
        return None


def load_variants(book_name: str, chapter: int) -> dict[str, list[dict]]:
    rows = json.loads((ROOT / "data" / "variants.json").read_text())
    by_verse: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        cit = row.get("citation", "")
        if not cit.startswith(book_name + " "):
            continue
        if chapter_of(cit) != chapter or not substantive(row):
            continue
        by_verse[cit].append(row)
    return by_verse


def load_candidates(slug: str, chapter: int) -> dict[str, list[dict]]:
    path = ROOT / "work" / slug / "candidates.jsonl"
    by_verse: dict[str, list[dict]] = defaultdict(list)
    with path.open() as fh:
        for line in fh:
            cand = json.loads(line)
            if chapter_of(cand["bom_ref"]) == chapter:
                by_verse[cand["bom_ref"]].append(cand)
    return by_verse


def score(cand: dict) -> float:
    # Fuzzy-only rows have no n-gram score; rank them below every n-gram hit but
    # keep them, since paraphrase and inverted quotation surface only there.
    return cand.get("ngram_rarity_score", 0.0)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug", help="book slug, e.g. 1-nephi")
    ap.add_argument("chapter", type=int)
    ap.add_argument("--top", type=int, default=50,
                    help="how many candidates to include, ranked by n-gram rarity")
    args = ap.parse_args()

    book = json.loads((ROOT / "data" / f"{args.slug}.json").read_text())
    name = book["name"]

    pericopes = [p for p in book["pericopes"] if p["ch"] == args.chapter]
    variants = load_variants(name, args.chapter)
    candidates = load_candidates(args.slug, args.chapter)

    ranked = sorted(
        (c for rows in candidates.values() for c in rows),
        key=score,
        reverse=True,
    )[: args.top]
    kept = defaultdict(list)
    for cand in ranked:
        kept[cand["bom_ref"]].append(cand)

    total = sum(len(v) for v in candidates.values())
    out = [
        f"# {name} {args.chapter} — adjudication dossier",
        "",
        f"Running text: {book['translation']}. "
        f"{len(pericopes)} verses. "
        f"{total} machine candidates for this chapter; the top {len(ranked)} by "
        f"n-gram rarity are shown below, grouped by verse.",
        "",
        "Substantive 1830-vs-1920 differences are flagged per verse. Note that KJV",
        "spellings (*shew*, *marvellous*) surviving in 1830 and modernized later are",
        "themselves evidence bearing on `kjvSpecific`.",
        "",
        "---",
        "",
        "## Text (1830) with candidates",
        "",
    ]

    for per in pericopes:
        ref = f"{name} {per['ref']}"
        out.append(f"### {per['ref']}")
        out.append("")
        out.append(per["text"])
        out.append("")
        for row in variants.get(ref, []):
            a = row.get("1830") or "(nothing)"
            b = row.get("1920") or "(deleted)"
            out.append(f"- *variant* 1830 `{a}` → 1920 `{b}`")
        if variants.get(ref):
            out.append("")
        for cand in sorted(kept.get(ref, []), key=score, reverse=True):
            s = cand.get("ngram_rarity_score")
            run = cand.get("ngram_max_run")
            head = f"**{cand['kjv_ref']}**"
            if s is not None:
                head += f" — rarity {s:.2f}, longest run {run}"
            else:
                head += f" — fuzzy {cand.get('fuzzy_ratio', 0):.2f}"
            out.append(f"- {head}")
            out.append(f"  > {cand['kjv_text']}")
            if cand.get("matched_ngrams"):
                grams = "; ".join(f"*{g}*" for g in cand["matched_ngrams"][:5])
                out.append(f"  shared: {grams}")
            if cand.get("shared_rare_words"):
                out.append(f"  rare words: {', '.join(cand['shared_rare_words'][:10])}")
        out.append("")

    print("\n".join(out))


if __name__ == "__main__":
    main()

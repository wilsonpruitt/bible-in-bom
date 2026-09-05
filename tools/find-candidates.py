#!/usr/bin/env python3.11
"""
Candidate generation, streams 1 and 2 of PLAN.md §4: exact/rare n-gram and
fuzzy/ordered-word matching between a Book of Mormon book (1830 text) and the
full KJV. Stream 3 (semantic/embedding) is not implemented yet — see the note
at the bottom of this file.

The machine finds candidates here; it does not decide what is a link. Every
row in the output is raw material for the adjudication pass (PLAN.md §5),
not a conclusion.

Usage: python3.11 tools/find-candidates.py 1-nephi "1 Nephi"
Output: work/<slug>/candidates.jsonl
"""
import difflib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

NGRAM_N = 4          # contiguous word run length for the exact/rare stream
RARE_WORD_TOP_N = 300  # word TYPES this frequent in the KJV are excluded from the fuzzy stream's prefilter
MIN_SHARED_RARE_WORDS = 2
MIN_FUZZY_RATIO = 0.28
# The Book of Mormon imitates KJV STYLE throughout, so raw 4-gram matches are
# dominated by formulaic phrases ("and it came to pass that," "thus saith the
# LORD") that repeat all over the KJV and carry no intertextual signal on
# their own. ngram_rarity_score sums 1/(KJV verses containing that 4-gram)
# over every matched window, so it rewards LONG runs and PENALIZES common
# ones; this cutoff is what separates "shares a formula" from "shares a
# passage." Chosen by inspecting the score distribution: at 0.25 the known
# Isaiah 48/49 quotation blocks score 20-34, and the bulk of formulaic noise
# (median raw score 0.005) is excluded. Every row below the cutoff is still
# kept in candidates-raw.jsonl — this is a display threshold, not a deletion.
NGRAM_RARITY_CUTOFF = 0.25
TOKEN_RE = re.compile(r"[a-z']+")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def build_ngrams(tokens: list[str], n: int) -> list[tuple]:
    return [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def main():
    if len(sys.argv) != 3:
        print("usage: find-candidates.py <slug> <Book Name>", file=sys.stderr)
        sys.exit(1)
    slug, book_name = sys.argv[1], sys.argv[2]

    kjv = json.load(open(ROOT / "text" / "kjv.json", encoding="utf-8"))
    bom_all = json.load(open(ROOT / "text" / "bom-1830.json", encoding="utf-8"))
    prefix = f"{book_name} "
    bom = {k[len(prefix):]: v for k, v in bom_all.items() if k.startswith(prefix)}
    if not bom:
        print(f"no verses found for {book_name!r}", file=sys.stderr)
        sys.exit(1)

    kjv_tokens = {ref: tokenize(text) for ref, text in kjv.items()}
    bom_tokens = {ref: tokenize(text) for ref, text in bom.items()}

    # --- word-type frequency across the whole KJV, for the fuzzy stream's stopword cut ---
    word_freq = Counter()
    for toks in kjv_tokens.values():
        word_freq.update(set(toks))  # document frequency: count verses containing the word, not raw occurrences
    common_words = {w for w, _ in word_freq.most_common(RARE_WORD_TOP_N)}

    # === Stream 1: exact / rare n-gram ===
    print(f"[stream 1] indexing {NGRAM_N}-grams across {len(kjv_tokens)} KJV verses...", file=sys.stderr)
    ngram_index: dict[tuple, list[str]] = defaultdict(list)
    for ref, toks in kjv_tokens.items():
        for ng in set(build_ngrams(toks, NGRAM_N)):
            ngram_index[ng].append(ref)

    ngram_hits: dict[tuple[str, str], dict] = {}
    for bref, btoks in bom_tokens.items():
        for ng in set(build_ngrams(btoks, NGRAM_N)):
            kjv_refs = ngram_index.get(ng)
            if not kjv_refs:
                continue
            rarity = 1.0 / len(kjv_refs)  # how many KJV verses contain this exact 4-gram
            for kref in kjv_refs:
                key = (bref, kref)
                entry = ngram_hits.setdefault(key, {"matched_ngrams": [], "max_run": 0, "rarity_score": 0.0})
                entry["matched_ngrams"].append(" ".join(ng))
                entry["rarity_score"] += rarity
                entry["max_run"] = max(entry["max_run"], NGRAM_N)
    print(f"[stream 1] {len(ngram_hits)} (BoM verse, KJV verse) pairs share a {NGRAM_N}-gram", file=sys.stderr)

    # Extend max_run by checking for longer contiguous overlap via difflib on the pairs we already found
    # (cheap: bounded to pairs that already share a 4-gram, so runs of 5+ get proper credit).
    for (bref, kref), entry in ngram_hits.items():
        sm = difflib.SequenceMatcher(None, bom_tokens[bref], kjv_tokens[kref])
        match = sm.find_longest_match(0, len(bom_tokens[bref]), 0, len(kjv_tokens[kref]))
        entry["max_run"] = max(entry["max_run"], match.size)

    # === Stream 2: fuzzy / ordered-word ===
    print("[stream 2] indexing rare words for the fuzzy prefilter...", file=sys.stderr)
    rare_word_index: dict[str, list[str]] = defaultdict(list)
    for ref, toks in kjv_tokens.items():
        for w in set(toks) - common_words:
            rare_word_index[w].append(ref)

    fuzzy_pool_counts: dict[tuple[str, str], int] = defaultdict(int)
    for bref, btoks in bom_tokens.items():
        rare_in_bref = set(btoks) - common_words
        seen_this_bref: dict[str, int] = defaultdict(int)
        for w in rare_in_bref:
            for kref in rare_word_index.get(w, ()):
                seen_this_bref[kref] += 1
        for kref, n_shared in seen_this_bref.items():
            if n_shared >= MIN_SHARED_RARE_WORDS:
                fuzzy_pool_counts[(bref, kref)] = n_shared
    print(f"[stream 2] {len(fuzzy_pool_counts)} pairs share >= {MIN_SHARED_RARE_WORDS} rare words; scoring...", file=sys.stderr)

    fuzzy_hits: dict[tuple[str, str], dict] = {}
    for (bref, kref), n_shared in fuzzy_pool_counts.items():
        ratio = difflib.SequenceMatcher(None, bom_tokens[bref], kjv_tokens[kref]).ratio()
        if ratio >= MIN_FUZZY_RATIO:
            shared_words = sorted((set(bom_tokens[bref]) - common_words) & (set(kjv_tokens[kref]) - common_words))
            fuzzy_hits[(bref, kref)] = {"fuzzy_ratio": round(ratio, 3), "shared_rare_words": shared_words}
    print(f"[stream 2] {len(fuzzy_hits)} pairs pass ratio >= {MIN_FUZZY_RATIO}", file=sys.stderr)

    # === Merge ===
    all_keys = set(ngram_hits) | set(fuzzy_hits)
    candidates = []
    for (bref, kref) in all_keys:
        streams = []
        row = {
            "bom_ref": f"{book_name} {bref}",
            "kjv_ref": kref,
            "bom_text": bom[bref],
            "kjv_text": kjv[kref],
        }
        if (bref, kref) in ngram_hits:
            streams.append("machine-ngram")
            n = ngram_hits[(bref, kref)]
            row["ngram_max_run"] = n["max_run"]
            row["ngram_rarity_score"] = round(n["rarity_score"], 3)
            row["matched_ngrams"] = sorted(set(n["matched_ngrams"]))[:5]
        if (bref, kref) in fuzzy_hits:
            streams.append("machine-fuzzy")
            row.update(fuzzy_hits[(bref, kref)])
        row["streams"] = streams
        candidates.append(row)

    # Rank: contiguous-run pairs first (strongest signal), then by rarity/fuzzy strength.
    candidates.sort(key=lambda r: (
        -r.get("ngram_max_run", 0),
        -r.get("ngram_rarity_score", 0),
        -r.get("fuzzy_ratio", 0),
    ))

    out_dir = ROOT / "work" / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_path = out_dir / "candidates-raw.jsonl"
    with open(raw_path, "w", encoding="utf-8") as f:
        for row in candidates:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    filtered = [
        r for r in candidates
        if r.get("ngram_rarity_score", 0) >= NGRAM_RARITY_CUTOFF or "machine-fuzzy" in r["streams"]
    ]
    out_path = out_dir / "candidates.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for row in filtered:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"\nwrote {raw_path}: {len(candidates)} raw candidate pairs "
          f"({len(ngram_hits)} n-gram, {len(fuzzy_hits)} fuzzy, "
          f"{len(set(ngram_hits) & set(fuzzy_hits))} both)")
    print(f"wrote {out_path}: {len(filtered)} pairs above the rarity cutoff — this is the review list")


if __name__ == "__main__":
    main()

# --- Stream 3 (semantic/embedding) — NOT YET IMPLEMENTED ---
# PLAN.md §4 calls for a third stream using sentence embeddings to surface
# conceptual/figural parallels with no shared wording (the kind streams 1-2
# structurally cannot find). Needs a local embedding model (fits comfortably
# in 8GB RAM as a batch job, not a long-running service) or an API call for
# ~618 short strings. Left for a follow-up pass rather than rushed here.

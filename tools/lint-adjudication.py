#!/usr/bin/env python3.11
"""
Check an adjudication against the things a machine can check.

`apply-adjudication.py --check` enforces the SCHEMA. This enforces the parts
of CONVENTIONS.md that are mechanically decidable, which matters much more once
chapters are being written by agents rather than in one sitting. The failure
modes it is built against are real ones:

  * The colleague's 1 Nephi pilot was discredited by 23 invented attributions
    (work/1-nephi/PROVENANCE-colleague-pilot.md). CONVENTIONS §6's hard limit
    is the most important rule in the project and the easiest to break at scale.
  * A hallucinated verse reference is invisible to a reader and fatal to a
    catalogue that calls itself definitive.
  * "Occurs in exactly one KJV verse" is the sentence most of the strongest
    links rest on, and it is trivially checkable — so it should never be wrong.

Exit code is non-zero if any ERROR is found. WARNs are advisory.

Usage:
  python3.11 tools/lint-adjudication.py 1-nephi
  python3.11 tools/lint-adjudication.py 1-nephi --chapter 17
"""
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Sources we actually hold. A bibliography entry that does not begin with one of
# these is either a citation to something nobody can check or an invention.
KNOWN_SOURCES = ("Hardy MSI", "Hardy 2023", "Frederick 2016", "Hays 1989",
                 "Hays 2016", "Skousen", "Spencer", "Barlow", "Wayment")

# Verbs that assert a named person made a claim. Legitimate, but they are the
# exact shape of the colleague's failure, so every one gets looked at.
ATTRIBUTION = re.compile(
    r"\b(Hardy|Frederick|Hays|Skousen|Spencer|Barlow|Wayment|Nibley|Givens)\b"
    r"[^.]{0,60}?\b(identifies|argues|pairs|proposes|shows|claims|derives|finds|says|notes|calls)\b",
    re.I)

# Only claims whose phrase is actually QUOTED are checked. The first version of
# this regex accepted bare prose and reported ten false errors — "the pairing of
# blinded eyes with a hardened heart occurs in exactly one KJV verse" is a true
# sentence about a collocation, not a claim that that string appears. Phrases
# containing a placeholder or an ellipsis describe a construction and are skipped
# for the same reason.
RARITY = re.compile(
    r"[“‘]([^“”‘’]{3,70})[”’]\s+occurs in exactly (one|two|three|four|five|\d+) KJV verses?",
    re.I)
SKIP_PHRASE = re.compile(r"[<>…]|\.\.\.")
NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
WORD = re.compile(r"[A-Za-z’']+")


def norm(s): return s.replace("’", "'").replace("‘", "'")
def wordset(s): return [w.lower() for w in WORD.findall(norm(s))]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--chapter", type=int)
    args = ap.parse_args()

    kjv = json.loads((ROOT / "text" / "kjv.json").read_text())
    kjv_norm = {r: norm(t) for r, t in kjv.items()}
    bom = json.loads((ROOT / "text" / "bom-1830.json").read_text())
    book = json.loads((ROOT / "data" / f"{args.slug}.json").read_text())
    name = book["name"]

    # Lint the CHAPTER FILES, not the merged book. data/<slug>.json is only as
    # fresh as the last apply, and during a dispatched run it is whatever some
    # other agent last merged — so linting it can pass a chapter whose file has
    # since changed, or fail one on another chapter's rows. The work files are
    # what the pass is actually producing. (Falls back to the merged book for a
    # book with no chapter files, e.g. one imported whole.)
    work = ROOT / "work" / args.slug / "adjudicated"
    if any(work.glob("ch*.json")):
        by_ref = {p["ref"]: p for p in book["pericopes"]}
        pericopes = []
        for path in sorted(work.glob("ch*.json")):
            for ref, links in json.loads(path.read_text())["links"].items():
                base = by_ref.get(ref, {"ref": ref, "ch": int(ref.split(":")[0])})
                pericopes.append({**base, "links": links})
        book = {**book, "pericopes": pericopes}

    errors, warns = [], []

    def err(where, msg): errors.append(f"{where}: {msg}")
    def warn(where, msg): warns.append(f"{where}: {msg}")

    for per in book["pericopes"]:
        if args.chapter and per["ch"] != args.chapter:
            continue
        for l in per["links"]:
            where = f"{name} {per['ref']} → {l.get('source', '?')}"

            # 1. Every reference must resolve. A hallucinated ref is fatal.
            for field in ("source",):
                if l.get(field) not in kjv:
                    err(where, f"{field} {l.get(field)!r} is not a KJV verse")
            for field in ("composite", "altSource"):
                vals = l.get(field) or []
                if isinstance(vals, str): vals = [vals]
                for v in vals:
                    base = v.split("-")[0].strip()
                    if base not in kjv:
                        err(where, f"{field} {v!r} is not a KJV verse")
            for v in l.get("recurrenceRefs") or []:
                base = v.split("-")[0].strip()
                chapter_ref = re.fullmatch(r"(.+?) \d+", base)
                known_chapter = chapter_ref and any(
                    k.startswith(chapter_ref.group(0) + ":") for k in list(bom) + list(kjv))
                if base not in bom and base not in kjv and not known_chapter:
                    err(where, f"recurrenceRefs {v!r} resolves to neither corpus")

            # 2. The quoted `text` must be the KJV text of `source`.
            if l.get("source") in kjv:
                if norm(l.get("text", "")).strip() != kjv_norm[l["source"]].strip():
                    err(where, "`text` does not match the KJV text of `source` — "
                               "misquotation or wrong verse")

            # 3. Rarity claims must be true.
            blob = " ".join([l.get("note", ""),
                             json.dumps(l.get("provenance") or {}, ensure_ascii=False)])
            for phrase, count in RARITY.findall(blob):
                if SKIP_PHRASE.search(phrase):
                    continue
                claimed = NUM.get(count.lower(), None)
                if claimed is None:
                    try: claimed = int(count)
                    except ValueError: continue
                pat = r"\s+".join(re.escape(w) for w in norm(phrase).split())
                try:
                    rx = re.compile(pat, re.I)
                except re.error:
                    continue
                actual = sum(1 for t in kjv_norm.values() if rx.search(t))
                if actual != claimed:
                    err(where, f"claims “{phrase}” occurs in exactly {claimed} KJV verse(s); "
                               f"it occurs in {actual}")

            # 4. CONVENTIONS §6: attributions get looked at, and citations must
            #    be to something we hold.
            for b in l.get("bibliography") or []:
                if not any(b.startswith(k) for k in KNOWN_SOURCES):
                    err(where, f"bibliography entry cites a source not on the known list: {b[:70]!r}")
            for field in ("note", "whyNot"):
                m = ATTRIBUTION.search(l.get(field) or "")
                if m:
                    warn(where, f"`{field}` attributes a claim to {m.group(1)} "
                                f"(“…{m.group(0)[:60]}…”) — CONVENTIONS §6: verify they say it")

            # 5. Advisory quality checks. A verse inside a transcribed block
            #    (1 Nephi 20-21) is a whole-verse quotation whose note is written
            #    by build-isaiah-adjudication.py; rarity counts and note length
            #    do not apply to it.
            transcribed = l.get("subtype") == "extended" and l.get("variants") is not None
            if (not transcribed and l.get("kjvSpecific") == "yes"
                    and "occurs in exactly" not in blob):
                warn(where, "kjvSpecific 'yes' with no rarity count (CONVENTIONS §4: "
                            "encouraged, not required — but run tools/kjv-rarity.py)")
            if (not transcribed and l.get("confidence") in ("certain", "high")
                    and len(l.get("note", "")) < 120):
                warn(where, f"confidence '{l['confidence']}' with a very short note — "
                            "the argument is the product (CONVENTIONS §0a)")
            if l.get("status") == "novel" and l.get("bibliography"):
                warn(where, "status 'novel' but a bibliography is present — is it still novel?")

    n = sum(1 for p in book["pericopes"] for _ in p["links"]
            if not args.chapter or p["ch"] == args.chapter)
    scope = f"chapter {args.chapter}" if args.chapter else "the whole book"
    print(f"lint {name} ({scope}): {n} link(s) checked")
    for w in warns: print(f"  WARN  {w}")
    for e in errors: print(f"  ERROR {e}")
    print(f"\n{len(errors)} error(s), {len(warns)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

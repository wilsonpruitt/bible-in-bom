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


def doc_freq(kjv) -> dict:
    """Verses containing each word type — the measure that decides a single-word test."""
    from collections import Counter
    df = Counter()
    for t in kjv.values():
        for w in {norm(x) for x in words(t)}:
            df[w] += 1
    return df


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
    df = doc_freq(kjv)
    # An INSERTION (one candidate has a word, the other has nothing) is much weaker
    # evidence than a REPLACE, because the word may be in the Book of Mormon verse
    # for its own reasons. The Jarom 1:3 pass reported "should" as decisive between
    # Isaiah 6:10 and Acts 28:27 on exactly that footing. So a lone inserted word
    # only counts if it is genuinely rare. 150 keeps every word the pilot's real
    # findings turned on (kindreds 8, vapour 4, smooth 6, ruler 82, worship 102)
    # and rejects should (690) and will (2855).
    RARE_ENOUGH = 150
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
        an_full, bn_full = [norm(w) for w in a], [norm(w) for w in b]
        sm = difflib.SequenceMatcher(a=an_full, b=bn_full)
        ops = sm.get_opcodes()
        # How much of the two candidates' OWN wording, apart from the
        # divergence itself, is actually shared? Two verses that were never a
        # real parallel to begin with — Alma 56:46's spurious pairing of
        # Isaiah 8:10 with Matthew 1:23, Alma 49:2's of two unrelated "borders
        # of the city" verses — can still throw a confident-looking DECISIVE
        # when they happen to collide on one word the Book of Mormon also
        # has. But a genuine two-witness quotation can ALSO show a thin
        # backbone (Isaiah 40:3/Luke 3:5 reorders too much to leave one), so
        # this number cannot be a threshold that suppresses a verdict — it is
        # only ever more evidence, reported so the adjudicator weighs it
        # alongside everything else they know, same as the tool already does
        # for every other kind of divergence. Found on the Alma 56/62 batch
        # (2026-09-07): both false decisives had a backbone of 0-1 words,
        # against 3-7 for the pilot's confirmed OT-via-NT findings.
        shared_content = [w for tag, i1, i2, j1, j2 in ops if tag == "equal" for w in an_full[i1:i2] if w not in stop]
        print(f"\n--- {base}  vs  {other} ---")
        any_op = False
        for tag, i1, i2, j1, j2 in ops:
            if tag == "equal":
                continue
            any_op = True
            av, bv = " ".join(a[i1:i2]) or "(nothing)", " ".join(b[j1:j2]) or "(nothing)"
            an = " ".join(norm(w) for w in a[i1:i2])
            bn = " ".join(norm(w) for w in b[j1:j2])
            # An INSERTION and a REPLACE are different strengths of evidence and
            # need different bars.
            #
            #   replace  — both candidates word the same slot, differently, and the
            #              Book of Mormon picked one. The alternative was on offer
            #              and was not taken, so even a moderately common word
            #              decides: "might" (439 verses) against "strength" (232)
            #              at Words of Mormon 1:18 is a real finding.
            #   insert   — one candidate has a word, the other has nothing. The word
            #              may be in the Book of Mormon verse for its own reasons,
            #              so it only counts if it is rare. "should" (690 verses)
            #              produced a false decisive between Isaiah 6:10 and Acts
            #              28:27 on the Jarom pass; this is the guard against it.
            is_insertion = not an or not bn
            other_full = set(map(norm, words(kjv[other])))
            base_full = set(map(norm, words(kjv[base])))

            def content(span: str) -> list[str]:
                return [t for t in span.split() if t not in stop]

            def distinguishes(span: str, other_side_full: set[str]) -> bool:
                """At least one of the span's content words is present in the
                BoM verse AND does not also occur in the OTHER candidate's own
                verse — i.e. the BoM's presence of that word genuinely favours
                this side, rather than being shared vocabulary difflib happened
                to align here.

                Two bugs, both from the Mosiah 1-3 pass, made that necessary:

                'scourge' is a word both Mark 10:34 and Matthew 20:19 actually
                contain, but difflib aligned it into one opcode only, so the
                old code credited it to whichever candidate happened to hold
                it. The `other_side_full` check catches that: a word shared by
                both candidates' full verses is never distinguishing, no
                matter which opcode it landed in.

                At Mosiah 2:11, 'might' is correctly Deuteronomy 6:5's, but the
                span on Mark 12:30's side was 'mind, and with all thy strength
                this is the first commandment' — Mark's own trailing sentence
                as well as the divergence. Requiring EVERY word in that span to
                match the BoM (the original check) failed on 'first' and
                'commandment', hiding the fact that 'mind' and 'strength' are
                independently in the BoM verse too — Mosiah 2:11 conflates both
                sources. Requiring only ONE distinguishing word, not all of
                them, is what makes a real conflation like this visible instead
                of reporting a false single-sided DECISIVE.

                A pure insertion still needs a RARE distinguishing word, same
                as before — this only changes ALL-vs-ANY, not the rarity bar."""
                toks = content(span)
                candidates = [t for t in toks if t in bom_norm and t not in other_side_full]
                if not candidates:
                    return False
                if is_insertion:
                    return any(df.get(t, 0) <= RARE_ENOUGH for t in candidates)
                return True

            in_a = bool(an) and distinguishes(an, other_full)
            in_b = bool(bn) and distinguishes(bn, base_full)
            # A single differing word is the cleanest kind of test — but only if
            # the word is distinctive enough that its presence means something,
            # and it must not ALSO occur in the other candidate's own verse
            # (see `distinguishes` above for why that check exists).
            if not in_a and not in_b and (i2 - i1) <= 1 and (j2 - j1) <= 1:
                insertion = not an or not bn
                for span, present, other_side_full in ((an, "a", other_full), (bn, "b", base_full)):
                    if not span or span in stop:
                        continue
                    if insertion and df.get(span, 0) > RARE_ENOUGH:
                        continue          # a common word inserted proves nothing
                    if span in other_side_full:
                        continue          # shared vocabulary difflib misaligned, not a divergence
                    if span in bom_norm:
                        if present == "a": in_a = True
                        else: in_b = True
            # An OMISSION is evidence too, and the first version of this tool
            # could not see it. Where one candidate has words the other lacks and
            # the Book of Mormon ALSO lacks them, that favours the candidate that
            # omits — provided the Book of Mormon is demonstrably tracking this
            # stretch of the verse, which we test by requiring the words on both
            # sides of the gap to be present. Found on the Jacob 1:7 pass: Psalm
            # 95:8 reads "as in the provocation, AND AS IN the day of temptation",
            # Hebrews 3:8 drops "and as", and Jacob drops it too.
            if not in_a and not in_b and is_insertion:
                span, side = (an, "a") if an else (bn, "b")
                # Rarity is the wrong bar here. "and as" is two stopwords, and
                # dropping them is still a real difference between two renderings
                # of one sentence. What protects against noise is not the span's
                # rarity but the FLANKING test below: the Book of Mormon must be
                # reproducing the words on either side of the gap, so the omission
                # is demonstrably at this point and not just a short verse missing
                # common words.
                if span and span not in bom_flat:
                    src_words = [norm(w) for w in (a if side == "a" else b)]
                    lo = i1 if side == "a" else j1
                    hi = i2 if side == "a" else j2
                    before = src_words[lo - 1] if lo > 0 else None
                    after = src_words[hi] if hi < len(src_words) else None
                    present = [w for w in (before, after) if w is not None]
                    flanked = (bool(present)
                               and all(w in bom_norm for w in present)
                               # at least one flank must be a content word, or the
                               # "match" is just function words either side of a gap
                               and any(w not in stop for w in present))
                    if flanked:
                        # The side WITHOUT the span is the one the BoM agrees with.
                        if side == "a": in_b = True
                        else: in_a = True

            words_seen = ", ".join(dict.fromkeys(shared_content)) or "none"
            backbone = f"  ◀── DECISIVE (backbone: {len(shared_content)} other shared word(s) — {words_seen})"
            if in_a and not in_b:
                verdict, mark = f"BoM has {base}'s form", backbone
                decisive.append((base, av, other, bv))
            elif in_b and not in_a:
                verdict, mark = f"BoM has {other}'s form", backbone
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

#!/usr/bin/env python3.11
"""
Extract the biblical cross-reference apparatus from Grant Hardy's Maxwell
Institute Study Edition of the Book of Mormon — the scholarship stream named
in PLAN.md §4.4, which had never been run (see CONVENTIONS.md §6).

Input:  text/hardy-msi-raw.txt — plain text via `pdftotext -layout`, GITIGNORED.
        The MSI is a purchased, copyrighted book; its prose and footnote
        commentary must never enter version control. What this script keeps
        is bare Bible citations attached to Book of Mormon verses — a fact
        index, the same kind of thing as a concordance, not the author's
        expression. Do not extend this script to copy footnote SENTENCES into
        tracked output.

Output: data/hardy-refs.json  { "1 Nephi 10:8": ["Isaiah 40:3", "Matthew 3:3", ...], ... }
        A second file, data/hardy-recurrence.json, holds the internal Book of
        Mormon cross-references from the same footnotes (Hays's "recurrence"
        criterion, CONVENTIONS.md §3a) — e.g. 1 Nephi 1:8's footnote that the
        same 21 words recur at Alma 36:22.

Method: the MSI's running header/footer on every page states the exact modern
chapter:verse at that page boundary ("1 Ne 1.4 [ First Nephi I ] 6"). Those
lines are used as checkpoints for a verse walker over the body text; footnotes
between two checkpoints are assigned to the chapter that walker has reached,
with a monotonicity check (a footnote verse number lower than the previous
one on the same page signals a chapter turned over mid-page). Every assigned
verse is cross-checked by word-overlap against text/bom-1830.json — a citation
attached to a verse whose reconstructed text does not match the real verse is
dropped and logged rather than silently kept.

Usage: python3.11 tools/parse-hardy.py [--book "1 Nephi" --heading "First Nephi"]
       Repeat for other books once the pattern is confirmed elsewhere.
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "text" / "hardy-msi-raw.txt"

BOOK_ABBREV = {
    "Gen": "Genesis", "Ex": "Exodus", "Exod": "Exodus", "Lev": "Leviticus",
    "Num": "Numbers", "Deut": "Deuteronomy", "Josh": "Joshua", "Judg": "Judges",
    "Ruth": "Ruth", "1 Sam": "1 Samuel", "2 Sam": "2 Samuel",
    "1 Kgs": "1 Kings", "2 Kgs": "2 Kings", "1 Kings": "1 Kings", "2 Kings": "2 Kings",
    "1 Chr": "1 Chronicles", "2 Chr": "2 Chronicles", "Ezra": "Ezra", "Neh": "Nehemiah",
    "Esth": "Esther", "Job": "Job", "Ps": "Psalm", "Pss": "Psalm", "Prov": "Proverbs",
    "Eccl": "Ecclesiastes", "Song": "Song of Solomon", "Isa": "Isaiah", "Jer": "Jeremiah",
    "Lam": "Lamentations", "Ezek": "Ezekiel", "Dan": "Daniel", "Hos": "Hosea",
    "Joel": "Joel", "Amos": "Amos", "Obad": "Obadiah", "Jonah": "Jonah", "Mic": "Micah",
    "Nah": "Nahum", "Hab": "Habakkuk", "Zeph": "Zephaniah", "Hag": "Haggai",
    "Zech": "Zechariah", "Mal": "Malachi",
    "Mt": "Matthew", "Matt": "Matthew", "Mk": "Mark", "Mark": "Mark", "Lk": "Luke",
    "Luke": "Luke", "Jn": "John", "John": "John", "Acts": "Acts", "Rom": "Romans",
    "1 Cor": "1 Corinthians", "2 Cor": "2 Corinthians", "Gal": "Galatians",
    "Eph": "Ephesians", "Phil": "Philippians", "Col": "Colossians",
    "1 Thess": "1 Thessalonians", "2 Thess": "2 Thessalonians",
    "1 Tim": "1 Timothy", "2 Tim": "2 Timothy", "Titus": "Titus",
    "Phlm": "Philemon", "Philem": "Philemon", "Heb": "Hebrews",
    "Jas": "James", "James": "James", "1 Pet": "1 Peter", "2 Pet": "2 Peter",
    "1 Jn": "1 John", "2 Jn": "2 John", "3 Jn": "3 John", "Jude": "Jude", "Rev": "Revelation",
}
# Longest-first so "1 Cor" matches before "Cor" would (it never would, but keep the discipline).
_ABBR_ALT = "|".join(sorted((re.escape(a) for a in BOOK_ABBREV), key=len, reverse=True))
CITATION_RE = re.compile(
    rf"\b({_ABBR_ALT})\.?\s+(\d{{1,3}})\.(\d{{1,3}})(?:[-–,]\s*(\d{{1,3}}))?"
)

BOM_ABBREV = {
    "1 Ne": "1 Nephi", "2 Ne": "2 Nephi", "Jacob": "Jacob", "Enos": "Enos",
    "Jarom": "Jarom", "Omni": "Omni", "W of M": "Words of Mormon", "Mosiah": "Mosiah",
    "Alma": "Alma", "Hel": "Helaman", "3 Ne": "3 Nephi", "4 Ne": "4 Nephi",
    "Morm": "Mormon", "Ether": "Ether", "Moro": "Moroni",
}
_BOM_ALT = "|".join(sorted((re.escape(a) for a in BOM_ABBREV), key=len, reverse=True))
BOM_CITATION_RE = re.compile(
    rf"\b({_BOM_ALT})\.?\s+(\d{{1,3}})[:.](\d{{1,3}})(?:[-–,]\s*(\d{{1,3}}))?"
)

REF_IN_HEADER_RE = re.compile(r"(\d?\s?[A-Za-z][a-z]*)\s+(\d{1,3})\.(\d{1,3})")

# A footnote marker: a single lowercase letter, a verse number, then its text.
# Entries are separated either by a run of 2+ spaces (the column gap in
# -layout output, when several fit on one physical line) or by a newline —
# both occur, so neither can be required beyond "some whitespace." What must
# be excluded is the inline superscript reference letter glued directly onto
# the end of the PRECEDING word with no space at all, e.g. "plates.a 3
# Nevertheless" — there the "a" is a superscript mark on "plates", and "3" is
# simply the next verse starting immediately after; requiring a period as an
# acceptable lookbehind (an earlier version of this regex did) collides the
# two. The letter must be preceded by real whitespace or start-of-string.
FOOTNOTE_MARKER_RE = re.compile(r'(?:^|\s)([a-z]) (\d{1,3}) (?=[A-Z0-9"“=])', re.MULTILINE)


def load_bom_text(book_name: str) -> dict[str, str]:
    all_verses = json.loads((ROOT / "text" / "bom-1830.json").read_text())
    return {k: v for k, v in all_verses.items() if k.startswith(book_name + " ")}


def word_overlap(a: str, b: str) -> float:
    wa = set(re.findall(r"[a-z']+", a.lower()))
    wb = set(re.findall(r"[a-z']+", b.lower()))
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / min(len(wa), len(wb))


def extract_section(text: str, heading: str, next_headings: list[str]) -> str:
    # Match the heading only as its own line, so a substring occurring inside a
    # longer book title elsewhere (e.g. in front-matter listings) is not hit.
    m = re.search(rf"^{re.escape(heading)}\s*$", text, re.MULTILINE)
    if not m:
        sys.exit(f"heading {heading!r} not found as its own line")
    start = m.start()
    end = len(text)
    for nh in next_headings:
        m2 = re.search(rf"^{re.escape(nh)}\s*$", text[start + 1:], re.MULTILINE)
        if m2:
            end = min(end, start + 1 + m2.start())
    return text[start:end]


Anchor = tuple[int, int, bool]   # (chapter, verse, ref_is_the_page's_FIRST_verse)


def strip_headers_track_chapter(section: str, section_label: str) -> list[tuple[Anchor | None, str]]:
    """
    Split the section into one (anchor, page-body) piece per printed page.

    The running head sits at the top of each page in `pdftotext -layout` output,
    and it is a dictionary-style guide ref, not a start-of-page ref: on a verso
    (ref printed to the LEFT of the bracket, page number to the right) it names
    the FIRST verse of that page; on a recto (page number left, ref right) it
    names the LAST. Verified on 2 Nephi page 87 — head "2 Ne 12.20", body 12.10-20
    — and its facing page 88, head "2 Ne 12.21", body starting at 12.21.

    So every page carries a hard checkpoint at one end or the other. That is what
    keeps the verse walker from drifting: without it a single missed chapter
    transition silently mis-keys every footnote until the next resync (2 Nephi:
    55 of 120 rows, whole chapters off by one, before this was understood).
    """
    pieces: list[tuple[Anchor | None, str]] = []
    pos = 0
    pending: Anchor | None = None
    for m in re.finditer(re.escape(f"[ {section_label}"), section):
        line_start = section.rfind("\n", 0, m.start()) + 1
        line_end = section.find("\n", m.end())
        if line_end == -1:
            line_end = len(section)
        line = section[line_start:line_end]
        pieces.append((pending, section[pos:line_start]))
        pos = line_end
        ref_m = REF_IN_HEADER_RE.search(line)
        pending = None
        if ref_m:
            ref_is_first = ref_m.start() < line.index("[")
            pending = (int(ref_m.group(2)), int(ref_m.group(3)), ref_is_first)
    pieces.append((pending, section[pos:]))
    return pieces


# The Book of Mormon's prose always spells numbers as words ("six hundred
# years", "forty days"), so any bare digit run in a non-footnote paragraph is
# almost certainly a verse marker — verse-initial words are not reliably
# capitalized (many verses begin mid-sentence after a semicolon: "12 and also
# a record..."), so capitalization cannot be required. The walker's own
# continuity check (n == verse+1, or the chapter-boundary rule) is what
# actually filters candidates; this regex only needs to not miss real ones.
VERSE_START_RE = re.compile(r'(?<![\d.])(\d{1,3})(?![\d.])')


def chapter_verse_counts(bom_text: dict[str, str]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for ref in bom_text:
        ch, v = ref.split(":")[0].rsplit(" ", 1)[1], ref.split(":")[1]
        counts[int(ch)] = max(counts.get(int(ch), 0), int(v))
    return counts


def walk_verses_and_footnotes(
    pieces: list[tuple[Anchor | None, str]], bom_text: dict[str, str], book_name: str
) -> tuple[dict[str, list[str]], dict[str, list[str]], list[str]]:
    bible_refs: defaultdict[str, list[str]] = defaultdict(list)
    bom_refs: defaultdict[str, list[str]] = defaultdict(list)
    warnings: list[str] = []
    max_verse = chapter_verse_counts(bom_text)

    # Key finding (2026-09-05): this edition does NOT print a literal "1" for
    # a chapter's first verse — the chapter's own number stands in for it
    # (confirmed: 1 Nephi 2:1 is typeset as a bare "2", not "1"). So a chapter
    # transition is recognized by the marker equalling chapter+1 while the
    # current chapter has already reached (or nearly reached) its known verse
    # count from bom_text — never by the marker being literally 1.
    chapter = 1
    verse = 0

    for anchor, chunk in pieces:
        # A verso head names the page's first verse: take it as a hard reset, so
        # a chapter transition the walker missed on an earlier page cannot travel
        # further than the spread it happened on.
        if anchor is not None and anchor[2]:
            chapter, verse = anchor[0], anchor[1] - 1

        # Two passes over the page. The body pass records every (chapter, verse)
        # printed on this page; the footnote pass then keys each note by what the
        # page actually shows, because a page-bottom note belongs to a verse ON
        # THAT PAGE — which is a fact about the page, not about where the walker
        # happens to have got to by the time the notes are read.
        paras = re.split(r"\n\s*\n", chunk)
        footnote_paras: list[list[re.Match]] = []
        page_seen: list[tuple[int, int]] = []
        for para in paras:
            matches = list(FOOTNOTE_MARKER_RE.finditer(para))
            marker_hits = len(matches)
            looks_like_footnotes = marker_hits >= 2 or (
                marker_hits == 1 and len(para.strip()) < 400
            )
            if looks_like_footnotes and marker_hits:
                footnote_paras.append(matches)
            else:
                for vm in VERSE_START_RE.finditer(para):
                    n = int(vm.group(1))
                    at_chapter_end = verse >= max_verse.get(chapter, 10**9) - 1
                    if n == verse + 1 and n <= max_verse.get(chapter, 10**9):
                        verse = n
                    elif at_chapter_end and n == chapter + 1 and (chapter + 1) in max_verse:
                        chapter = n
                        verse = 1
                    else:
                        continue  # not a verse marker (e.g. a footnote digit, a year)
                    page_seen.append((chapter, verse))

        last_fn: tuple[int, int] | None = None
        for matches in footnote_paras:
            para = matches[0].string
            for i, mm in enumerate(matches):
                fn_verse = int(mm.group(2))
                text_start = mm.end()
                text_end = matches[i + 1].start() if i + 1 < len(matches) else len(para)
                fn_text = para[text_start:text_end]
                # Which chapter does this verse number belong to? Ask the page.
                # A page-bottom note belongs to a verse the page shows, so the
                # candidates are bounded above by the last verse printed here —
                # which is what settles the two cases the verse number alone
                # cannot. (a) The note's verse is not on the page at all,
                # because its text ran over from the page before: 2 Nephi 5's
                # note "34" is 4:34, not 5:34, because the page stops at 5:10.
                # (b) The page straddles a chapter break and BOTH chapters have
                # that verse number: a page running 13:24-15:2 has a note "1"
                # for 15:1, not 14:1, and the later one is right because a note
                # sits with the verse the page ended on, not the one it passed.
                # Where the page shows nothing at all, fall back to the walker.
                if page_seen:
                    first, end = page_seen[0], page_seen[-1]
                    # The running head outranks the walk where they disagree:
                    # it is printed, and the walk can stall inside a page (a
                    # 1 Nephi 22 page whose walk stopped at 22:12 sent its notes
                    # for 22:15 and 22:17 back into chapter 21 before this).
                    if anchor is not None:
                        head = (anchor[0], anchor[1])
                        first, end = (min(first, head), end) if anchor[2] else (first, max(end, head))
                    cands = [
                        (c, fn_verse)
                        for c in range(max(first[0] - 1, 1), end[0] + 1)
                        if fn_verse <= max_verse.get(c, 0)
                    ]
                    cands = [x for x in cands if x <= end]
                    if last_fn is not None:
                        cands = [x for x in cands if x >= last_fn] or cands
                    fn_chapter = max(cands)[0] if cands else chapter
                else:
                    fn_chapter = chapter
                    if fn_verse > max_verse.get(chapter, 10**9) and fn_verse <= max_verse.get(chapter - 1, -1):
                        fn_chapter = chapter - 1
                last_fn = (fn_chapter, fn_verse)
                ref = f"{book_name} {fn_chapter}:{fn_verse}"
                for cm in CITATION_RE.finditer(fn_text):
                    abbr, c, v, v2 = cm.groups()
                    full = BOOK_ABBREV[abbr]
                    cite = f"{full} {c}:{v}" + (f"-{v2}" if v2 else "")
                    bible_refs[ref].append(cite)
                for cm in BOM_CITATION_RE.finditer(fn_text):
                    abbr, c, v, v2 = cm.groups()
                    full = BOM_ABBREV[abbr]
                    cite = f"{full} {c}:{v}" + (f"-{v2}" if v2 else "")
                    if cite != ref:  # skip self-reference (the verse citing itself)
                        bom_refs[ref].append(cite)

        # A recto head names the page's LAST verse: an end-of-page check. A
        # mismatch means the walk over this page is wrong, so say so rather than
        # resyncing in silence.
        if anchor is not None and not anchor[2]:
            if (chapter, verse) != (anchor[0], anchor[1]):
                warnings.append(
                    f"page ends at {book_name} {chapter}:{verse}, running head says "
                    f"{anchor[0]}:{anchor[1]}"
                )
                chapter, verse = anchor[0], anchor[1]

    return dict(bible_refs), dict(bom_refs), warnings


def apply_corrections(refs: dict) -> tuple[dict, int]:
    """
    Move rows the verse-walker mis-attributed.

    The walker checkpoints against page headers and can land a footnote one
    chapter early when a chapter turns over mid-page. Corrections live in
    data/hardy-corrections.json with their evidence, so a re-parse does not
    silently undo a checked fix.
    """
    path = ROOT / "data" / "hardy-corrections.json"
    if not path.exists():
        return refs, 0
    moved = 0
    # A citation can also be wrong in the source rather than in the walk: the
    # note at 2 Nephi 17:17 cites "Isa 17.7" while quoting Isaiah 7:17's own
    # words. Those are repaired by `cite_fixes`, with the evidence, rather than
    # left for an adjudicator to chase.
    for f in json.loads(path.read_text()).get("cite_fixes", []):
        cites = refs.get(f["ref"])
        if cites and f["from"] in cites:
            cites[cites.index(f["from"])] = f["to"]
            moved += 1
    for m in json.loads(path.read_text()).get("moves", []):
        src, dst = m["from"], m["to"]
        if src not in refs:
            continue
        keep = [r for r in refs[src] if r not in m["refs"]]
        take = [r for r in refs[src] if r in m["refs"]]
        if not take:
            continue
        refs[dst] = refs.get(dst, []) + [r for r in take if r not in refs.get(dst, [])]
        if keep:
            refs[src] = keep
        else:
            del refs[src]
        moved += len(take)
    return refs, moved


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", default="1 Nephi", help="Book of Mormon book name, our convention")
    ap.add_argument("--heading", default="The First Book of Nephi",
                     help="MSI section heading, matched as a whole line")
    ap.add_argument("--section-label", default="First Nephi",
                     help="the bracketed running-header label, e.g. 'First Nephi'")
    ap.add_argument("--next-heading", default="The Second Book of Nephi")
    args = ap.parse_args()

    if not RAW.exists():
        sys.exit(f"{RAW} not found — see the docstring: this file is gitignored and must be "
                  f"regenerated locally with `pdftotext -layout <MSI pdf> {RAW}`.")

    full = RAW.read_text().replace("\x0c", "")
    section = extract_section(full, args.heading, [args.next_heading])
    pieces = strip_headers_track_chapter(section, args.section_label)
    bom_text = load_bom_text(args.book)

    bible_refs, bom_refs, warnings = walk_verses_and_footnotes(pieces, bom_text, args.book)
    bible_refs, moved = apply_corrections(bible_refs)
    if moved:
        print(f"applied {moved} correction(s) from data/hardy-corrections.json")

    def validate_and_write(raw: dict[str, list[str]], filename: str, label: str) -> tuple[int, int, list[str]]:
        clean: dict[str, list[str]] = {}
        dropped = []
        for ref, cites in raw.items():
            if ref not in bom_text:
                dropped.append(ref)
                continue
            seen = []
            for c in cites:
                if c not in seen:
                    seen.append(c)
            if seen:
                clean[ref] = seen
        out_path = ROOT / "data" / filename
        existing = json.loads(out_path.read_text()) if out_path.exists() else {}
        # Drop this book's rows before merging, so a re-parse REPLACES them. A
        # plain update leaves the previous run's mis-keyed rows behind as ghosts
        # — which is how a fixed walker can still ship a broken apparatus.
        existing = {k: v for k, v in existing.items() if not k.startswith(args.book + " ")}
        existing.update(clean)
        existing = dict(sorted(existing.items(), key=lambda kv: (kv[0].split()[-1],)))
        out_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n")
        print(f"{args.book}: {len(clean)} verses with {label}, "
              f"{sum(len(v) for v in clean.values())} total")
        print(f"wrote {out_path.relative_to(ROOT)}")
        return len(clean), sum(len(v) for v in clean.values()), dropped

    verses, cites, dropped = validate_and_write(bible_refs, "hardy-refs.json", "Bible citations")
    validate_and_write(bom_refs, "hardy-recurrence.json", "internal Book of Mormon cross-refs")

    # Record that this book HAS been parsed. Jarom and the Words of Mormon
    # genuinely carry no Bible citations, so an empty result is not by itself a
    # sign that the apparatus is missing — without this file, a book nobody has
    # parsed yet reports "0 Hardy rows to account for" and reads as done.
    log_path = ROOT / "data" / "hardy-parsed.json"
    log = json.loads(log_path.read_text()) if log_path.exists() else {}
    log[args.book] = {
        "heading": args.heading, "sectionLabel": args.section_label,
        "verses": verses, "citations": cites, "warnings": len(warnings),
    }
    log_path.write_text(json.dumps(dict(sorted(log.items())), indent=2, ensure_ascii=False) + "\n")

    if dropped:
        print(f"  dropped {len(dropped)} refs not found in bom-1830.json: {dropped[:10]}")
    for w in warnings:
        print(f"  WARNING: {w}")


if __name__ == "__main__":
    main()

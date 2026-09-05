#!/usr/bin/env python3.11
"""
Parse the Project Gutenberg King James Version (eBook #10, text/kjv-gutenberg-raw.txt)
into a verse-keyed JSON store, using the SAME book-name convention as Catena
(~/catena) — singular "Psalm", "1 Samuel"/"2 Kings" etc. — so a `source` string
written for one corpus resolves cleanly against the other.

Output: text/kjv.json  { "Isaiah 53:5": "But he was wounded ...", ... }
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "text" / "kjv-gutenberg-raw.txt"
OUT = ROOT / "text" / "kjv.json"

# Gutenberg's body section-heading text -> Catena-convention canonical book name.
TITLE_MAP = {
    "The First Book of Moses: Called Genesis": "Genesis",
    "The Second Book of Moses: Called Exodus": "Exodus",
    "The Third Book of Moses: Called Leviticus": "Leviticus",
    "The Fourth Book of Moses: Called Numbers": "Numbers",
    "The Fifth Book of Moses: Called Deuteronomy": "Deuteronomy",
    "The Book of Joshua": "Joshua",
    "The Book of Judges": "Judges",
    "The Book of Ruth": "Ruth",
    "The First Book of Samuel": "1 Samuel",
    "The Second Book of Samuel": "2 Samuel",
    "The First Book of the Kings": "1 Kings",
    "The Second Book of the Kings": "2 Kings",
    "The First Book of the Chronicles": "1 Chronicles",
    "The Second Book of the Chronicles": "2 Chronicles",
    "Ezra": "Ezra",
    "The Book of Nehemiah": "Nehemiah",
    "The Book of Esther": "Esther",
    "The Book of Job": "Job",
    "The Book of Psalms": "Psalm",
    "The Proverbs": "Proverbs",
    "Ecclesiastes": "Ecclesiastes",
    "The Song of Solomon": "Song of Solomon",
    "The Book of the Prophet Isaiah": "Isaiah",
    "The Book of the Prophet Jeremiah": "Jeremiah",
    "The Lamentations of Jeremiah": "Lamentations",
    "The Book of the Prophet Ezekiel": "Ezekiel",
    "The Book of Daniel": "Daniel",
    "Hosea": "Hosea",
    "Joel": "Joel",
    "Amos": "Amos",
    "Obadiah": "Obadiah",
    "Jonah": "Jonah",
    "Micah": "Micah",
    "Nahum": "Nahum",
    "Habakkuk": "Habakkuk",
    "Zephaniah": "Zephaniah",
    "Haggai": "Haggai",
    "Zechariah": "Zechariah",
    "Malachi": "Malachi",
    "The Gospel According to Saint Matthew": "Matthew",
    "The Gospel According to Saint Mark": "Mark",
    "The Gospel According to Saint Luke": "Luke",
    "The Gospel According to Saint John": "John",
    "The Acts of the Apostles": "Acts",
    "The Epistle of Paul the Apostle to the Romans": "Romans",
    "The First Epistle of Paul the Apostle to the Corinthians": "1 Corinthians",
    "The Second Epistle of Paul the Apostle to the Corinthians": "2 Corinthians",
    "The Epistle of Paul the Apostle to the Galatians": "Galatians",
    "The Epistle of Paul the Apostle to the Ephesians": "Ephesians",
    "The Epistle of Paul the Apostle to the Philippians": "Philippians",
    "The Epistle of Paul the Apostle to the Colossians": "Colossians",
    "The First Epistle of Paul the Apostle to the Thessalonians": "1 Thessalonians",
    "The Second Epistle of Paul the Apostle to the Thessalonians": "2 Thessalonians",
    "The First Epistle of Paul the Apostle to Timothy": "1 Timothy",
    "The Second Epistle of Paul the Apostle to Timothy": "2 Timothy",
    "The Epistle of Paul the Apostle to Titus": "Titus",
    "The Epistle of Paul the Apostle to Philemon": "Philemon",
    "The Epistle of Paul the Apostle to the Hebrews": "Hebrews",
    "The General Epistle of James": "James",
    "The First Epistle General of Peter": "1 Peter",
    "The Second General Epistle of Peter": "2 Peter",
    "The First Epistle General of John": "1 John",
    "The Second Epistle General of John": "2 John",
    "The Third Epistle General of John": "3 John",
    "The General Epistle of Jude": "Jude",
    "The Revelation of Saint John the Divine": "Revelation",
}

# Short verses are often packed onto the SAME physical line as the previous
# verse (e.g. "...saith the LORD: yet I loved Jacob, 1:3 And I hated Esau...")
# so verse markers must be found ANYWHERE in the joined text, not just at the
# start of a line.
VERSE_RE = re.compile(r"(?<!\S)(\d{1,3}):(\d{1,3})\s+")
BODY_START = "The Old Testament of the King James Version of the Bible"


def main():
    lines = SRC.read_text(encoding="utf-8").splitlines()

    # Skip the front-matter table of contents: find the SECOND occurrence of
    # BODY_START (the first is the TOC heading, the second opens the real text).
    starts = [i for i, l in enumerate(lines) if l.strip() == BODY_START]
    if len(starts) < 2:
        raise SystemExit(f"expected 2 occurrences of {BODY_START!r}, found {len(starts)}")
    body = lines[starts[1] + 1:]

    end_idx = next(i for i, l in enumerate(body) if l.startswith("*** END OF THE PROJECT GUTENBERG"))
    body = body[:end_idx]

    # Split into per-book chunks on the recognized title lines. 1/2 Samuel and
    # 1/2 Kings each carry a THIRD heading line in this text — "The First Book
    # of Samuel / Otherwise Called: / The First Book of the Kings" and
    # symmetrically "The First Book of the Kings / Commonly Called: / The
    # Third Book of the Kings" — reusing the exact same TITLE_MAP strings in
    # both roles. Skip whatever title-like line follows an "Otherwise/Commonly
    # Called:" marker rather than letting it re-trigger a book transition.
    chunks = []  # (book_name, [text_lines])
    current_book = None
    current_lines = []
    pending_skip = False  # True: the next non-blank line is the alt-title, discard it unconditionally
    for raw in body:
        line = raw.strip()
        if not line:
            continue
        if pending_skip:
            pending_skip = False
            continue
        if line.rstrip(":") in ("Otherwise Called", "Commonly Called"):
            pending_skip = True
            continue
        if line == "***" or line == "The New Testament of the King James Bible":
            continue
        if line in TITLE_MAP:
            if current_book is not None:
                chunks.append((current_book, current_lines))
            current_book = TITLE_MAP[line]
            current_lines = []
            continue
        current_lines.append(line)
    if current_book is not None:
        chunks.append((current_book, current_lines))

    verses = {}
    for book, text_lines in chunks:
        blob = " ".join(text_lines)
        blob = re.sub(r"\s+", " ", blob).strip()
        matches = list(VERSE_RE.finditer(blob))
        for i, m in enumerate(matches):
            chap, verse = m.group(1), m.group(2)
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(blob)
            text = blob[start:end].strip()
            verses[f"{book} {chap}:{verse}"] = text

    OUT.write_text(json.dumps(verses, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {OUT}: {len(verses)} verses, {len(set(k.rsplit(' ', 1)[0] for k in verses))} books")


if __name__ == "__main__":
    main()

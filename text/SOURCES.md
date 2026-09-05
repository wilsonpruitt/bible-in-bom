# Text sources — provenance and licensing status (2026-09-05)

## Book of Mormon editions
**Do NOT use `gutenberg-17-raw.txt` (Project Gutenberg #17) as the site's "1920" or "public domain" text.**
Collation against known variants shows it carries the **current (1981/2013) LDS
canonical wording**, not the 1920 Salt Lake City edition — e.g. it reads
"pure and delightsome" (2 Nephi 30:6), the 1840/1981 reading, where the 1920
edition reads "white and delightsome." The current LDS text is copyrighted by
Intellectual Reserve, Inc. Keep this file only as a cross-check; never publish
from it directly.

**Actual source used: BYU Office of Digital Humanities' OpenScripture project**
(`text/openscripture/`, cloned from `github.com/BYU-ODH/OpenScripture`,
commit `b1cad82`, 2022-08-10). A word-level dataset aligning the 1830, 1837,
1840, 1841, 1879, 1920, 1981, and 2013 editions under a constant modern
chapter:verse citation. Verified against two independently-documented textual
variants (2 Ne 30:6 white/pure; 1 Ne 11:18 "mother of God" → "mother of the
Son of God") — both reconstruct correctly.

`tools/parse-openscripture.py` reconstructs `bom-1830.json`, `bom-1920.json`,
and `bom-current.json` (6,604 verses each) from this dataset, plus
`data/variants.json` (18,836 word-level rows where 1830 differs from 1920 or
current — the raw material for the variant register, §3/§5 of PLAN.md).

**⚠️ OPEN LICENSING QUESTION — resolve before the public site goes live.**
The OpenScripture GitHub repo declares no license (checked via GitHub API,
2026-09-05). The underlying 1830/1920 *wording* is unquestionably public
domain (pre-1923); BYU-ODH's *word-alignment transcription* is a compiled
dataset with no stated terms, though their README says "we welcome external
researchers to use the datasets." Two paths before publishing a running text
built from this data:
1. Email BYU-ODH (Rob Reynolds / Russell Hansen, odh.byu.edu) for an explicit
   license/permission statement, or
2. Independently source and cross-check the 1830 running text against the
   Wikisource 1830 transcription and archive.org's 1830 scans, using
   OpenScripture only as an internal alignment/QA tool, not as the published
   source.
`text/openscripture/` is gitignored for this reason — it is a working input,
not a committed asset, until this is resolved.

## KJV
`kjv-gutenberg-raw.txt` = Project Gutenberg eBook #10 (public domain, no
licensing concern). `tools/parse-kjv.py` → `kjv.json`, 31,102 verses across
66 books — matches the canonical KJV verse count exactly. Book names follow
Catena's convention (`~/catena`): singular "Psalm," "1 Samuel"/"2 Kings" etc.,
so a `source` string resolves against either corpus without translation.

Parsing gotcha (fixed, kept here so nobody reintroduces it): this Gutenberg
text numbers 1–2 Samuel / 1–2 Kings in the old fourfold "Kings" tradition —
each book's heading block carries a THROWAWAY alternate title line
("Otherwise Called: The First Book of the Kings" under 1 Samuel's heading;
"Commonly Called: The Third Book of the Kings" under 1 Kings' own heading)
that reuses the exact same string in two different roles. The parser skips
whatever line follows an "Otherwise/Commonly Called:" marker unconditionally,
rather than pattern-matching the alt-title text itself.

# Adjudicating a chapter

The runbook for one chapter of one book. `PLAN.md` is the project, `CONVENTIONS.md`
is the judgment; **this is the procedure**, written after adjudicating 1 Nephi in
full so that the next 6,000 verses are done the way the first 618 were.

Read `CONVENTIONS.md` first. It is short and it governs. This file assumes it.

---

## 0. The one thing that matters most

**Never write that a named scholar said something unless they said it.** The
colleague's pilot was discredited by 23 invented attributions
(`work/1-nephi/PROVENANCE-colleague-pilot.md`). `tools/lint-adjudication.py`
rejects any bibliography entry not citing a source we actually hold, and flags
every attribution verb in prose for a human to check — but the lint cannot tell
a true attribution from a plausible one. You can. Cite Hardy and Frederick only
from `data/hardy-refs.json` and `data/frederick-refs.json`, and say what they
actually do; Frederick in particular proposes almost no sources, he argues about
John, so "Frederick identifies X" is nearly always false.

---

## 0a. Before a new book, get the apparatus right

A book is not ready because `bootstrap-book.py` ran. Hardy's apparatus is parsed
**per book**, and until it is, the bootstrap reports "Hardy rows to account for: 0"
— which reads exactly like a book with nothing to account for. That happened on
2 Nephi on 2026-09-05; the real count was 120. `bootstrap-book.py` now refuses to
run for a book absent from `data/hardy-parsed.json`, and the parse comes first.

**Before running it, verify `--next-heading` is a real line, not a guess.** A
wrong heading does not error — `parse-hardy.py` exits 0 either way — it just
gives `extract_section` nothing to bound the section on, so the walk runs to
the end of the file and mis-keys whatever it finds there onto the last chapter
of the book you asked for. Found on Helaman: guessing `"The Third Book of
Nephi"` (the canonical title) instead of Hardy's own bare section label
`"Third Nephi"` swallowed ~90 of 3 Nephi's own footnotes onto Helaman 16.
Check first:

```bash
grep -n "^Third Nephi\s*$" text/hardy-msi-raw.txt   # must return exactly one line
```

Hardy's own labels, not the canonical book titles, are what actually sit on
their own line in the appendix — confirm the exact string before trusting a
clean exit code.

```bash
python3.11 tools/parse-hardy.py --book "2 Nephi" \
    --heading "The Second Book of Nephi" --section-label "Second Nephi" \
    --next-heading "The Book of Jacob"
python3.11 tools/audit-hardy.py 2-nephi     # then READ the suspects
```

The audit is not a formality either. The parse keys each footnote to a verse by
walking the page, and a page it walks wrong mis-keys every note on it — 55 of
2 Nephi's 120 rows, whole chapters off by one, on the first run. Two signatures
tell you which kind of error you have:

- **The verse number survives and the chapter is wrong** (`21:16 → 20:16`). That
  is ours, every time. The walker lost a chapter transition.
- **The keyed verse has no verbal contact and nothing nearby does either.** Read
  the page in `text/hardy-msi-raw.txt` before concluding it is thematic
  (CONVENTIONS §6a).

Nothing in a suspect list moves without a human reading both verses, and what
moves is written into `data/hardy-corrections.json` with its evidence — `moves`
for a row on the wrong verse, `cite_fixes` for a citation wrong in the printed
apparatus. Only then dispatch.

---

## 1. The loop

```bash
SLUG=2-nephi; NAME="2 Nephi"; CH=4

# a. the dossier: 1830 text, 1830/1920 variants, ranked machine candidates
python3.11 tools/chapter-dossier.py $SLUG $CH --top 24 > work/$SLUG/dossier-ch$CH.md

# b. READ THE CHAPTER COLD, before opening the candidate list.  (§1.2)

# c. verify every rarity claim you intend to make
python3.11 tools/kjv-rarity.py "mist of darkness" "rod of iron"

# d. where an OT verse has an NT quotation, let the diff decide the mediation
python3.11 tools/mediation-check.py "$NAME $CH:20" "Deuteronomy 18:15" "Acts 3:22"

# e. write work/$SLUG/adjudicated/ch$(printf %02d $CH).json

# f. gates — both must pass before you commit
python3.11 tools/apply-adjudication.py $SLUG --check   # schema
python3.11 tools/lint-adjudication.py  $SLUG --chapter $CH   # facts

# g. append this chapter's exclusions to data/exclusions.json, then
python3.11 tools/apply-adjudication.py $SLUG
git add -A && git commit
```

**Step (b) is not optional and not a formality.** Four of the ten links in the
chapter-1 pilot, and most of the strongest links in the whole book, were invisible
to the machine streams. The n-gram stream is a recall floor, not a ranking
(`CONVENTIONS.md` §9): it scored a Herod verse first in 1 Nephi 3 and missed
Psalm 145:9 behind 1 Nephi 1:20 entirely, because contiguous windows cannot see
agreement split across a clause boundary. If you read the candidate list first you
will adjudicate the candidate list, and the catalogue will be worth what the
candidate list is worth.

---

## 2. What the tools are for

| tool | question it answers |
| --- | --- |
| `chapter-dossier.py` | What does this chapter say, what changed since 1830, what did the machine propose? |
| `kjv-rarity.py` | How many KJV verses contain this phrase? **Run it before claiming a count.** |
| `mediation-check.py` | The OT verse and its NT quotation are worded differently — which form does the Book of Mormon have? |
| `apply-adjudication.py --check` | Does every link have the fields the schema requires? |
| `lint-adjudication.py` | Do the references resolve, does `text` match the KJV, are the rarity claims true, is anything attributed to a scholar? |
| `hardy-coverage.py` | Is every Hardy row for this book a link or a reasoned exclusion? (`PLAN.md` §7.2) |
| `collate-isaiah.py` | For a transcribed Isaiah block — see §5 below. |

`kjv-rarity.py` normalizes curly apostrophes, which is the bug that hid
Exodus 3:18's "three days' journey" during the pilot. Use it rather than an ad hoc
grep.

---

## 3. What a strong link looks like

The pilot's best rows share a shape. Aim for it, and do not manufacture it.

1. **An absolute rarity.** "X occurs in exactly one KJV verse" is the strongest
   evidence available and it is free to check. Roughly a third of the pilot's
   links rest on a KJV singleton: `mist of darkness` (2 Peter 2:17), `frankly`
   (Luke 7:42), `fiery darts` (Ephesians 6:16), `still small voice`, `past
   feeling`, `Bethabara`, `twelve apostles of the Lamb`.
2. **A mediation test where one exists.** If the source is an OT verse the NT
   quotes, run `mediation-check.py`. Sixteen such rows were the pilot's principal
   result, and each turns on a single word: `ruler` not `prince`, `kindreds` not
   `nations`, `vapour` not `pillars`, `smooth` not `plain`, `worship` not `fear`.
3. **Metalepsis in `provenance.significance`.** Recover the source's context and
   say what it does to the borrowing. The Caiaphas sentence at 1 Nephi 4:13 is
   the model: the words that justify killing Laban are the words that justify
   killing Jesus, and John glosses them as unwitting prophecy.
4. **An 1830 reading, where one bears.** The first edition is the running text
   for a reason. 1 Nephi 7:11 reads "how great things the Lord hath done for us",
   which is Mark 5:19 verbatim; 1920 changed "how" to "what", which is in no KJV
   verse. That link is invisible in the modern text.
5. **A `whyNot` whenever the case is thin.** Required at `low` and `contested`,
   and good practice well above them. A risk taken openly is the posture
   `CONVENTIONS.md` §0a asks for; a risk taken quietly is just an error.

---

## 4. Traps the pilot hit

- **A long n-gram run means nothing on its own.** The longest runs in most
  chapters are `and it came to pass that the Lord spake unto`. One standing
  exclusion covers them (filed at 1 Nephi 2:1); pass over the rest in silence.
- **Rare word, wrong sense.** Samson's brass fetters scored 2.00 against "plates
  of brass"; Herod being "exceeding glad" outscored everything in 1 Nephi 3.
  Category `wrong-sense`, and write it up — those entries are the register's best
  content.
- **The window closes one word early.** 2 Timothy 2:4's "hath chosen him to be a"
  is a six-word run whose next word is `soldier`, not `ruler`. Always read the
  candidate's whole verse.
- **A repeat is not a fresh borrowing — WITHIN a book.** Once a narrator has
  adopted a phrase (`scattered upon all the face of the earth`, `great shall be
  the fall of it`), later occurrences in the same book are him using his own
  formula. Adjudicate at first use; record later ones in `recurrenceRefs` and,
  if the machine proposes them again, as a `better-source-identified` exclusion
  pointing at the first.

  **Across a book boundary, write the link.** *Ratified 2026-09-05 after the
  Omni pass raised it.* A new book is a new authorial voice, the reader page is
  per-book, and a reader of Omni who is shown nothing at 1:15 has simply been
  told there is no borrowing there. So give the row, set `recurrenceRefs` back
  to its first adjudication, and let the note say the argument was made there
  rather than restating it. The exclusion form is for repeats a reader would
  meet twice in one sitting; the link form is for the same phrase re-entering
  in a different hand.

  **A phrase can return to its source, not just recur.** *Ratified 2026-09-07
  after Mosiah 29:2 raised it.* "Voice of the people" is adjudicated at Mosiah
  7:9 (1 Samuel 8:7, Israel's demand for a king) and used again, within the
  same book, at 29:2 — Mosiah's abolition of that same kingship. The default
  above still governs a narrator reusing his own formula; it does not govern a
  phrase's second use being the argument, because the passage it first
  translated is the passage now being answered. Write the full link when that
  is true, and say in the note why this use is not the formula recurring.
- **Check the pronoun.** `hardness of THEIR hearts` is Mark 3:5 and `hardness of
  YOUR hearts` is Matthew 19:8, and 1 Nephi uses each in its correct grammatical
  setting. `mediation-check.py` deliberately ignores single common words to avoid
  false positives, so pronouns are yours to catch by eye.

---

## 5. Transcribed Isaiah blocks

Where a chapter is a continuous transcription (1 Nephi 20-21 = Isaiah 48-49;
expect many more in 2 Nephi), **do not hand-write it.** Run:

```bash
python3.11 tools/collate-isaiah.py $SLUG $CH Isaiah 48 --json work/$SLUG/variants-ch$CH.json
```

then extend `tools/build-isaiah-adjudication.py` with the chapter and author prose
notes only for the verses whose departures carry an argument. The tool writes one
link per verse and registers every word-level departure in
`data/isaiah-collation.json`. Check the overlap-floor warnings before trusting the
verse alignment — a low overlap means either a large deliberate addition or a
versification slip, and only a human can tell which.

---

## 6. Scope, and when to stop

A chapter is done when both gates pass, the exclusions are written, and every
verse you gave a link has an argument a reader could dispute. It is not done when
every verse has a link — most verses have none, and the pilot linked 267 of 618.

**Do not pad.** A chapter with six real links and a good exclusion register is
worth more than one with thirty rows of `and it came to pass`. `CONVENTIONS.md`
§0a asks you to take risks, which is not the same as lowering the bar: a risk has
an argument attached and a `whyNot`.

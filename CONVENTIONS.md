# Brass — adjudication conventions

Established on the 1 Nephi 1 pilot, 2026-09-05 (Opus). These are the rules a
per-chapter adjudicator follows. PLAN.md §3 defines the *schema*; this file
defines the *judgment*. Read both before adjudicating a chapter.

Wilson ratifies changes to this file. An adjudicator who finds a case the rules
do not cover should write the link, flag it, and say so — not quietly invent a
sixth confidence level.

---

## 0. The one rule everything else serves

**The machine finds candidates; it never decides.** Every accepted link carries a
prose argument that a human could dispute. Every rejected candidate that was
plausible enough to tempt someone goes in the exclusion register with the reason.
A catalogue that records only its acceptances cannot be checked, and an unchecked
catalogue is not definitive no matter how large it gets.

## 1. Working method, per chapter

1. `python3.11 tools/chapter-dossier.py <slug> <N> --top 50 > work/<slug>/dossier-ch<N>.md`
2. Read the chapter *first*, before looking at candidates. Form your own sense of
   where it is leaning on scripture. The candidate list is an aid to recall, not
   an agenda — several of the strongest links in chapter 1 were not in it.
3. Work verse by verse. For each candidate: accept as a `Link`, or write an
   exclusion, or pass over it silently if it is pure connective noise already
   covered by a standing exclusion (see §5).
4. Write `work/<slug>/adjudicated/ch<NN>.json`.
5. `python3.11 tools/apply-adjudication.py <slug> --check` until it passes, then
   run it without `--check`.

## 2. Choosing `type` and `subtype`

`type` is the display category; `subtype` refines it. Decide on the evidence, not
on how important the link feels.

| type | when |
| --- | --- |
| `quotation` | A complete clause reproduced verbatim, or nearly so, from a verse that is identifiably its source. |
| `allusion` | Distinctive shared wording short of a reproduced clause, where the source is still identifiable. |
| `echo` | Faint verbal contact; the source is plausible but not demonstrable. |
| `figural` | The link is at the level of narrative form or typology, with little or no shared wording. |

**Length does not decide `quotation` on its own.** 1 Nephi 1:14 reproduces six
words of Revelation 15:3 exactly, from the only two verses in the Bible where
that phrase occurs, and is catalogued as a quotation. Skousen's sixteen-word
threshold is *his* operational definition for *his* purpose and we do not adopt
it — but where a link falls below it, **say so in the note**, so the catalogue
can be read alongside his. Never imply a passage is one of his 36 when it is not.

## 3. `confidence` is decoupled from `type`

A figural link can be `high` and a quotation can be `contested`. Confidence is
about how sure we are of *dependence*, not how much text is shared.

- `certain` — dependence is not seriously deniable.
- `high` — dependence is the best explanation by a clear margin.
- `moderate` — dependence is more likely than not; a reasonable reader could decline it.
- `low` — worth recording, probably not defensible. **Requires `whyNot`.**
- `contested` — the literature actually disagrees. **Requires `whyNot`.**

Do not use `low` as a way of keeping something you cannot argue for. If the case
is weak *and* uninteresting, it belongs in the exclusion register instead.

## 4. `kjvSpecific` is the historically significant field — do not inflate it

This is the claim that gives the project its point, so it is the one to be
strictest about. Answer the question: *could this wording have come from an
English Bible other than the KJV?*

- `yes` — the phrasing is the KJV's and other English versions differ. Say what
  they read instead, in `provenance.other`. Example: 1 Nephi 1:13's "carried away
  captive into Babylon", where modern versions read "carried into exile".
- `uncertain` — the KJV shares the reading with Geneva, Bishops', or Tyndale, so
  the passage cannot separate them. **This is the correct answer far more often
  than is comfortable**, and Skousen's own comparison tables (BYU Studies 59.1,
  93–95) are the model: he sets the KJV beside seven earlier English versions
  before claiming anything. 1 Nephi 1:14 is marked `uncertain` for exactly this
  reason — Geneva 1560 reads nearly the same.
- `no` — the phrase is common to essentially all English Bibles ("pillar of
  fire"), or the link is figural and has no wording to test.

A `yes` should be backed by rarity: check how many KJV verses contain the phrase
before claiming it. `text/kjv.json` is loaded as a `{ref: text}` dict; a two-line
regex count is enough, and it is not optional.

## 5. The exclusion register

Write an entry whenever a candidate was *plausible enough that a careful reader
might have accepted it*. Categories are defined in `data/exclusions.json`.

**Do not** write an entry for every one of the thousands of connective matches.
`and it came to pass`, `unto them concerning the`, and their kind are covered by
the standing exclusion at 1 Nephi 1:5 and may be passed over in silence.

**Do** write an entry, at length, when:
- the string match is real but the sense is opposed (`wrong-sense`) — see the
  Proverbs 12:10 entry, the model case;
- a better source displaces a machine proposal (`better-source-identified`);
- a typological expectation was pulling toward a link the wording will not bear
  (the Exodus 2:2 "goodly" entry).

## 6. Citations: never invent one

The scholarship stream (PLAN.md §4.4) **has not been run** — Hardy 2023 and
Frederick are not on disk and Skousen's KJQ list is unobtainable (§4.1). So:

- `bibliography` may only contain a citation whose source we actually hold and
  which has been checked. Today that is close to nothing.
- Where you are confident a link is standard in the field but cannot cite it,
  set `status` to your honest read (`consensus`, `majority`, …) **and set
  `citationsPending: true`.** That field exists so a `status` claim is not
  mistaken for a sourced one.
- `status: "novel"` means *nobody has claimed this before*. That is a strong
  claim about the literature. Do not use it as a synonym for "I have no citation."

`apply-adjudication.py` enforces the last two: a link with no bibliography must
be either `novel` or `citationsPending`.

## 7. Mediation

Decide, don't default. The interesting cases are OT sources that also appear in
the New Testament: whether the Book of Mormon follows the OT-KJV or the NT-KJV
form of a shared text is a real finding, and 1 Nephi 22:20 (Deuteronomy 18 via
Acts 3:22 / 7:37) is the chapter where it must be got right. `OT-via-earlier-BoM`
is for cases where an earlier Book of Mormon quotation, not the Bible, is the
proximate model — expect these from 2 Nephi onward.

## 8. The 1830 running text is evidence, not just a text choice

Flag it in the `note` whenever an 1830 reading bears on the judgment:

- 1830 preserves KJV orthography that later editions erased — `shew`/`show`,
  `marvellous`/`marvelous`. The first edition shows the borrowing more plainly
  than the current text does.
- 1830 sometimes departs from KJV grammar where a later edition "corrected" it
  back *toward* the source: 1 Nephi 1:20 reads "tender mercies … **is** over all"
  against the KJV's "are", and 1920 changed it to "are". The direction of that
  change is worth recording.

## 9. What the pilot found about the machine streams

Carry these forward; they shape how much to trust the dossier.

- **The n-gram stream is a recall floor, not a ranking.** Rare boilerplate scores
  high (Job 42:7, "that after the LORD had", scored 1.50 and is worthless) while
  the true source of 1 Nephi 1:20 scored nothing at all.
- **Contiguous windows are blind to split agreement.** Psalm 145:9 is the source
  of 1 Nephi 1:20 and shares only "tender mercies" plus "over all" across a
  clause boundary. The n-gram stream cannot see it, by construction. Four of the
  ten links in chapter 1 came from `streams: ["manual"]`.
- **This is the argument for the semantic stream** (PLAN.md §4.3, unimplemented).
  Until it exists, the adjudicator *is* the recall mechanism, and reading the
  chapter cold before opening the candidate list (§1.2) is what makes that work.

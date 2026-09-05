# The colleague's 1 Nephi pilot — provenance assessment

Assessed 2026-09-05 (Opus) against the primary sources, which Wilson supplied the
same day. Source file: `~/Downloads/The_Bible_in_1_Nephi.txt`, 127 records
covering all 22 chapters.

**Verdict: import as candidate rows, never as citations. Strip every attribution.**

## The citations are fabricated

The pilot attributes specific verse pairings to Nicholas Frederick (16 times) and
to Frederick-and-Spencer jointly (7 times). Checked against the books themselves:

| Claim in the pilot | What the book actually contains |
| --- | --- |
| "Frederick's index explicitly pairs" 1 Ne 2:10 ~ 1 Cor 15:58 | Frederick has **no scripture index**. |
| "Frederick indexes Romans 11:17 with 1 Nephi 10:12" | Not present in any citation format. |
| "Frederick's index explicitly pairs Romans 5:5 with 1 Nephi 11:22" | Not present. |
| "Frederick's Pauline index pairs 1 Cor 3:15 with 1 Ne 22:17" | Not present. |
| "Frederick and Spencer identify [Revelation 21:9–10 / 19:19 / 18:12 / 17:15 / 11:19]" | Spencer cites Revelation **once** in the whole book (Rev 20:6). |

Frederick, *The Bible, Mormon Scripture, and the Rhetoric of Allusivity* (Fairleigh
Dickinson, 2016) is a monograph on the **Prologue of John** — chapters titled
"Mormon Scripture and the Echo / Allusion / Expansion / Inversion of John." In
104,000 words it cites three verses of 1 Nephi (13:26, 13:27, 14:17) and four
Pauline verses total (Romans 4:3, Romans 12:1, 1 Corinthians 1:15, 1 Corinthians
1:26). Its back-matter "Index" (pp. 145–150) is a subject index.

Spencer, *A Word in Season: Isaiah's Reception in the Book of Mormon*, is about
Isaiah and barely touches Revelation.

Loose-pattern greps were run before concluding this (`1 Ne. 2:10`, `1 Nephi 2.10`,
abbreviated and full forms), per the standing rule that an empty grep is not
absence. The absence is real.

This is the ordinary citation-hallucination failure mode of an LLM asked for
scholarly grounding. It says nothing about the observations themselves, many of
which are sound — but it means the apparent sourcing is worthless and every row
enters our catalogue as `citationsPending: true` exactly like our own.

## Unverifiable attributions

The pilot also names McGuire (David/Goliath at 1 Ne 4), Swift (Revelation and the
tree at 1 Ne 8), Bowen (Isaiah 29:14 at 1 Ne 22:8), Brown (Exodus recital at
1 Ne 17), Lincoln Cannon (2 Kings 2:8 at 1 Ne 17:26), Hardy, and "ScriptureCentral"
and "the Psalms study". We hold none of those sources, so these are neither
confirmed nor refuted. Treat them as leads to check, not as citations. Given the
Frederick and Spencer results, assume nothing until checked.

## Substantive gaps, measured

- **No exclusion register.** 127 acceptances, 0 documented rejections.
- **Chapters 20 and 21 are one record each** — Isaiah 48–49 as two undifferentiated
  blocks. PLAN.md §5 explicitly requires verse-by-verse collation here, and the
  pilot itself concedes the point ("should be collated verse by verse in the full
  edition"). This is the single largest data gap: 48 verses of the most
  quotation-dense material in the book, reduced to two rows.
- **Chapter 9 has no records at all**; chapters 3 and 16 have two each.
- **Confidence inflation:** 105 of 127 are Certain or High; exactly one is Low.
- **KJV-specificity inflation:** 61 of 127 marked "Yes" (~48%), generally without
  checking earlier English versions. 1 Nephi 1:14 is marked "Yes" though Geneva
  1560 reads nearly identically — by CONVENTIONS.md §4 it is `uncertain`.
- Non-schema values appear in both fields ("Probable", "High", "N", "N/A").

## What it is genuinely good for

Real coverage breadth we do not otherwise have, and several finds our own
chapter 1 pass missed — notably 1 Nephi 1:20, "cast out, and stoned, and slain"
against Matthew 23:37 and Hebrews 11:37, which is a good catch.

Conversely our chapter 1 caught what it missed: the Jeremiah dateline at 1:4, and
both Jeremiah links at 1:13 — including "carried away captive into Babylon," a
phrase occurring exactly once in the entire KJV. The two passes are complementary,
which is the argument for merging rather than choosing.

**Caution on agreement.** Where the two pilots agree (1:3 Philemon, 1:8 the throne
vision, 1:14 Revelation 15:3, 1:20 Psalm 145:9), that is two LLM passes agreeing,
not two independent witnesses. Convergence here is one method reporting twice.

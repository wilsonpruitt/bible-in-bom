# The Bible in the Book of Mormon — build plan
*A Catena-family digital critical catalogue. Drafted 2026-09-05 (Fable, planning session). Execution is Sonnet/Opus work — see §9.*

## 0. Where we actually stand (verified on disk 2026-09-05)
- **Catena is done and live** (catena.wrootpress.com, `~/catena`, private GitHub `wilsonpruitt/catena`, Vercel auto-deploys from `main`). All 27 NT books, Index Fontium with significance ranking, per-source dossiers, trajectory reader, chord diagram, open-data export (`tools/export-dataset.mjs`). Schema in `lib/types.ts`: `Book → Pericope → Echo{source,type,confidence(high|med|low),text,lxxText?,note?,altSource?,contested?}`.
- **The colleague's 1 Nephi pilot (96 records) is NOT on this Mac.** It lived inside their chat session. Two paths: (a) ask them to export it as JSON/CSV/HTML and we import it as the first control set; (b) rebuild it — 96 hand-picked links is one Opus afternoon against the literature list below. Do (a) if it costs one email; do not wait on it.
- **Nothing BoM-specific exists yet.** This directory (`~/bible-in-bom`) is the home. Fork Catena's renderer into it rather than adding BoM books to `~/catena/data/books.ts` — mixing corpora would pollute the NT Index Fontium and the significance scores.

## 1. Architecture decision: sibling repo, shared conventions
- New repo `bible-in-bom` forked from `~/catena` (as Catena was forked from Loci). Keep the reader, filters, Index Fontium, dossiers, export. Replace `data/`, extend `lib/types.ts`, restyle the series mark.
- **One dataset, many presentations** stays the rule: per-book JSON is the single source of truth; site, CSV, PDF concordance, statistics are all derived.
- Proposed domain: a `wrootpress.com` subdomain (Wilson names it). Same Labs Vercel team as Catena.

## 2. Base texts — STATUS: acquired and reconstructed (2026-09-05)
**Running text = 1830 first-edition wording, stored under modern chapter:verse.** Wilson's ruling stands: the 1830 wording is what the Authorized Version actually shaped, before the 1837/1840/1879/1920 grammatical and doctrinal smoothing (e.g. the 1837 "mother of God" → "mother of the Son of God" at 1 Ne 11:18; hundreds of "which" → "who"). Modern versification (constant since 1879) is needed to align against Hardy/Frederick/Skousen, who all cite modern refs.

**Finding: Project Gutenberg #17 is NOT the 1920 edition.** Collated against known variants (2 Ne 30:6 "white/pure and delightsome"), it reproduces the CURRENT (1981/2013) LDS canonical wording — copyrighted by Intellectual Reserve, Inc. Do not use it as a base text. See `text/SOURCES.md`.

**Actual source: BYU-ODH's OpenScripture project** (`github.com/BYU-ODH/OpenScripture`, cloned to `text/openscripture/`) — a word-level dataset aligning 1830/1837/1840/1841/1879/1920/1981/2013 under one constant modern citation. `tools/parse-openscripture.py` reconstructs:
- `text/bom-1830.json` — 6,604 verses, the running text
- `text/bom-1920.json` — 6,604 verses, for cross-checking Hardy/Skousen citations
- `text/bom-current.json` — 6,604 verses, reference only
- `data/variants.json` — 18,836 word-level rows where 1830 differs from 1920 or current (1,998 of them in 1 Nephi) — raw material for the variant register (§3/§5)

Both diagnostic checks (2 Ne 30:6, 1 Ne 11:18) reconstruct correctly. **⚠️ OPEN before publishing:** OpenScripture's GitHub repo declares no license. Their transcription is fine as an internal alignment/QA tool now; resolve licensing (email BYU-ODH, or cross-verify the 1830 running text against Wikisource's 1830 transcription) before the public site ships it as the running text. `text/openscripture/` is gitignored for this reason.

**KJV: done.** `tools/parse-kjv.py` parses Project Gutenberg #10 (unambiguously PD) into `text/kjv.json` — 31,102 verses across 66 books, matching the canonical KJV verse count exactly. Book names follow Catena's own convention (singular "Psalm," "1 Samuel"/"2 Kings") so a `source` string resolves against either corpus without translation. **The source panel shows KJV, not WEB** — KJV-specific dependence is the thesis; WEB/LXX/Hebrew stay in the provenance panel only.

Remaining in this step: nothing blocking. 1837/1840 and Skousen's reconstructed readings can be added to the variant register later from the same OpenScripture columns; Skousen's own *Earliest Text* apparatus stays cite-only (copyrighted edition).

## 3. Data model — Catena's schema plus what a critical catalogue needs
Extend `Echo` (rename nothing in Catena; this is the fork's type):
```ts
type Link = {
  source: string;               // "Isaiah 53:5" (KJV ref)
  type: "quotation"|"allusion"|"echo"|"figural";
  subtype?: "explicit"|"extended"|"close-verbal"|"paraphrase"|"strong-verbal"|"conceptual"|"probable"|"possible"|"type-scene"|"structural";
  confidence: "certain"|"high"|"moderate"|"low"|"contested";   // 5 levels, decoupled from type
  evidence: { vocabulary:0-5; syntax:0-5; sequence:0-5; context:0-5; rarity:0-5; attestation:0-5 };
  kjvSpecific: "yes"|"no"|"uncertain";   // the historically significant claim
  mediation: "direct-OT"|"direct-NT"|"OT-via-NT"|"OT-via-earlier-BoM"|"uncertain";
  composite?: string[];          // other sources fused in the same phrase
  text: string;                  // KJV source text
  provenance?: { mt?: string; lxx?: string; other?: string; route: string; alternative?: string; significance: string };
  note: string;                  // the argument FOR
  whyNot?: string;               // the counter-evidence (required when confidence = contested|low)
  bibliography: string[];        // "Hardy 2023: 871", "Frederick 2016: §4", "Skousen KJQ: #12"
  status: "consensus"|"majority"|"minority"|"novel"|"rejected";
  variants?: string[];           // ids into text/variants.json when 1830≠1920 changes the judgment
  streams: ("scholarship"|"machine-ngram"|"machine-fuzzy"|"machine-semantic"|"manual")[];  // how it was FOUND
};
```
Plus two sidecar files the site renders but the reader rarely opens:
- `data/exclusions.json` — the exclusion register: every tempting parallel rejected, with the reason, **plus cross-references from a verse to another verse where its borrowing is actually adjudicated** (RULED 2026-09-07, after Mosiah 11:14/11:19 used it that way first). A verse whose strongest phrase is adjudicated elsewhere in the book gets a `better-source-identified` row here rather than silence — this is what makes "definitive" defensible for readers browsing verse by verse, not only for the register's own completeness.
- `data/kjv-phrases.json` — the Index Verborum: phrase → BoM occurrences → KJV backgrounds ("natural man", "steadfast and immovable", "works of righteousness").

Rule carried over from Catena and stated on the site: **the machine finds candidates; it never decides.** Every record has a human adjudication note.

## 4. Candidate generation — three machine streams (Wilson's addition: semantic)
All run BoM verse × KJV verse (≈6,600 × 31,100 = 205M pairs; trivial for n-grams, batched for embeddings). Run against BOTH 1830 and 1920 wording and diff the candidate sets — that diff is itself a finding.
1. **Exact / rare n-gram.** Shared 4-grams and up, weighted by KJV rarity (a 5-gram found in one KJV verse is worth more than "and it came to pass"). Skousen's criteria for his 36 long + 83 short KJV quotations are the calibration set — **but the itemized list only exists inside his KJQ volume (2019, part 5 of vol. 3 of the Critical Text Project), which is not available to this project** (checked 2026-09-05: his own BYU Studies 59.1 summary article gives methodology + a partial top-10 table, not the full 119; no online review reproduces the rest). For **1 Nephi specifically**, the one confirmable long quotation is **1 Nephi 20–21 ~ Isaiah 48–49** (his table: n-gram max 108, 31 runs >15) — already recovered as the top-scoring candidate in `work/1-nephi/candidates.jsonl`. 1 Nephi has no other substantial Isaiah block, so it likely contributes few or none of the 83 short/paraphrastic quotations either, but that can't be confirmed without the book. **Revisit acquiring KJQ itself when the pilot reaches 2 Nephi**, which has far more Isaiah and far more riding on full recall.
2. **Fuzzy / ordered-word.** Levenshtein on normalized text, longest common subsequence in order, to catch paraphrase and inverted quotation.
3. **Semantic (embeddings).** Embed every verse of both corpora; nearest-neighbour search surfaces conceptual parallels with no shared wording — the stream that can find figural and thematic links the n-gram streams cannot. Model: a small sentence-embedding model run locally in Python 3.11 (fits 8 GB), or an embeddings API; 38k short strings either way. **Caution:** this stream floods with theological commonplaces (grace, repentance, judgement). Rank by rarity-adjusted similarity, cap per verse, and expect most of it to land in the exclusion register — that is the register doing its job, not waste.
4. **Scholarship stream (not machine).** Hardy 2023 appendix (p. 867ff), Frederick's Pauline studies, Skousen's KJQ, Wayment, Barlow, individual articles. Transcribe as candidate rows with `streams:["scholarship"]` and citations. These are also the recall test: every Hardy row for 1 Nephi must end as either an accepted Link or an entry in the exclusion register with a reason.

Output of this stage: `work/1-nephi/candidates.jsonl`, one row per (BoM ref, KJV ref) with per-stream scores, deduplicated across streams. Expect low thousands for 1 Nephi after thresholds.

## 5. Adjudication — the human (Opus) stage
- Per chapter, an Opus agent receives: the BoM pericope in 1830 wording (with 1920 variants inline), the candidate list, the scholarship rows, and the rubric in §3. It writes the Link or the exclusion, never a bare score. Prose arguments → Opus (house rule).
- 1 Nephi 20–21 (Isaiah 48–49) is collated verse by verse against KJV Isaiah, and each departure is recorded as a variant row, not treated as two quotation blocks.
- Mediation gets its own pass: for every OT source that also appears in the NT (Isa 40:3 / 1 Ne 10:8; Deut 18 / Acts 3 / 1 Ne 22:20), decide whether the BoM wording follows the OT-KJV or the NT-KJV form.
- Wilson's read-through is the final gate for the pilot, chapter by chapter; then the rules freeze and 2 Nephi begins.

## 6. Site (fork of Catena, ~2 sessions of Sonnet work once data exists)
- Home: 15 books. Book page: Catena reader with 4 type chips, 5-level confidence ink, KJV-specific badge, mediation glyph. Click → source panel + **provenance panel** (KJV / BoM / MT / LXX / route / significance) + "Why this?" evidence bars + "Why not?" when present.
- Index Fontium: The Bible in the Book of Mormon (reverse index by biblical book, split by mediation class as the colleague proposed for Isaiah). Reuse `lib/fontium.ts`.
- Index Verborum: the KJV phrase index.
- Exclusion register page, variant register page, bibliography, downloads (JSON/CSV — `export-dataset.mjs` already does this shape).
- Not in the pilot: chord diagram, trajectory reader, PDF. Port later; they are derived views.

## 6a. STATUS — 1 Nephi adjudicated in full (2026-09-05, Opus)

All 22 chapters. 288 links across 267 of 618 verses; 247 exclusions; 99 Isaiah
variants. 96 quotations, 160 allusions, 30 echoes, 2 figural. Confidence: 80
certain, 129 high, 76 moderate, 3 low. `kjvSpecific: "yes"` on 226. Mediation:
163 direct-OT, 105 direct-NT, **16 OT-via-NT**, 3 OT-via-earlier-BoM.
170 rows are `status: "novel"`; 43 carry a Hardy citation, 245 remain pending.

Top source books by link count: Isaiah 65, Revelation 23, Matthew 23, Acts 20,
Genesis 18, Exodus 12, John 12, Psalm 10, 1 Samuel 10, Hebrews 9.

**The sixteen OT-via-NT rows are the pilot's principal result.** Each is decided
by a point where the KJV's Old Testament and its own New Testament quotation
differ, and in every case but two the Book of Mormon has the New Testament's
form. The clearest: 2:22 and 3:29 (`ruler` not `prince`, Acts 7:27 vs Exodus
2:14) · 6:4 (one conjunction, Acts 7:32 vs Exodus 3:6) · 10:8 (`make his paths
straight`, Synoptics vs Isaiah 40:3) · 12:17 (`blinded … hardened`, John 12:40
vs Isaiah 6:10) · 15:18 and 22:9 (`kindreds` not `nations`, Acts 3:25 vs Genesis
22:18) · 17:39 (third person, Matthew 5:35 vs Isaiah 66:1/Acts 7:49) · 17:46
(`smooth` not `plain`, Luke 3:5 vs Isaiah 40:4) · 17:55 (`worship` not `fear`,
Matthew 4:10 vs Deuteronomy 6:13) · 19:11 and 22:18 (`vapour` not `pillars`,
Acts 2:19 vs Joel 2:30) · **22:20**, the test CONVENTIONS §7 named in advance:
26 continuous words of Acts 3:22-23, with every divergence from Deuteronomy 18
on the New Testament side. Recorded counter-examples where the book follows the
Old Testament instead: 13:37 and 19:17, both Isaiah 52.

Acts 3 is a source at five places (3:20, 15:18, 19:10, 22:9, 22:20) and Acts 7
at six (2:22, 3:29, 5:14, 6:4, 11:13, 17:8). Hebrews 11 is used in its own
order across chapters 2-5 (11:8, 11:9, 11:13, 11:29). Mark 3:1-5 supplies three
separate elements across chapters 2, 7 and 17.

New tools: `collate-isaiah.py`, `build-isaiah-adjudication.py`,
`hardy-coverage.py`, `parse-frederick.py`. New data: `isaiah-collation.json`,
`frederick-refs.json`. Schema addition:
`Link.recurrenceRefs`.

## 6b. Agent passes — the harness (set up 2026-09-05, NOT yet run)

The pilot established the pattern; this is the machinery for repeating it 197
more times. Nothing has been dispatched.

**Runbook:** `ADJUDICATING.md` — the procedure, written after 1 Nephi so the
method is the thing that scales rather than the person. `CONVENTIONS.md` still
governs judgment; `ADJUDICATING.md` governs the loop.

**Agent:** `.claude/agents/adjudicator.md`, one per chapter, model Opus (§9).
It reads the conventions, the runbook, and two worked chapters, then runs the
loop and reports. It does not commit — the dispatching session reviews.

**New verification tools.** These were done by ad hoc heredoc during the pilot,
which is exactly what must not happen at scale:
- `kjv-rarity.py` — how many KJV verses contain a phrase. A third of the
  pilot's links rest on a singleton, and the claim is free to check. Normalizes
  curly apostrophes (the bug that hid Exodus 3:18 during the pilot).
- `mediation-check.py` — diffs an OT verse against its NT quotation and reports
  which form the Book of Mormon has. This is the mechanism behind all sixteen
  OT-via-NT rows. It ignores single common words after a false "decisive" on
  22:20, so pronouns still need a human eye.
- `lint-adjudication.py` — the gate that matters. Every reference must resolve
  against the KJV; `text` must be the actual wording of `source`; every
  "occurs in exactly N KJV verses" claim is verified; bibliography entries must
  cite a source we hold; attribution verbs are flagged for review. **It found a
  real error in hand-written pilot work on its first run** (1 Nephi 17:8 claimed
  a singleton for "I shall shew thee", which occurs in two — the singleton is
  "which I shall shew thee"). 1 Nephi now passes with 0 errors.
- `bootstrap-book.py` — a book from nothing to ready in one command, and
  reports what a pass will face (chapters, Hardy rows, Frederick verses).

**Estimated burn for the rest of the corpus** (Wilson's hard stop #6):

| | chapters | tokens |
| --- | --- | --- |
| hand-adjudicated | 197 | 7.9M – 11.8M |
| collated Isaiah/Malachi blocks | 20 | 0.1M – 0.2M |
| **total** | **217** | **8.0M – 12.0M** |

Rate is the pilot's own: 1 Nephi's 22 chapters cost roughly 1.0M tokens in one
session, and a dispatched agent adds start-up reading. Alma alone is 63
chapters and about a third of the whole job. **The twenty transcription
chapters are nearly free** — `collate-isaiah.py` does 2 Nephi 12-24 (Isaiah
2-14), 2 Nephi 7-8, 3 Nephi 22 and 24-25, Mosiah 14 mechanically, and those
are the chapters that would otherwise be the most expensive to hand-write.

**Recommended order, cheapest proof first:** the four one-chapter books (Enos,
Omni, Words of Mormon, Jarom — ~4 chapters, under 200k) to check agent output
against the pilot's standard, then Jacob (7), then 2 Nephi (17 hand + 16
collated), then the long books.

## 7. Pilot acceptance test ("definitive" for 1 Nephi means all of these)
1. Pipeline recovers the confirmable Skousen KJV-quotation row(s) in 1 Nephi — currently just 1 Nephi 20–21 ~ Isaiah 48–49 (recovered ✓, see §4 note on KJQ availability).
2. Every Hardy appendix row for 1 Nephi is either a Link or a reasoned exclusion.
3. Frederick's four Pauline parallels and the Rev network in 1 Ne 11–14 are present with bibliography.
4. 1 Ne 20–21 collated verse by verse; variant rows exist.
5. Every Link has a `note`, `mediation`, `kjvSpecific`, and ≥1 bibliography or `status:"novel"`.
6. Exclusion register non-empty and reviewed.
7. Wilson has read every chapter in the reader.

**Status of the seven, 2026-09-05:**
1. ✅ 1 Nephi 20-21 ~ Isaiah 48-49 recovered and collated (see §6a).
2. ✅ **All 62 Hardy rows for 1 Nephi accounted for** — `tools/hardy-coverage.py`
   checks it mechanically and exits non-zero on a gap. Run it before claiming this.
3. ⚠️ **The criterion was wrong, and is now restated.** Frederick was acquired
   2026-09-05 and indexed (`tools/parse-frederick.py` → `data/frederick-refs.json`).
   The criterion as drafted — "Frederick's four Pauline parallels and the Rev
   network in 1 Ne 11-14" — does not describe his book. Frederick's subject is
   **the Gospel of John** (289 Johannine citations against 4 in Revelation and
   2 in Romans), and across the whole monograph he cites 1 Nephi at exactly
   **four verses: 13:26, 13:27, 13:29, 14:17** — none of them Pauline, none of
   them in the Revelation network of 11-14. There are no four Pauline parallels
   to check against.

   What is now done: all four are catalogued, and three carry a Frederick
   citation that says what he actually argues (13:26 and 13:27 and 14:15/17;
   plus 22:25, where his claim about John 10:16's "other sheep" is directly on
   point). The Revelation network in 11-14 remains catalogued — 11:34, 13:26,
   14:10-11 are its spine — against Revelation itself, which is the right
   authority for it.

   **Restated criterion, for 2 Nephi onward:** every Frederick row for the book
   under adjudication is either a Link or a reasoned exclusion. That will bite,
   because his weight is elsewhere: 3 Nephi 23, 2 Nephi 18, Moroni 12. The
   pilot's overlap with him was always going to be near zero.

   **Correction, 2026-09-07 (Alma complete):** "Alma 47 citations" above was
   wrong. Checked directly against `data/frederick-refs.json` and
   `text/frederick-clean.txt` while adjudicating Alma 46-48: his Alma rows
   stop at 36:26, and no Frederick citation falls anywhere in Alma 45-49.
   His weight in Alma turned out to be 6:8 and 36:26 only.
4. ✅ Collated verse by verse; 99 variant rows in `data/isaiah-collation.json`.
5. ✅ Enforced by `apply-adjudication.py`, which refuses to write otherwise.
6. ✅ 247 exclusions across five categories.
7. ⛔ Pending Wilson's read-through — the last gate.

**Open, for Wilson's ruling:**
- `Mediation` enum: 4:14, 22:6 and 22:13 are mediated by the book's OWN earlier
  text, and two of the three have a New Testament ultimate source. The value is
  named `OT-via-earlier-BoM`; the category is right and the name is not.
- The italics question. The public-domain KJV in `text/kjv.json` does not mark
  italicized words, so whether the 99 Isaiah departures cluster at them cannot
  be answered here. Stated as a limit inside `isaiah-collation.json` itself.
- Skousen's KJQ list remains unobtainable, so no row can be checked against his
  36 + 83. Every quotation link says explicitly where it falls relative to his
  sixteen-word threshold. The two strongest candidates in 1 Nephi are 10:8 and
  22:20.

## 8. Order of work
1. Texts (§2): acquire, align, variant register. Sonnet. One session.
2. Fork Catena → this repo; schema (§3); KJV store; reader renders 1 Nephi text with zero links. Sonnet. One session.
3. Candidate pipeline (§4) with the Skousen recall test as its unit test. Sonnet. One to two sessions.
4. Import or rebuild the colleague's 96 records as the first adjudicated rows. Opus. Half a session.
5. Adjudicate 1 Nephi chapter by chapter (§5). Opus; this is the token burn — estimate before launch (hard stop #6).
6. Site features that need real data: provenance panel, Why-not, indices, registers. Sonnet.
7. Wilson read-through → freeze rules → 2 Nephi.

## 9. Model note
Steps 1–3 and 6 are pattern-following build work (Sonnet). Steps 4–5 are authored scholarly prose (Opus). Fable is done once this plan is approved; the only Fable-shaped decisions left are the rubric wording in §3 and the acceptance test in §7, and both are written down here.

## 10. Rulings still owed
- Domain / product name (working title: *The Bible in the Book of Mormon*).
- Whether to email the colleague for the 96-record export.
- ~~Confirm 1830-as-running-text~~ — RULED 2026-09-05: 1830, done (§2).
- **NEW: OpenScripture licensing.** Email BYU-ODH for a permission statement, or plan to cross-verify the published 1830 running text against Wikisource before the site goes live. Not blocking further build work — only blocking publication.
- ~~Mosiah 29:2 vs. 7:9~~ — RULED 2026-09-07: kept as its own link. A phrase can return to its source, not just recur as formula; codified in ADJUDICATING.md §4.
- ~~Exclusion register scope~~ — RULED 2026-09-07: the register also carries `better-source-identified` cross-references between two accepted links, not rejections only. PLAN §3 updated.
- ~~`variants` field~~ — RULED 2026-09-07: stays prose-only inside `provenance`/`note`. Not wired up structurally unless a future need (site rendering, cross-corpus query) actually requires it.

## 10a. Pre-publication punch list
Small, deferred items — none blocking Alma or any future book, all cheap to clear in one pass before the site goes live:
- **1 Nephi 8:12, "exceeding great joy."** A KJV singleton (Matthew 2:10) used 11 times in the corpus; 1 Nephi predates the convention of catching this, so 8:12 itself has no link. Needs one small dispatch plus a `recurrenceRefs` update on the other 10 occurrences.
- **Jonah 3:8, used three times in Mosiah** (9:17, 24:10 as full links; 21:14 as a route citation), each individually defended by a different agent but never reviewed together. Fold into the general first-book/cross-book consistency sweep this list implies doing before publication.

## 11. Progress log
- **2026-09-05 (Sonnet):** Acquired and reconstructed all three Book of Mormon edition texts (1830/1920/current) and the full KJV, via BYU-ODH's OpenScripture word-alignment dataset and Project Gutenberg #10. Built the 1830-vs-1920/current variant register (18,836 rows). Caught and corrected a real error along the way: Gutenberg's BoM text (#17) is the current copyrighted LDS wording, not 1920 as originally assumed — documented in `text/SOURCES.md` so it isn't reintroduced.
- **2026-09-05 (Sonnet), same day:** Named the project **Brass** (the plates of brass — Nephi's family's own name for the record of earlier scripture they carried and quoted). Forked Catena's reader: `lib/types.ts` extends Catena's `Echo` into the full `Link` schema from §3; `components/Reader.tsx` renders the provenance panel, KJV-specific/mediation badges, and "why not" block; `data/1-nephi.json` holds all 618 verses of 1 Nephi (22 chapters) with empty `links` arrays. Build is clean, dev server verified rendering both the home page and the reader. Home page lists all 15 books, 14 as placeholders. **Next (§8 step 3): the candidate-generation pipeline** — n-gram/fuzzy/semantic matching of 1 Nephi against the KJV, with Skousen's 36+83 quotations as the recall test.
- **2026-09-05 (Sonnet), continued:** Built `tools/find-candidates.py` — streams 1 (exact/rare n-gram) and 2 (fuzzy/ordered-word) of §4. Ran against 1 Nephi's 618 verses vs. all 31,102 KJV verses: 140,319 raw pairs share a 4-gram (`work/1-nephi/candidates-raw.jsonl`, gitignored — dominated by KJV-style formulaic phrases the Book of Mormon imitates throughout, not real borrowing), filtered by a rarity cutoff to **4,893 review candidates** (`work/1-nephi/candidates.jsonl`, committed) — within the plan's own "low thousands" expectation.

  **Validation:** the pipeline correctly surfaces the known Isaiah 48/49 quotation blocks at the top of the ranking (1 Nephi 20 ↔ Isaiah 48, 1 Nephi 21 ↔ Isaiah 49, up to 47 contiguous matched words) with no hint given — a strong correctness signal. It also catches one of Frederick's independently-published Pauline parallels (Romans 5:5 ↔ 1 Nephi 11:22) in both streams.

  **Real limitation found, not yet fixed:** two of Frederick's other parallels (Ephesians 6:16 ↔ 1 Nephi 15:24 "fiery darts"; 1 Corinthians 15:58 ↔ 1 Nephi 2:10 "steadfast... immovable") are missed by both streams — one because the shared run is only 3 words (below the 4-gram floor) and because the 1830 text spells it "firy" not "fiery"; the other because the KJV's own archaic wording ("stedfast, unmoveable") doesn't string-match the Book of Mormon's modernized synonyms ("steadfast... immovable") at all. This is exactly the gap stream 3 (semantic) and a historical-spelling normalization pass are for — not a bug in what's built, but evidence of what's still missing before the pipeline can claim full recall against the scholarship stream (§7 acceptance test).

  **Next:** either (a) stream 3 (semantic/embedding matching) to close the gap above, or (b) start adjudicating the 4,893-row candidate list chapter by chapter (§5) using streams 1-2 as-is, since 1 Nephi 20-21 (the Isaiah block) is already fully surfaced and ready for collation.

- **2026-09-05 (Opus), the Hardy walker rebuilt:** Bootstrapping 2 Nephi reported *0 Hardy rows to account for*. The apparatus is parsed per book and had never been run on 2 Nephi; the real figure is 120 citations across 99 verses. Running it exposed something worse than a missing parse — `audit-hardy.py` made 55 of the 120 rows suspect, in runs a whole chapter off, in both directions.

  **Cause:** the verse-walker used a page's running head only as a chapter-level resync, and applied it at the wrong end of the page. The head is in fact a dictionary-style guide ref — on a verso it names the page's FIRST verse, on a recto its LAST (verified against 2 Nephi pages 87 and 88) — so every page carries a hard checkpoint. The walker now takes it: a verso head resets the walk, a recto head checks it, and footnotes are keyed by the verses the page actually prints rather than by wherever the walk had got to. A re-parse now REPLACES a book's rows instead of merging over them, so a fixed walker cannot ship the previous run's ghosts.

  **Validation:** the rebuilt walker reproduces, from the page alone, all five verse corrections that had been found by hand and checked by a human (four in Jacob, one in 1 Nephi) — they are kept in `hardy-corrections.json` as no-ops for exactly that reason. 2 Nephi's chapter-shift suspects went 55 → 0; 1 Nephi and Jacob still pass every gate with 0 lint errors and 0 coverage gaps.

  **It also overturned two rulings made the same day.** 1 Nephi 22:26's Isaiah 49:22-26 row belongs at 21:26 (its note sits with 21:25-26 on the page, above chapter 22's opening verses), and Jacob 3:5's Genesis 22:1-18 row belongs at Jacob 4:5, where the offering of Isaac is named outright. Both had been reviewed and left in place on reasoning that was sound about what a study edition might do and wrong about what the page shows. The Jacob 3:5 figural link — which existed only because of that reference, and whose own `whyNot` named this exact condition — is withdrawn to the exclusion register; 1 Nephi 20:21 and 21:26 now carry the citations that were misfiled at 21:21 and 22:26. One genuine error in the printed apparatus turned up too: 2 Nephi 17:17's note cites "Isa 17.7" while quoting Isaiah 7:17's words, now repaired by a new `cite_fixes` list.

  **Next:** 2 Nephi is bootstrapped (33 chapters, 779 verses, 120 Hardy rows, 4 Frederick verses) and its apparatus is audited. Nineteen window-scan suspects remain, all of one shape — Nephi's exposition in chapters 25-30 cross-referencing Isaiah chapters he transcribes in 27 — and each is a row for the chapter pass to discharge, not a drift.

- **2026-09-05 (Opus), 2 Nephi complete:** 33 chapters, **682 links across 596 of 779 verses, 224 exclusions**, every one of Hardy's 120 rows discharged as a link or a reasoned exclusion (0 gaps), both gates clean on every chapter. Fifteen chapters were collated mechanically (7-8, 12-24); the eighteen hand chapters ran as dispatched Opus agents.

  **Rate, and Wilson's ruling.** The first seven chapters ran one agent per chapter and cost 160k tokens each against §9's estimate of 40-60k — the estimate came from 1 Nephi done in one sitting, where the conventions and worked examples are read once for 22 chapters, while a dispatched agent pays ~50k of start-up before it reads a verse. Wilson ruled on 2026-09-05: **three chapters to an agent** for the rest. The four batched agents came in at 53-81k per chapter, roughly a third of the per-chapter figure, and the batching bought something beyond price — a phrase argued in an agent's first chapter becomes a `recurrenceRefs` in its second, which is the rule (ADJUDICATING §4) that is hardest to apply across agent boundaries. Total for the book: ~2.3M.

  **Findings that carry the book:** Lehi's blessing is David's deathbed charge (1 Kings 2:1-4, eight words verbatim at 1:14); the Eden vocabulary of chapter 2 is Genesis 2-3 direct, with Paul supplying the frame and none of the words; Deuteronomy 18 reaches chapter 3 through Acts, decided on “raise up unto YOU” against “unto THEE”; the temple of chapter 5 is Bezalel's (Exodus 31:5) and not Solomon's, and 5:21's “a skin of blackness” has no KJV background whatever; “stiffened” is a King James hapax at 2 Chronicles 36:13, of Zedekiah, behind Jacob's 6:8-10; the baptism at 31:8 is Luke's on a single word (“the Holy Ghost descended”, where Matthew, Mark and John read “Spirit”); and Nephi's colophon claim, “what I have written”, is John 19:22 — Pilate refusing to amend the title on the cross.

  **Two results about the text's own transmission**, both from collating a quotation against this corpus's other copy of the same chapter rather than against the KJV alone: 2 Nephi 6 and 1 Nephi 21 are demonstrably NOT one text (6:16 agrees with 1 Nephi 21 in a reading found in no English Bible, while 6:18 restores a conjunction 1 Nephi 21:26 had dropped), whereas 2 Nephi 30 and the transcription at 21 ARE the same text, differing only in two connectives at the seam and one apostrophe. And at 28:14 the proximate source is internal: the KJV reads “the precept of men” (singular), this book's own 27:25 reads “precepts”, and 28:14, 28:26 and 28:31 all follow the plural.

  **Two gates repaired mid-run, both found by the agents using them.** `lint-adjudication.py` read the merged `data/<slug>.json`, which during a dispatched run is whatever another agent last applied — three agents had to build isolated trees to get a trustworthy gate; it now lints the chapter files directly. And `kjv-rarity.py` matched on whitespace alone, so a comma broke a phrase and produced FALSE SINGLETONS (“Holy Ghost and with fire” reported one verse because Matthew 3:11 has a comma where Luke 3:16 has none) — with the lint recomputing from a copy of the same code, so the gate would have certified the claim instead of catching it. Fixed, the lint now imports the matcher, and every rarity claim in the corpus was recomputed: 0 errors across all seven books.

  **Next:** Mosiah (`bootstrap-book.py` will refuse until Hardy is parsed for it — ADJUDICATING §0a), and, when Wilson wants it, an authored-prose pass over the fifteen collated Isaiah chapters, whose links are machine-noted and `citationsPending` as 1 Nephi 20-21's were before their notes were written.

- **2026-09-07 (Opus), Mosiah complete:** 29 chapters, **456 links across 369 of 785 verses, 246 exclusions**, all 30 of Hardy's rows discharged (0 gaps), both gates clean on every chapter. Chapter 14 (Isaiah 53) ran mechanically through `collate-isaiah.py`/`build-isaiah-adjudication.py`; the other 28 ran as ten dispatched Opus agents in nine three-chapter batches plus a solo chapter 29, all launched in parallel. Cost ~2.2M tokens.

  **Findings that carry the book:** Zeniff's people are cast as Israel in Egypt through Exodus 1's own vocabulary ("taskmasters," Mosiah 24:9); Limhi's temple sermon narrates Abinadi's trial in the words of Stephen's (Acts 7, across Mosiah 7); the seer discussion at 8:15 rests on the KJV's one verse that defines the word; Alma's conversion at 27:29 reaches past his own Damascus road to Simon Magus (Acts 8:23, "gall of bitterness"); Mosiah 29's abolition of kingship runs 1 Samuel 8 forward with the outcome reversed, on two KJV singletons ("voice of the people," "have a king"); and 25:24's "pour out my spirit" follows the Old Testament (Joel 2:28) against the New (Acts 2:17) on the one word `mediation-check.py` is built to ignore — the pronoun — caught only because an agent knew to look for it.

  **A genuine OT-vs-OT mediation case, new to the project:** Mosiah 13's Decalogue recital is decisively Exodus 20's wording against Deuteronomy 5's (six decisive points), which is a source choice between two Old Testament witnesses to the same text — a case CONVENTIONS §7 and the schema's `mediation` enum don't name, since both anticipate OT-vs-NT-vs-earlier-BoM. Recorded `direct-OT` with the Exodus/Deuteronomy argument carried in prose. Flagged because it will recur: 3 Nephi 12-14 raises the same problem against Matthew's and Luke's differing forms of the Sermon on the Mount.

  **Batching threw off a genuine duplicate, caught and fixed before merge:** two concurrent agents (chapters 1-3 and 4-6) each wrote a full link for "the Lord God Omnipotent" (Revelation 19:6, a KJV hapax) — one at its true first use, Mosiah 3:5, the other at 5:15 because chapter 3 hadn't landed yet when that agent started. Both agents caught it themselves and flagged it in their reports. Resolved by removing the 5:15 link, adding it to 3:5's `recurrenceRefs`, and filing a `better-source-identified` exclusion at 5:15 — the fix ADJUDICATING §4 already prescribes for a repeat within one book.

  **Two tool limitations found, not yet fixed:** `mediation-check.py`'s word-aligner reports a spurious `DECISIVE` verdict when the Book of Mormon *conflates* two candidate sources rather than substituting between them — it has nowhere to put the surplus words and credits one side (three false positives in chapters 1-3 alone, each caught and written up as a conflation rather than a decided mediation). And `kjv-rarity.py` matches substrings, not word boundaries, so a count for "rust" silently includes "thrust" and "trusted" — no false claims shipped because the auditing agent checked by hand, but the gate does not currently catch this class of error itself.

  **Open, for Wilson's ruling:**
  - **Mosiah 29:2 vs. 7:9, "voice of the people."** ADJUDICATING §4 says a repeated formula is adjudicated once, at first use, with later occurrences filed as exclusions pointing back. The chapter-29 agent kept a full second link anyway, arguing that 29:2 is the phrase *returning to the scene it came from* (1 Samuel 8) rather than the narrator reusing his own formula, and said so openly rather than defaulting. Left as written pending your call; reversing it is one deletion and one exclusion.
  - **Whether the exclusion register may hold "better-source-identified" cross-references between two accepted links**, not only rejected candidates. Two chapter-11 rows use it that way (11:14, 11:19); PLAN §5 defines the register as rejections only.
  - **A KJV singleton the corpus has never adjudicated:** "exceeding great joy" (Matthew 2:10) is used eleven times starting at 1 Nephi 8:12, which has no row for it — declined at Mosiah 21:24 under the first-use rule, but 1 Nephi 8 itself was adjudicated before this convention existed. Someone should decide it there.
  - **A source used three times across the book** without a single first-use consolidation: Jonah 3:8 stands as full links at 9:17 and 24:10 and as a route citation at 21:14. Individually defensible (9:17 and 24:10 are different narrators; 21:14 records a fulfillment, not a fresh borrowing) but worth a book-level glance before publication.
  - **Whether `variants` (schema field for 1830-vs-1920 readings) should ever be populated structurally.** No chapter file in the corpus uses it; every 1830-reading argument so far lives in prose inside `provenance`/`note`. At least four rows in Mosiah 26-28 alone would populate it if the field is wanted.

  **Next:** Nephi's line is now Book 1-2 plus Jacob/Enos/Jarom/Omni/Words of Mormon/Mosiah — seven books, 3,014 verses. Alma is next (63 chapters, by far the largest book) and, when Wilson wants it, an authored-prose pass over the collated Isaiah chapters still marked `citationsPending`.

- **2026-09-07 (Sonnet), the two flagged tool bugs fixed, and a corpus-wide correction they required.** `kjv-rarity.py` now anchors every query word at `\b` word boundaries — a rarity count was matching as a bare substring anywhere, so "rust" silently counted "thrust" and "trusted" and a claim like "occurs in exactly one KJV verse" could be true only because the tool couldn't tell "head" from "heads" or "way" from "ways". `mediation-check.py`'s decisiveness test (`distinguishes`) now requires that a content word not ALSO appear in the OTHER candidate's own verse, and needs only ONE distinguishing word rather than every word in the span — the first change stops difflib's local alignment from crediting one candidate with vocabulary both candidates share (`scourge`, Mark 10:34 vs Matthew 20:19), the second stops a real conflation of both sources from being hidden behind one candidate's irrelevant sentence tail (Mosiah 2:11's "might, mind, and strength" is Deuteronomy 6:5 AND Mark 12:30 at once; the old check missed Mark's contribution because Mark's diverging span also carried words — "this is the first commandment" — that are no part of the borrowing).

  **Fixing `kjv-rarity.py` invalidated 15 already-committed rarity claims across four books**, all of them counted too high by the old substring bug, none of them counted too low — 2 Nephi (6), Enos (1), Jacob (3), Mosiah (5). Re-verified each by hand against the actual KJV verse rather than trusting the new tool blind, since a second silent bug is exactly what that would risk. Two shapes recurred: a singular/plural mismatch counted as a match (`head`/`heads`, `way`/`ways`, `king's captain`/`king's captains`, `king`/`kingdom`), and a query using a deliberately truncated word stem that the new boundary anchor no longer permits (`iniquit` for `iniquity`/`iniquities`, restored to the whole word). In every case the corrected count is a *stronger* singleton than the false one claimed, not a weaker one, and each row's prose was rewritten to say so rather than just having its number swapped. Full corpus lint, which recomputes every claim from the fixed tool: 0 errors across all eight completed books.

  **Next:** Alma (§8), with both tools now trustworthy at that scale.

- **2026-09-07 (Opus), Alma 1-54 of 63 adjudicated, paused at Wilson's request.** Eighteen batched agents (three chapters each, three dispatch waves of six) produced **541 links across 484 verses**; both gates clean, 29 of Alma's 30 Hardy rows discharged (the last, 60:23, is in an unadjudicated chapter). Bootstrap found 0 chapter-shift drift and 4 window-scan suspects, all reviewed and confirmed correctly keyed (thematic/conceptual allusions the scoring underrates — documented in `hardy-corrections.json`'s `reviewed_not_drift`).

  Findings that carry the book so far: Amulek and Alma's Ammonihah trial narrated in the vocabulary of Jesus's own (10:13); Alma 12:33 decisively Hebrews 3:8 against Psalm 95:8 on the plural "hearts"; the Rameumptom (31:13) is Solomon's dedication scaffold (2 Chronicles 6:13) inverted, answered by 33:7's private-prayer reply to Matthew 6; Korihor's demand for "evidence" (30:15) negates Hebrews 11:1 term by term; Alma 36:11 resolves Acts's own contradiction about Saul's companions (9:7 vs 22:9) by taking the reading Mosiah 27:12's account did not; 42:2-3 is the fullest Genesis quotation in the book, with the 1830 text preserving a stranded pronoun 1920 silently repaired; and 44:9 stages 1 Samuel 17's armor-vs-God debate with the equipment swapped between armies.

  **Corrections and open items, not yet acted on:** PLAN §7's restated criterion ("Frederick's Alma 47 citations") is wrong — his Alma rows stop at 36:26, no Frederick citations fall in 45-49; needs a fix here once Alma closes. `mediation-check.py` returned a false DECISIVE verdict at 49:2 by matching a KJV noun against a Book-of-Mormon verb — worth a guard. Several within-book "second full link vs. register cross-reference" judgment calls are flagged in individual chapter reports (40:21, 42:27, 44:13, 48:13/48:24, and the Alma 3 tone question from the first wave) — none blocking, all worth a look at the book's close. **Remaining: chapters 55-63 (9 chapters, 3 more batches).**

- **2026-09-07 (Opus), Alma complete: all 63 chapters, 579 links across 519 verses, all 30 Hardy rows discharged.** Resumed and finished in one further dispatch — three batched agents covering 55-63, closing the largest single book in the corpus. Both gates clean on the merged book file (the same three pre-existing lint warnings, none new); `hardy-coverage.py` reports 30/30, 0 gaps, for the first time in the book's run. Total for Alma: 21 batched Opus agents across four dispatch waves, three chapters each.

  **Findings from the closing chapters:** 55:13's wine stratagem is narrated in Genesis 3:6's grammar of the first temptation; 56:46 takes Isaiah 8:10's war oracle ("God is with us") over Matthew 1:23's verbless Immanuel gloss; 57:21 fuses two Matthew 8-9 healing formulas ("according to their faith, it was done unto them") to report not one wounded soldier lost; 60:23 (the book's last Hardy row) fuses Matthew 23:26 and Luke 11:39's inward/outward saying, attributed to God and turned onto a legislature; 61:10-14 assembles a just-war doctrine from the two KJV verses that most plainly forbid one (Hebrews 12:4, Matthew 5:39); 62:50 reverses Judges 8:34's epitaph on a forgetful generation, whose own sequel — a usurper's murders once the deliverer dies — arrives on schedule at the start of Helaman; and 63:8's drowning is Matthew 18:6, a different hand and a different drowning from 1 Nephi 8:32.

  **Two tool bugs found in this batch, not yet fixed:** `mediation-check.py` can return a confident "decisive" verdict on a pair that is not actually a quotation relation at all (56:46 against Isaiah 8:10/Matthew 1:23 — the tool fuzzy-matched a phrase Alma doesn't contain), and separately returns "neither" on every point of comparison including one where the wording plainly resolves (62:50). Both need a look before the next book, alongside the 49:2 noun/verb false positive found earlier in the run.

  **Open, for Wilson's ruling before the book closes — the full list, gathered across all four waves:** the Alma 3 "skin curse" tone question (wave 1); whether Alma 5:24's three-source composite should be split; Alma 14:3's opposite-sense Matthew 1:19 link (wrong-sense candidate); Alma 17:36's uncited David/Goliath `status:majority`; whether within-book formula repeats like "made an end of speaking these words" should stop earning cross-book rows after their first use; two duplicate-source first-use pointers caught between concurrent agents (Romans 6:16/6:23 at 3:27 vs 5:42; Acts 5:4 at 11:25 vs 12:3); whether Hardy citations can coexist with `status:novel` (36:28, lint still warns); Alma 30:44's OT-via-NT call (pronoun vs. situation — could flip to direct-OT); whether 34:31 should move to a verse with closer verbal contact; 39:2's onomastic Jezebel/Isabel argument, a case CONVENTIONS doesn't squarely cover; a missing `mediation` value for an NT source reached through an earlier Book-of-Mormon passage (41:11); several full-link-vs-cross-reference calls at book-internal and book-boundary recurrences (40:21, 42:27, 44:13, 48:13/48:24, 58:40 vs 44:2, 63:8 vs 1 Nephi 8:32); and PLAN §7's Frederick/Alma-47 claim, confirmed wrong and still needing the fix here.

  **Next:** Helaman (16 chapters) — much smaller than Alma, and the next book in Nephi's line. Fix PLAN §7's Frederick claim and consider the two mediation-check.py bugs before dispatching.

- **2026-09-07 (Sonnet), the two flagged `mediation-check.py` bugs investigated and given a guard, not a suppression.** Reproduced both: Alma 56:46's spurious pairing of Isaiah 8:10 against Matthew 1:23, and Alma 49:2's of two unrelated "borders of the city" verses (1 Chronicles 7:29, Numbers 35:27), each threw a confident DECISIVE off one word ("forth", "city") that happens to sit in the Book of Mormon verse for unrelated reasons.

  **Why this can't be a mechanical filter.** Tried scoring the two candidates' overall shared vocabulary ("backbone") to gate DECISIVE on a threshold — the two false positives scored 0 and 1 shared words, against 3-7 for the pilot's confirmed OT-via-NT findings (Deuteronomy 18:15/Acts 3:22, Genesis 22:18/Acts 3:25). But Isaiah 40:3/Luke 3:5 — a textbook-genuine case, already in the corpus — also scores near 0, because Luke reorders Isaiah's clauses enough that no backbone survives the diff. A threshold that catches the false positives also catches a real one; there is no numeric cutoff that doesn't.

  **What the tool does instead:** every DECISIVE line now reports its backbone count and the actual words in it (`◀── DECISIVE (backbone: 1 other shared word(s) — city)`), always, unconditionally — evidence for the adjudicator to weigh, exactly the tool's existing philosophy ("it reports evidence, never a verdict"), rather than a gate that would need to be right every time or it silently hides a real finding. This is the honest stopping point: the actual discrimination between a real parallel and a coincidental collision is a judgment only a reader with the verse in view can make, which is why both instances were already caught and corrected by the agents that hit them, without this tool's help.

  **Next:** dispatch Helaman.


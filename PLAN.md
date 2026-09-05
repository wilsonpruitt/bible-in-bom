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
- `data/exclusions.json` — the exclusion register: every tempting parallel rejected, with the reason. This is what makes "definitive" defensible.
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
`hardy-coverage.py`. New data: `isaiah-collation.json`. Schema addition:
`Link.recurrenceRefs`.

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
3. ⛔ **Cannot be checked.** Frederick is not on disk (CONVENTIONS §6 says we
   hold him; we do not). The Revelation network in 11-14 IS catalogued — 11:34
   and 13:26 and 14:10-11 are the spine of it — but against Revelation itself,
   not against Frederick. This is the one acceptance criterion the pilot fails,
   and it fails for want of a book, not for want of work.
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

## 11. Progress log
- **2026-09-05 (Sonnet):** Acquired and reconstructed all three Book of Mormon edition texts (1830/1920/current) and the full KJV, via BYU-ODH's OpenScripture word-alignment dataset and Project Gutenberg #10. Built the 1830-vs-1920/current variant register (18,836 rows). Caught and corrected a real error along the way: Gutenberg's BoM text (#17) is the current copyrighted LDS wording, not 1920 as originally assumed — documented in `text/SOURCES.md` so it isn't reintroduced.
- **2026-09-05 (Sonnet), same day:** Named the project **Brass** (the plates of brass — Nephi's family's own name for the record of earlier scripture they carried and quoted). Forked Catena's reader: `lib/types.ts` extends Catena's `Echo` into the full `Link` schema from §3; `components/Reader.tsx` renders the provenance panel, KJV-specific/mediation badges, and "why not" block; `data/1-nephi.json` holds all 618 verses of 1 Nephi (22 chapters) with empty `links` arrays. Build is clean, dev server verified rendering both the home page and the reader. Home page lists all 15 books, 14 as placeholders. **Next (§8 step 3): the candidate-generation pipeline** — n-gram/fuzzy/semantic matching of 1 Nephi against the KJV, with Skousen's 36+83 quotations as the recall test.
- **2026-09-05 (Sonnet), continued:** Built `tools/find-candidates.py` — streams 1 (exact/rare n-gram) and 2 (fuzzy/ordered-word) of §4. Ran against 1 Nephi's 618 verses vs. all 31,102 KJV verses: 140,319 raw pairs share a 4-gram (`work/1-nephi/candidates-raw.jsonl`, gitignored — dominated by KJV-style formulaic phrases the Book of Mormon imitates throughout, not real borrowing), filtered by a rarity cutoff to **4,893 review candidates** (`work/1-nephi/candidates.jsonl`, committed) — within the plan's own "low thousands" expectation.

  **Validation:** the pipeline correctly surfaces the known Isaiah 48/49 quotation blocks at the top of the ranking (1 Nephi 20 ↔ Isaiah 48, 1 Nephi 21 ↔ Isaiah 49, up to 47 contiguous matched words) with no hint given — a strong correctness signal. It also catches one of Frederick's independently-published Pauline parallels (Romans 5:5 ↔ 1 Nephi 11:22) in both streams.

  **Real limitation found, not yet fixed:** two of Frederick's other parallels (Ephesians 6:16 ↔ 1 Nephi 15:24 "fiery darts"; 1 Corinthians 15:58 ↔ 1 Nephi 2:10 "steadfast... immovable") are missed by both streams — one because the shared run is only 3 words (below the 4-gram floor) and because the 1830 text spells it "firy" not "fiery"; the other because the KJV's own archaic wording ("stedfast, unmoveable") doesn't string-match the Book of Mormon's modernized synonyms ("steadfast... immovable") at all. This is exactly the gap stream 3 (semantic) and a historical-spelling normalization pass are for — not a bug in what's built, but evidence of what's still missing before the pipeline can claim full recall against the scholarship stream (§7 acceptance test).

  **Next:** either (a) stream 3 (semantic/embedding matching) to close the gap above, or (b) start adjudicating the 4,893-row candidate list chapter by chapter (§5) using streams 1-2 as-is, since 1 Nephi 20-21 (the Isaiah block) is already fully surfaced and ready for collation.

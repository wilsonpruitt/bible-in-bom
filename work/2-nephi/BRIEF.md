# 2 Nephi: the run brief

Read this after `CONVENTIONS.md` and `ADJUDICATING.md`. It says only what is
particular to this book and this dispatch. Everything else stands.

## What is already done, and must not be redone

Fifteen chapters of 2 Nephi are continuous transcription and have been collated
mechanically: **7-8 (Isaiah 50, 51:1-52:2) and 12-24 (Isaiah 2-14)**. Their
files exist in `work/2-nephi/adjudicated/`, one Link per verse, departures in
the note. Do not touch them.

The eighteen hand chapters are **1, 2, 3, 4, 5, 6, 9, 10, 11, 25, 26, 27, 28,
29, 30, 31, 32, 33**. One agent per chapter.

Three of them quote Isaiah at length and are still hand chapters, because the
argument in an exposition is what the expositor does with the text:

- **6** — Jacob quotes Isaiah 49:22-26 (and 50:1-52:2 runs on into chapters 7-8).
  Where he quotes, the wording is the finding; where he glosses, the gloss is.
- **27** — an expansion of Isaiah 29, not a transcription of it. Whole verses
  have no KJV counterpart and others carry Isaiah's words inside new sentences.
  Collate by eye against Isaiah 29 before you judge any verse.
- **30** — quotes Isaiah 11:4-9 inside Nephi's own prophecy. Note that 2 Nephi
  21 already transcribes Isaiah 11 in full: this is the same chapter re-entering
  in a different frame, so give the link and point `recurrenceRefs` at 21.

## Your dossier is already built

`work/2-nephi/dossier-ch<N>.md` — do not regenerate it. Read the chapter cold
first anyway (ADJUDICATING §1.2); the dossier's candidate list is a recall
floor, not a ranking.

## Exclusions go in your own file

**Do not append to `data/exclusions.json`.** Eighteen agents are running at once
and would overwrite each other. Write your chapter's exclusions to

    work/2-nephi/exclusions/ch<NN>.json

as a JSON array of exclusion objects in the same shape as the entries in
`data/exclusions.json` (`bomRef`, `source`, `category`, `sharedText`, `streams`,
`reason`). The dispatching session merges them. Do not edit any file in `data/`.

## The apparatus, and one warning about it

`data/hardy-refs.json` and `data/frederick-refs.json` are the only sources you
may attribute anything to. Frederick touches four verses in this whole book —
9:23, 9:24, 25:16, 25:19 — and he argues about the Gospel of John; he proposes
almost no sources.

Hardy's rows for 2 Nephi were re-keyed on 2026-09-05 after his verse-walker was
rebuilt (ADJUDICATING §0a). `tools/audit-hardy.py 2-nephi` still reports
nineteen rows whose keyed verse has little verbal contact with the passage
cited. They are nearly all one shape — **Nephi's exposition in 25-30
cross-referencing Isaiah chapters he transcribes elsewhere in the book**, e.g.
28:14 citing Isaiah 29:13 when the transcription of that verse is at 27:25.
That is a study edition doing its job, not drift. Discharge such a row the way
§6a says: our link goes where our evidence is, and the register or a
`recurrenceRefs` sends the reader to his verse. If you find one that looks like
real drift — the verse number preserved, the chapter wrong — say so in your
report with both verses quoted, and do NOT move it yourself.

## Gates

```bash
python3.11 tools/apply-adjudication.py 2-nephi --check
python3.11 tools/lint-adjudication.py 2-nephi --chapter <N>
```

Both must return zero errors before you report. `hardy-coverage.py` runs after
the merge, not per chapter — but every Hardy row keyed to your chapter must end
as a link or as an exclusion you wrote, so account for them all.

## Multi-chapter passes (the second batch)

Chapters 1-6 and 9 were done one agent per chapter, at 160k tokens each,
because a dispatched agent pays its whole start-up — conventions, runbook,
schema, worked examples — before it reads a verse. Wilson's ruling, 2026-09-05:
**the rest of 2 Nephi runs three chapters to an agent.** Read once, adjudicate
three.

If you have been given several chapters:

- **Do them in order, and finish one before starting the next.** One file per
  chapter, `ch<NN>.json`, and one exclusion file per chapter. Never one file for
  the batch.
- **Run both gates after each chapter**, not once at the end, so a fault is
  found next to the chapter that caused it.
- **Do not let the chapters bleed.** A phrase adjudicated in the first of your
  chapters is a `recurrenceRefs` back to it in the second, not a fresh argument
  (ADJUDICATING §4). That rule is easier to apply well with three chapters in
  one head, which is part of why the batch is shaped this way.
- **Report per chapter**, in the same form as before, and keep the whole report
  under 25 lines even when it covers three chapters.

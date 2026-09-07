// Brass — the intertextual lens for the Book of Mormon as a biblical intertext.
// Forked from Catena (~/catena); the schema here is Catena's `Echo` extended
// per PLAN.md §3 with what a critical catalogue needs beyond a reading lens:
// a subtype under each of the four display types, confidence decoupled from
// type (5 levels, not 3), evidence subscores, KJV-specificity, textual
// mediation, an exclusion-style "why not" for contested links, bibliography,
// and which candidate stream(s) surfaced it.

export type LinkType = "quotation" | "allusion" | "echo" | "figural";

export type LinkSubtype =
  | "explicit" | "extended" | "close-verbal"      // quotation
  | "paraphrase" | "strong-verbal" | "conceptual"  // allusion
  | "probable" | "possible"                        // echo
  | "type-scene" | "structural";                   // figural

export type Confidence = "certain" | "high" | "moderate" | "low" | "contested";

export type Mediation =
  | "direct-OT"        // Book of Mormon depends on the Old Testament text directly
  | "direct-NT"        // depends on a New Testament text directly (no OT intermediary)
  | "OT-via-NT"        // an OT source reused, but via its NT quotation/echo
  | "OT-via-earlier-BoM" // an earlier Book of Mormon quotation of an OT source is the proximate model
  | "NT-via-earlier-BoM" // an earlier Book of Mormon quotation of an NT source is the proximate model
  | "uncertain";

// A reworking of Richard Hays's seven criteria for testing claims about
// scriptural echo (Echoes of Scripture in the Letters of Paul, 1989, 29-32).
// See CONVENTIONS.md §3a for the mapping, including why Hays's first criterion
// — availability — inverts for this corpus rather than applying.
export type EvidenceScores = {
  vocabulary: number;   // 0-5  ┐
  syntax: number;       // 0-5  ├ Hays's "volume"
  sequence: number;     // 0-5  ┘
  rarity: number;       // 0-5  — volume's second half: distinctiveness of the precursor
  context: number;      // 0-5  — Hays's "thematic coherence"
  attestation: number;  // 0-5  — Hays's "history of interpretation"; never a negative test
  // Hays's "recurrence": how often this source is used elsewhere in the Book of
  // Mormon. Optional because it is only meaningful once enough of the corpus is
  // adjudicated to count against; backfill mechanically rather than guessing.
  recurrence?: number;  // 0-5
};

export type Provenance = {
  mt?: string;           // Masoretic Text reading, where it diverges materially from KJV
  lxx?: string;          // Septuagint reading, where the Greek diverges from KJV/MT
  other?: string;        // another English Bible reading worth showing
  route: string;         // e.g. "Isaiah → KJV → Book of Mormon"
  alternative?: string;  // a plausible competing route
  significance: string;  // why the route matters — the KJV-specific claim in prose
};

export type CandidateStream = "scholarship" | "machine-ngram" | "machine-fuzzy" | "machine-semantic" | "manual";

export type LinkStatus = "consensus" | "majority" | "minority" | "novel" | "rejected";

export type Link = {
  source: string;              // KJV reference, e.g. "Isaiah 53:5"
  type: LinkType;
  subtype?: LinkSubtype;
  confidence: Confidence;
  text: string;                // the KJV source text
  evidence?: EvidenceScores;
  kjvSpecific?: "yes" | "no" | "uncertain";
  mediation?: Mediation;
  composite?: string[];        // other sources fused into the same phrase
  // Where this source, or the formula it supplies, recurs elsewhere in the Book
  // of Mormon — Hays's "recurrence" criterion at the level of the individual
  // link, as against the 0-5 score in EvidenceScores, which is a magnitude.
  // Refs are Book of Mormon citations, e.g. "1 Nephi 20:18". Added on the
  // chapter 2 adjudication; not yet rendered (PLAN.md §6 is Sonnet work).
  recurrenceRefs?: string[];
  provenance?: Provenance;
  note: string;                 // the argument FOR this link
  whyNot?: string;              // the counter-evidence — expected when confidence is "low" or "contested"
  bibliography?: string[];      // e.g. "Hardy 2023: 871", "Skousen KJQ: #12"
  status?: LinkStatus;
  // TRUE when `status` records the adjudicator's read of where this link sits in
  // the field, but no citation has yet been verified against a source we hold.
  // The scholarship stream (PLAN.md §4.4) has not been run: Hardy 2023 and
  // Frederick are not on disk, and Skousen's KJQ list is unobtainable (§4.1).
  // Marking these is what keeps `status: "consensus"` from being an unsourced
  // assertion and stops us from padding `bibliography` with citations we cannot
  // check. Every such row needs a real citation before the volume can call
  // itself definitive (§7.5).
  citationsPending?: boolean;
  streams?: CandidateStream[];  // how the candidate was found
  altSource?: string;           // a parallel/alternative precursor
  contested?: boolean;          // renders a trailing "?" chip — kept for the visual grammar
};

export type Pericope = {
  id: string;
  ch: number;
  ref: string;
  text: string;      // Book of Mormon text, 1830 wording (see text/SOURCES.md)
  links: Link[];
  marker?: string;
};

export type Book = {
  slug: string;
  name: string;
  subtitle?: string;
  translation: string;   // edition note for the running text, e.g. "1830 first edition"
  pericopes: Pericope[];
  howToRead?: string;
  chapterSections?: { label: string; from: number; to: number }[];
};

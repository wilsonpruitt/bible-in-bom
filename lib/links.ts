import type { LinkType, Confidence, Link } from "./types";

// House palette — Wroot Press cream + ink. Brass takes its own accent: the
// warm metal tone of "the plates of brass," Nephi's name for the record of
// earlier scripture his family carries and quotes throughout — sibling to
// Catena's oxblood, Loci's gold, Topographia's map-blue.
export const ACCENT = "#8a6b1f";

// The chip's visual grammar encodes the *kind* of link; its ink encodes
// *confidence*. Border style is the type's signature: solid quotation, dashed
// allusion, dotted echo. Figural reuse (no verbal borrowing) is marked by the
// ◇ glyph rather than a border style.
export const TYPE_META: Record<
  LinkType,
  { label: string; glyph: string; borderStyle: "solid" | "dashed" | "dotted"; desc: string }
> = {
  quotation: {
    label: "Quotation",
    glyph: "",
    borderStyle: "solid",
    desc: "Explicit or close verbal quotation of the KJV text.",
  },
  allusion: {
    label: "Allusion",
    glyph: "",
    borderStyle: "dashed",
    desc: "Strong intentional verbal or conceptual reuse, without a citation formula.",
  },
  echo: {
    label: "Echo",
    glyph: "",
    borderStyle: "dotted",
    desc: "A probable or possible verbal resonance — can be quite certain while being less verbally explicit than a quotation.",
  },
  figural: {
    label: "Figural",
    glyph: "◇",
    borderStyle: "solid",
    desc: "A narrative or type-scene correspondence without significant shared wording.",
  },
};

export const ORDER: LinkType[] = ["quotation", "allusion", "echo", "figural"];

// Confidence is decoupled from type — an echo can be quite certain while
// being less verbally explicit than a quotation. Five levels, not three.
export const CONFIDENCE_INK: Record<Confidence, string> = {
  certain: "#5c4813",
  high: "#8a6b1f",
  moderate: "#a68a3f",
  low: "#c2b07a",
  contested: "#b0523f",
};

export const CONFIDENCE_LABEL: Record<Confidence, string> = {
  certain: "Certain",
  high: "High confidence",
  moderate: "Moderate confidence",
  low: "Low confidence",
  contested: "Contested",
};

export const MEDIATION_LABEL: Record<string, string> = {
  "direct-OT": "Direct from the Old Testament",
  "direct-NT": "Direct from the New Testament",
  "OT-via-NT": "Old Testament, mediated through the New Testament",
  "OT-via-earlier-BoM": "Mediated through an earlier Book of Mormon quotation",
  uncertain: "Mediation uncertain",
};

// Reduce a source reference to its book name, for the "biblical books
// echoed" filter — same collapse rule as Catena's sourceBook().
export function sourceBook(source: string): string {
  return source.replace(/\s+\d.*$/u, "").trim() || source;
}

export function chipLabel(l: Link): string {
  const g = TYPE_META[l.type].glyph;
  return `${g ? g + " " : ""}${l.source}${l.contested || l.confidence === "contested" ? " ?" : ""}`;
}

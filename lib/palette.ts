/**
 * Brass — the single source of truth for colour.
 *
 * The fork inherited Catena's sepia palette, in which every value was written
 * as a raw hex literal at some sixty sites across three files. That made a
 * palette change a find-and-replace and a palette *iteration* impossible, so
 * the values live here now and the components reference them.
 *
 * Revised 2026-09-05 (brighter, at Wilson's request). The move is to lift the
 * grounds toward white and let the brass supply the colour, rather than
 * tinting everything and ending up muddy. Two rules held the revision honest:
 *
 *  1. INK STAYS DARK. Body text and the accent are load-bearing for contrast
 *     against a page that is now much lighter, so `ink` went slightly deeper
 *     and `accent` gained saturation without gaining lightness. Brightening
 *     the accent itself would have cost roughly 1.5:1 of contrast ratio.
 *  2. The bright feeling comes from `page`, `panel`, `rule` and the accent
 *     washes — the large areas — not from the text.
 */

export const P: Record<string, string> = {
  // Grounds, lightest first.
  panel: "#ffffff",      // insets, source panels, the select
  page: "#fbf8f1",       // the page itself — was #f5f0e8
  fill: "#f6f1e6",       // soft blocks — was #eee9df
  band: "#33291a",       // the dark header band — was #2c2418, warmed
  inkStrong: "#332a1c",  // emphatic text (titles, verse refs) — same weight as `band`, different job

  // Ink.
  ink: "#3b3126",        // body text — was #4a3d30, deepened for the lighter page
  inkSoft: "#6a5c4b",    // secondary prose — was #6b5d4e
  inkMuted: "#7d6e5a",   // labels, counts — was #8a7a6a
  inkFaint: "#a2917c",   // disabled, deselected — was #a09080 / #a89a86 / #a08c78
  inkGhost: "#bdb09a",   // faded-out chapters — was #c8bfae

  // Rules and edges.
  rule: "#e4dac6",       // section rules — was #d4c9b5
  edge: "#d7c8a6",       // button borders — was #c9b99a
  edgeFaint: "#efe8d9",  // faded borders — was #e8e0d0 / #e0d8c5

  // Brass.
  accent: "#96731a",     // the working accent — was #8a6b1f, more saturated
  accentOnBand: "#e6c775", // gold on the dark band — was #d4b463, brighter
  accentSoft: "#c2b07a",

  // Accent washes, in ascending weight.
  wash05: "rgba(150,115,26,0.06)",
  wash07: "rgba(150,115,26,0.08)",
  wash08: "rgba(150,115,26,0.09)",
  wash10: "rgba(150,115,26,0.12)",
  wash13: "rgba(150,115,26,0.16)",
  wash25: "rgba(150,115,26,0.28)",

  // Contested / counter-evidence reds.
  warn: "#b0523f",
  warnSoft: "#d4a89a",
  warnDeep: "#8a5a4e",
  neutral: "#b09a86",
  paperShade: "rgba(122,110,90,0.05)",
};

/**
 * The confidence ramp. Darkest ink is the most certain link, so the reader can
 * see how sure the catalogue is without reading a label. Brightened with the
 * rest of the palette, but the top of the ramp stays deep: a `certain` link
 * should look settled, and settled means dark.
 */
export const INK = {
  certain: "#63500f",
  high: P.accent,
  moderate: "#b0913c",
  low: "#c9b478",
  contested: P.warn,
};

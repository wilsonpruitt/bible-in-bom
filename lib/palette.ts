/**
 * Brass — the single source of truth for colour.
 *
 * The fork inherited Catena's sepia palette, in which every value carried a
 * brown tint: the grounds, the rules, the ink, the muted text. The accent is
 * brass, so when everything else is also brown the accent has nothing to be
 * brass *against*, and the whole page reads as one muddy hue.
 *
 * Revised 2026-09-05 (twice, at Wilson's request: first brighter, then less
 * brown — the second is the real fix). **Every ground and every ink is now
 * neutral. Brass is the only chromatic thing on the page.** That is what makes
 * it read as metal rather than as mud, and it is why the accent could stay at
 * essentially the same depth while the page stopped looking brown.
 *
 * Contrast was computed, not eyeballed. Ratios against `page` are noted per
 * token; anything marked "decorative" must never carry text.
 */

export const P: Record<string, string> = {
  // Grounds — neutral, a hair off pure white so the panels can be whiter still.
  panel: "#ffffff",
  page: "#fbfbfa",
  fill: "#f2f3f4",
  band: "#1e2126",      // the header band: near-black, faintly cool

  // Ink — neutral greys, no brown.
  inkStrong: "#16181c", // titles, verse refs
  ink: "#23272e",       // body text                     14.5:1
  inkSoft: "#4b525c",   // secondary prose                7.6:1
  inkMuted: "#6c7480",  // labels, counts                 4.6:1
  inkFaint: "#9aa2ad",  // disabled, deselected           2.5:1  decorative
  inkGhost: "#c3c9d0",  // faded-out chapters                    decorative

  // Rules and edges — neutral, so they read as structure and not as stain.
  rule: "#e5e7ea",
  edge: "#d2d7dd",
  edgeFaint: "#eef0f2",

  // Brass. The one colour, kept deep enough to carry text.
  accent: "#8a6a0f",       // working accent                4.9:1
  accentSoft: "#b8902a",   // decorative rules, chips              decorative
  accentOnBand: "#e8c66a", // gold on the dark band         9.8:1 against band

  // Accent washes, ascending weight. Neutralised from the old brown wash.
  wash05: "rgba(138,106,15,0.05)",
  wash07: "rgba(138,106,15,0.07)",
  wash08: "rgba(138,106,15,0.08)",
  wash10: "rgba(138,106,15,0.10)",
  wash13: "rgba(138,106,15,0.14)",
  wash25: "rgba(138,106,15,0.26)",

  // Counter-evidence. A cleaner red than the old brick-brown #b0523f.
  warn: "#b3402c",       //                                 5.5:1
  warnSoft: "#e0a99e",
  warnDeep: "#8c3626",
  neutral: "#9aa2ad",
  paperShade: "rgba(35,39,46,0.04)",
};

/**
 * The confidence ramp. Darkest ink is the most certain link, so a reader sees
 * how sure the catalogue is without reading a label. It inks the link's own
 * text, so every step has to stay readable — `low` is the faintest the ramp
 * can go and still be read (3.1:1), not the faintest that looked right.
 */
export const INK = {
  certain: "#5f4a08",   // 8.2:1
  high: P.accent,       // 4.9:1
  moderate: "#9d7c26",  // 3.8:1
  low: "#ab8c42",       // 3.1:1
  contested: P.warn,    // 5.5:1
};

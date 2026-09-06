"use client";

import { P } from "@/lib/palette";
import { useState, useMemo, useEffect, type CSSProperties } from "react";
import Link from "next/link";
import type { Book, Link as LinkT, LinkType } from "@/lib/types";
import {
  TYPE_META,
  ORDER,
  CONFIDENCE_INK,
  CONFIDENCE_LABEL,
  MEDIATION_LABEL,
  sourceBook,
  ACCENT,
} from "@/lib/links";

const FONT_URL =
  "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Crimson+Pro:ital,wght@0,300;0,400;0,500;1,300;1,400&display=swap";

export default function Reader({ book }: { book: Book }) {
  const [activeTypes, setActiveTypes] = useState<Set<LinkType>>(new Set());
  const [activeSource, setActiveSource] = useState<string | null>(null);
  const [activeChapter, setActiveChapter] = useState<number | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [legendOpen, setLegendOpen] = useState(true);
  const [flashId, setFlashId] = useState<string | null>(null);

  useEffect(() => {
    if (!document.getElementById("brass-fonts")) {
      const l = document.createElement("link");
      l.id = "brass-fonts";
      l.rel = "stylesheet";
      l.href = FONT_URL;
      document.head.appendChild(l);
    }
  }, []);

  // Deep link from Index Fontium: /[book]#p-<id> scrolls to and flags a passage.
  useEffect(() => {
    const hash = window.location.hash;
    if (!hash.startsWith("#p-")) return;
    const pid = hash.slice(3);
    setFlashId(pid);
    const raf = requestAnimationFrame(() =>
      document.getElementById("p-" + pid)?.scrollIntoView({ behavior: "smooth", block: "center" })
    );
    const clear = setTimeout(() => setFlashId(null), 2600);
    return () => {
      cancelAnimationFrame(raf);
      clearTimeout(clear);
    };
  }, []);

  // A chapter change is a navigation, so start the new chapter at its top.
  const goToChapter = (ch: number | null) => {
    setActiveChapter(ch);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const toggleType = (t: LinkType) =>
    setActiveTypes((prev) => {
      const n = new Set(prev);
      if (n.has(t)) n.delete(t);
      else n.add(t);
      return n;
    });

  const toggleExpand = (key: string) =>
    setExpanded((prev) => {
      const n = new Set(prev);
      if (n.has(key)) n.delete(key);
      else n.add(key);
      return n;
    });

  const matchLink = (e: LinkT): boolean =>
    (activeTypes.size === 0 || activeTypes.has(e.type)) &&
    (activeSource === null || sourceBook(e.source) === activeSource);

  const filtersActive = activeTypes.size > 0 || activeSource !== null;

  // Counts for the type legend.
  const typeCounts = useMemo(() => {
    const c: Record<LinkType, number> = {
      quotation: 0,
      allusion: 0,
      echo: 0,
      figural: 0,
    };
    book.pericopes.forEach((p) => p.links.forEach((e) => (c[e.type] += 1)));
    return c;
  }, [book]);

  // Books echoed, by frequency.
  const sourceCounts = useMemo(() => {
    const map = new Map<string, number>();
    book.pericopes.forEach((p) =>
      p.links.forEach((e) => {
        const b = sourceBook(e.source);
        map.set(b, (map.get(b) ?? 0) + 1);
      })
    );
    return [...map.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  }, [book]);

  const chapters = useMemo(
    () => [...new Set(book.pericopes.map((p) => p.ch))].sort((a, b) => a - b),
    [book]
  );

  // Chapter-at-a-time reading. With no chapter selected the whole book is shown,
  // so "next" starts at the first chapter and "previous" is unavailable.
  const chIndex = activeChapter === null ? -1 : chapters.indexOf(activeChapter);
  const prevChapter = chIndex > 0 ? chapters[chIndex - 1] : null;
  const nextChapter =
    chIndex === -1 ? chapters[0] ?? null
    : chIndex < chapters.length - 1 ? chapters[chIndex + 1]
    : null;

  // Chapters that contain a matching echo (for the sidebar grid tint).
  const matchingChapters = useMemo(() => {
    if (!filtersActive) return null;
    const set = new Set<number>();
    book.pericopes.forEach((p) => {
      if (p.links.some(matchLink)) set.add(p.ch);
    });
    return set;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [book, activeTypes, activeSource]);

  const visiblePassages = useMemo(() => {
    let p = book.pericopes.filter((x) => x.text.length > 0);
    if (activeChapter !== null) p = p.filter((x) => x.ch === activeChapter);
    return p;
  }, [book, activeChapter]);

  const grouped = useMemo(() => {
    const map: Record<number, typeof book.pericopes> = {};
    visiblePassages.forEach((p) => {
      if (!map[p.ch]) map[p.ch] = [];
      map[p.ch].push(p);
    });
    return Object.entries(map).sort(([a], [b]) => +a - +b);
  }, [visiblePassages, book.pericopes]);

  const chapterHeading = (ref: string): string => {
    const prefix = ref.split(":")[0];
    return /^\d+$/.test(prefix) ? `Chapter ${prefix}` : prefix;
  };

  const clearFilters = () => {
    setActiveTypes(new Set());
    setActiveSource(null);
  };

  return (
    <div style={S.root}>
      <style>{`
        .brass-passage:hover { background: ${P.wash05} !important; }
        .brass-home-link:hover { color: ${P.page} !important; }
        .brass-type-btn:hover { transform: translateX(1px); }
        .brass-ch-btn:hover { background: ${P.wash10} !important; }
        .brass-chip:hover { background: ${P.wash10} !important; }
        @media (max-width: 800px) {
          .brass-layout { flex-direction: column !important; }
          .brass-sidebar { position: relative !important; width: 100% !important; max-height: none !important; border-right: none !important; border-bottom: 1px solid ${P.rule} !important; }
          .brass-main { padding: 20px 16px !important; }
          .brass-prow { flex-direction: column !important; gap: 12px !important; }
          .brass-margin { width: 100% !important; flex-direction: row !important; flex-wrap: wrap !important; align-items: center !important; padding-top: 0 !important; }
        }
      `}</style>

      <header style={S.header}>
        <Link href="/" className="brass-home-link" style={S.homeLink}>
          ← BRASS
        </Link>
        <div style={S.headerOrnament}>⚒ ⚒ ⚒</div>
        <h1 style={S.title}>{book.name.toUpperCase()}</h1>
        <div style={S.titleRule} />
        {book.subtitle && <p style={S.subtitle}>{book.subtitle}</p>}
        <p style={S.credit}>{book.translation}</p>
      </header>

      <div className="brass-layout" style={S.layout}>
        <aside className="brass-sidebar" style={S.sidebar}>
          <div style={S.chapterNavTop}>
            <div style={S.sectionLabel}>Read a chapter</div>
            <div style={S.chapterGrid}>
              {chapters.map((ch) => {
                const isActive = activeChapter === ch;
                const matches = matchingChapters === null || matchingChapters.has(ch);
                const faded = matchingChapters !== null && !matches;
                let bg = "transparent";
                let color = P.ink;
                let borderColor = P.edge;
                if (isActive) {
                  bg = ACCENT;
                  color = P.page;
                  borderColor = ACCENT;
                } else if (faded) {
                  color = P.inkGhost;
                  borderColor = P.edgeFaint;
                } else if (matchingChapters !== null && matches) {
                  bg = P.wash10;
                  color = ACCENT;
                  borderColor = ACCENT;
                }
                return (
                  <button
                    key={ch}
                    className="brass-ch-btn"
                    onClick={() => goToChapter(isActive ? null : ch)}
                    style={{
                      ...S.chBtn,
                      background: bg,
                      color,
                      borderColor,
                      opacity: faded ? 0.5 : 1,
                    }}
                  >
                    {ch}
                  </button>
                );
              })}
            </div>
            {activeChapter && (
              <button onClick={() => goToChapter(null)} style={S.clearBtn}>
                Show all chapters
              </button>
            )}
          </div>

          <button onClick={() => setLegendOpen(!legendOpen)} style={S.legendToggle}>
            {legendOpen ? "▾" : "▸"} Kinds of Links
          </button>

          {legendOpen && (
            <div style={S.typeList}>
              {ORDER.map((t) => {
                const meta = TYPE_META[t];
                const active = activeTypes.has(t);
                return (
                  <button
                    key={t}
                    className="brass-type-btn"
                    onClick={() => toggleType(t)}
                    style={{
                      ...S.typeBtn,
                      background: active ? P.wash10 : "transparent",
                      borderLeft: `4px solid ${active ? ACCENT : "transparent"}`,
                      fontWeight: active ? 600 : 400,
                    }}
                    title={meta.desc}
                  >
                    <span style={S.chipPreviewWrap}>
                      <span
                        style={{
                          ...S.chipPreview,
                          border: `1.5px ${meta.borderStyle} ${ACCENT}`,
                        }}
                      >
                        {meta.glyph || "Aa"}
                      </span>
                    </span>
                    <span style={{ flex: 1, color: active ? ACCENT : P.ink }}>
                      {meta.label}
                    </span>
                    <span style={S.typeCount}>{typeCounts[t]}</span>
                  </button>
                );
              })}
            </div>
          )}

          <div style={S.sourceSection}>
            <div style={S.sectionLabel}>Source books</div>
            <div style={S.sourceList}>
              {sourceCounts.map(([b, count]) => {
                const active = activeSource === b;
                return (
                  <button
                    key={b}
                    className="brass-type-btn"
                    onClick={() => setActiveSource(active ? null : b)}
                    style={{
                      ...S.sourceBtn,
                      background: active ? P.wash10 : "transparent",
                      borderLeft: `3px solid ${active ? ACCENT : "transparent"}`,
                      color: active ? ACCENT : P.ink,
                      fontWeight: active ? 600 : 400,
                    }}
                  >
                    <span style={{ flex: 1 }}>{b}</span>
                    <span style={S.typeCount}>{count}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {filtersActive && (
            <button onClick={clearFilters} style={S.clearBtn}>
              Clear filters
            </button>
          )}


          {book.howToRead && <div style={S.howTo}>{book.howToRead}</div>}
        </aside>

        <main className="brass-main" style={S.main}>
          <nav style={S.chapterBar} aria-label="Chapter navigation">
            <button
              className="brass-chip"
              onClick={() => goToChapter(prevChapter)}
              disabled={prevChapter === null}
              style={{ ...S.chapterBarBtn, opacity: prevChapter === null ? 0.3 : 1,
                       cursor: prevChapter === null ? "default" : "pointer" }}
            >
              ← {prevChapter === null ? "" : `Chapter ${prevChapter}`}
            </button>

            <label style={S.chapterBarCentre}>
              <select
                value={activeChapter ?? "all"}
                onChange={(e) =>
                  goToChapter(e.target.value === "all" ? null : Number(e.target.value))
                }
                style={S.chapterSelect}
              >
                <option value="all">All {chapters.length} chapters</option>
                {chapters.map((ch) => (
                  <option key={ch} value={ch}>
                    Chapter {ch}
                  </option>
                ))}
              </select>
            </label>

            <button
              className="brass-chip"
              onClick={() => goToChapter(nextChapter)}
              disabled={nextChapter === null}
              style={{ ...S.chapterBarBtn, textAlign: "right",
                       opacity: nextChapter === null ? 0.3 : 1,
                       cursor: nextChapter === null ? "default" : "pointer" }}
            >
              {nextChapter === null ? "" : `Chapter ${nextChapter}`} →
            </button>
          </nav>

          {grouped.map(([ch, passages]) => (
            <div key={ch} style={S.chapterBlock}>
              <div style={S.chapterHead}>
                <span style={S.chapterNum}>{chapterHeading(passages[0].ref)}</span>
              </div>

              {passages.map((p) => {
                const passageMatches = !filtersActive || p.links.some(matchLink);
                const openLinks = p.links
                  .map((e, i) => ({ e, i }))
                  .filter(({ i }) => expanded.has(`${p.id}:${i}`));
                return (
                  <div
                    key={p.id}
                    id={`p-${p.id}`}
                    className="brass-passage"
                    style={{
                      ...S.passage,
                      opacity: passageMatches ? 1 : 0.32,
                      background: flashId === p.id ? P.wash13 : undefined,
                      transition: "opacity 0.3s, background 0.5s ease",
                      scrollMarginTop: 24,
                    }}
                  >
                    <div className="brass-prow" style={S.passageRow}>
                      <div style={S.textCol}>
                        <div style={S.refLine}>
                          <span style={S.refText}>{p.ref}</span>
                        </div>
                        <p style={S.scriptureText}>{p.text}</p>
                      </div>

                      <div className="brass-margin" style={S.marginCol}>
                        {p.links.length > 0 && (
                          <div style={S.marginLabel}>
                            {p.links.length}{" "}
                            {p.links.length === 1 ? "link" : "links"}
                          </div>
                        )}
                        {p.links.map((e, i) => {
                            const key = `${p.id}:${i}`;
                            const open = expanded.has(key);
                            const meta = TYPE_META[e.type];
                            const ink = CONFIDENCE_INK[e.confidence];
                            const dim = filtersActive && !matchLink(e);
                            return (
                              <button
                                key={key}
                                className="brass-chip"
                                onClick={() => toggleExpand(key)}
                                title={`${meta.label} · ${CONFIDENCE_LABEL[e.confidence]}`}
                                style={{
                                  ...S.chip,
                                  border: `1.5px ${meta.borderStyle} ${ink}`,
                                  color: ink,
                                  opacity: dim ? 0.3 : 1,
                                  background: open ? P.wash10 : "transparent",
                                }}
                              >
                                {meta.glyph && (
                                  <span style={{ marginRight: 5 }}>{meta.glyph}</span>
                                )}
                                {e.source}
                                {e.contested && <span style={S.contested}> ?</span>}
                              </button>
                            );
                          })}
                      </div>
                    </div>

                    {openLinks.length > 0 && (
                      <div style={S.expansions}>
                        {openLinks.map(({ e, i }) => {
                          const meta = TYPE_META[e.type];
                          const ink = CONFIDENCE_INK[e.confidence];
                          return (
                            <div
                              key={`${p.id}:${i}`}
                              style={{ ...S.sourcePanel, borderLeftColor: ink }}
                            >
                              <div style={S.sourceHead}>
                                <span style={{ ...S.sourceRef, color: ink }}>
                                  {e.source}
                                  {e.altSource && (
                                    <span style={S.altSource}> · also {e.altSource}</span>
                                  )}
                                </span>
                                <span style={S.sourceKind}>
                                  {meta.glyph ? meta.glyph + " " : ""}
                                  {meta.label} · {CONFIDENCE_LABEL[e.confidence]}
                                </span>
                              </div>

                              <div style={S.srcLabel}>King James Version</div>
                              <p style={S.sourceText}>{e.text}</p>

                              {(e.kjvSpecific || e.mediation) && (
                                <div style={S.badgeRow}>
                                  {e.kjvSpecific && (
                                    <span style={S.badge}>
                                      KJV-specific: {e.kjvSpecific}
                                    </span>
                                  )}
                                  {e.mediation && (
                                    <span style={S.badge}>{MEDIATION_LABEL[e.mediation]}</span>
                                  )}
                                </div>
                              )}

                              {e.provenance && (
                                <div style={S.provenance}>
                                  {e.provenance.mt && (
                                    <>
                                      <div style={S.srcLabel}>Hebrew (Masoretic Text)</div>
                                      <p style={S.sourceText}>{e.provenance.mt}</p>
                                    </>
                                  )}
                                  {e.provenance.lxx && (
                                    <>
                                      <div style={{ ...S.srcLabel, color: ink }}>Septuagint</div>
                                      <p style={S.sourceText}>{e.provenance.lxx}</p>
                                    </>
                                  )}
                                  {e.provenance.other && (
                                    <>
                                      <div style={S.srcLabel}>Other reading</div>
                                      <p style={S.sourceText}>{e.provenance.other}</p>
                                    </>
                                  )}
                                  <p style={S.sourceNote}>
                                    <strong>Probable route:</strong> {e.provenance.route}
                                    {e.provenance.alternative && (
                                      <>
                                        {" "}
                                        · <strong>Alternative:</strong> {e.provenance.alternative}
                                      </>
                                    )}
                                  </p>
                                  <p style={S.sourceNote}>{e.provenance.significance}</p>
                                </div>
                              )}

                              {e.note && <p style={S.sourceNote}>{e.note}</p>}

                              {e.whyNot && (
                                <div style={S.whyNot}>
                                  <div style={S.srcLabel}>Why not?</div>
                                  <p style={S.sourceNote}>{e.whyNot}</p>
                                </div>
                              )}

                              {e.bibliography && e.bibliography.length > 0 && (
                                <p style={S.bibliography}>{e.bibliography.join(" · ")}</p>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ))}

          {visiblePassages.length === 0 && (
            <div style={S.empty}>No passages to display.</div>
          )}
        </main>
      </div>

      <footer style={S.footer}>
        Book of Mormon: {book.translation} · Source text: King James Version · Wroot Press
      </footer>
    </div>
  );
}

const S: Record<string, CSSProperties> = {
  root: {
    fontFamily: "'Crimson Pro', 'Georgia', serif",
    background: P.page,
    minHeight: "100vh",
    color: P.inkStrong,
  },
  header: {
    background: P.band,
    padding: "44px 24px 36px",
    textAlign: "center",
    position: "relative",
  },
  homeLink: {
    position: "absolute",
    top: 20,
    left: 24,
    color: P.accentOnBand,
    textDecoration: "none",
    fontFamily: "'Cormorant Garamond', Georgia, serif",
    fontSize: 13,
    fontWeight: 600,
    letterSpacing: 3,
    transition: "color 0.15s",
  },
  headerOrnament: {
    color: P.accentOnBand,
    fontSize: 13,
    letterSpacing: 10,
    marginBottom: 14,
  },
  title: {
    fontFamily: "'Cormorant Garamond', serif",
    fontSize: 52,
    fontWeight: 700,
    color: P.page,
    margin: 0,
    letterSpacing: 14,
  },
  titleRule: { width: 80, height: 1, backgroundColor: P.accentOnBand, margin: "14px auto" },
  subtitle: {
    fontFamily: "'Cormorant Garamond', serif",
    fontSize: 19,
    color: P.accentOnBand,
    margin: 0,
    fontStyle: "italic",
    letterSpacing: 2,
  },
  credit: { fontSize: 11, color: "#7a6e60", margin: "10px 0 0", letterSpacing: 1.5 },
  layout: { display: "flex", maxWidth: 1100, margin: "0 auto" },
  sidebar: {
    width: 270,
    flexShrink: 0,
    padding: "20px 16px",
    borderRight: "1px solid #d4c9b5",
    background: P.fill,
    position: "sticky",
    top: 0,
    maxHeight: "100vh",
    overflowY: "auto",
  },
  legendToggle: {
    fontFamily: "'Cormorant Garamond', serif",
    fontSize: 15,
    fontWeight: 600,
    color: P.ink,
    background: "none",
    border: "none",
    cursor: "pointer",
    padding: "4px 0",
    letterSpacing: 1,
    textTransform: "uppercase",
    width: "100%",
    textAlign: "left",
    marginBottom: 10,
  },
  typeList: { display: "flex", flexDirection: "column", gap: 2, marginBottom: 8 },
  typeBtn: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "6px 8px",
    border: "none",
    borderRadius: 4,
    cursor: "pointer",
    fontFamily: "'Crimson Pro', serif",
    fontSize: 13.5,
    transition: "all 0.15s ease",
    textAlign: "left",
  },
  chipPreviewWrap: { width: 30, flexShrink: 0, display: "flex", justifyContent: "center" },
  chipPreview: {
    fontFamily: "'Cormorant Garamond', serif",
    fontSize: 10,
    fontWeight: 600,
    color: ACCENT,
    borderRadius: 3,
    padding: "1px 4px",
    lineHeight: 1.3,
    minWidth: 16,
    textAlign: "center",
  },
  typeCount: { fontSize: 11, fontWeight: 600, opacity: 0.6, color: ACCENT },
  sourceSection: { borderTop: "1px solid #d4c9b5", paddingTop: 12, marginTop: 8 },
  sectionLabel: {
    fontFamily: "'Cormorant Garamond', serif",
    fontSize: 13,
    fontWeight: 600,
    color: P.ink,
    letterSpacing: 1,
    textTransform: "uppercase",
    marginBottom: 8,
  },
  sourceList: { display: "flex", flexDirection: "column", gap: 1 },
  sourceBtn: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "5px 8px",
    border: "none",
    borderRadius: 4,
    cursor: "pointer",
    fontFamily: "'Crimson Pro', serif",
    fontSize: 13,
    transition: "all 0.15s ease",
    textAlign: "left",
  },
  clearBtn: {
    marginTop: 10,
    padding: "5px 12px",
    border: "none",
    borderRadius: 4,
    background: P.wash08,
    cursor: "pointer",
    fontFamily: "'Crimson Pro', serif",
    fontSize: 12,
    color: P.warnDeep,
    width: "100%",
    textAlign: "center",
  },
  chapterNavTop: { marginBottom: 16 },
  chapterBar: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    marginBottom: 28,
    paddingBottom: 12,
    borderBottom: "1px solid #d4c9b5",
  },
  chapterBarBtn: {
    flex: "0 0 auto",
    minWidth: 96,
    padding: "5px 10px",
    border: "1px solid #c9b99a",
    borderRadius: 4,
    background: "transparent",
    color: P.ink,
    fontFamily: "'Crimson Pro', serif",
    fontSize: 13,
    transition: "all 0.15s",
  } as CSSProperties,
  chapterBarCentre: { flex: 1, display: "flex", justifyContent: "center" },
  chapterSelect: {
    padding: "5px 10px",
    border: "1px solid #c9b99a",
    borderRadius: 4,
    background: P.panel,
    color: P.ink,
    fontFamily: "'Cormorant Garamond', serif",
    fontSize: 16,
    fontWeight: 600,
    letterSpacing: 0.5,
    cursor: "pointer",
  } as CSSProperties,
  chapterNav: { borderTop: "1px solid #d4c9b5", paddingTop: 14, marginTop: 14 },
  chapterGrid: { display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: 3 },
  chBtn: {
    padding: "4px 0",
    border: "1px solid #c9b99a",
    borderRadius: 3,
    cursor: "pointer",
    fontFamily: "'Crimson Pro', serif",
    fontSize: 12,
    fontWeight: 500,
    textAlign: "center",
    transition: "all 0.15s",
  },
  howTo: {
    marginTop: 16,
    padding: 12,
    background: P.wash07,
    borderRadius: 6,
    fontSize: 12,
    lineHeight: 1.6,
    color: P.inkSoft,
    borderLeft: `3px solid ${ACCENT}`,
  },
  main: { flex: 1, padding: "32px 40px", minWidth: 0 },
  chapterBlock: { marginBottom: 40 },
  chapterHead: { marginBottom: 20, paddingBottom: 10, borderBottom: "1px solid #d4c9b5" },
  chapterNum: {
    fontFamily: "'Cormorant Garamond', serif",
    fontSize: 24,
    fontWeight: 600,
    color: P.ink,
    letterSpacing: 2,
  },
  passage: { marginBottom: 26, padding: "8px 12px", borderRadius: 6 },
  passageRow: { display: "flex", gap: 28, alignItems: "flex-start" },
  textCol: { flex: 1, minWidth: 0 },
  marginCol: {
    width: 188,
    flexShrink: 0,
    display: "flex",
    flexDirection: "column",
    alignItems: "flex-start",
    gap: 7,
    paddingTop: 2,
  },
  marginLabel: {
    fontFamily: "'Cormorant Garamond', serif",
    fontSize: 11,
    fontWeight: 600,
    letterSpacing: 1,
    textTransform: "uppercase",
    color: P.neutral,
    marginBottom: 3,
  },
  expansions: { marginTop: 14, display: "flex", flexDirection: "column", gap: 8 },
  refLine: { display: "flex", alignItems: "center", gap: 10, marginBottom: 6 },
  refText: {
    fontFamily: "'Cormorant Garamond', serif",
    fontSize: 13,
    fontWeight: 600,
    color: P.inkMuted,
    letterSpacing: 1,
    flexShrink: 0,
  },
  refSpacer: { flex: 1 },
  refCount: {
    fontFamily: "'Cormorant Garamond', serif",
    fontSize: 11,
    fontWeight: 600,
    letterSpacing: 1,
    textTransform: "uppercase",
    color: P.neutral,
    flexShrink: 0,
  },
  scriptureText: {
    fontSize: 17,
    lineHeight: 1.85,
    color: P.inkStrong,
    margin: 0,
    fontFamily: "'Crimson Pro', serif",
    fontWeight: 300,
  },
  gutter: { display: "flex", flexWrap: "wrap", gap: 7, marginTop: 12 },
  chipWrap: { display: "block", width: "100%" },
  chip: {
    display: "inline-flex",
    alignItems: "center",
    padding: "3px 10px",
    borderRadius: 13,
    cursor: "pointer",
    fontFamily: "'Cormorant Garamond', Georgia, serif",
    fontSize: 13,
    fontWeight: 600,
    letterSpacing: 0.4,
    transition: "all 0.15s",
    whiteSpace: "nowrap",
    maxWidth: "100%",
  },
  contested: { fontWeight: 700 },
  sourcePanel: {
    marginTop: 8,
    marginBottom: 4,
    padding: "12px 16px",
    background: P.paperShade,
    borderLeft: "3px solid",
    borderRadius: "0 4px 4px 0",
  },
  sourceHead: {
    display: "flex",
    flexWrap: "wrap",
    alignItems: "baseline",
    gap: 10,
    marginBottom: 8,
  },
  sourceRef: {
    fontFamily: "'Cormorant Garamond', Georgia, serif",
    fontSize: 15,
    fontWeight: 600,
    letterSpacing: 0.5,
  },
  altSource: { fontSize: 12, fontWeight: 400, fontStyle: "italic", color: P.inkMuted },
  sourceKind: {
    fontFamily: "'Cormorant Garamond', Georgia, serif",
    fontSize: 11,
    fontWeight: 600,
    letterSpacing: 1,
    textTransform: "uppercase",
    color: P.inkMuted,
  },
  sourceText: {
    fontFamily: "'Crimson Pro', Georgia, serif",
    fontSize: 15.5,
    lineHeight: 1.7,
    color: "#3a3024",
    fontStyle: "italic",
    fontWeight: 300,
    margin: 0,
  },
  srcLabel: {
    fontFamily: "'Cormorant Garamond', Georgia, serif",
    fontSize: 10.5,
    fontWeight: 600,
    letterSpacing: 1,
    textTransform: "uppercase",
    color: P.inkMuted,
    marginBottom: 3,
  },
  sourceNote: {
    fontFamily: "'Crimson Pro', Georgia, serif",
    fontSize: 13.5,
    lineHeight: 1.6,
    color: P.inkSoft,
    margin: "10px 0 0",
    fontWeight: 400,
  },
  badgeRow: {
    display: "flex",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 8,
  },
  badge: {
    fontFamily: "'Cormorant Garamond', Georgia, serif",
    fontSize: 11,
    fontWeight: 600,
    letterSpacing: 0.5,
    color: P.inkSoft,
    background: P.wash10,
    border: "1px solid rgba(138,107,31,0.25)",
    borderRadius: 3,
    padding: "2px 8px",
  },
  provenance: {
    marginTop: 12,
    paddingTop: 12,
    borderTop: "1px dashed #d4c9b5",
  },
  whyNot: {
    marginTop: 12,
    paddingTop: 10,
    borderTop: "1px solid #d4a89a",
  },
  bibliography: {
    fontFamily: "'Crimson Pro', Georgia, serif",
    fontSize: 11.5,
    fontStyle: "italic",
    color: P.inkFaint,
    margin: "10px 0 0",
  },
  empty: {
    textAlign: "center",
    padding: "80px 24px",
    color: P.inkFaint,
    fontStyle: "italic",
    fontSize: 16,
  },
  footer: {
    textAlign: "center",
    padding: "20px",
    borderTop: "1px solid #d4c9b5",
    fontSize: 11,
    color: P.inkFaint,
    letterSpacing: 0.5,
    background: P.fill,
  },
};

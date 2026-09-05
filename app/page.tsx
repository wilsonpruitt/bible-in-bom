import Link from "next/link";
import { BOOKS, getBook } from "@/data/books";

// The 15 books of the Book of Mormon, in canonical order. Only the slugs
// present in BOOKS (data/books.ts) are built and clickable; the rest render
// as a greyed-out placeholder so the home page always shows the whole shape
// of the project, not just what exists today.
const ALL_BOOKS: { slug: string; name: string }[] = [
  { slug: "1-nephi", name: "1 Nephi" },
  { slug: "2-nephi", name: "2 Nephi" },
  { slug: "jacob", name: "Jacob" },
  { slug: "enos", name: "Enos" },
  { slug: "jarom", name: "Jarom" },
  { slug: "omni", name: "Omni" },
  { slug: "words-of-mormon", name: "Words of Mormon" },
  { slug: "mosiah", name: "Mosiah" },
  { slug: "alma", name: "Alma" },
  { slug: "helaman", name: "Helaman" },
  { slug: "3-nephi", name: "3 Nephi" },
  { slug: "4-nephi", name: "4 Nephi" },
  { slug: "mormon", name: "Mormon" },
  { slug: "ether", name: "Ether" },
  { slug: "moroni", name: "Moroni" },
];

export default function Home() {
  return (
    <div style={{ minHeight: "100vh", background: "#f5f0e8", color: "#2c2418" }}>
      <header
        style={{
          background: "#2c2418",
          color: "#f5f0e8",
          padding: "64px 24px 56px",
          textAlign: "center",
        }}
      >
        <div style={{ color: "#d4b463", letterSpacing: 10, marginBottom: 16, fontSize: 14 }}>
          ⚒ ⚒ ⚒
        </div>
        <h1
          style={{
            fontFamily: "'Cormorant Garamond', Georgia, serif",
            fontSize: 72,
            fontWeight: 700,
            margin: 0,
            letterSpacing: 18,
          }}
        >
          BRASS
        </h1>
        <div style={{ width: 80, height: 1, background: "#d4b463", margin: "16px auto" }} />
        <p
          style={{
            fontFamily: "'Cormorant Garamond', Georgia, serif",
            fontStyle: "italic",
            color: "#d4b463",
            fontSize: 19,
            letterSpacing: 2,
            margin: 0,
          }}
        >
          The Bible in the Book of Mormon
        </p>
      </header>

      <main
        style={{
          maxWidth: 760,
          margin: "0 auto",
          padding: "48px 24px 80px",
          fontFamily: "'Crimson Pro', Georgia, serif",
        }}
      >
        <p style={{ fontSize: 17, lineHeight: 1.75, color: "#4a3d30" }}>
          A Wroot Press critical catalogue. <em>Brass</em> takes its name from the
          plates of brass — Nephi&rsquo;s family&rsquo;s own name for the record of
          earlier scripture they carried out of Jerusalem and quoted from for the
          rest of the book. Every passage carries links back to the King James
          Version beneath it: a quotation, an allusion, a fainter echo, or a
          figure with no words shared at all. Each link records not just the kind
          of connection but its confidence, whether the wording is
          King-James-specific, how the source likely reached the text, and the
          scholarship behind the judgment — with the counter-evidence shown too,
          where a connection is disputed.
        </p>

        <h2
          style={{
            marginTop: 48,
            marginBottom: 16,
            fontFamily: "'Cormorant Garamond', Georgia, serif",
            fontSize: 15,
            fontWeight: 600,
            letterSpacing: 3,
            textTransform: "uppercase",
            color: "#8a7a6a",
          }}
        >
          The Books
        </h2>

        <div style={{ display: "grid", gap: 12 }}>
          {ALL_BOOKS.map((b) => {
            const built = getBook(b.slug);
            const count = built
              ? built.pericopes.reduce((n, p) => n + p.links.length, 0)
              : 0;
            if (!built) {
              return (
                <div
                  key={b.slug}
                  style={{
                    display: "block",
                    padding: "16px 24px",
                    background: "#eee9df",
                    border: "1px solid #e0d8c5",
                    borderRadius: 6,
                    opacity: 0.45,
                  }}
                >
                  <div
                    style={{
                      fontFamily: "'Cormorant Garamond', serif",
                      fontSize: 22,
                      fontWeight: 600,
                      letterSpacing: 3,
                      color: "#2c2418",
                    }}
                  >
                    {b.name.toUpperCase()}
                  </div>
                </div>
              );
            }
            return (
              <Link
                key={b.slug}
                href={`/${b.slug}`}
                style={{
                  display: "block",
                  padding: "20px 24px",
                  background: "#eee9df",
                  border: "1px solid #d4c9b5",
                  borderRadius: 6,
                  textDecoration: "none",
                  color: "inherit",
                  transition: "all 0.15s",
                }}
              >
                <div
                  style={{
                    fontFamily: "'Cormorant Garamond', serif",
                    fontSize: 28,
                    fontWeight: 600,
                    letterSpacing: 4,
                    color: "#2c2418",
                  }}
                >
                  {built.name.toUpperCase()}
                </div>
                {built.subtitle && (
                  <div
                    style={{
                      fontFamily: "'Cormorant Garamond', serif",
                      fontStyle: "italic",
                      color: "#8a7a6a",
                      fontSize: 15,
                      marginTop: 4,
                      letterSpacing: 1,
                    }}
                  >
                    {built.subtitle}
                  </div>
                )}
                <div style={{ fontSize: 12, color: "#a89a86", marginTop: 6 }}>
                  {count} biblical {count === 1 ? "connection" : "connections"} adjudicated
                </div>
              </Link>
            );
          })}
        </div>

        <p
          style={{
            marginTop: 48,
            fontSize: 12,
            color: "#8a7a6a",
            textAlign: "center",
            letterSpacing: 1,
          }}
        >
          Book of Mormon: 1830 first edition, modern versification · Source: King
          James Version · Wroot Press
        </p>
      </main>
    </div>
  );
}

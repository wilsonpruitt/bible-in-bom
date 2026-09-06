import { P } from "@/lib/palette";
import { ImageResponse } from "next/og";

// Social-share card for Brass. Mirrors the landing header: ink ground, brass
// gold accents, a plate motif (drawn as stacked bars — echoing the plates of
// brass), BRASS in Cormorant Garamond, the house tagline.
export const runtime = "nodejs";
export const alt = "Brass — The Bible in the Book of Mormon · Wroot Press";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const INK = P.band;
const CREAM = P.page;
const BRONZE = P.accent;
const GOLD = P.accentOnBand;
const MUTE = P.inkFaint;

// Subset Cormorant Garamond to just the glyphs the card uses.
async function cormorant(text: string, weight: 600 | 700) {
  const css = await (
    await fetch(
      `https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,${weight};1,${weight}&text=${encodeURIComponent(
        text
      )}`,
      { headers: { "User-Agent": "Mozilla/5.0" } }
    )
  ).text();
  const url = css.match(/src: url\((.+?)\) format\(['"]?(opentype|truetype)['"]?\)/);
  if (!url) throw new Error("font url not found");
  return (await fetch(url[1])).arrayBuffer();
}

// One plate: a stacked bar.
function Plate({ width }: { width: number }) {
  return (
    <div
      style={{
        width,
        height: 14,
        borderRadius: 3,
        border: `4px solid ${GOLD}`,
      }}
    />
  );
}

export default async function Image() {
  const wordmark = "BRASS";
  const tagline = "The Bible in the Book of Mormon";
  const press = "WROOT PRESS";
  let fonts;
  try {
    const [bold, italic] = await Promise.all([
      cormorant(wordmark + press, 700),
      cormorant(tagline, 600),
    ]);
    fonts = [
      { name: "Cormorant", data: bold, weight: 700 as const, style: "normal" as const },
      { name: "Cormorant", data: italic, weight: 600 as const, style: "italic" as const },
    ];
  } catch {
    fonts = undefined; // fall back to satori's default serif metrics
  }

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          background: INK,
          fontFamily: "Cormorant, Georgia, serif",
        }}
      >
        {/* inset printed-frame border */}
        <div
          style={{
            position: "absolute",
            top: 36,
            left: 36,
            right: 36,
            bottom: 36,
            border: `1px solid ${BRONZE}`,
          }}
        />

        {/* plate motif */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6, marginBottom: 40 }}>
          <Plate width={140} />
          <Plate width={100} />
          <Plate width={140} />
        </div>

        <div
          style={{
            fontSize: 150,
            fontWeight: 700,
            letterSpacing: 30,
            color: CREAM,
            // shift to optically center the letterspacing
            paddingLeft: 30,
            lineHeight: 1,
          }}
        >
          {wordmark}
        </div>

        <div style={{ width: 96, height: 1, background: GOLD, margin: "30px 0" }} />

        <div
          style={{
            fontSize: 42,
            fontStyle: "italic",
            fontWeight: 600,
            letterSpacing: 3,
            color: GOLD,
          }}
        >
          {tagline}
        </div>

        <div
          style={{
            position: "absolute",
            bottom: 70,
            fontSize: 24,
            letterSpacing: 14,
            color: MUTE,
            paddingLeft: 14,
          }}
        >
          {press}
        </div>
      </div>
    ),
    { ...size, fonts }
  );
}

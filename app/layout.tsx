import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  metadataBase: new URL("https://brass.wrootpress.com"),
  title: "Brass · Wroot Press",
  description:
    "The Bible in the Book of Mormon — a digital critical catalogue of quotations, allusions, echoes, and figures, read against the King James Version.",
  openGraph: {
    title: "Brass · Wroot Press",
    description:
      "The Bible in the Book of Mormon — a digital critical catalogue of quotations, allusions, echoes, and figures, read against the King James Version.",
    siteName: "Brass",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Brass · Wroot Press",
    description: "The Bible in the Book of Mormon — a Wroot Press reading lens.",
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <script defer src="/_vercel/insights/script.js"></script>
      </head>
      <body style={{ margin: 0, background: "#f5f0e8" }}>{children}</body>
    </html>
  );
}

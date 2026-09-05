import type { Book } from "@/lib/types";
import firstNephi from "./1-nephi.json";

// Add a book: run `python3.11 tools/build-book-data.py "<Book Name>" <slug>`
// to generate its data/<slug>.json from the 1830 text, then import and list
// it here — same pattern as Catena's data/books.ts.
export const BOOKS: Book[] = [firstNephi as Book];

export function getBook(slug: string): Book | undefined {
  return BOOKS.find((b) => b.slug === slug);
}

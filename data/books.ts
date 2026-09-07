import type { Book } from "@/lib/types";
import firstNephi from "./1-nephi.json";
import secondNephi from "./2-nephi.json";
import jacob from "./jacob.json";
import enos from "./enos.json";
import jarom from "./jarom.json";
import omni from "./omni.json";
import wordsOfMormon from "./words-of-mormon.json";
import mosiah from "./mosiah.json";
import alma from "./alma.json";
import helaman from "./helaman.json";
import thirdNephi from "./3-nephi.json";

// Add a book: `python3.11 tools/bootstrap-book.py "<Book Name>" <slug>` builds
// data/<slug>.json from the 1830 text and generates its machine candidates;
// import and list it here. Order follows the Book of Mormon's own.
export const BOOKS: Book[] = [
  firstNephi as Book,
  secondNephi as Book,
  jacob as Book,
  enos as Book,
  jarom as Book,
  omni as Book,
  wordsOfMormon as Book,
  mosiah as Book,
  alma as Book,
  helaman as Book,
  thirdNephi as Book,
];

export function getBook(slug: string): Book | undefined {
  return BOOKS.find((b) => b.slug === slug);
}

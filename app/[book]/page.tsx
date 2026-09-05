import { notFound } from "next/navigation";
import Reader from "@/components/Reader";
import { BOOKS, getBook } from "@/data/books";

export function generateStaticParams() {
  return BOOKS.map((b) => ({ book: b.slug }));
}

export default async function BookPage({
  params,
}: {
  params: Promise<{ book: string }>;
}) {
  const { book: slug } = await params;
  const book = getBook(slug);
  if (!book) notFound();
  return <Reader book={book} />;
}

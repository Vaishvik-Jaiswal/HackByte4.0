import type { ThreadEmail } from "./types";

/** Collapse whitespace for fuzzy substring checks on LLM quotes. */
export function normalizeWhitespace(s: string): string {
  return s.replace(/\s+/g, " ").trim();
}

/**
 * Pick which email in the thread best matches the LLM's supporting quote
 * (exact substring in body or subject; then whitespace-normalized body match).
 */
export function findSupportingEmailId(
  emails: ThreadEmail[],
  supportingQuote: string,
): number | null {
  const q = supportingQuote.trim();
  if (!q) return null;

  for (const e of emails) {
    if (e.body_text.includes(q)) return e.id;
    if (e.subject.includes(q)) return e.id;
  }

  const nq = normalizeWhitespace(q);
  if (nq.length < 6) return null;

  for (const e of emails) {
    if (normalizeWhitespace(e.body_text).includes(nq)) return e.id;
  }

  return null;
}

"use client";

import type { ThreadEmail } from "@/lib/types";

function formatWhen(iso: string): string {
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

type Props = {
  emails: ThreadEmail[];
  highlightEmailId: number | null;
};

/**
 * Vertical timeline of messages; the email that grounds the answer is emphasized.
 */
export function ThreadTimeline({ emails, highlightEmailId }: Props) {
  return (
    <div className="relative pl-8">
      <div
        className="absolute left-[11px] top-2 bottom-2 w-px bg-zinc-300 dark:bg-zinc-600"
        aria-hidden
      />
      <ul className="space-y-6">
        {emails.map((email, index) => {
          const isHit = highlightEmailId !== null && email.id === highlightEmailId;
          return (
            <li key={email.id} className="relative">
              <span
                className={`absolute left-0 top-4 h-3 w-3 rounded-full border-2 border-white dark:border-zinc-900 ${
                  isHit ? "bg-amber-500 ring-2 ring-amber-400/80" : "bg-zinc-400 dark:bg-zinc-500"
                }`}
                aria-hidden
              />
              <article
                className={`rounded-xl border p-4 transition-colors ${
                  isHit
                    ? "border-amber-500/70 bg-amber-500/[0.07] shadow-sm ring-1 ring-amber-500/30"
                    : "border-zinc-200 bg-white/60 dark:border-zinc-700 dark:bg-zinc-900/40"
                }`}
                aria-current={isHit ? "true" : undefined}
              >
                <header className="mb-2 flex flex-wrap items-baseline gap-x-2 gap-y-1 text-sm">
                  <span className="font-semibold text-zinc-900 dark:text-zinc-50">
                    {email.sender_display}
                  </span>
                  <time
                    dateTime={email.date}
                    className="text-xs text-zinc-500 dark:text-zinc-400"
                  >
                    {formatWhen(email.date)}
                  </time>
                  <span className="text-xs text-zinc-400 dark:text-zinc-500">
                    · Message {index + 1}
                  </span>
                </header>
                {email.subject ? (
                  <p className="mb-2 text-sm font-medium text-zinc-700 dark:text-zinc-300">
                    {email.subject}
                  </p>
                ) : null}
                <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-zinc-800 dark:text-zinc-200">
                  {email.body_text}
                </pre>
              </article>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

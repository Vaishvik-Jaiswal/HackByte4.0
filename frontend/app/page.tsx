"use client";

import { useCallback, useMemo, useState } from "react";

import { ThreadTimeline } from "@/components/ThreadTimeline";
import { getThread, postAsk } from "@/lib/api";
import { findSupportingEmailId } from "@/lib/grounding";
import type { AskResponse, ThreadDetail } from "@/lib/types";

export default function Home() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AskResponse | null>(null);

  const [threadOpen, setThreadOpen] = useState(false);
  const [threadLoading, setThreadLoading] = useState(false);
  const [threadDetail, setThreadDetail] = useState<ThreadDetail | null>(null);
  const [threadError, setThreadError] = useState<string | null>(null);

  const highlightId = useMemo(() => {
    if (!threadDetail?.emails.length || !result?.answer.supporting_email) return null;
    return findSupportingEmailId(
      threadDetail.emails,
      result.answer.supporting_email,
    );
  }, [threadDetail, result]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const q = question.trim();
    if (!q) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setThreadOpen(false);
    setThreadDetail(null);
    setThreadError(null);
    try {
      const data = await postAsk(q);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  };

  const loadThread = useCallback(async () => {
    if (!result?.thread_id) return;
    setThreadLoading(true);
    setThreadError(null);
    try {
      const detail = await getThread(result.thread_id);
      setThreadDetail(detail);
      setThreadOpen(true);
    } catch (err) {
      setThreadError(err instanceof Error ? err.message : "Failed to load thread");
    } finally {
      setThreadLoading(false);
    }
  }, [result?.thread_id]);

  const onViewThread = () => {
    if (!result?.thread_id) return;
    if (threadDetail?.thread_id === result.thread_id && threadOpen) {
      setThreadOpen(false);
      return;
    }
    if (threadDetail?.thread_id === result.thread_id) {
      setThreadOpen(true);
      return;
    }
    void loadThread();
  };

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100">
      <main className="mx-auto flex max-w-2xl flex-col gap-8 px-4 py-12 sm:px-6">
        <header className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">Inbox Copilot</h1>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            Ask questions about your email threads — answers stay grounded in retrieved
            messages.
          </p>
        </header>

        <form onSubmit={onSubmit} className="flex flex-col gap-3">
          <label htmlFor="q" className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Your question
          </label>
          <textarea
            id="q"
            name="question"
            rows={3}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder='e.g. When is my NVIDIA assessment confirmed for?'
            className="resize-y rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm shadow-sm outline-none ring-zinc-400/30 placeholder:text-zinc-400 focus:border-zinc-400 focus:ring-2 dark:border-zinc-600 dark:bg-zinc-900 dark:focus:border-zinc-500"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="inline-flex h-10 items-center justify-center rounded-lg bg-zinc-900 px-4 text-sm font-medium text-white shadow transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-white"
          >
            {loading ? "Asking…" : "Ask"}
          </button>
        </form>

        {error ? (
          <p
            className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/50 dark:text-red-200"
            role="alert"
          >
            {error}
          </p>
        ) : null}

        {result ? (
          <section className="space-y-4 rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/80">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
              Answer
            </h2>
            <p className="whitespace-pre-wrap text-base leading-relaxed">{result.answer.answer}</p>

            <div className="space-y-2 border-t border-zinc-100 pt-4 dark:border-zinc-800">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                Supporting email (quote)
              </h3>
              {result.answer.supporting_email ? (
                <blockquote className="border-l-4 border-amber-500/80 pl-3 text-sm italic text-zinc-700 dark:text-zinc-300">
                  {result.answer.supporting_email}
                </blockquote>
              ) : (
                <p className="text-sm text-zinc-500">No exact quote returned.</p>
              )}
            </div>

            <dl className="grid gap-2 text-sm text-zinc-600 dark:text-zinc-400">
              <div className="flex justify-between gap-4">
                <dt>Summary</dt>
                <dd className="text-right text-zinc-800 dark:text-zinc-200">
                  {result.answer.summary}
                </dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt>Confidence</dt>
                <dd>{result.answer.confidence.toFixed(2)}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt>Thread</dt>
                <dd className="truncate font-mono text-xs text-zinc-500" title={result.thread_id}>
                  {result.thread_id}
                </dd>
              </div>
            </dl>

            <div className="flex flex-wrap gap-2 pt-2">
              <button
                type="button"
                onClick={onViewThread}
                disabled={threadLoading}
                className="inline-flex h-9 items-center rounded-lg border border-zinc-300 bg-zinc-50 px-3 text-sm font-medium text-zinc-900 hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-100 dark:hover:bg-zinc-700"
              >
                {threadLoading
                  ? "Loading…"
                  : threadOpen && threadDetail?.thread_id === result.thread_id
                    ? "Hide thread"
                    : "View thread"}
              </button>
            </div>

            {threadError ? (
              <p className="text-sm text-red-600 dark:text-red-400" role="alert">
                {threadError}
              </p>
            ) : null}

            {threadOpen && threadDetail ? (
              <div className="space-y-3 border-t border-zinc-100 pt-4 dark:border-zinc-800">
                <h3 className="text-sm font-semibold text-zinc-800 dark:text-zinc-200">
                  Conversation timeline
                </h3>
                {highlightId === null && result.answer.supporting_email ? (
                  <p className="text-xs text-amber-800 dark:text-amber-200/90">
                    Could not auto-match the supporting quote to a single message — review the
                    thread manually.
                  </p>
                ) : null}
                <ThreadTimeline
                  emails={threadDetail.emails}
                  highlightEmailId={highlightId}
                />
              </div>
            ) : null}
          </section>
        ) : null}
      </main>
    </div>
  );
}

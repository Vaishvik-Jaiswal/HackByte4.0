"use client";

import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Database,
  ClipboardList,
  Tags,
  FileText,
  Palette,
  Scale,
  Link2,
  Sparkles,
  ChevronRight,
  Cpu,
} from "lucide-react";

/** Stages aligned with backend: pipeline.py + gmail sync. */
export const PIPELINE_STAGES = [
  {
    id: "sync",
    title: "Gmail sync",
    detail: "Pull INBOX & SENT via Gmail API, persist new rows.",
    icon: Database,
  },
  {
    id: "briefing",
    title: "Briefing extraction",
    detail:
      "Groq detects manager/teammate briefings (topic + what to tell the client) and stores relay context.",
    icon: ClipboardList,
  },
  {
    id: "classify",
    title: "Classification",
    detail: "LLM assigns a category for routing and reply policy.",
    icon: Tags,
  },
  {
    id: "summarize",
    title: "Summarization",
    detail: "Condensed summary for the side panel and downstream agents.",
    icon: FileText,
  },
  {
    id: "tone",
    title: "Tone suggestion",
    detail: "Matches your recent sent mail; suggests tone + short rationale.",
    icon: Palette,
  },
  {
    id: "reply_policy",
    title: "Reply policy",
    detail: "Heuristic + category: skip drafts for promos, newsletters, OTPs, etc.",
    icon: Scale,
  },
  {
    id: "relay",
    title: "Relay matching",
    detail: "If a reply is needed, match inbox text to active briefing topics; inject instructions into the prompt.",
    icon: Link2,
  },
  {
    id: "draft",
    title: "Draft generation",
    detail: "Groq composes a reply using category, summary, tone, sent-mail style, and optional relay block.",
    icon: Sparkles,
  },
];

function StageRow({ stage, index, active, done, compact }) {
  const Icon = stage.icon;
  return (
    <motion.div
      layout
      initial={false}
      animate={{
        backgroundColor: active ? "rgba(11, 87, 208, 0.08)" : "transparent",
      }}
      className={`flex gap-3 rounded-xl border transition-colors ${
        active
          ? "border-[#0b57d0] shadow-sm"
          : done
            ? "border-[#e2e8f0] bg-[#f8fafc]"
            : "border-[#f1f3f4]"
      } p-3 ${compact ? "py-2" : ""}`}
    >
      <div
        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${
          active
            ? "bg-[#0b57d0] text-white"
            : done
              ? "bg-[#e8f0fe] text-[#0b57d0]"
              : "bg-[#f1f3f4] text-[#5e5e5e]"
        }`}
      >
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-[#64748b]">
            {String(index + 1).padStart(2, "0")}
          </span>
          <p className="text-sm font-semibold text-[#1f1f1f]">{stage.title}</p>
        </div>
        {!compact && (
          <p className="mt-1 text-xs leading-relaxed text-[#5e5e5e]">{stage.detail}</p>
        )}
      </div>
      {active && (
        <motion.span
          className="self-center"
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ repeat: Infinity, duration: 1.2 }}
        >
          <Cpu className="h-4 w-4 text-[#0b57d0]" />
        </motion.span>
      )}
    </motion.div>
  );
}

/**
 * Full-height panel for hackathon demo: explains the full stack.
 * @param {object} props
 * @param {boolean} props.open
 * @param {function} props.onClose
 * @param {boolean} props.syncInProgress
 * @param {number} props.highlightIndex — 0..length-1 while syncing (animated)
 * @param {object | null} props.lastAiProcessing — API `ai_processing` from POST /gmail/sync
 */
export function AIPipelineDrawer({
  open,
  onClose,
  syncInProgress,
  highlightIndex = 0,
  lastAiProcessing = null,
}) {
  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.button
            type="button"
            aria-label="Close pipeline panel"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[70] bg-black/25"
            onClick={onClose}
          />
          <motion.aside
            role="dialog"
            aria-labelledby="ai-pipeline-title"
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 28, stiffness: 320 }}
            className="fixed right-0 top-0 z-[80] flex h-full w-full max-w-md flex-col bg-white shadow-2xl"
          >
            <div className="flex h-14 shrink-0 items-center justify-between border-b border-[#f1f3f4] px-4">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-[#0b57d0]" />
                <h2 id="ai-pipeline-title" className="text-base font-semibold text-[#1f1f1f]">
                  AI pipeline
                </h2>
              </div>
              <button
                type="button"
                onClick={onClose}
                className="rounded-full p-2 text-[#444746] hover:bg-[#f1f3f4]"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4">
              <p className="mb-4 text-sm leading-relaxed text-[#5e5e5e]">
                Each inbox message runs through Groq LLM calls and heuristics. Sent mail is only used as style
                context and marked processed without generation.
              </p>

              {lastAiProcessing && (
                <div className="mb-4 rounded-xl border border-[#c7d9fc] bg-[#e8f0fe] p-3 text-sm text-[#001d35]">
                  <p className="font-semibold">Last run</p>
                  {lastAiProcessing.status === "error" ? (
                    <p className="mt-1 text-xs text-[#b3261e]">{lastAiProcessing.detail}</p>
                  ) : (
                    <ul className="mt-2 space-y-1 text-xs">
                      <li>
                        Status: <strong>{lastAiProcessing.status}</strong>
                      </li>
                      {typeof lastAiProcessing.inbox_processed === "number" && (
                        <li>Inbox messages processed: {lastAiProcessing.inbox_processed}</li>
                      )}
                      {typeof lastAiProcessing.sent_marked_processed === "number" && (
                        <li>Sent rows marked (no AI): {lastAiProcessing.sent_marked_processed}</li>
                      )}
                      {lastAiProcessing.reason === "groq_not_configured" && (
                        <li className="text-amber-800">Groq API key not set — pipeline skipped.</li>
                      )}
                    </ul>
                  )}
                </div>
              )}

              <div className="space-y-2">
                {PIPELINE_STAGES.map((stage, i) => (
                  <StageRow
                    key={stage.id}
                    stage={stage}
                    index={i}
                    active={syncInProgress && i === highlightIndex}
                    done={syncInProgress && i < highlightIndex}
                  />
                ))}
              </div>

              <div className="mt-6 flex items-start gap-2 rounded-xl bg-[#f8fafc] p-3 text-xs text-[#64748b]">
                <ChevronRight className="mt-0.5 h-4 w-4 shrink-0" />
                <span>
                  Open any inbox message to see category, summary, tone, and drafts. “Uses prior briefing”
                  appears when relay matching supplied context from an earlier briefing mail.
                </span>
              </div>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}

/**
 * Compact checklist in the email detail sidebar — maps stored AI fields to stages.
 */
export function EmailPipelineTrace({ ai }) {
  if (!ai) return null;

  const hasDraft = Boolean(ai.reply_needed && ai.suggested_reply);
  const steps = [
    { label: "Classified", ok: Boolean(ai.category) },
    { label: "Summarized", ok: Boolean((ai.summary || "").trim()) },
    { label: "Tone + rationale", ok: Boolean(ai.tone) },
    { label: "Reply needed", ok: typeof ai.reply_needed === "boolean" },
    { label: "Relay briefing used", ok: ai.relay_applied === true, muted: !ai.reply_needed },
    { label: "Draft generated", ok: hasDraft, muted: !ai.reply_needed },
  ];

  return (
    <div className="mt-4 rounded-2xl border border-[#e2e8f0] bg-white p-4 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-[#64748b] mb-3">Pipeline trace</p>
      <ul className="space-y-2">
        {steps.map((s) => (
          <li
            key={s.label}
            className={`flex items-center gap-2 text-xs ${
              s.muted ? "text-[#cbd5e1]" : "text-[#334155]"
            }`}
          >
            <span
              className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${
                s.ok && !s.muted ? "bg-[#e6f4ea] text-[#137333]" : "bg-[#f1f5f9] text-[#94a3b8]"
              }`}
            >
              {s.ok && !s.muted ? "✓" : "—"}
            </span>
            {s.label}
          </li>
        ))}
      </ul>
    </div>
  );
}

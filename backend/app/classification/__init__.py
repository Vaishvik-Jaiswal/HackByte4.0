"""Email AI pipeline: classify, summarize, tone suggestion, draft reply."""

from app.classification.pipeline import process_pending_emails_for_user

__all__ = ["process_pending_emails_for_user"]

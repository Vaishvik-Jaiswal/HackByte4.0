"""Decide whether an inbound message expects a human reply (skip promos, newsletters, etc.)."""


def compute_reply_needed(category: str, summary: str) -> bool:
    """
    Uses classification + summary text. When False, we skip generating a suggested reply
    (saves tokens and keeps the inbox focused on actionable mail).
    """
    cat = (category or "").strip().lower()
    summ = (summary or "").strip().lower()

    if "promotional" in cat or "spam" in cat:
        return False

    # OTP, password resets, security alerts — usually no reply.
    if "authentication" in cat or "security" in cat:
        return False

    # Pure acknowledgments — typically no response expected.
    if "confirmation" in cat and "thanks" in cat:
        return False

    newsletter_markers = (
        "unsubscribe",
        "newsletter",
        "marketing",
        "promotional offer",
        "view in browser",
        "you are receiving this email because",
        "no longer wish to receive",
        "manage preferences",
        "email preferences",
    )
    if any(m in summ for m in newsletter_markers):
        return False

    return True

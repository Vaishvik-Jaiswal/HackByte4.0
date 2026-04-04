from sqlalchemy import text
from app.db import get_db

from app.agents.classification_agent import classify_email
from app.agents.summarizer_agent import summarize_email
from app.agents.tone_agent import suggest_tone
from app.agents.supervisor_agent import generate_reply

from data.past_emails import past_user_emails


class EmailGraph:
    def run_pipeline(self):
        db = get_db()

        print("🚀 Fetching emails from database...")

        # ✅ Only fetch unprocessed emails
        emails = db.execute(
            text("SELECT * FROM emails WHERE is_processed = FALSE")
        ).fetchall()

        if not emails:
            print("✅ No new emails to process.")
            return []

        results = []

        for email in emails:
            email_id = email.id
            thread_id = email.thread_id
            email_text = email.body_text
            is_inbox = email.is_inbox

            print(f"\n📩 Processing Email ID: {email_id}")

            if is_inbox:
                # -------------------------
                # INCOMING EMAIL FLOW
                # -------------------------
                category = classify_email(email_text)
                summary = summarize_email(email_text)

                db.execute(text("""
                    INSERT INTO processed_emails
                    (email_id, thread_id, category, summary)
                    VALUES (:email_id, :thread_id, :category, :summary)
                """), {
                    "email_id": email_id,
                    "thread_id": thread_id,
                    "category": category,
                    "summary": summary
                })

                tone = None
                tone_reason = None

            else:
                # -------------------------
                # OUTGOING EMAIL FLOW
                # -------------------------
                tone_data = suggest_tone(past_user_emails, email_text, "")

                tone = tone_data.get("suggested_tone")
                tone_reason = tone_data.get("reason")

                db.execute(text("""
                    INSERT INTO processed_emails
                    (email_id, thread_id, tone, tone_reasoning)
                    VALUES (:email_id, :thread_id, :tone, :tone_reason)
                """), {
                    "email_id": email_id,
                    "thread_id": thread_id,
                    "tone": tone,
                    "tone_reason": tone_reason
                })

                category = None
                summary = None

            # -------------------------
            # ✅ MARK EMAIL AS PROCESSED (VERY IMPORTANT)
            # -------------------------
            db.execute(text("""
                UPDATE emails 
                SET is_processed = TRUE 
                WHERE id = :email_id
            """), {"email_id": email_id})

            # -------------------------
            # SUPERVISOR (FINAL REPLY)
            # -------------------------
            reply = generate_reply(
                category if category else "general",
                summary if summary else email_text,
                tone if tone else "professional"
            )

            results.append({
                "email_id": email_id,
                "thread_id": thread_id,
                "category": category,
                "summary": summary,
                "tone": tone,
                "tone_reason": tone_reason,
                "reply": reply
            })

            print("✅ Stored and processed.")

        db.commit()

        print("\n🎯 Pipeline execution completed.")

        return results


def build_graph():
    print("🚀 Graph is building...")
    return EmailGraph()
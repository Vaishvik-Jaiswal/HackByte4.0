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

    def invoke(self, input_data):
        """
        Process a single email through the agent workflow.
        Input format: {"email": {"id": "...", "content": "..."}}
        Returns the processed result in a format suitable for the API response.
        """
        try:
            email_data = input_data.get("email", {})
            email_id = email_data.get("id", "unknown")
            email_content = email_data.get("content", "")

            print(f"\n📩 Processing Email via API: {email_id}")

            # ✅ Assume incoming email flow (can be extended to detect outgoing)
            is_inbox = True

            if is_inbox:
                # -------------------------
                # INCOMING EMAIL FLOW
                # -------------------------
                category = classify_email(email_content)
                summary = summarize_email(email_content)
                tone = None
                tone_reason = None
            else:
                # -------------------------
                # OUTGOING EMAIL FLOW
                # -------------------------
                tone_data = suggest_tone(past_user_emails, email_content, "")
                tone = tone_data.get("suggested_tone")
                tone_reason = tone_data.get("reason")
                category = None
                summary = None

            # -------------------------
            # SUPERVISOR (FINAL REPLY)
            # -------------------------
            reply = generate_reply(
                category if category else "general",
                summary if summary else email_content,
                tone if tone else "professional"
            )

            result = {
                "id": email_id,
                "content": email_content,
                "category": category or "general",
                "summary": summary or "",
                "suggested_tone": tone or "professional",
                "tone_reason": tone_reason or "",
                "reply": reply
            }

            print("✅ Email processed successfully.")
            return result

        except Exception as e:
            print(f"❌ Error in invoke: {str(e)}")
            raise


def build_graph():
    print("🚀 Graph is building...")
    return EmailGraph()
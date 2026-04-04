import base64
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import OAuth
from app.models.email import Email
from app.core.config import settings
from datetime import datetime
import json
from email.utils import parseaddr, parsedate_to_datetime

class GmailService:
    def get_creds(self, db_oauth: OAuth):
        creds = Credentials(
            token=db_oauth.access_token,
            refresh_token=db_oauth.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=db_oauth.scope.split(' ') if db_oauth.scope else None
        )
        return creds

    async def refresh_if_needed(self, db: AsyncSession, db_oauth: OAuth):
        creds = self.get_creds(db_oauth)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            db_oauth.access_token = creds.token
            db_oauth.expires_at = creds.expiry
            db.add(db_oauth)
            await db.commit()
        return creds

    def strip_html(self, html):
        import re
        if not html:
            return ""
        # Remove script and style elements
        clean = re.compile('<script.*?>.*?</script>|<style.*?>.*?</style>', re.DOTALL)
        html = re.sub(clean, '', html)
        # Remove all other tags
        clean = re.compile('<.*?>')
        text = re.sub(clean, ' ', html)
        # Normalize whitespace
        return ' '.join(text.split()).strip()

    def extract_body(self, payload):
        """Recursively extract the body from Gmail message payload."""
        body = ""
        if 'parts' in payload:
            # First pass: try to find text/plain
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part.get('body', {}).get('data')
                    if data:
                        body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                elif 'parts' in part:
                    # Nested multiparts
                    nested_body = self.extract_body(part)
                    if nested_body:
                        body += nested_body
            
            # Second pass: if no plain text found, look for text/html
            if not body:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/html':
                        data = part.get('body', {}).get('data')
                        if data:
                            body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        else:
            # Singular part message
            data = payload.get('body', {}).get('data')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        return body

    def parse_address_field(self, field_value):
        if not field_value:
            return []
        addresses = []
        # Handle multiple addresses separated by comma
        parts = field_value.split(',')
        for p in parts:
            name, email = parseaddr(p.strip())
            addresses.append({"name": name, "email": email})
        return addresses

    async def sync_emails(self, db: AsyncSession, user_id):
        import asyncio
        from datetime import UTC
        
        query = select(OAuth).where(OAuth.user_id == user_id, OAuth.provider == "google")
        result = await db.execute(query)
        db_oauth = result.scalars().first()
        
        if not db_oauth:
            return {"status": "error", "message": "Google account not linked"}

        creds = await self.refresh_if_needed(db, db_oauth)
        service = build('gmail', 'v1', credentials=creds)

        sync_configs = [
            {"label": "INBOX", "limit": 30, "is_inbox": True},
            {"label": "SENT", "limit": 10, "is_inbox": False}
        ]

        synced_count = 0
        all_new_emails = []

        for config in sync_configs:
            # Run in a thread since googleapiclient is synchronous
            results = await asyncio.to_thread(
                service.users().messages().list(
                    userId='me', 
                    labelIds=[config["label"]], 
                    maxResults=config["limit"]
                ).execute
            )
            messages = results.get('messages', [])

            # Filter out messages that already exist in DB
            new_msgs = []
            for m in messages:
                q = select(Email).where(Email.gmail_msg_id == m['id'])
                r = await db.execute(q)
                if not r.scalars().first():
                    new_msgs.append(m)

            if not new_msgs:
                continue

            # Parallel detail fetch
            async def fetch_and_parse(msg):
                data = await asyncio.to_thread(
                    service.users().messages().get(userId='me', id=msg['id'], format='full').execute
                )
                headers = data.get('payload', {}).get('headers', [])
                
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                sender_raw = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
                to_raw = next((h['value'] for h in headers if h['name'].lower() == 'to'), '')
                date_raw = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
                
                from_json = self.parse_address_field(sender_raw)[0] if sender_raw else {"name": "Unknown", "email": ""}
                to_json = self.parse_address_field(to_raw)
                
                try:
                    dt = parsedate_to_datetime(date_raw)
                except:
                    dt = datetime.now(UTC)

                body_raw = self.extract_body(data.get('payload', {}))
                body = self.strip_html(body_raw)

                return Email(
                    user_id=user_id,
                    thread_id=msg['threadId'],
                    gmail_msg_id=msg['id'],
                    from_json=from_json,
                    to_json=to_json,
                    subject=subject,
                    body_text=body,
                    date=dt,
                    is_inbox=config["is_inbox"]
                )

            # Gather all details in parallel for this config
            detail_tasks = [fetch_and_parse(m) for m in new_msgs]
            batch_emails = await asyncio.gather(*detail_tasks)
            all_new_emails.extend(batch_emails)
            synced_count += len(batch_emails)

        if all_new_emails:
            for email in all_new_emails:
                db.add(email)
            await db.commit()
            
        return {"status": "success", "synced": synced_count}

    async def get_messages(self, db: AsyncSession, user_id, label="INBOX"):
        query = select(OAuth).where(OAuth.user_id == user_id, OAuth.provider == "google")
        result = await db.execute(query)
        db_oauth = result.scalars().first()
        
        if not db_oauth:
            return []

        creds = await self.refresh_if_needed(db, db_oauth)
        service = build('gmail', 'v1', credentials=creds)
        
        results = service.users().messages().list(
            userId='me', 
            labelIds=[label], 
            maxResults=50
        ).execute()
        messages = results.get('messages', [])

        detailed_messages = []
        for msg in messages:
            msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            headers = msg_data.get('payload', {}).get('headers', [])
            
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
            snippet = msg_data.get('snippet', '')
            
            # Extract full body
            body = self.extract_body(msg_data.get('payload', {}))

            detailed_messages.append({
                "id": msg['id'],
                "threadId": msg['threadId'],
                "subject": subject,
                "from": sender,
                "date": date,
                "snippet": snippet,
                "body": body
            })
            
        return detailed_messages

    async def get_message_detail(self, db: AsyncSession, user_id, message_id):
        query = select(OAuth).where(OAuth.user_id == user_id, OAuth.provider == "google")
        result = await db.execute(query)
        db_oauth = result.scalars().first()
        
        if not db_oauth:
            return None

        creds = await self.refresh_if_needed(db, db_oauth)
        service = build('gmail', 'v1', credentials=creds)
        
        msg_data = service.users().messages().get(userId='me', id=message_id, format='full').execute()
        
        return msg_data

    async def send_email(self, db: AsyncSession, user_id, to, subject, body):
        query = select(OAuth).where(OAuth.user_id == user_id, OAuth.provider == "google")
        result = await db.execute(query)
        db_oauth = result.scalars().first()
        
        if not db_oauth:
            raise Exception("Google account not linked")

        creds = await self.refresh_if_needed(db, db_oauth)
        service = build('gmail', 'v1', credentials=creds)

        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        msg_body = {'raw': raw}
        sent_msg = service.users().messages().send(userId='me', body=msg_body).execute()
        return sent_msg

gmail_service = GmailService()

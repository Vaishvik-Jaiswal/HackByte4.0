from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.services.gmail_service import gmail_service
from app.classification.pipeline import process_pending_emails_for_user
from app.core.security import verify_token
from app.core.config import settings
import uuid

router = APIRouter(prefix="/gmail", tags=["gmail"])

async def get_current_user_id(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    token = auth_header.split(" ")[1]
    user_id = verify_token(token, settings.JWT_SECRET)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid access token")
    return uuid.UUID(user_id)

@router.get("/messages")
async def get_messages(label: str = "INBOX", user_id: uuid.UUID = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    try:
        return await gmail_service.get_messages(db, user_id, label.upper())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages/{message_id}")
async def get_message_detail(message_id: str, user_id: uuid.UUID = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    try:
        msg = await gmail_service.get_message_detail(db, user_id, message_id)
        if not msg:
            raise HTTPException(status_code=404, detail="Message not found")
        return msg
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync")
async def sync_emails(user_id: uuid.UUID = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    try:
        return await gmail_service.sync_emails(db, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-pending")
async def process_pending_emails(
    user_id: uuid.UUID = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)
):
    """Retry or run AI on any emails with is_processed=false (e.g. after setting GROQ_API_KEY)."""
    try:
        return await process_pending_emails_for_user(db, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send")
async def send_email(request: Request, user_id: uuid.UUID = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    try:
        data = await request.json()
        to = data.get('to')
        subject = data.get('subject')
        body = data.get('body')
        
        if not to or not subject or not body:
            raise HTTPException(status_code=400, detail="Missing required fields: to, subject, body")
            
        return await gmail_service.send_email(db, user_id, to, subject, body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

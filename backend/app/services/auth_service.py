from datetime import datetime, timedelta, UTC
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User, OAuth
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from app.schemas.user import UserCreate
from app.schemas.auth import LoginRequest

class AuthService:
    async def create_user(self, db: AsyncSession, user_in: UserCreate):
        hashed_password = get_password_hash(user_in.password)
        
        new_user = User(
            username=user_in.username,
            email=user_in.email,
            hashed_password=hashed_password,
            provider="local"
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user

    async def authenticate(self, db: AsyncSession, login_data: LoginRequest):
        query = select(User).where((User.email == login_data.identifier) | (User.username == login_data.identifier))
        result = await db.execute(query)
        user = result.scalars().first()
        
        if not user or not user.hashed_password:
            return None
        
        if not verify_password(login_data.password, user.hashed_password):
            return None
            
        return user

    async def store_tokens(self, db: AsyncSession, user_id: uuid.UUID, access_token: str, refresh_token: str):
        db_oauth = OAuth(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            provider="local"
        )
        db.add(db_oauth)
        await db.commit()
        return db_oauth

    async def store_google_tokens(self, db: AsyncSession, user_id: uuid.UUID, google_token: dict):
        # Check if a google provider OAuth record already exists for this user
        query = select(OAuth).where(OAuth.user_id == user_id, OAuth.provider == "google")
        result = await db.execute(query)
        db_oauth = result.scalars().first()
        
        expires_at = None
        if 'expires_at' in google_token:
            expires_at = datetime.fromtimestamp(google_token['expires_at'])
        elif 'expires_in' in google_token:
            expires_at = datetime.now(UTC) + timedelta(seconds=google_token['expires_in'])
            expires_at = expires_at.replace(tzinfo=None)

        if db_oauth:
            db_oauth.access_token = google_token['access_token']
            if 'refresh_token' in google_token:
                db_oauth.refresh_token = google_token['refresh_token']
            db_oauth.expires_at = expires_at
            db_oauth.scope = google_token.get('scope')
        else:
            db_oauth = OAuth(
                user_id=user_id,
                access_token=google_token['access_token'],
                refresh_token=google_token.get('refresh_token'),
                expires_at=expires_at,
                provider="google",
                scope=google_token.get('scope')
            )
            db.add(db_oauth)
            
        await db.commit()
        return db_oauth

    async def logout(self, db: AsyncSession, refresh_token: str):
        query = select(OAuth).where(OAuth.refresh_token == refresh_token)
        result = await db.execute(query)
        db_oauth = result.scalars().first()
        if db_oauth:
            await db.delete(db_oauth)
            await db.commit()
        return True

    async def get_user_by_id(self, db: AsyncSession, user_id: uuid.UUID):
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_user_by_email_or_username(self, db: AsyncSession, email: str, username: str):
        query = select(User).where(
            (User.email == email) | (User.username == username)
        )
        result = await db.execute(query)
        return result.scalars().first()

    async def get_user_by_email(self, db: AsyncSession, email: str):
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        return result.scalars().first()

auth_service = AuthService()

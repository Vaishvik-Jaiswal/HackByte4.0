from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.user import UserCreate, User
from app.schemas.auth import LoginRequest, Token, TokenRefresh
from app.services.auth_service import auth_service
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.core.config import settings
from app.core.oauth import oauth
from app.models.user import User as UserModel
import uuid

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=User)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await auth_service.get_user_by_email_or_username(db, user_in.email, user_in.username)
    if db_user:
        raise HTTPException(status_code=400, detail="User already exists")
    return await auth_service.create_user(db, user_in)

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.authenticate(db, login_data)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    await auth_service.store_tokens(db, user.id, access_token, refresh_token)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/google/login")
async def google_login(request: Request):
    return await oauth.google.authorize_redirect(request, settings.GOOGLE_REDIRECT_URI)

@router.get("/google/callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    profile = token.get('userinfo')
    
    if not profile:
        raise HTTPException(status_code=400, detail="Google authentication failed")
        
    email = profile.get('email')
    user = await auth_service.get_user_by_email(db, email)
    
    if not user:
        user = UserModel(
            email=email,
            username=profile.get('name', email).replace(" ", "_").lower() + "_" + str(uuid.uuid4())[:4],
            provider="google",
            provider_id=profile.get('sub')
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
    # Store Google tokens in the oauth table
    await auth_service.store_google_tokens(db, user.id, token)
        
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    # Store internal JWT refresh token session
    await auth_service.store_tokens(db, user.id, access_token, refresh_token)
    
    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/oauth-success?access_token={access_token}&refresh_token={refresh_token}"
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(data: TokenRefresh, db: AsyncSession = Depends(get_db)):
    user_id = verify_token(data.refresh_token, settings.JWT_REFRESH_SECRET)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
        
    user = await auth_service.get_user_by_id(db, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
        
    access_token = create_access_token(user.id)
    return {
        "access_token": access_token,
        "refresh_token": data.refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/logout")
async def logout(data: TokenRefresh, db: AsyncSession = Depends(get_db)):
    await auth_service.logout(db, data.refresh_token)
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=User)
async def get_me(request: Request, db: AsyncSession = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    token = auth_header.split(" ")[1]
    user_id = verify_token(token, settings.JWT_SECRET)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid access token")
        
    user = await auth_service.get_user_by_id(db, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
        
    return user

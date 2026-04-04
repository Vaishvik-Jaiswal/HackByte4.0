import logging
import sys
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings
from app.api.auth_routes import router as auth_router
from app.api.gmail_routes import router as gmail_router
from app.database.session import engine
from app.database.base import Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("auth-system")

app = FastAPI(title=settings.PROJECT_NAME)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    origin = request.headers.get("origin")
    logger.info(f"--- INCOMING REQUEST: {request.method} {request.url} ---")
    logger.info(f"Origin: {origin}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(f"--- COMPLETED REQUEST: {request.method} {request.url} - Status: {response.status_code} - Time: {process_time:.2f}ms ---")
        return response
    except Exception as e:
        logger.error(f"--- REQUEST FAILED: {request.method} {request.url} - Error: {str(e)} ---")
        import traceback
        logger.error(traceback.format_exc())
        raise e

# Middleware
app.add_middleware(SessionMiddleware, secret_key=settings.JWT_SECRET)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):[0-9]+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(gmail_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup():
    logger.info("Starting up Modern Auth System...")
    try:
        async with engine.begin() as conn:
            # Create all tables if they don't exist
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Successfully connected to the database and ensured tables exist.")
    except Exception as e:
        logger.error(f"DATABASE INITIALIZATION ERROR: {e}")
        logger.warning("Continuing anyway (ensure your fallback or primary DB is accessible later).")

@app.get("/api/health")
async def health_check():
    logger.info("Health check endpoint called")
    return {"status": "ok", "message": "Backend is running and logging!"}

if __name__ == "__main__":
    import os

    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)

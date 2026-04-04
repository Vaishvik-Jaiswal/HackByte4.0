from sqlalchemy.orm import sessionmaker
from app.config import engine

SessionLocal = sessionmaker(bind=engine)

def get_db():
    return SessionLocal()
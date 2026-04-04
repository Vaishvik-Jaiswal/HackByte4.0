from app.db import get_db
from sqlalchemy import text

def get_all_emails():
    db = get_db()
    result = db.execute(text("SELECT * FROM emails"))
    return result.fetchall()
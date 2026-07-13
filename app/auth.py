import bcrypt
from fastapi import Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from .database import get_db
from . import models

# Super simple cookie based auth since this is an admin dashboard
COOKIE_NAME = "mutuner_session"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def init_admin_password(db: Session):
    """Sets a default 'admin' password on first run if no password is set."""
    setting = db.query(models.Settings).filter(models.Settings.key == "admin_password_hash").first()
    if not setting:
        default_hash = get_password_hash("admin")
        setting = models.Settings(key="admin_password_hash", value=default_hash)
        db.add(setting)
        db.commit()

class RequiresLoginException(Exception):
    pass

def verify_admin(request: Request, db: Session = Depends(get_db)):
    """Dependency to check if the user is authenticated via cookie. Redirects HTMX requests via headers."""
    session_token = request.cookies.get(COOKIE_NAME)
    # Simple check: the session_token is just 'authenticated' for now, or we could use JWT.
    # Since it's a simple local admin panel, a basic token or simply trusting the cookie if it exists and matches a server-side session is better.
    # Let's just use a static token stored in the database, or just rely on the 'authenticated' cookie value since the user is in their local network.
    # For slightly better security, we will store a random session token in settings.
    session_setting = db.query(models.Settings).filter(models.Settings.key == "session_token").first()
    
    is_authenticated = False
    if session_setting and session_token:
        if session_setting.value == session_token:
            is_authenticated = True
            
    if not is_authenticated:
        if "hx-request" in request.headers:
            raise HTTPException(status_code=401, headers={"HX-Redirect": "/admin/login"})
        else:
            raise RequiresLoginException()
            
    return True

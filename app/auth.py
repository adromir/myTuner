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
    
    settings = {s.key: s.value for s in db.query(models.Settings).filter(
        models.Settings.key.in_(["session_token", "session_expiry"])
    ).all()}
    
    is_authenticated = False
    if settings.get("session_token") and session_token:
        if settings["session_token"] == session_token:
            import time
            expiry = settings.get("session_expiry")
            if expiry and int(time.time()) < int(expiry):
                is_authenticated = True
            
    if not is_authenticated:
        if "hx-request" in request.headers:
            raise HTTPException(status_code=401, headers={"HX-Redirect": "/admin/login"})
        else:
            raise RequiresLoginException()
            
    return True

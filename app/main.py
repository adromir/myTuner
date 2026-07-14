"""μTuner — FastAPI application entry point.

Sets up logging, database tables, routers, and the background scheduler.
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from .database import engine, Base, SessionLocal
from . import models
from . import mytuner
from .auth import RequiresLoginException, init_admin_password

# Create data directory if not exists
os.makedirs('data', exist_ok=True)

# Create DB tables
Base.metadata.create_all(bind=engine)

# Initialize admin password on first run
db = SessionLocal()
try:
    init_admin_password(db)
finally:
    db.close()

# Setup rotating log handler
log_file = 'data/mytuner.log'
file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
if os.path.exists(log_file):
    try:
        file_handler.doRollover()
    except Exception:
        pass
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Attach to uvicorn and root loggers
for logger_name in ('uvicorn', 'uvicorn.error', 'uvicorn.access'):
    logging.getLogger(logger_name).addHandler(file_handler)

logging.getLogger().addHandler(file_handler)
logging.getLogger().setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: start the background scheduler on startup."""
    from .scheduler import start_scheduler
    start_scheduler()
    yield


app = FastAPI(title="μTuner", lifespan=lifespan)

templates = Jinja2Templates(directory="app/templates")

app.include_router(mytuner.router)

from .routers import admin, stream
app.include_router(admin.router)
app.include_router(stream.router)


@app.get("/", response_class=RedirectResponse)
async def root(request: Request):
    """Redirect root to admin dashboard."""
    return RedirectResponse(url="/admin/", status_code=303)


@app.exception_handler(RequiresLoginException)
async def requires_login_exception_handler(request: Request, exc: RequiresLoginException):
    """Redirect unauthenticated requests to the login page."""
    return RedirectResponse(url="/admin/login", status_code=303)

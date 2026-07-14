from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from .database import engine, Base
from . import models, mytuner
from .auth import RequiresLoginException
from fastapi.responses import RedirectResponse

# Create DB tables
Base.metadata.create_all(bind=engine)

import logging
from logging.handlers import RotatingFileHandler
import os

# Create data directory if not exists
os.makedirs('data', exist_ok=True)

# Setup logging to file
log_file = 'data/mytuner.log'
file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
if os.path.exists(log_file):
    try:
        file_handler.doRollover()
    except Exception:
        pass
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Get uvicorn loggers
for logger_name in ('uvicorn', 'uvicorn.error', 'uvicorn.access'):
    logging.getLogger(logger_name).addHandler(file_handler)

logging.getLogger().addHandler(file_handler)
logging.getLogger().setLevel(logging.INFO)

app = FastAPI(title="μTuner")

# Static files could be mounted here
# app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(mytuner.router)

from .routers import admin, stream
app.include_router(admin.router)
app.include_router(stream.router)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return RedirectResponse(url="/admin/", status_code=303)

@app.exception_handler(RequiresLoginException)
async def requires_login_exception_handler(request: Request, exc: RequiresLoginException):
    return RedirectResponse(url="/admin/login", status_code=303)

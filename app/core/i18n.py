import os
import gettext
from fastapi import Request

LOCALES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "locales")
DOMAIN = "messages"

def get_translation(request: Request):
    accept_language = request.headers.get("Accept-Language", "de")
    langs = [lang.split(";")[0].split(",")[0].strip() for lang in accept_language.split(",")]
    
    try:
        t = gettext.translation(DOMAIN, localedir=LOCALES_DIR, languages=langs)
    except FileNotFoundError:
        t = gettext.translation(DOMAIN, localedir=LOCALES_DIR, languages=["de"], fallback=True)
    
    return t.gettext

def gettext_dummy(message: str) -> str:
    """Dummy gettext for extracting messages."""
    return message

_ = gettext_dummy

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

from fastapi.templating import Jinja2Templates

class I18nJinja2Templates(Jinja2Templates):
    def TemplateResponse(self, request: Request, name: str, context: dict | None = None, **kwargs):
        if context is None:
            context = {}
        # Ensure request is in context as required by FastAPI
        if "request" not in context:
            context["request"] = request
            
        context["_"] = get_translation(request)
        return super().TemplateResponse(request=request, name=name, context=context, **kwargs)

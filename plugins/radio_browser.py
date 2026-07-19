import requests
import logging
from typing import Dict, Any, List
from app.providers import MediaProvider

logger = logging.getLogger(__name__)

class RadioBrowserProvider(MediaProvider):
    @property
    def id(self) -> str: return "radio_browser"
    @property
    def name(self) -> str: return "Radio-Browser.info"
    @property
    def icon(self) -> str: return "radio"
    @property
    def allow_as_source(self) -> bool: return True
    @property
    def allow_as_node(self) -> bool: return False
    
    @property
    def config_schema(self) -> List[Dict[str, Any]]:
        return [
            {"name": "search_type", "label": "Search By", "type": "select", "options": ["tag", "country", "name", "language"], "required": True},
            {"name": "search_term", "label": "Search Term", "type": "text", "required": True, "placeholder": "e.g., jazz, Germany, BBC..."},
            {"name": "limit", "label": "Result Limit", "type": "number", "required": False, "default": 100}
        ]

    def browse_folder(self, config: Dict[str, Any], node_id: int) -> List[Dict[str, Any]]:
        search_type = config.get("search_type", "tag")
        search_term = config.get("search_term", "")
        limit = config.get("limit", 100)
        
        if not search_term:
            return []

        # Find the best API server
        try:
            dns_url = "https://de1.api.radio-browser.info/json/servers"
            servers = requests.get(dns_url, timeout=5).json()
            base_url = f"https://{servers[0]['name']}"
        except Exception:
            base_url = "https://de1.api.radio-browser.info"

        api_url = f"{base_url}/json/stations/search"
        
        # Build query params based on search_type
        params = {
            "limit": limit,
            "hidebroken": "true",
            "order": "clickcount",
            "reverse": "true"
        }
        
        if search_type == "tag":
            params["tag"] = search_term
        elif search_type == "country":
            params["country"] = search_term
        elif search_type == "name":
            params["name"] = search_term
        elif search_type == "language":
            params["language"] = search_term
            
        try:
            logger.info(f"Querying Radio-Browser API: {api_url} with {params}")
            resp = requests.get(api_url, params=params, timeout=10)
            resp.raise_for_status()
            stations = resp.json()
            
            items = []
            for st in stations:
                if not st.get("url_resolved"):
                    continue
                    
                items.append({
                    "id": f"rb_{st['stationuuid']}",
                    "name": st["name"].strip() or "Unknown Station",
                    "type": "audio",
                    "provider": "web_stream", # We reuse the web_stream provider to play the URL
                    "config": {"url": st["url_resolved"]},
                    "image_url": st.get("favicon", "")
                })
            return items
            
        except Exception as e:
            logger.error(f"Radio-Browser API error: {e}")
            return []

    def get_stream_url(self, config: Dict[str, Any]) -> str:
        # Not used since the items map to web_stream
        return ""

def register() -> MediaProvider:
    return RadioBrowserProvider()

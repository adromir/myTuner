from typing import List, Dict, Any
from .base import MediaProvider

class WebStreamProvider(MediaProvider):
    @property
    def id(self) -> str: return "web_stream"
    @property
    def name(self) -> str: return "Web Stream"
    @property
    def icon(self) -> str: return "add_link"
    @property
    def allow_as_source(self) -> bool: return False
    @property
    def allow_as_node(self) -> bool: return True
    @property
    def config_schema(self) -> List[Dict[str, Any]]:
        return [
            {"name": "url", "label": "Stream URL", "type": "text", "required": True, "placeholder": "http://..."}
        ]

    def get_stream_url(self, config: Dict[str, Any]) -> str:
        return config.get("url", "")
    
    def browse_folder(self, config: Dict[str, Any], node_id: int) -> List[Dict[str, Any]]:
        return []

class WebStreamListProvider(MediaProvider):
    @property
    def id(self) -> str: return "web_stream_list"
    @property
    def name(self) -> str: return "Web Stream List"
    @property
    def icon(self) -> str: return "list_alt"
    @property
    def allow_as_source(self) -> bool: return True
    @property
    def allow_as_node(self) -> bool: return True
    @property
    def config_schema(self) -> List[Dict[str, Any]]:
        return [
            {"name": "streams", "label": "Streams (One per line, format: Name|URL)", "type": "textarea", "required": True, "placeholder": "My Radio|http://...\nhttp://another..."}
        ]

    def get_stream_url(self, config: Dict[str, Any]) -> str:
        return ""
    
    def browse_folder(self, config: Dict[str, Any], node_id: int) -> List[Dict[str, Any]]:
        streams = config.get("streams", "")
        items = []
        for line in streams.split("\n"):
            line = line.strip()
            if not line: continue
            parts = line.split("|", 1)
            if len(parts) == 2:
                name, url = parts
            else:
                name, url = line, line
            items.append({
                "id": f"stream_{len(items)}",
                "name": name,
                "type": "audio",
                "config": {"url": url},
                "provider": "web_stream"
            })
        return items

from typing import List, Dict, Any
from .base import MediaProvider

class WebStreamProvider(MediaProvider):
    def get_stream_url(self, config: Dict[str, Any]) -> str:
        return config.get("url", "")
    
    def browse_folder(self, config: Dict[str, Any], node_id: int) -> List[Dict[str, Any]]:
        return []

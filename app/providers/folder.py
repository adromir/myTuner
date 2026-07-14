from typing import List, Dict, Any
from .base import MediaProvider

class FolderProvider(MediaProvider):
    @property
    def id(self) -> str: return "folder"
    @property
    def name(self) -> str: return "Category (Folder)"
    @property
    def icon(self) -> str: return "folder"
    @property
    def allow_as_source(self) -> bool: return False
    @property
    def allow_as_node(self) -> bool: return True
    @property
    def config_schema(self) -> List[Dict[str, Any]]:
        return []

    def get_stream_url(self, config: Dict[str, Any]) -> str:
        return ""
    
    def browse_folder(self, config: Dict[str, Any], node_id: int) -> List[Dict[str, Any]]:
        return []

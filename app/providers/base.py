from abc import ABC, abstractmethod
from typing import List, Dict, Any

class MediaProvider(ABC):
    @property
    @abstractmethod
    def id(self) -> str:
        """Unique identifier for the provider (e.g. 'm3u')"""
        pass
        
    @property
    @abstractmethod
    def name(self) -> str:
        """Human readable name for the provider"""
        pass
        
    @property
    @abstractmethod
    def icon(self) -> str:
        """Material symbols icon name"""
        pass
        
    @property
    @abstractmethod
    def allow_as_source(self) -> bool:
        """Can be added to the dashboard as a background source"""
        pass
        
    @property
    @abstractmethod
    def allow_as_node(self) -> bool:
        """Can be added directly to the explorer tree"""
        pass
        
    @property
    @abstractmethod
    def config_schema(self) -> List[Dict[str, Any]]:
        """
        Returns a list of configuration fields required by the provider.
        Format: [{"name": "url", "label": "Stream URL", "type": "text", "required": True, "placeholder": "..."}]
        Types can be: 'text', 'password', 'smb_path', 'local_path'
        """
        pass

    @abstractmethod
    def get_stream_url(self, config: Dict[str, Any]) -> str:
        """Return the actual audio stream URL for playback."""
        pass
    
    @abstractmethod
    def browse_folder(self, config: Dict[str, Any], node_id: int) -> List[Dict[str, Any]]:
        """Return child nodes (e.g. for dynamic SMB folders or Podcasts)."""
        pass

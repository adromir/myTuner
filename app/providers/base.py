from abc import ABC, abstractmethod
from typing import List, Dict, Any

class MediaProvider(ABC):
    @abstractmethod
    def get_stream_url(self, config: Dict[str, Any]) -> str:
        """Return the actual audio stream URL for playback."""
        pass
    
    @abstractmethod
    def browse_folder(self, config: Dict[str, Any], node_id: int) -> List[Dict[str, Any]]:
        """Return child nodes (e.g. for dynamic SMB folders or Podcasts)."""
        pass

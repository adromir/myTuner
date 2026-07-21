import requests
import logging
from typing import Dict, Any, List
from .base import MediaProvider

logger = logging.getLogger(__name__)

class SomaFMProvider(MediaProvider):
    @property
    def id(self) -> str: return "somafm"
    @property
    def name(self) -> str: return "SomaFM"
    @property
    def icon(self) -> str: return "radio"
    @property
    def allow_as_source(self) -> bool: return True
    @property
    def allow_as_node(self) -> bool: return False
    
    @property
    def config_schema(self) -> List[Dict[str, Any]]:
        return []

    def browse_folder(self, config: Dict[str, Any], node_id: int) -> List[Dict[str, Any]]:
        try:
            logger.info("Fetching SomaFM channels list...")
            resp = requests.get("https://somafm.com/channels.json", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            channels = data.get("channels", [])
            items = []
            
            for ch in channels:
                playlists = ch.get("playlists", [])
                if not playlists: continue
                
                best_pl = playlists[0].get("url")
                for pl in playlists:
                    if pl.get("format") == "mp3" and pl.get("quality") == "highest":
                        best_pl = pl.get("url")
                        break
                        
                items.append({
                    "id": f"soma_{ch.get('id')}",
                    "name": ch.get("title", "SomaFM Channel"),
                    "title": ch.get("title", "SomaFM Channel"),
                    "type": "audio",
                    "provider": "m3u",
                    "config": {"url": best_pl},
                    "stream_url": best_pl,
                    "image_url": ch.get("image", "") or ch.get("xlimage", "")
                })
                
            return items
            
        except Exception as e:
            logger.error(f"SomaFM fetching error: {e}")
            return []

    def get_stream_url(self, config: Dict[str, Any]) -> str:
        return config.get("url", "")

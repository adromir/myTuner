import requests
import logging
from typing import Dict, Any, List
from app.providers import MediaProvider

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
                # SomaFM provides multiple playlists, we will just use the first highest quality one or the default
                playlists = ch.get("playlists", [])
                if not playlists: continue
                
                # We usually get highest quality MP3 or AAC
                best_pl = playlists[0].get("url")
                for pl in playlists:
                    if pl.get("format") == "mp3" and pl.get("quality") == "highest":
                        best_pl = pl.get("url")
                        break
                        
                items.append({
                    "id": f"soma_{ch.get('id')}",
                    "name": ch.get("title", "SomaFM Channel"),
                    "type": "audio",
                    "provider": "m3u", # We can use our built-in M3U provider because SomaFM playlists are M3U or PLS
                    "config": {"url": best_pl},
                    "image_url": ch.get("image", "") or ch.get("xlimage", "")
                })
                
            return items
            
        except Exception as e:
            logger.error(f"SomaFM fetching error: {e}")
            return []

    def get_stream_url(self, config: Dict[str, Any]) -> str:
        # Not used since the items map to m3u provider
        return ""

def register() -> MediaProvider:
    return SomaFMProvider()

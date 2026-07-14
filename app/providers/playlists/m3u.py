from typing import List, Dict, Any
from ..base import MediaProvider
import logging
import urllib.request

logger = logging.getLogger(__name__)

class M3UProvider(MediaProvider):
    @property
    def id(self) -> str: return "m3u"
    @property
    def name(self) -> str: return "M3U Playlist"
    @property
    def icon(self) -> str: return "queue_music"
    @property
    def allow_as_source(self) -> bool: return True
    @property
    def allow_as_node(self) -> bool: return False
    @property
    def config_schema(self) -> List[Dict[str, Any]]:
        return [
            {"name": "url", "label": "M3U URL", "type": "text", "required": True, "placeholder": "http://..."}
        ]

    def get_stream_url(self, config: Dict[str, Any]) -> str:
        return config.get("stream_url", "")
        
    def browse_folder(self, config: Dict[str, Any], node_id: int) -> List[Dict[str, Any]]:
        source_id = config.get("source_id")
        if source_id:
            from ...database import SessionLocal
            from ... import models
            import json
            db = SessionLocal()
            try:
                cache = db.query(models.SourceCache).filter(models.SourceCache.source_id == source_id).first()
                if cache and cache.data:
                    # Update IDs dynamically relative to the node
                    items = json.loads(cache.data)
                    for idx, item in enumerate(items):
                        item["id"] = f"{node_id}_{idx}"
                    return items
            finally:
                db.close()
                
            # Fallback if not cached but source_id provided
            db = SessionLocal()
            try:
                source = db.query(models.Source).filter(models.Source.id == source_id).first()
                if source and source.config:
                    source_config = json.loads(source.config)
                    config["url"] = source_config.get("url", "")
            finally:
                db.close()

        items = []
        m3u_url = config.get("url", "")
        if not m3u_url:
            return items
            
        try:
            if m3u_url.startswith("http://") or m3u_url.startswith("https://"):
                req = urllib.request.Request(m3u_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    content = response.read().decode('utf-8')
            else:
                with open(m3u_url, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
            import re
            lines = content.splitlines()
            current_title = "Unknown Stream"
            current_logo = None
            idx = 0
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("#EXTINF:"):
                    # Extract title
                    parts = line.split(",", 1)
                    if len(parts) > 1:
                        current_title = parts[1].strip()
                    
                    # Extract logo
                    logo_match = re.search(r'tvg-logo="([^"]+)"', line)
                    if logo_match:
                        current_logo = logo_match.group(1)
                elif not line.startswith("#"):
                    # This is a URL
                    items.append({
                        "type": "Station",
                        "id": f"{node_id}_{idx}",
                        "title": current_title,
                        "stream_url": line,
                        "image_url": current_logo
                    })
                    idx += 1
                    current_title = f"Unknown Stream {idx+1}"
                    current_logo = None
                    
        except Exception as e:
            logger.error(f"Error parsing M3U: {e}")
            
        return items

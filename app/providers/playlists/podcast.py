from typing import List, Dict, Any
from ..base import MediaProvider
import logging
import feedparser

logger = logging.getLogger(__name__)

class PodcastProvider(MediaProvider):
    @property
    def id(self) -> str: return "podcast"
    @property
    def name(self) -> str: return "RSS Podcast"
    @property
    def icon(self) -> str: return "podcasts"
    @property
    def allow_as_source(self) -> bool: return True
    @property
    def allow_as_node(self) -> bool: return False
    @property
    def config_schema(self) -> List[Dict[str, Any]]:
        return [
            {"name": "url", "label": "Podcast RSS URL", "type": "text", "required": True, "placeholder": "https://..."}
        ]

    def get_stream_url(self, config: Dict[str, Any]) -> str:
        # For podcasts, the dynamic item stream URL is directly the audio file URL from the feed
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
        feed_url = config.get("url", "")
        if not feed_url:
            return items
            
        try:
            feed = feedparser.parse(feed_url)
            for idx, entry in enumerate(feed.entries):
                # Find audio enclosure
                audio_url = None
                for link in entry.get("links", []):
                    if link.get("type", "").startswith("audio/"):
                        audio_url = link.get("href")
                        break
                        
                if audio_url:
                    # Try to get image from entry or feed
                    image_url = ""
                    if "image" in entry and hasattr(entry.image, "href"):
                        image_url = entry.image.href
                    elif "image" in feed.feed and hasattr(feed.feed.image, "href"):
                        image_url = feed.feed.image.href

                    items.append({
                        "type": "Podcast",
                        "id": f"{node_id}_{idx}",
                        "title": entry.get("title", f"Episode {idx+1}"),
                        "desc": entry.get("summary", ""),
                        "stream_url": audio_url,
                        "image_url": image_url
                    })
        except Exception as e:
            logger.error(f"Error parsing podcast: {e}")
            
        return items

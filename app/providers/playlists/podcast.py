from typing import List, Dict, Any
from ..base import MediaProvider
import feedparser

class PodcastProvider(MediaProvider):
    def get_stream_url(self, config: Dict[str, Any]) -> str:
        # For podcasts, the dynamic item stream URL is directly the audio file URL from the feed
        return config.get("stream_url", "")
        
    def browse_folder(self, config: Dict[str, Any], node_id: int) -> List[Dict[str, Any]]:
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
            print(f"Error parsing podcast: {e}")
            
        return items

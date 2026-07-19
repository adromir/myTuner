import requests
import logging
from bs4 import BeautifulSoup
from typing import Dict, Any, List
from app.providers import MediaProvider

logger = logging.getLogger(__name__)

class PodcastDeProvider(MediaProvider):
    @property
    def id(self) -> str: return "podcast_de"
    @property
    def name(self) -> str: return "podcast.de"
    @property
    def icon(self) -> str: return "podcasts"
    @property
    def allow_as_source(self) -> bool: return True
    @property
    def allow_as_node(self) -> bool: return True
    
    @property
    def config_schema(self) -> List[Dict[str, Any]]:
        return [
            {"name": "url", "label": "Podcast URL", "type": "url", "required": True, "placeholder": "https://www.podcast.de/podcast/... or episode URL"}
        ]

    def browse_folder(self, config: Dict[str, Any], node_id: int) -> List[Dict[str, Any]]:
        url = config.get("url", "")
        if not url:
            return []

        try:
            logger.info(f"Scraping podcast.de: {url}")
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Check if it's already an episode page
            og_audio = soup.find("meta", property="og:audio")
            if og_audio:
                title = soup.find("meta", property="og:title")
                image = soup.find("meta", property="og:image")
                
                return [{
                    "id": f"pde_{hash(url)}",
                    "name": title["content"] if title else "Unknown Episode",
                    "type": "audio",
                    "provider": "podcast_de",
                    "config": {"url": url},
                    "image_url": image["content"] if image else ""
                }]
                
            # Otherwise, assume it's a show page and look for episode links
            items = []
            
            # Heuristic: podcast.de episode links usually contain '/episode/'
            episode_links = soup.select("a[href*='/episode/']")
            
            # Deduplicate by URL
            seen_urls = set()
            
            for a in episode_links:
                ep_url = a.get("href")
                if not ep_url: continue
                
                if ep_url.startswith("/"):
                    ep_url = "https://www.podcast.de" + ep_url
                    
                if ep_url in seen_urls:
                    continue
                seen_urls.add(ep_url)
                
                ep_title = a.get_text(strip=True)
                if not ep_title:
                    # Sometimes the title is in a child element
                    title_elem = a.find(class_="title") or a.find(["h3", "h4", "strong"])
                    if title_elem:
                        ep_title = title_elem.get_text(strip=True)
                        
                if not ep_title:
                    ep_title = "Episode"

                # Find the nearest image
                img = a.find("img")
                img_url = img.get("src") if img else ""
                if img_url and img_url.startswith("/"):
                    img_url = "https://www.podcast.de" + img_url

                items.append({
                    "id": f"pde_{hash(ep_url)}",
                    "name": ep_title,
                    "type": "audio",
                    "provider": "podcast_de",
                    "config": {"url": ep_url},
                    "image_url": img_url
                })
                
            return items
            
        except Exception as e:
            logger.error(f"podcast.de scraping error: {e}")
            return []

    def get_stream_url(self, config: Dict[str, Any]) -> str:
        url = config.get("url", "")
        if not url:
            return ""
            
        try:
            logger.info(f"Resolving audio stream for podcast.de episode: {url}")
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            og_audio = soup.find("meta", property="og:audio")
            
            if og_audio and og_audio.get("content"):
                return og_audio["content"]
                
            return ""
            
        except Exception as e:
            logger.error(f"podcast.de audio resolution error: {e}")
            return ""

def register() -> MediaProvider:
    return PodcastDeProvider()

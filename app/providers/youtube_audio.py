import logging
import yt_dlp
from typing import Dict, Any, List
from .base import MediaProvider

logger = logging.getLogger(__name__)

class YouTubeProvider(MediaProvider):
    @property
    def id(self) -> str: return "youtube_audio"
    @property
    def name(self) -> str: return "YouTube Audio"
    @property
    def icon(self) -> str: return "smart_display"
    @property
    def allow_as_source(self) -> bool: return True
    @property
    def allow_as_node(self) -> bool: return True
    
    @property
    def config_schema(self) -> List[Dict[str, Any]]:
        return [
            {"name": "url", "label": "YouTube URL", "type": "text", "required": True, "placeholder": "https://www.youtube.com/watch?v=... or playlist URL"}
        ]

    def _extract_info(self, url: str, flat: bool = True) -> Dict[str, Any]:
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist' if flat else False,
            'noplaylist': not flat
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    def browse_folder(self, config: Dict[str, Any], node_id: int) -> List[Dict[str, Any]]:
        url = config.get("url", "")
        if not url:
            return []

        try:
            logger.info(f"Extracting YouTube info for: {url}")
            info = self._extract_info(url, flat=True)
            
            items = []
            if 'entries' in info:
                # It's a playlist
                for entry in info['entries']:
                    if not entry: continue
                    entry_url = entry.get('url') or entry.get('webpage_url')
                    if not entry_url and entry.get('id'):
                        entry_url = f"https://www.youtube.com/watch?v={entry['id']}"
                        
                    items.append({
                        "id": f"yt_{entry.get('id', 'unknown')}",
                        "name": entry.get('title', 'Unknown Video'),
                        "title": entry.get('title', 'Unknown Video'),
                        "type": "audio",
                        "provider": "youtube_audio",
                        "config": {"url": entry_url},
                        "image_url": entry.get('thumbnails', [{}])[-1].get('url', '') if entry.get('thumbnails') else ''
                    })
            else:
                # It's a single video
                items.append({
                    "id": f"yt_{info.get('id', 'unknown')}",
                    "name": info.get('title', 'Unknown Video'),
                    "title": info.get('title', 'Unknown Video'),
                    "type": "audio",
                    "provider": "youtube_audio",
                    "config": {"url": url},
                    "image_url": info.get('thumbnail', '')
                })
            return items
            
        except Exception as e:
            logger.error(f"YouTube extraction error: {e}")
            return []

    def get_stream_url(self, config: Dict[str, Any]) -> str:
        url = config.get("url", "")
        if not url:
            return ""
            
        try:
            # We must NOT use extract_flat here, we need the actual stream URL
            info = self._extract_info(url, flat=False)
            
            # Find the best audio format URL
            if 'url' in info:
                return info['url']
            elif 'formats' in info:
                for f in reversed(info['formats']):
                    if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                        return f['url']
                # Fallback to the first available format
                return info['formats'][-1]['url']
                
            return ""
            
        except Exception as e:
            logger.error(f"YouTube stream resolution error: {e}")
            return ""

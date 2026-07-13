from typing import List, Dict, Any
from ..base import MediaProvider
import urllib.request

class M3UProvider(MediaProvider):
    def get_stream_url(self, config: Dict[str, Any]) -> str:
        return config.get("stream_url", "")
        
    def browse_folder(self, config: Dict[str, Any], node_id: int) -> List[Dict[str, Any]]:
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
            print(f"Error parsing M3U: {e}")
            
        return items

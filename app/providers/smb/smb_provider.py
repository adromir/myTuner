from typing import List, Dict, Any
from ..base import MediaProvider
import smbclient
from urllib.parse import urlparse, unquote

class SMBProvider(MediaProvider):
    def _parse_url(self, smb_url: str):
        # smb://user:pass@host/share/path
        parsed = urlparse(smb_url)
        host = parsed.hostname
        user = unquote(parsed.username) if parsed.username else None
        password = unquote(parsed.password) if parsed.password else None
        path = parsed.path.replace('/', '\\')
        unc_path = r"\\" + host + path
        return host, user, password, unc_path
        
    def get_stream_url(self, config: Dict[str, Any]) -> str:
        if "file_path" in config:
            return config["file_path"]
        path = config.get("path", "")
        return path
        
    def browse_folder(self, config: Dict[str, Any], node_id: int) -> List[Dict[str, Any]]:
        items = []
        smb_url = config.get("path", "")
        if not smb_url:
            return items
            
        try:
            host, user, password, unc_path = self._parse_url(smb_url)
            if user:
                smbclient.register_session(host, username=user, password=password)
            else:
                smbclient.register_session(host, username="guest", password="")
                
            for idx, entry in enumerate(smbclient.scandir(unc_path)):
                entry_url = f"{smb_url.rstrip('/')}/{entry.name}"
                if entry.is_dir():
                    items.append({
                        "type": "Dir",
                        "id": f"{node_id}_{idx}",
                        "title": entry.name,
                        "path": entry_url
                    })
                elif entry.name.lower().endswith(('.mp3', '.m4a', '.aac', '.wav', '.flac', '.ogg')):
                    items.append({
                        "type": "Station",
                        "id": f"{node_id}_{idx}",
                        "title": entry.name,
                        "stream_url": entry_url,
                        "path": entry_url
                    })
        except Exception as e:
            print(f"SMB Browse error: {e}")
            
        return items

from typing import List, Dict, Any
from ..base import MediaProvider
import logging

logger = logging.getLogger(__name__)

class LocalProvider(MediaProvider):
    @property
    def id(self) -> str: return "local_dir"
    @property
    def name(self) -> str: return "Local Directory"
    @property
    def icon(self) -> str: return "hard_drive"
    @property
    def allow_as_source(self) -> bool: return True
    @property
    def allow_as_node(self) -> bool: return True
    @property
    def config_schema(self) -> List[Dict[str, Any]]:
        return [
            {"name": "path", "label": "Directory Path", "type": "local_path", "required": True, "placeholder": "/media/music"}
        ]

    def get_stream_url(self, config: Dict[str, Any]) -> str:
        # Expected config: {"path": "/media/music/song.mp3"}
        path = config.get("path", "")
        # If the node itself is a file, return it
        # If it's a dynamic child from browse_folder, it comes from the _full_node_id or directly from config if we passed it?
        # Actually, in `stream.py`:
        # `config["_full_node_id"]` contains the node_id string.
        # But wait, local files could be added individually? If added individually, `config["path"]` is the file.
        # If added as a directory, the dynamic child `id` is `123_index`.
        # I'll rely on config["path"] being the actual path.
        if "file_path" in config:
            return f"local://{config['file_path']}"
        return f"local://{path}"
        
    def browse_folder(self, config: Dict[str, Any], node_id: int) -> List[Dict[str, Any]]:
        import os
        items = []
        path = config.get("path", "")
        if not path or not os.path.isdir(path):
            return items
            
        try:
            for idx, entry in enumerate(sorted(os.listdir(path))):
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):
                    items.append({
                        "type": "Dir",
                        "id": f"{node_id}_{idx}",
                        "title": entry,
                        "path": full_path
                    })
                elif entry.lower().endswith(('.mp3', '.m4a', '.aac', '.wav', '.flac', '.ogg')):
                    items.append({
                        "type": "Station",
                        "id": f"{node_id}_{idx}",
                        "title": entry,
                        "stream_url": f"local://{full_path}",
                        "path": full_path
                    })
        except Exception as e:
            logger.error(f"Error browsing local dir {path}: {e}")
            
        return items

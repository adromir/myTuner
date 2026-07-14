import json
from typing import Dict, Type, List, Any
from .base import MediaProvider
from .streams import WebStreamProvider
from .playlists.m3u import M3UProvider
from .playlists.podcast import PodcastProvider
from .smb.smb_provider import SMBProvider
from .local.local_provider import LocalProvider
from .folder import FolderProvider

_providers: Dict[str, MediaProvider] = {
    "web_stream": WebStreamProvider(),
    "m3u": M3UProvider(),
    "podcast": PodcastProvider(),
    "smb": SMBProvider(),
    "local_dir": LocalProvider(),
    "folder": FolderProvider()
}

def get_provider(name: str) -> MediaProvider:
    return _providers.get(name)

def get_all_providers() -> List[MediaProvider]:
    return list(_providers.values())


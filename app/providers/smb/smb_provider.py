"""SMB Share media provider.

Provides access to audio files on SMB/CIFS network shares.
Credentials are stored as separate config fields, never embedded in URLs.
"""
from typing import List, Dict, Any, Optional, Tuple
from ..base import MediaProvider
import smbclient
from urllib.parse import urlparse, unquote
import logging

logger = logging.getLogger(__name__)


class SMBProvider(MediaProvider):
    """Provider for browsing and streaming audio from SMB network shares."""

    @property
    def id(self) -> str: return "smb"
    @property
    def name(self) -> str: return "SMB Share"
    @property
    def icon(self) -> str: return "lan"
    @property
    def allow_as_source(self) -> bool: return True
    @property
    def allow_as_node(self) -> bool: return True
    @property
    def config_schema(self) -> List[Dict[str, Any]]:
        return [
            {"name": "host", "label": "Hostname/IP", "type": "text", "required": True, "placeholder": "192.168.1.100"},
            {"name": "path", "label": "Share / Path", "type": "smb_path", "required": True, "placeholder": "music"},
            {"name": "user", "label": "Username", "type": "text", "required": False, "placeholder": "guest"},
            {"name": "pass", "label": "Password", "type": "password", "required": False, "placeholder": ""}
        ]

    def _resolve_config(self, config: Dict[str, Any]) -> Tuple[str, Optional[str], Optional[str], str]:
        """Resolve SMB config into (host, user, password, unc_path).

        Supports both new format (individual fields) and legacy URL format
        for backward compatibility with existing database entries.
        """
        host = config.get("host")
        user = config.get("user") or None
        password = config.get("pass") or None
        share_path = config.get("path", "")

        # Legacy format: path contains a full smb:// URL
        if share_path.startswith("smb://"):
            return self._parse_url(share_path)

        # New format: individual fields
        if not host:
            return "", None, None, ""

        # Build UNC path from host + share_path
        share_path = share_path.strip("/").replace("/", "\\")
        unc_path = f"\\\\{host}\\{share_path}"
        return host, user, password, unc_path

    def _parse_url(self, smb_url: str) -> Tuple[str, Optional[str], Optional[str], str]:
        """Parse legacy smb://user:pass@host/share/path URLs."""
        parsed = urlparse(smb_url)
        host = parsed.hostname or ""
        user = unquote(parsed.username) if parsed.username else None
        password = unquote(parsed.password) if parsed.password else None
        path = parsed.path.replace('/', '\\')
        unc_path = f"\\\\{host}{path}"
        return host, user, password, unc_path

    def _build_smb_url(self, config: Dict[str, Any]) -> str:
        """Build an smb:// URL from config fields (for streaming, never stored)."""
        host = config.get("host", "")
        share_path = config.get("path", "")

        # If path is already a full URL, return it
        if share_path.startswith("smb://"):
            return share_path

        user = config.get("user", "")
        password = config.get("pass", "")
        share_path = share_path.strip("/")
        auth_part = f"{user}:{password}@" if user else ""
        return f"smb://{auth_part}{host}/{share_path}"

    def _register_session(self, host: str, user: Optional[str], password: Optional[str]) -> None:
        """Register an SMB session with proper credential handling."""
        if user:
            smbclient.register_session(host, username=user, password=password or "")
        else:
            smbclient.register_session(host, username="guest", password="")

    def get_stream_url(self, config: Dict[str, Any]) -> str:
        """Return the SMB URL for streaming."""
        if "file_path" in config:
            return config["file_path"]
        return self._build_smb_url(config)

    def browse_folder(self, config: Dict[str, Any], node_id: int) -> List[Dict[str, Any]]:
        """List audio files and subdirectories in the configured SMB path."""
        items = []
        host, user, password, unc_path = self._resolve_config(config)
        if not host or not unc_path:
            return items

        try:
            self._register_session(host, user, password)

            smb_url = self._build_smb_url(config)
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
            logger.error(f"SMB Browse error for {host}: {e}")

        return items

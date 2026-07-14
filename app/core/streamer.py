"""Audio file streaming helpers for local and SMB files."""
import os
import logging
from fastapi import Request, HTTPException
from fastapi.responses import StreamingResponse
import smbclient
from urllib.parse import urlparse, unquote

logger = logging.getLogger(__name__)


def stream_local_file(file_path: str, request: Request):
    """Stream a local audio file."""
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    def iterfile():
        with open(file_path, mode="rb") as file_like:
            yield from file_like

    return StreamingResponse(iterfile(), media_type="audio/mpeg")


def stream_smb_file(smb_url: str, request: Request):
    """Stream an audio file from an SMB share."""
    parsed = urlparse(smb_url)
    host = parsed.hostname
    user = unquote(parsed.username) if parsed.username else None
    password = unquote(parsed.password) if parsed.password else None
    path = parsed.path.replace('/', '\\')
    unc_path = f"\\\\{host}{path}"

    try:
        if user:
            smbclient.register_session(host, username=user, password=password or "")
        else:
            smbclient.register_session(host, username="guest", password="")

        def iterfile():
            with smbclient.open_file(unc_path, mode="rb") as file_like:
                while chunk := file_like.read(1024 * 1024):
                    yield chunk

        return StreamingResponse(iterfile(), media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"SMB stream error for {host}: {e}")
        raise HTTPException(status_code=500, detail="Failed to stream SMB file")

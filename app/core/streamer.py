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
        with open(file_path, mode="rb") as f:
            while chunk := f.read(1024 * 1024):
                yield chunk

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

def stream_transcoded(stream_url: str, request: Request):
    """Transcode a stream (HTTP, local, or SMB) to MP3 128k using FFmpeg."""
    import subprocess
    import threading
    
    cmd = [
        "ffmpeg",
        "-nostdin",
        "-i", "pipe:0" if stream_url.startswith("smb://") else stream_url,
        "-c:a", "libmp3lame",
        "-b:a", "128k",
        "-f", "mp3",
        "pipe:1"
    ]
    
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE if stream_url.startswith("smb://") else None, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    # If it's an SMB URL, we need a background thread to read from smbclient and write to ffmpeg's stdin
    if stream_url.startswith("smb://"):
        parsed = urlparse(stream_url)
        host = parsed.hostname
        user = unquote(parsed.username) if parsed.username else None
        password = unquote(parsed.password) if parsed.password else None
        path = parsed.path.replace('/', '\\')
        unc_path = f"\\\\{host}{path}"
        
        def pump_smb_to_ffmpeg():
            try:
                if user:
                    smbclient.register_session(host, username=user, password=password or "")
                else:
                    smbclient.register_session(host, username="guest", password="")
                with smbclient.open_file(unc_path, mode="rb") as file_like:
                    while chunk := file_like.read(1024 * 1024):
                        process.stdin.write(chunk)
                        process.stdin.flush()
            except Exception as e:
                logger.error(f"SMB to FFmpeg pump error: {e}")
            finally:
                try:
                    process.stdin.close()
                except:
                    pass
        
        t = threading.Thread(target=pump_smb_to_ffmpeg, daemon=True)
        t.start()
        
    def iterfile():
        try:
            while chunk := process.stdout.read(65536):
                yield chunk
        finally:
            process.stdout.close()
            process.kill()
            process.wait()
            
    return StreamingResponse(iterfile(), media_type="audio/mpeg")

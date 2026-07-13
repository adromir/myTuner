import os
from fastapi import Request
from fastapi.responses import StreamingResponse

def stream_local_file(file_path: str, request: Request):
    if not os.path.exists(file_path):
        return StreamingResponse(iter(["File not found"]), status_code=404)
        
    def iterfile():
        with open(file_path, mode="rb") as file_like:
            yield from file_like

    return StreamingResponse(iterfile(), media_type="audio/mpeg")

def stream_smb_file(smb_url: str, request: Request):
    import smbclient
    from urllib.parse import urlparse, unquote
    
    parsed = urlparse(smb_url)
    host = parsed.hostname
    user = unquote(parsed.username) if parsed.username else None
    password = unquote(parsed.password) if parsed.password else None
    path = parsed.path.replace('/', '\\')
    unc_path = r"\\" + host + path
    
    try:
        if user:
            smbclient.register_session(host, username=user, password=password)
        else:
            smbclient.register_session(host, username="guest", password="")
            
        def iterfile():
            with smbclient.open_file(unc_path, mode="rb") as file_like:
                while chunk := file_like.read(1024 * 1024):
                    yield chunk
                    
        return StreamingResponse(iterfile(), media_type="audio/mpeg")
    except Exception as e:
        return StreamingResponse(iter([f"Error: {e}".encode()]), status_code=500)

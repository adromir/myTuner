from fastapi import APIRouter, Request, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse, RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from ..providers import get_provider
import json

router = APIRouter()

@router.get("/stream/{node_id}")
async def stream_media(request: Request, node_id: str, db: Session = Depends(get_db)):
    # node_id might be "123" or "123_episode_1" (for dynamic children)
    base_id = node_id.split('_')[0]
    
    if not base_id.isdigit():
        raise HTTPException(status_code=404, detail="Invalid node ID")
        
    node = db.query(models.Node).filter(models.Node.id == int(base_id)).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
        
    # MAC-Sensitive History Tracking
    client_ip = request.client.host
    client = db.query(models.Client).filter(models.Client.last_ip == client_ip).first()
    if client:
        hist = models.History(mac_address=client.mac_address, node_id=node.id)
        db.add(hist)
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            
    provider = get_provider(node.provider)
    if not provider:
        raise HTTPException(status_code=500, detail="Provider not found")
        
    config = {}
    if node.provider_config:
        try:
            config = json.loads(node.provider_config)
        except (json.JSONDecodeError, TypeError):
            config = {"url": node.provider_config, "path": node.provider_config}
            
    # Allow the provider to resolve the exact URL (it might need the full node_id for dynamic items)
    # E.g. node_id="123_ep_0"
    config["_full_node_id"] = node_id
    
    stream_url = provider.get_stream_url(config)
    
    if not stream_url:
        raise HTTPException(status_code=404, detail="Stream URL not found")
        
    # TODO: Implement FFmpeg transcoding here if node.use_transcoding is True
    # For now, just redirect or stream directly
    
    if stream_url.startswith("http://") or stream_url.startswith("https://"):
        return RedirectResponse(url=stream_url, status_code=302)
    elif stream_url.startswith("local://"):
        # Local file
        file_path = stream_url[8:]
        from ..core.streamer import stream_local_file
        return stream_local_file(file_path, request)
    elif stream_url.startswith("smb://"):
        # SMB file
        from ..core.streamer import stream_smb_file
        return stream_smb_file(stream_url, request)
        
    raise HTTPException(status_code=500, detail="Unknown stream protocol")

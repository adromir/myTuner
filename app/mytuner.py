from fastapi import APIRouter, Request, Depends, Query, Response
from sqlalchemy.orm import Session
from .database import get_db
from . import models
from typing import List

router = APIRouter()

import html

def get_host_url(request: Request, db: Session) -> str:
    setting = db.query(models.Settings).filter(models.Settings.key == "host_url").first()
    if setting and setting.value:
        return setting.value.rstrip('/')
    return str(request.base_url).rstrip('/')

def generate_vtuner_xml(items: List[dict], nav_host: str, stream_host: str, brand: str, mac: str) -> str:
    xml = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>']
    xml.append('<ListOfItems>')
    xml.append(f'    <ItemCount>{len(items)}</ItemCount>')
    for item in items:
        xml.append('    <Item>')
        if item["type"] == "Dir":
            xml.append('        <ItemType>Dir</ItemType>')
            xml.append(f'        <Title>{html.escape(item["title"])}</Title>')
            url = f"{nav_host}/setupapp/{brand}/asp/browseXML/navXML.asp?node_id={item['id']}&amp;mac={html.escape(mac)}"
            xml.append(f'        <Url>{url}</Url>')
        elif item["type"] == "Station":
            xml.append('        <ItemType>Station</ItemType>')
            xml.append(f'        <Title>{html.escape(item["title"])}</Title>')
            # Streaming endpoint
            stream_url = f"{stream_host}/stream/{item['id']}"
            if "stream_url_override" in item:
                stream_url = item["stream_url_override"]
            xml.append(f'        <StationUrl>{html.escape(stream_url)}</StationUrl>')
            desc = item.get("desc", item["title"])
            xml.append(f'        <StationDesc>{html.escape(desc)}</StationDesc>')
            xml.append('        <StationFormat>MP3</StationFormat>')
            if item.get("logo"):
                xml.append(f'        <Logo>{html.escape(item["logo"])}</Logo>')
        xml.append('    </Item>')
    xml.append('</ListOfItems>')
    return "\n".join(xml)

def check_mac_access(mac: str, allowed_macs: str) -> bool:
    if not allowed_macs:
        return True
    macs = [m.strip().lower() for m in allowed_macs.split(',') if m.strip()]
    if not macs:
        return True
    return mac.lower() in macs

@router.get("/setupapp/{brand}/asp/browseXML/loginXML.asp")
async def mytuner_login(request: Request, brand: str, mac: str = Query(""), db: Session = Depends(get_db)):
    stream_host = get_host_url(request, db)
    nav_host = str(request.base_url).rstrip('/')
    
    # Get root nodes
    nodes = db.query(models.Node).filter(models.Node.parent_id == None).all()
    
    items = []
    for node in nodes:
        if not check_mac_access(mac, node.allowed_macs):
            continue
            
        if node.provider == "folder":
            items.append({
                "type": "Dir",
                "id": node.id,
                "title": node.name
            })
        else:
            item_data = {
                "type": "Station",
                "id": node.id,
                "title": node.name,
                "logo": node.image_url
            }
            if node.provider == "web_stream" and not node.use_transcoding:
                try:
                    import json
                    cfg = json.loads(node.provider_config) if node.provider_config else {}
                    if "url" in cfg:
                        item_data["stream_url_override"] = cfg["url"]
                except (json.JSONDecodeError, TypeError):
                    pass
            items.append(item_data)
            
    xml_content = generate_vtuner_xml(items, nav_host, stream_host, brand, mac)
    return Response(content=xml_content, media_type="application/xml")

@router.get("/setupapp/{brand}/asp/browseXML/navXML.asp")
async def mytuner_nav(request: Request, brand: str, node_id: int = Query(...), mac: str = Query(""), db: Session = Depends(get_db)):
    stream_host = get_host_url(request, db)
    nav_host = str(request.base_url).rstrip('/')
    
    # We may need to get children from DB or dynamically from a provider
    node = db.query(models.Node).filter(models.Node.id == node_id).first()
    if not node:
        return Response(content='<?xml version="1.0" encoding="UTF-8"?><ListOfItems><ItemCount>0</ItemCount></ListOfItems>', media_type="application/xml")
        
    items = []
    
    # Normal DB folder
    if node.provider == "folder":
        children = db.query(models.Node).filter(models.Node.parent_id == node_id).all()
        for child in children:
            if not check_mac_access(mac, child.allowed_macs):
                continue
                
            if child.provider == "folder":
                items.append({
                    "type": "Dir",
                    "id": child.id,
                    "title": child.name
                })
            else:
                item_data = {
                    "type": "Station",
                    "id": child.id,
                    "title": child.name,
                    "logo": child.image_url
                }
                if child.provider == "web_stream" and not child.use_transcoding:
                    try:
                        import json
                        cfg = json.loads(child.provider_config) if child.provider_config else {}
                        if "url" in cfg:
                            item_data["stream_url_override"] = cfg["url"]
                    except (json.JSONDecodeError, TypeError):
                        pass
                items.append(item_data)
    else:
        # Dynamic provider
        from .providers import get_provider
        import json
        provider = get_provider(node.provider)
        if provider:
            config = {}
            if node.provider_config:
                try:
                    config = json.loads(node.provider_config)
                except (json.JSONDecodeError, TypeError):
                    pass
            # Fallback if config is stored as plain string in older version
            if not isinstance(config, dict):
                config = {"url": node.provider_config, "path": node.provider_config}
                
            dynamic_items = provider.browse_folder(config, node.id)
            for d_item in dynamic_items:
                item_data = {
                    "type": d_item.get("type", "Station"),
                    "id": d_item.get("id"),
                    "title": d_item.get("title"),
                    "logo": d_item.get("logo") or node.image_url,
                    "desc": d_item.get("desc")
                }
                if not node.use_transcoding and d_item.get("stream_url"):
                    item_data["stream_url_override"] = d_item.get("stream_url")
                items.append(item_data)
        
    xml_content = generate_vtuner_xml(items, nav_host, stream_host, brand, mac)
    return Response(content=xml_content, media_type="application/xml")

@router.get("/setupapp/{brand}/asp/browseXML/statXML.asp")
async def mytuner_stat(request: Request):
    return Response(content='<?xml version="1.0" encoding="UTF-8"?><ListOfItems><ItemCount>0</ItemCount></ListOfItems>', media_type="application/xml")

@router.get("/setupapp/{brand}/asp/browseXML/mac_check.asp")
@router.get("/setupapp/{brand}/asp/browseXML/maccheck.asp")
async def mytuner_mac_check(request: Request):
    return Response(content='<?xml version="1.0" encoding="UTF-8"?><ListOfItems><ItemCount>0</ItemCount></ListOfItems>', media_type="application/xml")

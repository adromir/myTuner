from fastapi import APIRouter, Request, Depends, Form, HTTPException, Response, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from ..auth import verify_admin, verify_password, get_password_hash, init_admin_password, COOKIE_NAME
import json
import uuid
import os
from pathlib import Path

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None):
    return templates.TemplateResponse(request=request, name="login.html", context={"request": request, "error": error})

@router.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, response: Response, password: str = Form(...), db: Session = Depends(get_db)):
    init_admin_password(db)
    setting = db.query(models.Settings).filter(models.Settings.key == "admin_password_hash").first()
    
    if setting and verify_password(password, setting.value):
        # Create session token
        token = str(uuid.uuid4())
        session_setting = db.query(models.Settings).filter(models.Settings.key == "session_token").first()
        if session_setting:
            session_setting.value = token
        else:
            session_setting = models.Settings(key="session_token", value=token)
            db.add(session_setting)
        db.commit()
        
        redirect = RedirectResponse(url="/admin/", status_code=303)
        redirect.set_cookie(key=COOKIE_NAME, value=token, httponly=True)
        return redirect
    else:
        return templates.TemplateResponse(request=request, name="login.html", context={"request": request, "error": "Invalid password"})

@router.get("/logout")
async def logout(response: Response):
    redirect = RedirectResponse(url="/admin/login", status_code=303)
    redirect.delete_cookie(COOKIE_NAME)
    return redirect

@router.get("/", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    nodes = db.query(models.Node).all()
    root_nodes = [n for n in nodes if n.parent_id is None]
    sources = db.query(models.Source).all()
    
    # Check if this is an HTMX request for the root content or full page load
    if "hx-request" in request.headers and "hx-target" in request.headers:
        # Client just wants the right-side main content for the root
        return templates.TemplateResponse(request=request, name="partials/main_content.html", context={
            "request": request,
            "selected_node": None,
            "list_nodes": root_nodes,
            "all_nodes": nodes,
            "sources": sources
        })

    return templates.TemplateResponse(request=request, name="admin.html", context={
        "request": request,
        "nodes": root_nodes,
        "all_nodes": nodes,
        "selected_node": None,
        "list_nodes": root_nodes,
        "sources": sources
    })

@router.get("/nodes/{node_id}", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def get_node_content(request: Request, node_id: int, db: Session = Depends(get_db)):
    node = db.query(models.Node).filter(models.Node.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404)
        
    children = db.query(models.Node).filter(models.Node.parent_id == node_id).all()
    return templates.TemplateResponse(request=request, name="partials/main_content.html", context={
        "request": request,
        "selected_node": node,
        "list_nodes": children,
        "all_nodes": db.query(models.Node).all(),
        "sources": db.query(models.Source).all()
    })

@router.get("/profile", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def get_profile(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(request=request, name="partials/profile.html", context={"request": request})

@router.get("/settings", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def get_settings(request: Request, db: Session = Depends(get_db)):
    clients = db.query(models.Client).all()
    host_setting = db.query(models.Settings).filter(models.Settings.key == "host_url").first()
    host_url = host_setting.value if host_setting else ""
    return templates.TemplateResponse(request=request, name="partials/settings.html", context={
        "request": request, 
        "clients": clients,
        "host_url": host_url
    })

@router.post("/settings/system", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def update_system_settings(host_url: str = Form(""), db: Session = Depends(get_db)):
    setting = db.query(models.Settings).filter(models.Settings.key == "host_url").first()
    if setting:
        setting.value = host_url
    else:
        setting = models.Settings(key="host_url", value=host_url)
        db.add(setting)
    db.commit()
    return RedirectResponse(url="/admin/settings", status_code=303)

@router.post("/settings/client", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def add_client(
    name: str = Form(...),
    mac_address: str = Form(...),
    icon: str = Form("devices"),
    color: str = Form("#3b82f6"),
    db: Session = Depends(get_db)
):
    try:
        new_client = models.Client(name=name, mac_address=mac_address, icon=icon, color=color)
        db.add(new_client)
        db.commit()
    except Exception as e:
        db.rollback()
        pass # Ignore unique constraint violations for simplicity
    
    return RedirectResponse(url="/admin/settings", status_code=303)

@router.delete("/settings/client/{client_id}", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def delete_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if client:
        db.delete(client)
        db.commit()
    return RedirectResponse(url="/admin/settings", status_code=303)

@router.post("/profile/password", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def update_password(new_password: str = Form(...), confirm_password: str = Form(...), db: Session = Depends(get_db)):
    if new_password != confirm_password:
        return HTMLResponse(content='<span class="text-error">Passwords do not match!</span>')
        
    setting = db.query(models.Settings).filter(models.Settings.key == "admin_password_hash").first()
    if setting:
        setting.value = get_password_hash(new_password)
        db.commit()
        return HTMLResponse(content='<span class="text-primary">Password updated successfully!</span>')
    return HTMLResponse(content='<span class="text-error">Error updating password.</span>')

@router.post("/avatar", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def upload_avatar(avatar: UploadFile = File(...)):
    import os
    os.makedirs('data/avatars', exist_ok=True)
    file_location = "data/avatars/profile.png"
    with open(file_location, "wb+") as file_object:
        file_object.write(avatar.file.read())
    return HTMLResponse(content='<span class="text-primary">Avatar updated! Refresh to see changes.</span>')

@router.get("/avatar")
async def get_avatar():
    import os
    from fastapi.responses import FileResponse
    file_location = "data/avatars/profile.png"
    if os.path.exists(file_location):
        return FileResponse(file_location)
    return HTMLResponse(status_code=404)

@router.get("/fs/browse", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def browse_fs(request: Request, path: str = "/", target_id: str = "config_path_input"):
    try:
        current_path = Path(path).resolve()
        # Fallback to root if path doesn't exist
        if not current_path.exists() or not current_path.is_dir():
            current_path = Path("/").resolve()
            
        parent_path = current_path.parent
        
        directories = []
        for entry in os.scandir(current_path):
            if entry.is_dir() and not entry.name.startswith('.'):
                directories.append({
                    "name": entry.name,
                    "path": str(Path(entry.path).resolve())
                })
        
        directories.sort(key=lambda x: x['name'].lower())
        
        return templates.TemplateResponse(request=request, name="partials/modal_fs_browse.html", context={
            "request": request,
            "current_path": str(current_path),
            "parent_path": str(parent_path) if str(current_path) != str(parent_path) else None,
            "directories": directories,
            "target_id": target_id
        })
    except Exception as e:
        return HTMLResponse(content=f'<div class="text-error p-4">Error accessing path: {str(e)}</div>')

@router.get("/modal/add", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def get_add_node_modal(request: Request, provider: str = "folder", parent_id: int = None, db: Session = Depends(get_db)):
    clients = db.query(models.Client).all()
    return templates.TemplateResponse(request=request, name="partials/modal_add_node.html", context={
        "request": request,
        "provider": provider,
        "parent_id": parent_id,
        "clients": clients
    })

@router.get("/modal/preview", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def get_preview_modal(request: Request, node_id: int = None, db: Session = Depends(get_db)):
    clients = db.query(models.Client).all()
    node = None
    if node_id:
        node = db.query(models.Node).filter(models.Node.id == node_id).first()
    return templates.TemplateResponse(request=request, name="partials/modal_preview.html", context={
        "request": request,
        "node": node,
        "clients": clients
    })


@router.get("/modal/smb", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def get_smb_modal(request: Request, parent_id: int = None):
    return templates.TemplateResponse(request=request, name="partials/modal_add_smb.html", context={
        "request": request,
        "parent_id": parent_id
    })


import os

@router.post("/smb/browse_path", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def browse_smb_path(
    request: Request, 
    smb_host: str = Form(None), 
    smb_share: str = Form(None), 
    smb_user: str = Form(""), 
    smb_pass: str = Form(""), 
    base_url: str = Form(None),
    target_path: str = Form(""),
    parent_id: int = Form(None)
):
    import smbclient
    directories = []
    error = None
    
    # If starting from the wizard, reconstruct base_url
    if not base_url and smb_host and smb_share:
        smb_share = smb_share.strip('/')
        auth_part = f"{smb_user}:{smb_pass}@" if smb_user or smb_pass else ""
        base_url = f"smb://{smb_host}/{smb_share}"
        
    # Extract host and share from base_url to connect
    # format: smb://user:pass@host/share or smb://host/share
    import re
    m = re.match(r'smb://(?:(.*?):(.*?)@)?([^/]+)/(.+)', base_url)
    if not m:
        return HTMLResponse("Invalid SMB URL")
    
    parsed_user, parsed_pass, parsed_host, parsed_share = m.groups()
    if parsed_user is not None:
        smb_user = parsed_user
        smb_pass = parsed_pass
        
    try:
        current_path_unc = target_path.replace('/', '\\\\')
        if current_path_unc.startswith('\\\\'):
            current_path_unc = current_path_unc[1:]
            
        unc_path = r"\\\\" + f"{parsed_host}\\\\{parsed_share}\\\\{current_path_unc}"
        unc_path = unc_path.rstrip('\\\\')
        
        if smb_user:
            smbclient.register_session(parsed_host, username=smb_user, password=smb_pass)
        else:
            smbclient.register_session(parsed_host, username="guest", password="")
        
        for entry in smbclient.scandir(unc_path):
            if entry.is_dir():
                directories.append(entry.name)
    except Exception as e:
        error = f"Failed to connect: {str(e)}"
        
    parent_path = "\\".join(target_path.replace('/', '\\').split('\\')[:-1]) if '\\' in target_path.replace('/', '\\') else ""
        
    return templates.TemplateResponse(request=request, name="partials/browser_results.html", context={
        "request": request,
        "base_url": base_url,
        "current_path": target_path,
        "parent_path": parent_path,
        "parent_id": parent_id,
        "directories": sorted(directories),
        "smb_user": smb_user,
        "smb_pass": smb_pass,
        "btype": "smb",
        "error": error
    })

@router.post("/smb/add", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def add_smb_nodes(
    request: Request,
    base_url: str = Form(...),
    current_path: str = Form(""),
    selected_dirs: list[str] = Form([]),
    use_transcoding: bool = Form(False),
    parent_id: int = Form(None),
    db: Session = Depends(get_db)
):
    nodes_html = ""
    current_path = current_path.replace('\\', '/')
    if current_path and not current_path.startswith('/'):
        current_path = '/' + current_path
        
    for dir_name in selected_dirs:
        path = f"{base_url}{current_path}/{dir_name}"
        
        import json
        new_node = models.Node(
            name=dir_name,
            provider="smb",
            provider_config=json.dumps({"path": path}),
            use_transcoding=use_transcoding,
            parent_id=parent_id
        )
        db.add(new_node)
        db.commit()
        
    root_nodes = db.query(models.Node).filter(models.Node.parent_id == None).all()
    return RedirectResponse(url="/admin/", status_code=303)

@router.get("/modal/local", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def get_local_modal(request: Request, parent_id: int = None):
    return templates.TemplateResponse(request=request, name="partials/modal_add_local.html", context={
        "request": request,
        "parent_id": parent_id
    })

@router.post("/local/browse_path", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def browse_local_path(
    request: Request, 
    base_url: str = Form("local://"),
    target_path: str = Form("/"),
    parent_id: int = Form(None)
):
    directories = []
    error = None
    
    try:
        if os.path.exists(target_path) and os.path.isdir(target_path):
            for entry in os.scandir(target_path):
                if entry.is_dir() and not entry.name.startswith('.'):
                    directories.append(entry.name)
        else:
            error = f"Path does not exist or is not a directory: {target_path}"
    except Exception as e:
        error = f"Failed to read directory: {str(e)}"
        
    parent_path = os.path.dirname(target_path.rstrip('/\\\\'))
    if not parent_path:
        parent_path = "/"
        
    return templates.TemplateResponse(request=request, name="partials/browser_results.html", context={
        "request": request,
        "base_url": base_url,
        "current_path": target_path,
        "parent_path": parent_path,
        "parent_id": parent_id,
        "directories": sorted(directories),
        "btype": "local",
        "error": error
    })

@router.post("/local/add", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def add_local_nodes(
    request: Request,
    current_path: str = Form("/"),
    selected_dirs: list[str] = Form([]),
    use_transcoding: bool = Form(False),
    parent_id: int = Form(None),
    db: Session = Depends(get_db)
):
    for dir_name in selected_dirs:
        path = os.path.join(current_path, dir_name)
        
        import json
        new_node = models.Node(
            name=dir_name,
            provider="local_dir",
            provider_config=json.dumps({"path": path}),
            use_transcoding=use_transcoding,
            parent_id=parent_id
        )
        db.add(new_node)
        db.commit()
        
    root_nodes = db.query(models.Node).filter(models.Node.parent_id == None).all()
    return RedirectResponse(url="/admin/", status_code=303)

@router.get("/logs", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def get_logs(request: Request):
    import os
    logs = []
    log_file = "data/mytuner.log"
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            logs = f.readlines()[-100:]
    return templates.TemplateResponse(request=request, name="partials/logs.html", context={"request": request, "logs": logs})

@router.get("/sources", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def get_sources(request: Request, db: Session = Depends(get_db)):
    sources = db.query(models.Source).all()
    return templates.TemplateResponse(request=request, name="partials/sources.html", context={"request": request, "sources": sources})

@router.post("/sources/", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def create_source(
    request: Request,
    name: str = Form(...),
    provider: str = Form(...),
    config_url: str = Form(""),
    config_path: str = Form(""),
    smb_host: str = Form(""),
    smb_path: str = Form(""),
    smb_user: str = Form(""),
    smb_pass: str = Form(""),
    db: Session = Depends(get_db)
):
    import json
    config_dict = {}
    
    if provider == 'smb' and smb_host and smb_path:
        smb_path = smb_path.strip('/')
        auth_part = f"{smb_user}:{smb_pass}@" if smb_user or smb_pass else ""
        config_path = f"smb://{auth_part}{smb_host}/{smb_path}"
        
    if config_url:
        config_dict["url"] = config_url
    if config_path:
        config_dict["path"] = config_path
        
    new_source = models.Source(
        name=name,
        provider=provider,
        config=json.dumps(config_dict) if config_dict else None
    )
    db.add(new_source)
    db.commit()
    
    sources = db.query(models.Source).all()
    return templates.TemplateResponse(request=request, name="partials/sources.html", context={"request": request, "sources": sources})

@router.delete("/sources/{source_id}", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def delete_source(request: Request, source_id: int, db: Session = Depends(get_db)):
    source = db.query(models.Source).filter(models.Source.id == source_id).first()
    if source:
        db.delete(source)
        db.commit()
    sources = db.query(models.Source).all()
    return templates.TemplateResponse(request=request, name="partials/sources.html", context={"request": request, "sources": sources})

@router.get("/modal/add_source", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def get_modal_add_source(request: Request, provider: str):
    return templates.TemplateResponse(request=request, name="partials/modal_add_source.html", context={"request": request, "provider": provider})

@router.get("/modal/edit_source/{source_id}", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def get_modal_edit_source(request: Request, source_id: int, db: Session = Depends(get_db)):
    source = db.query(models.Source).filter(models.Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    import json
    config = {}
    if source.config:
        config = json.loads(source.config)
        
    if source.provider == 'smb' and config.get('path', '').startswith('smb://'):
        import re
        m = re.match(r'smb://(?:(.*?):(.*?)@)?([^/]+)/(.*)', config['path'])
        if m:
            config['user'] = m.group(1) or ""
            config['pass'] = m.group(2) or ""
            config['host'] = m.group(3) or ""
            config['path'] = m.group(4) or ""

    return templates.TemplateResponse(request=request, name="partials/modal_edit_source.html", context={
        "request": request, 
        "provider": source.provider,
        "source": source,
        "config": config
    })

@router.put("/sources/{source_id}", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def edit_source(
    request: Request,
    source_id: int,
    name: str = Form(...),
    provider: str = Form(...),
    config_url: str = Form(""),
    config_path: str = Form(""),
    smb_host: str = Form(""),
    smb_path: str = Form(""),
    smb_user: str = Form(""),
    smb_pass: str = Form(""),
    db: Session = Depends(get_db)
):
    source = db.query(models.Source).filter(models.Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
        
    import json
    config_dict = {}
    
    if provider == 'smb' and smb_host and smb_path:
        smb_path = smb_path.strip('/')
        auth_part = f"{smb_user}:{smb_pass}@" if smb_user or smb_pass else ""
        config_path = f"smb://{auth_part}{smb_host}/{smb_path}"
        
    if config_url:
        config_dict["url"] = config_url
    if config_path:
        config_dict["path"] = config_path
        
    source.name = name
    source.provider = provider
    source.config = json.dumps(config_dict) if config_dict else None
    
    db.commit()
    
    sources = db.query(models.Source).all()
    return templates.TemplateResponse(request=request, name="partials/sources.html", context={"request": request, "sources": sources})

@router.get("/sources/{source_id}/browse", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def browse_source(request: Request, source_id: int, db: Session = Depends(get_db)):
    source = db.query(models.Source).filter(models.Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
        
    config = {}
    if source.config:
        config = json.loads(source.config)
        
    items = []
    try:
        from ..providers import get_provider
        provider_instance = get_provider(source.provider)
        if provider_instance:
            # For SMB and Local, we might need to list files
            items = provider_instance.browse_folder(config, 0)
    except Exception as e:
        print(f"Error browsing source: {e}")
        
    return templates.TemplateResponse(request=request, name="partials/source_browser.html", context={"request": request, "source": source, "items": items})

@router.get("/sources/{source_id}/items", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def browse_source_items(request: Request, source_id: int, db: Session = Depends(get_db)):
    source = db.query(models.Source).filter(models.Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
        
    config = {}
    if source.config:
        config = json.loads(source.config)
        
    items = []
    try:
        from ..providers import get_provider
        provider_instance = get_provider(source.provider)
        if provider_instance:
            items = provider_instance.browse_folder(config, 0)
    except Exception as e:
        print(f"Error browsing source items: {e}")
        
    return templates.TemplateResponse(request=request, name="partials/source_items.html", context={"request": request, "source": source, "items": items})

@router.post("/nodes/", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def create_node(
    request: Request,
    name: str = Form(...),
    provider: str = Form(...),
    config_url: str = Form(""),
    config_path: str = Form(""),
    image_url: str = Form(""),
    allowed_macs: str = Form(""),
    use_transcoding: bool = Form(False),
    is_continuous_stream: bool = Form(False),
    parent_id: int = Form(None),
    db: Session = Depends(get_db)
):
    import json
    
    provider_config = {}
    if config_url:
        provider_config["url"] = config_url
    if config_path:
        provider_config["path"] = config_path

    new_node = models.Node(
        name=name,
        provider=provider,
        provider_config=json.dumps(provider_config) if provider_config else None,
        image_url=image_url if image_url else None,
        allowed_macs=allowed_macs if allowed_macs else None,
        use_transcoding=use_transcoding,
        is_continuous_stream=is_continuous_stream,
        parent_id=parent_id
    )
    db.add(new_node)
    db.commit()
    
    root_nodes = db.query(models.Node).filter(models.Node.parent_id == None).all()
    return RedirectResponse(url="/admin/", status_code=303)

def _extract_folder_image(path: str) -> str:
    import os
    if path.startswith("local://"):
        local_path = path[8:]
        for img in ["folder.jpg", "cover.jpg", "Folder.jpg", "Cover.jpg"]:
            if os.path.exists(os.path.join(local_path, img)):
                return f"local://{os.path.join(local_path, img)}"
    elif path.startswith("smb://") or "smb://" in path:
        # Complex to extract over SMB without downloading, skip for now
        pass
    return ""

@router.post("/nodes/drop", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def drop_node(
    request: Request,
    parent_id: int = Form(...),
    type: str = Form(...),
    title: str = Form(...),
    stream_url: str = Form(""),
    image_url: str = Form(""),
    path: str = Form(""),
    db: Session = Depends(get_db)
):
    import json
    if type == "Dir":
        return templates.TemplateResponse(request=request, name="partials/modal_drop_folder.html", context={
            "request": request,
            "parent_id": parent_id,
            "title": title,
            "path": path,
            "stream_url": stream_url
        })
    else:
        provider = "web_stream"
        config = {"url": stream_url}
        if stream_url.startswith("local://"):
            provider = "local_dir"
            config = {"file_path": path}
        elif stream_url.startswith("smb://") or "smb://" in stream_url:
            provider = "smb"
            config = {"file_path": stream_url}
            
        new_node = models.Node(
            name=title,
            provider=provider,
            provider_config=json.dumps(config),
            image_url=image_url if image_url else None,
            parent_id=parent_id
        )
        db.add(new_node)
        db.commit()
        return RedirectResponse(url="/admin/", status_code=303)

@router.post("/nodes/drop_confirm", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def drop_node_confirm(
    request: Request,
    parent_id: int = Form(...),
    title: str = Form(...),
    path: str = Form(...),
    stream_url: str = Form(""),
    folder_type: str = Form(...),
    db: Session = Depends(get_db)
):
    import json
    
    provider = "local_dir"
    config = {"path": path}
    
    if path.startswith("smb://") or "smb://" in stream_url:
        provider = "smb"
        config = {"path": path}
        
    is_continuous = (folder_type == "continuous")
    use_transcoding = is_continuous
    
    image_url = _extract_folder_image(path)
    
    new_node = models.Node(
        name=title,
        provider=provider,
        provider_config=json.dumps(config),
        is_continuous_stream=is_continuous,
        use_transcoding=use_transcoding,
        image_url=image_url if image_url else None,
        parent_id=parent_id
    )
    db.add(new_node)
    db.commit()
    return RedirectResponse(url="/admin/", status_code=303)

@router.get("/modal/edit/{node_id}", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def edit_node_modal(request: Request, node_id: int, db: Session = Depends(get_db)):
    import json
    node = db.query(models.Node).filter(models.Node.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
        
    clients = db.query(models.Client).all()
    config = json.loads(node.provider_config) if node.provider_config else {}
    return templates.TemplateResponse(request=request, name="partials/modal_edit_node.html", context={
        "request": request,
        "node": node,
        "config": config,
        "clients": clients
    })

@router.post("/nodes/edit/{node_id}", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def edit_node_submit(
    request: Request,
    node_id: int,
    name: str = Form(...),
    provider: str = Form(...),
    config_url: str = Form(""),
    config_path: str = Form(""),
    image_url: str = Form(""),
    allowed_macs: str = Form(""),
    use_transcoding: bool = Form(False),
    is_continuous_stream: bool = Form(False),
    db: Session = Depends(get_db)
):
    import json
    node = db.query(models.Node).filter(models.Node.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
        
    node.name = name
    node.provider = provider
    node.image_url = image_url if image_url else None
    node.allowed_macs = allowed_macs if allowed_macs else None
    node.use_transcoding = use_transcoding
    node.is_continuous_stream = is_continuous_stream
    
    provider_config = json.loads(node.provider_config) if node.provider_config else {}
    if config_url:
        provider_config["url"] = config_url
    if config_path:
        provider_config["path"] = config_path
        
    node.provider_config = json.dumps(provider_config)
    
    db.commit()
    return RedirectResponse(url="/admin/", status_code=303)

@router.delete("/nodes/{node_id}", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def delete_node(request: Request, node_id: int, db: Session = Depends(get_db)):
    # Find the node and all its children to delete
    node = db.query(models.Node).filter(models.Node.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
        
    def delete_recursive(n):
        children = db.query(models.Node).filter(models.Node.parent_id == n.id).all()
        for child in children:
            delete_recursive(child)
        db.query(models.Favorite).filter(models.Favorite.node_id == n.id).delete()
        db.query(models.History).filter(models.History.node_id == n.id).delete()
        db.delete(n)

    delete_recursive(node)
    db.commit()
    
    return RedirectResponse(url="/admin/", status_code=303)

@router.get("/search", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def search_nodes(request: Request, q: str = "", db: Session = Depends(get_db)):
    if q:
        nodes = db.query(models.Node).filter(models.Node.name.ilike(f"%{q}%")).all()
    else:
        nodes = []
    return templates.TemplateResponse(request=request, name="partials/search_results.html", context={"request": request, "nodes": nodes, "query": q})

@router.get("/notifications", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def get_notifications(request: Request):
    return HTMLResponse(content="<div id='modal-backdrop-alert' class='fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50' x-data='{ open: true }' x-show='open'><div class='bg-surface rounded-xl shadow-lg p-6' @click.away='open = false'><h2 class='text-headline-md mb-4'>Notifications</h2><p>No new notifications.</p><button @click='open = false' class='mt-4 px-4 py-2 bg-primary text-on-primary rounded-lg'>Close</button></div></div>")

@router.get("/help", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def get_help(request: Request):
    return HTMLResponse(content="<div id='modal-backdrop-help' class='fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50' x-data='{ open: true }' x-show='open'><div class='bg-surface rounded-xl shadow-lg p-6' @click.away='open = false'><h2 class='text-headline-md mb-4'>Help & Documentation</h2><p>For more information, please check the Github repository for μTuner.</p><button @click='open = false' class='mt-4 px-4 py-2 bg-primary text-on-primary rounded-lg'>Close</button></div></div>")

"""Admin router — dashboard, CRUD, settings, and media browser."""
from fastapi import APIRouter, Request, Depends, Form, HTTPException, Response, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from ..auth import verify_admin, verify_password, get_password_hash, COOKIE_NAME
import json
import logging
import uuid
import os
from pathlib import Path

from ..providers import get_all_providers, get_provider

logger = logging.getLogger(__name__)

AVATAR_ALLOWED_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
AVATAR_MAX_SIZE = 2 * 1024 * 1024  # 2 MB
MIN_PASSWORD_LENGTH = 4

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["get_all_providers"] = get_all_providers
templates.env.globals["get_provider"] = get_provider


def render_explorer_tree(request: Request, db: Session):
    """Helper to re-render the explorer tree partial after mutations."""
    nodes = db.query(models.Node).all()
    sources = db.query(models.Source).all()
    return templates.TemplateResponse(request=request, name="partials/main_content.html", context={
        "request": request,
        "selected_node": None,
        "list_nodes": [n for n in nodes if n.parent_id is None],
        "all_nodes": nodes,
        "sources": sources
    })

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None):
    return templates.TemplateResponse(request=request, name="login.html", context={"request": request, "error": error})

@router.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, response: Response, password: str = Form(...), db: Session = Depends(get_db)):
    setting = db.query(models.Settings).filter(models.Settings.key == "admin_password_hash").first()
    
    if setting and verify_password(password, setting.value):
        # Create session token
        import time
        token = str(uuid.uuid4())
        expiry = str(int(time.time() + 86400)) # 24 hours
        
        session_setting = db.query(models.Settings).filter(models.Settings.key == "session_token").first()
        if session_setting:
            session_setting.value = token
        else:
            session_setting = models.Settings(key="session_token", value=token)
            db.add(session_setting)
            
        expiry_setting = db.query(models.Settings).filter(models.Settings.key == "session_expiry").first()
        if expiry_setting:
            expiry_setting.value = expiry
        else:
            expiry_setting = models.Settings(key="session_expiry", value=expiry)
            db.add(expiry_setting)
            
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

@router.get("/logs", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def get_logs(request: Request):
    return templates.TemplateResponse(request=request, name="partials/logs.html", context={"request": request})

from fastapi.responses import StreamingResponse
from ..core.log_streamer import queue_handler

@router.get("/logs/stream", dependencies=[Depends(verify_admin)])
async def log_stream(request: Request):
    return StreamingResponse(queue_handler.subscribe(), media_type="text/event-stream")

@router.get("/profile", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def get_profile(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(request=request, name="partials/profile.html", context={"request": request})

@router.get("/clients", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def get_clients(request: Request, db: Session = Depends(get_db)):
    clients = db.query(models.Client).order_by(models.Client.last_seen.desc()).all()
    return templates.TemplateResponse(request=request, name="partials/clients.html", context={
        "request": request,
        "clients": clients
    })

@router.get("/clients/{mac}/favorites", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def get_client_favorites(request: Request, mac: str, db: Session = Depends(get_db)):
    client = db.query(models.Client).filter(models.Client.mac_address == mac).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    favorites = [fav.node_id for fav in db.query(models.Favorite).filter(models.Favorite.mac_address == mac).all()]
    all_stations = db.query(models.Node).filter(models.Node.provider != 'folder').all()
    
    return templates.TemplateResponse(request=request, name="partials/modal_favorites.html", context={
        "request": request,
        "client": client,
        "favorites": favorites,
        "stations": all_stations
    })

@router.post("/clients/{mac}/favorites/toggle", response_class=Response, dependencies=[Depends(verify_admin)])
async def toggle_client_favorite(mac: str, node_id: int = Form(...), action: str = Form(...), db: Session = Depends(get_db)):
    if action == "add":
        if not db.query(models.Favorite).filter(models.Favorite.mac_address == mac, models.Favorite.node_id == node_id).first():
            fav = models.Favorite(mac_address=mac, node_id=node_id)
            db.add(fav)
    else:
        db.query(models.Favorite).filter(models.Favorite.mac_address == mac, models.Favorite.node_id == node_id).delete()
    db.commit()
    return Response(status_code=200)

@router.get("/settings", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def get_settings(request: Request, db: Session = Depends(get_db)):
    clients = db.query(models.Client).all()
    host_setting = db.query(models.Settings).filter(models.Settings.key == "host_url").first()
    refresh_setting = db.query(models.Settings).filter(models.Settings.key == "background_refresh_interval").first()
    
    return templates.TemplateResponse(request=request, name="partials/settings.html", context={
        "request": request, 
        "clients": clients,
        "host_url": host_setting.value if host_setting else "",
        "background_refresh_interval": refresh_setting.value if refresh_setting else "60"
    })

@router.post("/settings/system", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def update_system_settings(host_url: str = Form(""), background_refresh_interval: int = Form(60), db: Session = Depends(get_db)):
    setting = db.query(models.Settings).filter(models.Settings.key == "host_url").first()
    if setting:
        setting.value = host_url
    else:
        setting = models.Settings(key="host_url", value=host_url)
        db.add(setting)
        
    refresh_setting = db.query(models.Settings).filter(models.Settings.key == "background_refresh_interval").first()
    if refresh_setting:
        refresh_setting.value = str(background_refresh_interval)
    else:
        refresh_setting = models.Settings(key="background_refresh_interval", value=str(background_refresh_interval))
        db.add(refresh_setting)
        
    db.commit()
    
    try:
        from ..scheduler import update_scheduler_interval
        update_scheduler_interval(background_refresh_interval)
    except Exception:
        pass
        
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
    if len(new_password) < MIN_PASSWORD_LENGTH:
        return HTMLResponse(content=f'<span class="text-error">Password must be at least {MIN_PASSWORD_LENGTH} characters.</span>')
        
    setting = db.query(models.Settings).filter(models.Settings.key == "admin_password_hash").first()
    if setting:
        setting.value = get_password_hash(new_password)
        db.commit()
        return HTMLResponse(content='<span class="text-primary">Password updated successfully!</span>')
    return HTMLResponse(content='<span class="text-error">Error updating password.</span>')

@router.post("/avatar", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def upload_avatar(avatar: UploadFile = File(...)):
    # Validate content type
    if avatar.content_type not in AVATAR_ALLOWED_TYPES:
        return HTMLResponse(content='<span class="text-error">Invalid file type. Use PNG, JPEG, WebP, or GIF.</span>')
    # Validate file size
    content = await avatar.read()
    if len(content) > AVATAR_MAX_SIZE:
        return HTMLResponse(content='<span class="text-error">File too large (max 2 MB).</span>')
    os.makedirs('data/avatars', exist_ok=True)
    file_location = "data/avatars/profile.png"
    with open(file_location, "wb") as file_object:
        file_object.write(content)
    return HTMLResponse(content='<span class="text-primary">Avatar updated! Refresh to see changes.</span>')

@router.get("/avatar", dependencies=[Depends(verify_admin)])
async def get_avatar():
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




@router.post("/smb/browse_modal", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def browse_smb_modal(
    request: Request, 
    target_id: str = Form(""),
    smb_host: str = Form(None, alias="config_host"), 
    smb_path: str = Form(None, alias="config_path"), 
    smb_user: str = Form("", alias="config_user"), 
    smb_pass: str = Form("", alias="config_pass")
):
    import smbclient
    directories = []
    error = None
    
    smb_host = (smb_host or "").strip()
    smb_path = (smb_path or "").strip('/')
    auth_part = f"{smb_user}:{smb_pass}@" if smb_user or smb_pass else ""
    base_url = f"smb://{smb_host}/{smb_path}"
    
    if not smb_host:
        error = "Please enter a Host / IP address first."
    else:
        try:
            unc_path = r"\\" + f"{smb_host}\\{smb_path}"
            unc_path = unc_path.rstrip('\\')
            
            if smb_user:
                smbclient.register_session(smb_host, username=smb_user, password=smb_pass)
            else:
                smbclient.register_session(smb_host, username="guest", password="")
                
            for entry in smbclient.scandir(unc_path):
                if entry.is_dir():
                    directories.append(entry.name)
        except Exception as e:
            error = f"Failed to connect: {str(e)}"
        
    return templates.TemplateResponse(request=request, name="partials/modal_smb_browse.html", context={
        "request": request,
        "base_url": base_url,
        "current_path": "",
        "target_id": target_id,
        "directories": sorted(directories),
        "smb_host": smb_host,
        "smb_path": smb_path,
        "smb_user": smb_user,
        "smb_pass": smb_pass,
        "error": error
    })

@router.post("/smb/browse_modal_path", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def browse_smb_modal_path(
    request: Request, 
    target_id: str = Form(""),
    target_path: str = Form(""),
    base_url: str = Form(""),
    smb_host: str = Form("", alias="config_host"), 
    smb_path: str = Form("", alias="config_path"), 
    smb_user: str = Form("", alias="config_user"), 
    smb_pass: str = Form("", alias="config_pass")
):
    import smbclient
    directories = []
    error = None
    
    smb_host = smb_host or ""
    smb_path = smb_path or ""
    target_path = target_path or ""
    
    try:
        unc_path = r"\\" + f"{smb_host}\\{smb_path}\\{target_path}"
        unc_path = unc_path.rstrip('\\')
        
        if smb_user:
            smbclient.register_session(smb_host, username=smb_user, password=smb_pass)
        else:
            smbclient.register_session(smb_host, username="guest", password="")
            
        for entry in smbclient.scandir(unc_path):
            if entry.is_dir():
                directories.append(entry.name)
    except Exception as e:
        error = f"Failed to connect: {str(e)}"
        
    return templates.TemplateResponse(request=request, name="partials/modal_smb_browse.html", context={
        "request": request,
        "base_url": base_url,
        "current_path": target_path,
        "target_id": target_id,
        "directories": sorted(directories),
        "smb_host": smb_host,
        "smb_path": smb_path,
        "smb_user": smb_user,
        "smb_pass": smb_pass,
        "error": error
    })

@router.post("/smb/browse_path", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def browse_smb_path(
    request: Request, 
    smb_host: str = Form("", alias="config_host"), 
    smb_share: str = Form("", alias="config_path"), 
    smb_user: str = Form("", alias="config_user"), 
    smb_pass: str = Form("", alias="config_pass"), 
    base_url: str = Form(""),
    target_path: str = Form(""),
    parent_id: int = Form(None)
):
    import smbclient
    directories = []
    error = None
    
    if not base_url and smb_host and smb_share:
        smb_share = smb_share.strip('/')
        base_url = f"smb://{smb_host}/{smb_share}"
        
    try:
        current_path_unc = target_path.replace('/', '\\')
        if current_path_unc.startswith('\\'):
            current_path_unc = current_path_unc[1:]
            
        unc_path = r"\\" + f"{smb_host}\\{smb_share}\\{current_path_unc}"
        unc_path = unc_path.rstrip('\\')
        
        if smb_user:
            smbclient.register_session(smb_host, username=smb_user, password=smb_pass)
        else:
            smbclient.register_session(smb_host, username="guest", password="")
        
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
        "smb_host": smb_host,
        "smb_pass": smb_pass,
        "smb_user": smb_user,
        "btype": "smb",
        "error": error
    })

@router.post("/smb/add", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def add_smb_nodes(
    request: Request,
    smb_host: str = Form(""),
    smb_path: str = Form(""),
    smb_user: str = Form(""),
    smb_pass: str = Form(""),
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
        path = f"{smb_path}{current_path}/{dir_name}".strip('/')
        

        config = {
            "host": smb_host,
            "path": path,
            "user": smb_user,
            "pass": smb_pass
        }
        
        new_node = models.Node(
            name=dir_name,
            provider="smb",
            provider_config=json.dumps(config),
            use_transcoding=use_transcoding,
            parent_id=parent_id
        )
        db.add(new_node)
        
    db.commit()
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
        

        new_node = models.Node(
            name=dir_name,
            provider="local_dir",
            provider_config=json.dumps({"path": path}),
            use_transcoding=use_transcoding,
            parent_id=parent_id
        )
        db.add(new_node)
        
    db.commit()
    return RedirectResponse(url="/admin/", status_code=303)



@router.get("/sources", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def get_sources(request: Request, db: Session = Depends(get_db)):
    sources = db.query(models.Source).all()
    return templates.TemplateResponse(request=request, name="partials/sources.html", context={"request": request, "sources": sources})

@router.post("/sources/", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def create_source(
    request: Request,
    db: Session = Depends(get_db)
):
    form_data = await request.form()
    name = form_data.get("name")
    provider = form_data.get("provider")
    
    from ..providers import get_provider
    provider_inst = get_provider(provider)
    

    config_dict = {}
    
    if provider_inst:
        for field in provider_inst.config_schema:
            val = form_data.get(f"config_{field['name']}")
            if val is not None:
                config_dict[field['name']] = val

    # Special handling for SMB builder fields if present
    if provider == 'smb' and form_data.get("smb_host") and form_data.get("smb_path"):
        smb_host = form_data.get("smb_host")
        smb_path = form_data.get("smb_path", "").strip('/')
        smb_user = form_data.get("smb_user", "")
        smb_pass = form_data.get("smb_pass", "")
        auth_part = f"{smb_user}:{smb_pass}@" if smb_user or smb_pass else ""
        config_dict["path"] = f"smb://{auth_part}{smb_host}/{smb_path}"

    new_source = models.Source(
        name=name,
        provider=provider,
        config=json.dumps(config_dict) if config_dict else None
    )
    db.add(new_source)
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
    

    config = {}
    if source.config:
        config = json.loads(source.config)
        
    if source.provider == 'smb':
        from ..providers.smb.smb_provider import SMBProvider
        smb = SMBProvider()
        h, u, p, _ = smb._resolve_config(config)
        if h:
            config['host'] = h
            config['user'] = u or ""
            config['pass'] = p or ""
            # Strip smb:// prefix if present to match share path field
            import re
            m = re.match(r'smb://(?:.*?@)?[^/]+/(.*)', config.get('path', ''))
            if m:
                config['path'] = m.group(1)

    return templates.TemplateResponse(request=request, name="partials/modal_edit_source.html", context={
        "request": request, 
        "provider": source.provider,
        "source": source,
        "config": config
    })

@router.delete("/sources/{source_id}", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def delete_source(
    request: Request,
    source_id: int,
    db: Session = Depends(get_db)
):
    source = db.query(models.Source).filter(models.Source.id == source_id).first()
    if source:
        db.query(models.SourceCache).filter(models.SourceCache.source_id == source_id).delete()
        db.delete(source)
        db.commit()
    
    sources = db.query(models.Source).all()
    return templates.TemplateResponse(request=request, name="partials/sources.html", context={"request": request, "sources": sources})

@router.put("/sources/{source_id}", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def edit_source(
    request: Request,
    source_id: int,
    db: Session = Depends(get_db)
):
    source = db.query(models.Source).filter(models.Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
        
    form_data = await request.form()
    name = form_data.get("name")
    provider = form_data.get("provider")
        
    from ..providers import get_provider
    provider_inst = get_provider(provider)
    

    config_dict = {}
    
    if provider_inst:
        for field in provider_inst.config_schema:
            val = form_data.get(f"config_{field['name']}")
            if val is not None:
                config_dict[field['name']] = val

    # Special handling for SMB builder fields if present
    if provider == 'smb' and form_data.get("smb_host") and form_data.get("smb_path"):
        smb_host = form_data.get("smb_host")
        smb_path = form_data.get("smb_path", "").strip('/')
        smb_user = form_data.get("smb_user", "")
        smb_pass = form_data.get("smb_pass", "")
        auth_part = f"{smb_user}:{smb_pass}@" if smb_user or smb_pass else ""
        config_dict["path"] = f"smb://{auth_part}{smb_host}/{smb_path}"
        
    if name:
        source.name = name
    if provider:
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
        logger.error(f"Error browsing source: {e}")
        
    return templates.TemplateResponse(request=request, name="partials/source_browser.html", context={"request": request, "source": source, "items": items})

@router.get("/sources/{source_id}/items", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def browse_source_items(request: Request, source_id: int, db: Session = Depends(get_db)):
    source = db.query(models.Source).filter(models.Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
        
    # Try cached items first
    items = []
    cache = db.query(models.SourceCache).filter(models.SourceCache.source_id == source_id).first()
    if cache and cache.data:
        try:
            items = json.loads(cache.data)
        except (json.JSONDecodeError, TypeError):
            items = []
    
    # Fallback to live fetch if no cache
    if not items:
        config = json.loads(source.config) if source.config else {}
        try:
            provider_instance = get_provider(source.provider)
            if provider_instance:
                items = provider_instance.browse_folder(config, 0)
        except Exception as e:
            logger.error(f"Error browsing source items: {e}")
        
    return templates.TemplateResponse(request=request, name="partials/source_items.html", context={"request": request, "source": source, "items": items})

@router.post("/nodes/", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def create_node(
    request: Request,
    db: Session = Depends(get_db)
):
    form_data = await request.form()
    name = form_data.get("name")
    provider = form_data.get("provider")
    image_url = form_data.get("image_url", "")
    allowed_macs = form_data.get("allowed_macs", "")
    use_transcoding = form_data.get("use_transcoding") is not None
    is_continuous_stream = form_data.get("is_continuous_stream") is not None
    parent_id = form_data.get("parent_id")
    if parent_id: parent_id = int(parent_id)

    from ..providers import get_provider
    provider_inst = get_provider(provider)
    

    provider_config = {}
    
    if provider_inst:
        for field in provider_inst.config_schema:
            val = form_data.get(f"config_{field['name']}")
            if val is not None:
                provider_config[field['name']] = val

    # Special handling for SMB builder fields if present
    if provider == 'smb' and form_data.get("smb_host") and form_data.get("smb_path"):
        provider_config["host"] = form_data.get("smb_host")
        provider_config["path"] = form_data.get("smb_path", "").strip('/')
        provider_config["user"] = form_data.get("smb_user", "")
        provider_config["pass"] = form_data.get("smb_pass", "")

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
    source_id: str = Form(""),
    source_provider: str = Form(""),
    db: Session = Depends(get_db)
):

    if type == "Source":
        new_node = models.Node(
            name=title,
            provider=source_provider,
            provider_config=json.dumps({"source_id": int(source_id)}),
            image_url=None,
            parent_id=parent_id
        )
        db.add(new_node)
        db.commit()
        return RedirectResponse(url="/admin/", status_code=303)
    elif type == "Dir":
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
            config = {"path": path}
        elif stream_url.startswith("smb://") or "smb://" in stream_url:
            provider = "smb"
            config = {"path": stream_url}
            
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
    db: Session = Depends(get_db)
):

    node = db.query(models.Node).filter(models.Node.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
        
    form_data = await request.form()
    name = form_data.get("name")
    provider = form_data.get("provider")
    image_url = form_data.get("image_url", "")
    allowed_macs = form_data.get("allowed_macs", "")
    use_transcoding = form_data.get("use_transcoding") is not None
    is_continuous_stream = form_data.get("is_continuous_stream") is not None
        
    node.name = name
    node.provider = provider
    node.image_url = image_url if image_url else None
    node.allowed_macs = allowed_macs if allowed_macs else None
    node.use_transcoding = use_transcoding
    node.is_continuous_stream = is_continuous_stream
    
    from ..providers import get_provider
    provider_inst = get_provider(provider)
    
    provider_config = json.loads(node.provider_config) if node.provider_config else {}
    if provider_inst:
        for field in provider_inst.config_schema:
            val = form_data.get(f"config_{field['name']}")
            if val is not None:
                provider_config[field['name']] = val
                
    # Special handling for SMB builder fields if present
    if provider == 'smb' and form_data.get("smb_host") and form_data.get("smb_path"):
        provider_config["host"] = form_data.get("smb_host")
        provider_config["path"] = form_data.get("smb_path", "").strip('/')
        provider_config["user"] = form_data.get("smb_user", "")
        provider_config["pass"] = form_data.get("smb_pass", "")

    node.provider_config = json.dumps(provider_config)
    
    db.commit()
    return RedirectResponse(url="/admin/", status_code=303)

@router.post("/nodes/bulk", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def bulk_action_nodes(request: Request, selected_nodes: list[int] = Form([]), bulk_action: str = Form(...), db: Session = Depends(get_db)):
    if selected_nodes:
        nodes = db.query(models.Node).filter(models.Node.id.in_(selected_nodes)).all()
        for node in nodes:
            if bulk_action == "transcode_on":
                node.use_transcoding = True
            elif bulk_action == "transcode_off":
                node.use_transcoding = False
        
        try:
            db.commit()
        except Exception:
            db.rollback()
            
    return render_explorer_tree(request, db)

@router.post("/nodes/{node_id}/move", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def move_node(request: Request, node_id: int, target_id: int = Form(...), position: str = Form("inside"), db: Session = Depends(get_db)):
    node = db.query(models.Node).filter(models.Node.id == node_id).first()
    target = db.query(models.Node).filter(models.Node.id == target_id).first()
    
    if node and target and node.id != target.id:
        if position == "inside":
            node.move_inside(target.id)
        elif position == "after":
            node.move_after(target.id)
        elif position == "before":
            node.move_before(target.id)
            
        try:
            db.commit()
        except Exception:
            db.rollback()
            
    return render_explorer_tree(request, db)

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

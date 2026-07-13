import re

with open('app/routers/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

smb_routes = """
@router.get("/modal/smb", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def get_smb_modal(request: Request, parent_id: int = None):
    return templates.TemplateResponse(request=request, name="partials/modal_add_smb.html", context={
        "request": request,
        "parent_id": parent_id
    })

@router.post("/smb/browse", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def browse_smb(request: Request, smb_url: str = Form(...), parent_id: int = Form(None)):
    import smbclient
    from smbclient import smbprotocol
    directories = []
    error = None
    try:
        # Example smb_url: smb://user:pass@192.168.1.10/share
        if smb_url.startswith("smb://"):
            parts = smb_url[6:].split('@')
            if len(parts) == 2:
                creds = parts[0].split(':')
                username = creds[0]
                password = creds[1] if len(creds) > 1 else ""
                server_share = parts[1]
                
                # smbclient expects \\\\server\\share format
                # Replace forward slashes with backslashes
                unc_path = "\\\\\\\\" + server_share.replace('/', '\\\\')
                
                smbclient.register_session(server_share.split('/')[0], username=username, password=password)
                
                for entry in smbclient.scandir(unc_path):
                    if entry.is_dir():
                        directories.append(entry.name)
            else:
                error = "Invalid SMB URL format. Ensure it contains user:pass@host/share"
        else:
            error = "URL must start with smb://"
    except Exception as e:
        error = f"Failed to connect: {str(e)}"
        
    return templates.TemplateResponse(request=request, name="partials/smb_browse_results.html", context={
        "request": request,
        "smb_url": smb_url,
        "parent_id": parent_id,
        "directories": directories,
        "error": error
    })

@router.post("/smb/add", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
async def add_smb_nodes(
    request: Request,
    smb_url: str = Form(...),
    selected_dirs: list[str] = Form([]),
    use_transcoding: bool = Form(False),
    parent_id: int = Form(None),
    db: Session = Depends(get_db)
):
    nodes_html = ""
    for dir_name in selected_dirs:
        # Create full SMB path
        path = f"{smb_url}/{dir_name}" if not smb_url.endswith('/') else f"{smb_url}{dir_name}"
        
        new_node = models.Node(
            name=dir_name,
            provider="smb",
            config_path=path,
            use_transcoding=use_transcoding,
            parent_id=parent_id
        )
        db.add(new_node)
        db.commit()
        db.refresh(new_node)
        
    # Re-render tree
    root_nodes = db.query(models.Node).filter(models.Node.parent_id == None).all()
    return templates.TemplateResponse(request=request, name="partials/tree.html", context={"request": request, "nodes": root_nodes})

"""

content = content.replace(
    "@router.get(\"/modal/edit/{node_id}\"",
    smb_routes + "\n@router.get(\"/modal/edit/{node_id}\""
)

with open('app/routers/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated admin.py")

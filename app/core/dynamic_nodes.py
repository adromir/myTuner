import base64
import json
import logging
from typing import Dict, Any, List, Optional
from ..providers import get_provider

logger = logging.getLogger(__name__)

class DynamicNode:
    """Virtual Node object mimicking models.Node for dynamic provider browsing in templates."""
    def __init__(self, id: str, name: str, provider: str, provider_config: Any = None, image_url: Optional[str] = None, use_transcoding: bool = False, allowed_macs: Optional[str] = None):
        self.id = id
        self.name = name
        self.provider = provider
        self.provider_config = provider_config if isinstance(provider_config, str) else json.dumps(provider_config or {})
        self.image_url = image_url
        self.use_transcoding = use_transcoding
        self.allowed_macs = allowed_macs

def encode_dynamic_id(prefix: str, provider_name: str, config: Dict[str, Any], use_transcoding: bool = False, allowed_macs: Optional[str] = None) -> str:
    """Encode dynamic node payload into URL-safe base64 string."""
    payload = {
        "p": provider_name,
        "c": config,
        "t": use_transcoding,
        "m": allowed_macs
    }
    dumped = json.dumps(payload).encode('utf-8')
    encoded = base64.urlsafe_b64encode(dumped).decode('utf-8').rstrip('=')
    return f"{prefix}_{encoded}"

def decode_dynamic_id(dynamic_id: str) -> Optional[Dict[str, Any]]:
    """Decode dynamic node payload from base64 string."""
    try:
        parts = dynamic_id.split('_', 1)
        if len(parts) < 2:
            return None
        encoded = parts[1]
        # Restore padding
        padding = '=' * (-len(encoded) % 4)
        dumped = base64.urlsafe_b64decode((encoded + padding).encode('utf-8')).decode('utf-8')
        return json.loads(dumped)
    except Exception as e:
        logger.error(f"Failed to decode dynamic node ID {dynamic_id}: {e}")
        return None

def build_dynamic_children(provider_name: str, config: Dict[str, Any], parent_node_id: Any, use_transcoding: bool = False, allowed_macs: Optional[str] = None) -> List[DynamicNode]:
    """Browse provider folder and convert returned items to DynamicNode instances."""
    provider_inst = get_provider(provider_name)
    if not provider_inst:
        return []

    try:
        raw_items = provider_inst.browse_folder(config, parent_node_id)
    except Exception as e:
        logger.error(f"Error browsing folder for provider {provider_name}: {e}")
        return []

    children = []
    for idx, item in enumerate(raw_items):
        item_type = str(item.get("type", "")).lower()
        title = item.get("title") or item.get("name") or "Unnamed"

        is_dir = item_type in ["dir", "folder", "directory"]
        if is_dir:
            # Build sub-config for dynamic subfolder
            if provider_name == "smb":
                sub_config = {
                    "host": config.get("host"),
                    "path": item.get("path") or item.get("stream_url"),
                    "user": config.get("user"),
                    "pass": config.get("pass")
                }
            elif provider_name == "local_dir":
                sub_config = {"path": item.get("path")}
            else:
                sub_config = item.get("config") or {"url": item.get("path") or item.get("stream_url")}

            dyn_id = encode_dynamic_id("dyn", provider_name, sub_config, use_transcoding, allowed_macs)

            children.append(DynamicNode(
                id=dyn_id,
                name=title,
                provider=provider_name,
                provider_config=sub_config,
                image_url=item.get("image_url") or item.get("logo"),
                use_transcoding=use_transcoding,
                allowed_macs=allowed_macs
            ))
        else:
            stream_url = item.get("stream_url") or item.get("path") or (item.get("config", {}).get("url") if isinstance(item.get("config"), dict) else "")
            item_provider = item.get("provider") or "web_stream"
            item_config = item.get("config") or {"url": stream_url, "path": stream_url}

            item_id = encode_dynamic_id("item", item_provider, item_config, use_transcoding, allowed_macs)

            children.append(DynamicNode(
                id=item_id,
                name=title,
                provider=item_provider,
                provider_config=item_config,
                image_url=item.get("image_url") or item.get("logo"),
                use_transcoding=use_transcoding,
                allowed_macs=allowed_macs
            ))

    return children

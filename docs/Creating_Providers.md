# Developing Custom Providers

μTuner uses a dynamic plugin system that makes it incredibly easy to extend its capabilities. If you want to add support for a new media source (like Spotify, a custom API, or a new file protocol), you simply need to create a new Provider class.

## Step 1: Create Your Provider Class

1. Create a new Python file in the `app/providers/` directory (e.g., `app/providers/my_custom_provider.py`).
2. Import the base class and implement the required methods.

Here is a minimal template:

```python
from typing import List, Dict, Any
from app.providers.base import MediaProvider

class MyCustomProvider(MediaProvider):
    @property
    def id(self) -> str:
        # Unique identifier used in the database
        return "my_custom"
        
    @property
    def name(self) -> str:
        # Display name in the UI
        return "My Custom Source"
        
    @property
    def icon(self) -> str:
        # Material symbols icon name (e.g., 'audiotrack', 'folder')
        return "extension"
        
    @property
    def allow_as_source(self) -> bool:
        # Can this be added from the "Sources" tab to run background tasks?
        return True
        
    @property
    def allow_as_node(self) -> bool:
        # Can this be added directly into the Playlist tree?
        return True
        
    @property
    def config_schema(self) -> List[Dict[str, Any]]:
        """
        Defines the form fields presented to the user in the UI.
        Supported types: 'text', 'password', 'smb_path', 'local_path'
        """
        return [
            {
                "name": "api_key",
                "label": "API Key",
                "type": "password",
                "required": True,
                "placeholder": "Enter your API key"
            },
            {
                "name": "stream_id",
                "label": "Stream ID",
                "type": "text",
                "required": False,
                "placeholder": "12345"
            }
        ]

    def get_stream_url(self, config: Dict[str, Any]) -> str:
        """
        Return the raw audio URL that FFmpeg or the AVR will connect to.
        `config` contains the values the user filled out in the UI.
        """
        api_key = config.get("api_key")
        stream_id = config.get("stream_id", "default")
        return f"http://my-custom-api.com/stream/{stream_id}?token={api_key}"
    
    def browse_folder(self, config: Dict[str, Any], node_id: int) -> List[Dict[str, Any]]:
        """
        If this provider acts like a folder (like Podcasts or SMB),
        return a list of items to display when the AVR queries it.
        Otherwise, return an empty list.
        """
        return [
            {
                "name": "Track 1",
                "type": "stream", # 'stream' or 'folder'
                "url": f"my_custom://stream_id_1"
            },
            {
                "name": "Subfolder",
                "type": "folder",
                "url": f"my_custom://subfolder"
            }
        ]
```

## Step 2: Automatic Discovery

That's it! You **do not** need to manually register your provider.

μTuner uses a True Dynamic Plugin System. When the application starts, it automatically scans for classes that inherit from `MediaProvider` and registers them using their `id`.

You have two options for where to place your provider file:
1. **Built-in:** Place it inside the `app/providers/` directory (or a subdirectory like `app/providers/my_provider/`).
2. **External Plugin (Recommended):** Place your `.py` file directly into the `plugins/` folder in the root directory of the project. This is the best way to keep your custom providers safe from being overwritten during updates!

## How It Works in the UI
As soon as you register your provider, μTuner will automatically:
- Add a **"+ Add My Custom Source"** button to the **Sources** tab.
- Generate an HTML form modal dynamically based on your `config_schema`.
- Save the user's input securely into the SQLite database as JSON.
- Route AVR playback requests to your `get_stream_url` logic.
- Route AVR folder navigation to your `browse_folder` logic.

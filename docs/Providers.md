# Managing Media (Providers)

μTuner uses a **Dynamic Plugin System** to support multiple ways to organize and play your media. You can add these from the **Sources** tab and organize them in the **Playlists** tree.

## Supported Providers

### 🌐 Web Streams
The simplest type of media for direct internet radio streams.
1. Navigate to **Sources**.
2. Click **+ Add Web Stream**.
3. Provide a name and the direct streaming URL (e.g., `http://stream.radioparadise.com/aac-320`).
4. Optionally, add an image URL for the cover art to be displayed on your AVR.

### 🎙️ Podcasts (RSS)
μTuner automatically fetches and parses the latest episodes from a podcast RSS feed in the background.
1. Click **+ Add Podcast (RSS)**.
2. Paste the URL of the podcast RSS feed.
3. When you drag this source into your Playlist tree, μTuner dynamically generates a folder containing the latest episodes. 
4. The episodes update automatically whenever the background scheduler syncs.

### 🎵 M3U Playlists
Have a large list of stations in an `.m3u` file?
1. Click **+ Add M3U Playlist**.
2. Provide the URL to the M3U file.
3. μTuner fetches the file in the background, parses the stations, and presents them as a browsable folder on your AVR.

### 📁 SMB Shares
Play local MP3/FLAC files stored on your NAS securely.
1. Click **+ Add SMB Share**.
2. Enter the server IP, the exact share path, and your username and password. 
   *(Security Note: Credentials are never embedded in URLs. They are stored securely via separated AES-encrypted JSON database fields).*
3. Use the interactive folder browser to select the specific directories you want to mount.
4. Choose whether to import the directories as browsable folders or concat-stream them.

### 📂 Local Directories
If you have music files physically stored on the same server running μTuner (or mounted via Docker volumes):
1. Click **+ Add Local Directory**.
2. Use the interactive file browser to navigate the server's filesystem.
3. Select the directory containing your music to mount it virtually for the AVR.

---

## Advanced Features

### MAC Address Filtering 🔒
You can restrict specific folders or streams so they only appear for certain AVRs on your network.
1. Edit any node in the Playlist tree.
2. In the **Allowed MAC Addresses** field, enter the MAC address of the receiver (e.g., `00:11:22:33:44:55`).
3. You can specify multiple MAC addresses separated by commas. Leave blank to allow all devices.

### FFmpeg Transcoding ⚙️
If your AVR is older and does not support modern streaming formats (like modern AAC streams, HLS, or certain FLAC files), you can enable **FFmpeg Transcoding** for any node.
1. Right-click a node in the **Playlists** tab and click **Edit**.
2. Check the **Use FFmpeg Transcoding** option.
3. μTuner will intercept the audio stream and convert it to a highly compatible MP3 stream on the fly.

### Dynamic Cover Art 🖼️
μTuner supports serving cover art to supported receivers. 
- You can manually specify an **Image URL** when editing a node.
- For Local and SMB folders, μTuner will automatically search for `folder.jpg` or `cover.jpg` inside the directory and serve it as the icon for that specific node.

# Managing Media (Providers)

μTuner supports multiple ways to organize and play your media. You can add these from the **Sources** tab and organize them in the **Playlists** tree.

## Web Streams
The simplest type of media. 
1. Navigate to **Sources**.
2. Click **+ Add Source** and select **Web Stream**.
3. Provide a name and the direct streaming URL (e.g., `http://stream.radioparadise.com/aac-320`).
4. Optionally, add an image URL for the cover art.

## Podcasts (RSS)
μTuner can automatically fetch and parse the latest episodes from a podcast RSS feed.
1. Click **+ Add Source** and select **Podcast (RSS)**.
2. Paste the URL of the podcast RSS feed.
3. When you drag this source into your Playlist tree, μTuner will dynamically generate a folder containing the latest episodes.

## M3U Playlists
Have a large list of stations in an `.m3u` file?
1. Click **+ Add Source** and select **M3U Playlist**.
2. Provide the URL to the M3U file.
3. μTuner will fetch the file, parse the stations, and present them as a browsable folder on your AVR.

## SMB Shares
Play local MP3/FLAC files stored on your NAS.
1. Click **+ Add Source** and select **SMB Share**.
2. In the modal, you can browse your local network to find the SMB share. Enter the server IP, username, and password if required.
3. Select the folder you want to add.
4. μTuner will mount this share virtually and allow your AVR to browse the files.

## Local Directories
If you have music files physically stored on the same server running μTuner (or mounted via Docker volumes):
1. Click **+ Add Source** and select **Local Directory**.
2. Use the interactive file browser to navigate the server's filesystem and select the directory containing your music.

## Transcoding
If your AVR is older and does not support modern streaming formats (like modern AAC streams or certain FLAC files), you can enable **FFmpeg Transcoding** for any node in your playlist. 
* Right-click a node in the **Playlists** tab.
* Click **Edit**.
* Check the **Use FFmpeg Transcoding** option.
μTuner will intercept the audio stream and convert it to a highly compatible MP3 stream on the fly.

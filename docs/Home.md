# Welcome to the μTuner Wiki!

**μTuner** is a complete, self-hosted emulation of the vTuner XML API for older network audio receivers (specifically Denon and Marantz). It acts as a drop-in replacement for the proprietary vTuner infrastructure, which often requires paid subscriptions or may become unreliable over time.

## Architecture
At its core, μTuner intercepts the HTTP requests made by your AVR to `radiodenon.com` (or `vtuner.com`) via DNS hijacking. Instead of talking to the official servers, your AVR connects to your local μTuner instance.

μTuner translates your customized media hierarchy (configured via a modern web interface) into the exact XML format that your AVR expects.

## Key Features
* **Drop-in Replacement**: No custom firmware is needed on your AVR.
* **Modern Dashboard**: A fast, responsive UI built with HTMX, Alpine.js, and Tailwind CSS.
* **Versatile Media Sources**:
  * Internet Radio (Web Streams)
  * Podcasts (Automatic RSS Parsing)
  * M3U Playlists
  * Local Directories / SMB Shares (with real-time browsing)
* **FFmpeg Transcoding**: Fix compatibility issues on older hardware by transcoding unsupported formats to standard MP3 streams on the fly.
* **Live Logs**: Watch exactly what your AVR is requesting in real-time from the dashboard.

## Next Steps
- Head over to [Installation](Installation.md) to get the server running.
- Learn about [Configuration](Configuration.md) to set up DNS hijacking.
- Discover how to manage your media in [Providers](Providers.md).

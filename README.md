<div align="center">
  <h1>μTuner (myTuner)</h1>
  
  **Breathe new life into your Denon/Marantz AVR by replacing the legacy vTuner service with your own local server!**

  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://www.docker.com/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![HTMX](https://img.shields.io/badge/HTMX-336699?logo=htmx&logoColor=white)](https://htmx.org/)
</div>

---

## 📻 Why use μTuner?

Older network audio receivers, particularly those from Denon and Marantz, rely on the proprietary **vTuner** infrastructure to stream internet radio, podcasts, and digital media. When this service requires paid subscriptions, becomes unreliable, or shuts down, your expensive hardware loses a core feature.

**μTuner** is a complete, self-hosted emulation of the vTuner XML API. By simply pointing your AVR's DNS traffic for `radiodenon.com` to μTuner, your receiver will believe it is talking to the official servers. 

Instead of being limited to their curated lists, you gain absolute control over your media through a stunning, modern web interface. 

## ✨ Features

- 🔌 **Seamless AVR Integration:** Emulates `loginXML.asp` and `navXML.asp` out of the box. No hardware modifications or custom firmware required.
- 🎨 **Beautiful Modern UI:** A responsive, HTMX-powered dashboard with a modern design system and built-in Dark Mode.
- 🎵 **Extensive Media Support:**
  - **Web Streams:** Add individual internet radio stations via URL.
  - **Podcasts:** Paste an RSS feed and let μTuner automatically parse the latest episodes.
  - **M3U Playlists:** Import station lists seamlessly.
  - **SMB Shares & Local Storage:** Connect your NAS or local drives. Use the **Interactive File Browser** right from the web dashboard to navigate and add your personal music folders.
- ⚙️ **FFmpeg Transcoding:** Optionally transcode streams on the fly to ensure maximum compatibility with older AVR hardware that might not support modern codecs.
- 🐳 **Docker Ready:** Deploy in seconds using Docker and Docker Compose.

---

## 🚀 Getting Started

### 1. Installation

The easiest way to get μTuner running is via Docker Compose.

Clone the repository and spin up the container:

```bash
git clone https://github.com/adromir/myTuner.git
cd myTuner
docker-compose up -d --build
```

### 2. Network Configuration (DNS Hijacking)

For your AVR to communicate with μTuner, you need to intercept the DNS requests. 

If you use **Pi-hole**, **AdGuard Home**, or a capable router (like OPNsense/pfSense):
1. Create a custom DNS record.
2. Point `radiodenon.com` (and `vtuner.com` depending on your model) to the **local IP address** of the machine running the μTuner Docker container.

*Example:* `radiodenon.com` -> `192.168.1.100`

### 3. Dashboard Configuration

Open your browser and navigate to the μTuner Dashboard:

👉 `http://<your-server-ip>/`

*(You will be redirected to the `/admin/login` page. The default password is `admin`.)*

From the Dashboard, you can:
- Change your password and upload a custom avatar.
- Build your custom folder hierarchy.
- Browse SMB shares and local paths to add your personal library.
- Watch real-time logs of what your AVR is requesting.

---

## 🛠️ Tech Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy, SQLite, FFmpeg
- **Frontend:** HTMX, Alpine.js, Tailwind CSS (via CDN)
- **Deployment:** Docker, Uvicorn

---

## ⚖️ Disclaimer

**μTuner** is a reverse-engineered emulation project created for educational and personal archiving purposes. It allows users to retain the functionality of their legally purchased hardware. This project is **not** affiliated with, endorsed by, or associated with vTuner, Denon, Marantz, or D&M Holdings Inc. 

Please respect copyright laws and the terms of service of media providers when adding custom streams and podcasts to your server.

---

## 📜 License

MIT License

Copyright (c) 2026 **Adromir**

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---
*Created with ❤️ by [Adromir](https://github.com/adromir)*

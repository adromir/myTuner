# Installation

The recommended and fully supported way to install and run μTuner is via **Docker**. This ensures that all dependencies (including Python 3.12, FFmpeg, and SMB client libraries) are isolated and working out of the box.

## Prerequisites
* A server running Docker and Docker Compose (e.g., Raspberry Pi, Unraid, Synology NAS, Ubuntu server).
* A network router or DNS server (like Pi-hole or AdGuard Home) capable of local DNS overriding.

## Deploying via Docker Compose

1. **Clone the repository:**
   ```bash
   git clone https://github.com/adromir/myTuner.git
   cd myTuner
   ```

2. **Start the container:**
   ```bash
   docker compose up -d --build
   ```

3. **Verify it's running:**
   Open a web browser and navigate to `http://<your-server-ip>/`. You should be greeted by the μTuner admin login screen. The default password is `admin`.

## Deploying via Pre-built Image (ghcr.io)
*Note: This assumes the GitHub Action for pushing to the container registry is active.*

You can run μTuner without cloning the repository by using a `docker-compose.yml` file:

```yaml
services:
  mytuner:
    image: ghcr.io/adromir/mytuner:latest
    container_name: mytuner
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./data:/app/data
    environment:
      - TZ=Europe/Berlin
```

Save this to a directory and run `docker compose up -d`.

## Important Note on Ports
Your AVR will make requests on **Port 80**. Therefore, μTuner **must** be accessible on port 80. If you are already running something on port 80 (like a reverse proxy), you will need to configure your reverse proxy to route traffic for `radiodenon.com` to the μTuner container.

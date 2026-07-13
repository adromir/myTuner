# Configuration & Setup

For your AVR to communicate with μTuner, you need to trick it into thinking it is talking to the official vTuner servers. This requires **DNS Hijacking**.

## Determining the Target Domain
The domain your AVR tries to contact depends on the brand and age of your device. Common domains include:
* `radiodenon.com`
* `radiomarantz.com`
* `vtuner.com`

*Tip: Check your router's DNS logs or the μTuner Logs tab to see which domains are being requested.*

## Setting up DNS Hijacking

### Using Pi-hole
1. Open your Pi-hole admin interface.
2. Navigate to **Local DNS > DNS Records**.
3. In the "Domain" field, enter `radiodenon.com` (or your specific domain).
4. In the "IP Address" field, enter the local IP address of your μTuner server (e.g., `192.168.1.50`).
5. Click **Add**.

### Using AdGuard Home
1. Open the AdGuard Home admin interface.
2. Navigate to **Filters > DNS rewrites**.
3. Click **Add DNS rewrite**.
4. Set the domain name to `radiodenon.com`.
5. Set the IP address to your μTuner server's IP.
6. Click **Save**.

### Using OPNsense / pfSense (Unbound DNS)
1. Navigate to **Services > Unbound DNS > Overrides**.
2. Add a new **Host Override**.
3. Set the Host to `*` or leave blank, and Domain to `radiodenon.com`.
4. Enter the IP of your μTuner server.
5. Apply changes.

## Initial App Setup
1. Once DNS is configured, turn your AVR off and on again.
2. Open the μTuner Dashboard (`http://<your-server-ip>/`).
3. Log in with the default password `admin`.
4. Navigate to the **Settings** tab.
5. In the "General Settings" modal, ensure your **Host URL** is set correctly (e.g., `http://192.168.1.50`). This is crucial because μTuner serves dynamic stream URLs to your AVR based on this IP.

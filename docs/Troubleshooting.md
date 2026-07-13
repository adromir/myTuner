# Troubleshooting

## The AVR says "Server Disconnected" or "Network Error"
* **DNS Caching:** AVRs are notorious for aggressive DNS caching. If you just set up your DNS hijacking, you must physically unplug the AVR from the wall and plug it back in to flush its cache.
* **Port Conflicts:** Ensure μTuner is running on Port 80. The vTuner service hardcodes port 80 requests.
* **Firewall Rules:** Ensure that your router or server firewall is not blocking traffic on port 80 between the AVR and the server.

## I can see folders, but streams won't play
* **Host URL Mismatch:** The AVR receives URLs from μTuner that point back to the μTuner server (which then proxies the audio). If the `Host URL` in the μTuner Settings is incorrect (e.g., set to `localhost` instead of the local network IP), the AVR will try to connect to itself and fail.
* **Codec Compatibility:** Older AVRs only support MP3 and sometimes WMA. Modern web streams are often AAC or HLS. Right-click the station in the μTuner Dashboard, click **Edit**, and enable **Use FFmpeg Transcoding** to force the stream into MP3.

## SMB Share won't connect
* Verify that you have provided the correct username and password.
* Check the syntax of the share path. Do not include `smb://`; just select it from the interactive browser.
* Ensure your NAS supports SMBv2 or SMBv3, as SMBv1 is deprecated and disabled in most modern Linux distributions (including the μTuner Docker container).

## Checking Logs
The **Logs** tab in the μTuner dashboard is your best friend. It shows every incoming request from your AVR in real-time. If you see requests coming in (like `GET /setupapp/yamaha/asp/browseXML/loginXML.asp`), then DNS hijacking is working successfully. If it remains empty when you open "Internet Radio" on your AVR, DNS hijacking is failing.

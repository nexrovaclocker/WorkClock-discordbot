"""
WorkClock Bot — Keep-Awake Pinger
===================================
Pings the Render-hosted bot's HTTP endpoint every 2 minutes to prevent
the free-tier instance from spinning down due to inactivity.

Usage:
  Set the RENDER_SERVICE_URL environment variable to your Render service URL
  (e.g. https://workclock-discordbot.onrender.com), then run:

      python keep-awake/pinger.py

You can also deploy this as a separate Render Background Worker or Cron Job,
or use a free external service like UptimeRobot to hit the same URL.
"""

import os
import time
import urllib.request
import urllib.error
from datetime import datetime

PING_INTERVAL_SECONDS = 120  # 2 minutes

def get_service_url() -> str:
    url = "https://workclock-discordbot.onrender.com/"
    return url

def ping(url: str) -> bool:
    """Sends a GET request to the bot's root endpoint. Returns True on success."""
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            status = response.getcode()
            print(f"[{now()}] ✅ Pinged {url} — HTTP {status}")
            return True
    except urllib.error.HTTPError as e:
        print(f"[{now()}] ⚠️  HTTP Error {e.code} pinging {url}: {e.reason}")
        return False
    except urllib.error.URLError as e:
        print(f"[{now()}] ❌ Failed to reach {url}: {e.reason}")
        return False
    except Exception as e:
        print(f"[{now()}] ❌ Unexpected error pinging {url}: {e}")
        return False

def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main():
    url = get_service_url()
    print(f"[{now()}] 🚀 Keep-awake pinger started. Pinging {url} every {PING_INTERVAL_SECONDS}s")
    while True:
        ping(url)
        time.sleep(PING_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()

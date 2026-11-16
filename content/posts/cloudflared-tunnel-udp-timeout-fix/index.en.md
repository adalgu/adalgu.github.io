---
title: "🚀 [Home Server War Stories] I Finally Fixed My Cloudflared Tunnel Dropping Every 1–2 Minutes! (The Culprit: My Router's UDP Timeout)"
description: "The 'timeout' errors that kept dropping my Cloudflared Docker tunnel every 1–2 minutes turned out to be caused by my router's 30-second UDP timeout."
draft: false
translationKey: "cloudflared-tunnel-udp-timeout-fix"
author: Gunn Kim
date: '2025-11-14'
lastmod: '2025-11-14T12:58:00.000Z'
notion_id: 2ab7522e-eb2f-80cc-9428-cc598a2c9861
slug: "cloudflared-tunnel-udp-timeout-fix"
cover:
  image: "cover.jpg"
  alt: "홈 서버와 공유기를 잇는 안정적인 데이터 터널"
  relative: true
  hiddenInSingle: false
  hiddenInList: false
---
![](image-01.png)

Hi there! I've been running a home server for N months now.

Today I want to share a miserable problem I wrestled with for nearly a month, and the almost embarrassingly simple fix.

If you've ever found yourself saying **"My services behind a Cloudflared tunnel keep dropping and reconnecting every 1–2 minutes!"** or **"My SSH session keeps dying!"**, this post will save you some time.

### 😭 The symptoms that tormented me for a month

I run a bunch of services in Docker on a Mac mini and expose them on external domains through Cloudflare's `cloudflared` tunnel.

But at some point, every one of those services turned into a 'zombie', dropping and coming back to life every 1–2 minutes.

1. Web services would intermittently go unresponsive, then work again after a refresh.
1. SSH sessions through the `cloudflared` tunnel would freeze outright if I stopped typing for a moment.
1. I tried restarting the containers, setting up `autoheal`, and plenty of other things, and all of them failed.
To figure out what was going on, I pulled up the `cloudflared` container's logs.

`docker logs -f [your cloudflared container name]`

In the logs, the following **messages from hell** were repeating every 1–2 minutes.

> ERR failed to accept incoming stream requests error="failed to accept QUIC stream: timeout: no recent network activity"

`ERR failed to run the datagram handler error="timeout: no recent network activity"`

`INF Retrying connection in up to 1s...`

`INF Registered tunnel connection ... protocol=quic`

... (1–2 minutes later) ...

`ERR failed to accept QUIC stream: timeout: no recent network activity`

In other words, the connection was timing out because there had been "no recent network activity."

---

### 🕵️‍♂️ The real culprit was somewhere else: my home router

The key word in the logs was **`QUIC`**.

By default, `cloudflared` tries to talk to Cloudflare's edge servers over **QUIC (which is UDP-based)**. It's fast and efficient, after all.

"UDP... timeout...?"

On a hunch, I logged into the settings page of my main home router (an ipTIME, a router brand found in a huge number of Korean homes).

> ❗️ (Pro tip) How to find the IP of the router your Mac mini is connected to

Run netstat -nr | grep default in a terminal, and the Gateway IP it shows is your router's address.

In the router's admin page, under the `Traffic Management > Connection Control` (트래픽 관리 > 커넥션 제어) menu, I came face to face with the culprit.

- **TCP ESTABLISHED TIMEOUT: 86400 seconds (24 hours)**
- **UDP TIMEOUT: 30 seconds**
That was it!

`cloudflared` was connecting over UDP, and whenever a UDP connection saw no activity for **just 30 seconds**, my router went "You dead?" and forcibly cut it off.

That set off the following 'cycle of death', over and over.

1. `cloudflared` successfully connects over QUIC (UDP). (`protocol=quic`)
1. The service sees no traffic for 30 seconds. (An idle SSH session, for example.)
1. The router says "30 seconds are up? You're out!" and forcibly kills the UDP connection.
1. `cloudflared` belatedly notices the connection is gone and spits out a `timeout` error.
1. `cloudflared` tries to reconnect. (Back to step 1.)
---

### 💡 "So just raise the UDP timeout to 24 hours!" ...is that what you were thinking?

**🚨 Absolutely not! (It's a trap card)**

At first I thought the same thing: "I should change the UDP timeout from 30 seconds to 86400!" But that invites an even bigger disaster.

- **TCP** has both sides exchange signals when a connection starts (SYN) and ends (FIN), like saying "Hello!" and "Goodbye!" The router sees that "Goodbye!" and removes the connection from its list right away. The 24-hour timeout is just a last line of defense for sweeping up 'zombie sessions' that died without sending a signal.
- **UDP** has no such signals. It just throws data over. From the router's point of view, there's no way to tell whether a connection is finished or just taking a breather. That makes **the 'timeout' the only means of cleaning up connections**.
If you raise the UDP timeout to 24 hours, every short-lived UDP connection (DNS lookups, game traffic, and so on) piles up in the router's memory for 24 hours. Home routers have a very small amount of this memory (the session table), so **within a few hours the table fills up and your entire internet connection goes down, a full-blown catastrophe**.

Those 30 seconds were there for a reason.

---

### ✅ The final fix: change Cloudflared, not the router

Once you know the cause, the fix is simple. Instead of touching the router settings, you just make `**cloudflared**`** sidestep the 30-second rule**.

> "Don't connect over UDP (30 seconds). Use TCP (24 hours)!"

Helpfully, `cloudflared` offers exactly this option. All you have to do is add one line, an **environment variable**, to your `docker-compose.yml` file.

**Before: **`**docker-compose.yml**`** (example):**

YAML

`services:
  cloudflared:
    container_name: assemblywatch-tunnel
    image: cloudflare/cloudflared:latest
    restart: unless-stopped
    environment:
      - CLOUDFLARE_TUNNEL_TOKEN
    # ... (기타 설정) ...`

**After: **`**docker-compose.yml**`** (the final fix):**

YAML

`services:
  cloudflared:
    container_name: assemblywatch-tunnel
    image: cloudflare/cloudflared:latest
    restart: unless-stopped
    environment:
      - CLOUDFLARE_TUNNEL_TOKEN
      # 👇 [Fix] add this one line!
      - TUNNEL_TRANSPORT_PROTOCOL=http2
    # ... (기타 설정) ...
    dns: # (선택 사항) It also helps to point DNS at Cloudflare.
      - "1.1.1.1"
      - "1.0.0.1"`

- `TUNNEL_TRANSPORT_PROTOCOL: http2` is an environment variable that tells `cloudflared` to "open the tunnel over HTTP/2, which runs on TCP, instead of UDP (QUIC)."
Now recreate the container.

Bash

`docker-compose up -d --force-recreate cloudflared`

---

### 🎉 Confirming the kill: peace returns to the logs

I checked the logs again.

Bash

`assemblywatch-tunnel | 2025-11-14T12:50:07Z INF Environmental variables map[... TUNNEL_TRANSPORT_PROTOCOL:http2]
assemblywatch-tunnel | 2025-11-14T12:50:07Z INF Initial protocol http2
assemblywatch-tunnel | 2025-11-14T12:50:07Z INF Registered tunnel connection ... protocol=http2
assemblywatch-tunnel | 2025-11-14T12:50:07Z INF Registered tunnel connection ... protocol=http2`

See how `protocol=quic` has changed to `protocol=http2`?

My tunnel now runs reliably on top of TCP, with its 24-hour timeout guaranteed. The disconnects and frozen SSH sessions that plagued me for a month are completely gone!

### Wrapping up

To my future self, and to all the other home server users out there...

"When something breaks, read the logs closely, and make sure the keyword (the protocol) that shows up in them isn't clashing with the rules of your network environment (your router)!"

It came down to one very simple environment variable, but it took me a month of detours to find it. I hope this post ends your own flailing in just five minutes.

Happy home serving, everyone! 🥳

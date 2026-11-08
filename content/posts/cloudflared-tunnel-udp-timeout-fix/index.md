---
author: Gunn Kim
date: '2025-11-14'
description: Cloudflared Docker 터널이 1~2분마다 끊기는 'timeout' 오류, 30초짜리 공유기 UDP 타임아웃이 원인이었습니다.
  --protocol http2 옵션으로 한 줄 만에 해결한 방법을 공유합니다.
draft: false
lastmod: '2025-11-14T12:58:00.000Z'
notion_id: 2ab7522e-eb2f-80cc-9428-cc598a2c9861
slug: "cloudflared-tunnel-udp-timeout-fix"
subtitle: ''
summary: Cloudflared Docker 터널이 1~2분마다 끊기는 'timeout' 오류, 30초짜리 공유기 UDP 타임아웃이 원인이었습니다.
  --protocol http2 옵션으로 한 줄 만에 해결한 방법을 공유합니다.
title: 🚀 [홈 서버 삽질] Cloudflared 터널이 1~2분마다 끊기는 현상, 드디어 잡았습니다! (원인은 공유기 UDP 타임아웃)
---

![](image-01.png)

안녕하세요! N개월 차 홈 서버 운영자입니다.

오늘은 제가 거의 한 달간 겪었던 끔찍한 문제와, 너무나도 허무하고 간단했던 그 해결책을 공유하려 합니다.

혹시 **"Cloudflared 터널로 연결한 내 서비스가 1~2분마다 끊겼다가 다시 붙어요!"** 혹은 **"SSH 접속이 자꾸 끊겨요!"** 하는 분이 있다면, 이 글이 당신의 시간을 아껴줄 것입니다.

### 😭 한 달간 저를 괴롭힌 증상

저는 맥미니(Mac mini)에 Docker로 각종 서비스를 올려두고, Cloudflare의 `cloudflared` 터널을 이용해 외부 도메인을 연결해 사용하고 있었습니다.

하지만 언젠가부터 모든 서비스가 1~2분 간격으로 접속이 끊겼다 살아나는 '좀비' 상태가 되었습니다.

1. 웹 서비스 접속이 간헐적으로 먹통이 되었다가 새로고침하면 다시 됩니다.
1. `cloudflared` 터널을 통해 연결한 SSH 세션이 타이핑을 잠시 멈추면 그대로 멈춰버립니다.
1. 컨테이너 재시작, `autoheal` 적용 등 다양한 시도를 해봤지만 모두 실패했습니다.
문제를 확인하기 위해 `cloudflared` 컨테이너의 로그를 찍어봤습니다.

`docker logs -f [내 cloudflared 컨테이너 이름]`

로그에는 1~2분 간격으로 다음과 같은 **지옥의 메시지**가 반복되고 있었습니다.

> ERR failed to accept incoming stream requests error="failed to accept QUIC stream: timeout: no recent network activity"

`ERR failed to run the datagram handler error="timeout: no recent network activity"`

`INF Retrying connection in up to 1s...`

`INF Registered tunnel connection ... protocol=quic`

... (1~2분 뒤) ...

`ERR failed to accept QUIC stream: timeout: no recent network activity`

"최근 네트워크 활동이 없어서" 타임아웃이 났다는 메시지였습니다.

---

### 🕵️‍♂️ 진짜 범인은 따로 있었다: 홈 공유기

로그의 핵심 키워드는 **`QUIC`**였습니다.

`cloudflared`는 기본적으로 Cloudflare 엣지 서버와 **QUIC (UDP 기반)** 프로토콜로 통신을 시도합니다. 빠르고 효율적이니까요.

"UDP... 타임아웃...?"

혹시나 하는 마음에 저희 집 메인 공유기(ipTIME) 설정 페이지에 접속했습니다.

> ❗️ (꿀팁) 내 맥미니가 연결된 공유기 IP 확인법

터미널에서 netstat -nr | grep default를 치면 나오는 Gateway IP가 바로 당신의 공유기 주소입니다.

공유기 관리 페이지의 `트래픽 관리 > 커넥션 제어` 메뉴에서 저는 범인을 마주했습니다.

- **TCP ESTABLISHED TIMEOUT: 86400초 (24시간)**
- **UDP TIMEOUT: 30초**
바로 이것이었습니다!

`cloudflared`는 UDP로 연결했는데, 제 공유기는 UDP 연결이 **단 30초 동안** 아무런 활동이 없으면 "너 죽었니?" 하고 연결을 강제로 끊어버렸던 것입니다.

이로 인해 다음과 같은 '죽음의 사이클'이 반복되었습니다.

1. `cloudflared`가 QUIC(UDP)으로 연결에 성공합니다. (`protocol=quic`)
1. 서비스에 트래픽이 30초간 없습니다. (SSH 잠시 대기 등)
1. 공유기가 "30초 지났네? 아웃!"이라며 UDP 연결을 강제 종료합니다.
1. `cloudflared`는 뒤늦게 연결이 끊긴 것을 감지하고 `timeout` 오류를 뿜어냅니다.
1. `cloudflared`가 재연결을 시도합니다. (1번으로 돌아감)
---

### 💡 "그럼 UDP 타임아웃을 24시간으로 늘리면 되지!" ...라고 생각하셨다면?

**🚨 절대 안 됩니다! (함정 카드)**

저도 처음엔 "UDP 타임아웃을 30초에서 86400초로 바꿔야겠다!"라고 생각했습니다. 하지만 이는 더 큰 재앙을 부릅니다.

- **TCP**는 연결을 시작(SYN)하고 종료(FIN)할 때 서로 "안녕!", "잘 가!" 하고 신호를 주고받습니다. 공유기는 이 "잘 가!" 신호를 보고 연결을 바로 목록에서 지웁니다. 24시간 타임아웃은 혹시나 신호 없이 죽은 '좀비 세션'을 치우기 위한 최후의 보루일 뿐입니다.
- **UDP**는 그런 신호가 없습니다. 그냥 데이터를 던집니다. 공유기 입장에서는 이 연결이 끝난 건지, 잠시 쉬는 건지 알 방법이 없습니다. 그래서 **'타임아웃'이 연결을 청소하는 유일한 수단**입니다.
만약 UDP 타임아웃을 24시간으로 늘리면, 잠깐 사용된 모든 UDP 연결(DNS 조회, 게임 신호 등)이 공유기 메모리에 24시간 동안 쌓이게 됩니다. 가정용 공유기는 이 메모리(세션 테이블)가 매우 작아서, **몇 시간 안에 테이블이 꽉 차 인터넷 전체가 먹통이 되는 대참사**가 벌어집니다.

30초는 다 이유가 있었던 것입니다.

---

### ✅ 최종 해결책: 공유기가 아닌 Cloudflared를 바꾸자

원인을 알았으니 해결은 간단합니다. 공유기 설정을 건드리는 것이 아니라, `**cloudflared**`**가 30초 룰을 피해가도록** 만들면 됩니다.

> "UDP(30초) 말고, TCP(24시간)로 연결해!"

`cloudflared`는 친절하게도 이 옵션을 제공합니다. `docker-compose.yml` 파일에 **환경 변수** 한 줄만 추가하면 됩니다.

**수정 전 **`**docker-compose.yml**`** (예시):**

YAML

`services:
  cloudflared:
    container_name: assemblywatch-tunnel
    image: cloudflare/cloudflared:latest
    restart: unless-stopped
    environment:
      - CLOUDFLARE_TUNNEL_TOKEN
    # ... (기타 설정) ...`

**수정 후 **`**docker-compose.yml**`** (최종 해결책):**

YAML

`services:
  cloudflared:
    container_name: assemblywatch-tunnel
    image: cloudflare/cloudflared:latest
    restart: unless-stopped
    environment:
      - CLOUDFLARE_TUNNEL_TOKEN
      # 👇 [해결책] 이 한 줄을 추가합니다!
      - TUNNEL_TRANSPORT_PROTOCOL=http2
    # ... (기타 설정) ...
    dns: # (선택 사항) DNS도 Cloudflare로 지정해주면 좋습니다.
      - "1.1.1.1"
      - "1.0.0.1"`

- `TUNNEL_TRANSPORT_PROTOCOL: http2`는 `cloudflared`에게 "UDP(QUIC) 대신 TCP 기반인 HTTP/2 프로토콜로 터널을 뚫어라"고 명령하는 환경 변수입니다.
이제 컨테이너를 다시 생성합니다.

Bash

`docker-compose up -d --force-recreate cloudflared`

---

### 🎉 확인 사살: 평화가 찾아온 로그

다시 로그를 확인해 봤습니다.

Bash

`assemblywatch-tunnel | 2025-11-14T12:50:07Z INF Environmental variables map[... TUNNEL_TRANSPORT_PROTOCOL:http2]
assemblywatch-tunnel | 2025-11-14T12:50:07Z INF Initial protocol http2
assemblywatch-tunnel | 2025-11-14T12:50:07Z INF Registered tunnel connection ... protocol=http2
assemblywatch-tunnel | 2025-11-14T12:50:07Z INF Registered tunnel connection ... protocol=http2`

`protocol=quic`이 `protocol=http2`로 바뀐 것이 보이시나요?

이제 제 터널은 24시간 타임아웃이 보장된 TCP 위에서 안정적으로 작동합니다. 한 달간 저를 괴롭히던 끊김 현상과 SSH 먹통 현상이 완벽하게 사라졌습니다!

### 맺으며

미래의 나와 또 다른 홈 서버 유저분들에게...

"문제가 생기면 로그를 자세히 보고, 그 로그에 나온 키워드(프로토콜)가 내 네트워크 환경(공유기)의 룰과 충돌하지 않는지 꼭 확인해 보세요!"

정말 간단한 환경 변수 하나였지만, 이걸 찾기 위해 한 달을 돌아왔네요. 이 글이 여러분의 삽질을 단 5분 만에 끝내주길 바랍니다.

모두 즐거운 홈 서버 운영 되세요! 🥳


---
title: "LiveCast HUD"
summary: "한국어 발표에 실시간 영어 자막을 전체 화면 슬라이드 위에 띄웁니다."
status: "실험"
weight: 2
cover:
  image: "cover.jpg"
  alt: "전체 화면 슬라이드 아래에 영어 자막 막대가 뜬 데모 화면"
repo_public: true
links:
  - {kind: repo, url: "https://github.com/adalgu/livecast-hud", label: "adalgu/livecast-hud"}
  - {kind: demo, url: "demo.gif", label: "데모 움짤"}
version: ""
version_note: "버전 표시 없음 — 저장소에 릴리스·태그가 없음"
hidemeta: true
ShowReadingTime: false
ShowWordCount: false
ShowShareButtons: false
ShowPostNavLinks: false
---

## 무엇

한국어 발표에 영어 자막을 실시간으로 붙여 슬라이드 위에 띄웁니다. 발표자의 말을 알아듣고 전체 화면 PowerPoint나 Keynote 슬라이드 쇼 위의 얇은 자막 막대에 영어를 보여 줍니다. 대본을 미리 준비했다면 말한 문장을 대본과 맞춰 직접 써 둔 영어를 그대로 띄웁니다.

## 화면

{{< figure src="subtitle-bar.jpg" alt="자막 막대: 영어 두 줄, 말하는 중인 문장의 흐린 줄, 한국어 줄" caption="자막 막대. 출처 [adalgu/livecast-hud](https://github.com/adalgu/livecast-hud) (Apache-2.0)" >}}

{{< figure src="demo-frame.jpg" alt="지어낸 내용의 예시 슬라이드 위에 영어 자막 막대가 뜬 데모 프레임" caption="데모 프레임 — 예시 슬라이드는 지어낸 내용. [움직이는 데모 보기](demo.gif)(790KB)" >}}

## 어떻게 도나

- 말을 한국어 문장으로 알아듣고(라이브 모드는 Google Cloud 음성 인식), 대본에 있는 문장이면 미리 써 둔 영어를, 없으면 번역을 띄웁니다.
- 자막 막대는 전체 화면 슬라이드 위에 떠 있고 클릭은 그대로 통과시켜, 클리커와 마우스로 슬라이드를 계속 넘길 수 있습니다.
- 데모 모드는 마이크·계정·네트워크 없이 바로 돌려 볼 수 있습니다.
- macOS 전용, Python 3.10 이상.

---
# Documentation: https://sourcethemes.com/academic/docs/managing-content/

title: "외장두뇌 프로젝트"
summary: ""
authors: []
tags: [exobrain]
categories: [exobrain]
date: 2020-02-18T01:00:55+09:00

# Optional external URL for project (replaces project detail page).
external_link: ""

# Featured image
# To use, add an image named `featured.jpg/png` to your page's folder.
# Focal points: Smart, Center, TopLeft, Top, TopRight, Left, Right, BottomLeft, Bottom, BottomRight.
image:
  caption: ""
  focal_point: ""
  preview_only: false

# Custom links (optional).
#   Uncomment and edit lines below to show custom links.
# links:
# - name: Follow
#   url: https://twitter.com
#   icon_pack: fab
#   icon: twitter

url_code: ""
url_pdf: ""
url_slides: ""
url_video: ""

# Slides (optional).
#   Associate this project with Markdown slides.
#   Simply enter your slide deck's filename without extension.
#   E.g. `slides = "example-slides"` references `content/slides/example-slides.md`.
#   Otherwise, set `slides = ""`.
slides: ""
---

> "The web as a second brain."

외장두뇌는 한마디로 나의 두번째 두뇌로써 웹을 활용하는 프로젝트이다.
정보 저장이 될 수도 있고, 정보 정리가 될 수도 있으며, 정보 출력이 될 수도 있다.

## 외장두뇌 프로젝트

*외장두뇌 프로젝트는 퍼블릭(공개)과 프라이빗(비공개) 2가지 채널로 운영하고 있습니다. 본 웹사이트 [gunn.kim](https://gunn.kim)은 public 외장두뇌 프로젝트이며, private 외장두뇌 프로젝트는 디지털 기록도구인 [Dynalist](https://dynalist.io)를 이용하여 가동 중에 있습니다. 2020년 3월 현재 Dynalist에서 [Notion](https://notion.so)으로의 이동을 준비 중입니다.*

- 외장두뇌 프로젝트
  - Public : https://gunn.kim으로 접속, 현재는 gitlab 기반의 정적 웹 페이지(static web page)로 운영. 추후에 블로그 기능을 넘어 동적 정보처리 기능을 붙일 예정.
  - Private : [Dynalist](https://dynalist.io)로 진행. Feedly와 Pocket, IFTTT, 구글캘린더로 보조. 궁극적으로 웹과 통합하여 운영할 예정. 기성 서비스 중에 **Notion** 이 가장 유사한 형태.

## <입력하기>
1. Feedly로 RSS 구독
2. Pocket으로 아티클 수집
3. IFTTT로 컨텐츠 자동 처리
4. Notion으로 컨텐츠를 1차 가공

## <출력하기>
1. 도구 세팅하기 (Tool)
   1. git 설치 (+github 또는 gitlab 계정 만들기)
   2. hugo 설치
   3. vs code 설치
2. 웹사이트 만들기 (Repo)
   1. Gitlab에 저장소 만들기(Github도 가능)
   2. 저장소에 휴고(hugo)로 만든 사이트 올리기
   3. 빌드하고 배포하기(Gitlab pages 또는 Netlify)
3. 웹사이트 세팅하기 (Web)
   1. 도메인 네임 구매하기
   2. 도메인 네임 세팅하기
   3. https 세팅하기
4. 컨텐츠 만들기 (Production)
   1. 메뉴 구성하기
   2. [컨텐츠 제작 환경 만들기(feat. vs code 또는 RStudio)](/post/2020-01-30-vscode-markdown-writing/)
   3. git으로 커밋하고 푸쉬하기

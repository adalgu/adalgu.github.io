---
# Documentation: https://sourcethemes.com/academic/docs/managing-content/

title: "Writing Tool Project"
summary: ""
authors: []
tags: [writing, python]
categories: [writing]
date: 2020-02-25T10:07:27+09:00

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

0. 프롤로그
   - 예전부터 만들고 싶은 앱이 있었는데, 글쓰기 도구다. 시중에도 많은 글쓰기 관련 앱과 책들이 있지만, 내가 원하는 도구는 아직 보지 못한 것 같다. 그래서 직접 만들어 보고자 구상한 것을 정리해 보고자 한다.
1. 앱 기능
   - 내가 글 쓰기 할 때 필요한 것 
     - 첫째, 글의 틀을 미리 세팅해 놓는 것 : 백지에 글을 쓰기보다, 글의 틀이 만들어져 있으면 시작하기가 편하다. 몇가지 예시가 있어도 도움이 된다.
     - 둘째, 링크, 이미지 등을 쉽게 가져올 수 있는 것 : 글만 있는 글은 보기가 싫다. 간단한 이미지가 있어서 보고 싶어진다. 좋은 글쓰기 툴들은 글에 포함되는 이미지나 링크, 영상을 쉽게 가져올 수 있다. 브런치, 네이버 블로그 등등.
     - 셋째, 오타 수정이 간편 : 맞춤법이나 오타는 옥의 티다. 퇴고할 때 오타는 자동으로 고칠 수 있으면, 더 풍부한 표현에 집중할 수 있다.
     - 넷째, 글의 분량 : A4지 몇장, 200자 원고지 몇장, 몇분짜리 글 등의 글쓰기 분량이 정해져 있다. 글을 쓰면서 분량을 알 수 있으면 참고하는데 좋다.
     - 다섯째, 두괄식 검사 : 글쓰기 테크닉에는 여러 방법이 있겠지만, 일단은 두괄식 글쓰기가 쓰는 사람이나 읽는 사람이 편하다. 두괄식으로 문단의 소주제문을 미리 완성해 놓으면, 글을 전체 얼개를 잡는데 도움이 된다. 문단의 첫문장만 뽑아서 보여주는 앱!
     - 여섯째, 주제어 검색 : 자연어 처리 기능을 이용해서 주제어나 반복어를 뽑아 주면 좋다. 태그 등에 바로 활용할 수 있다.
     - 일곱째, 제목 제안 : 완성된 글을 분석하여 적절한 제목을 복수로 제안한다. 비슷한 상황에서 유사한 종류의 글 중에 주목을 끌었던 제목을 참고하여 제안한다.ㄴ
2. 구현 방법
   1. 파이썬으로 기본 앱을 만든다.
      1. 파이썬 자연어처리 라이브러리를 이용해서 글을 분석할 수 있는 모듈을 만든다.
      2. VS CODE로 글쓰기 앱의 목업을 만들어 본다.
      3. API를 활용해서 오타 수정 등의 기능을 구현한다.
   2. 좋은 글에 대한 DB를 구축한다.
      1. 참고할 만한 글들을 모아서 db를 구축하고,
      2. 이 글들에서 공통적인 패턴을 찾아서 인사이트를 뽑는다.
   3. 웹, 앱, 워드 애드온 버전을 만든다.
      1. 웹에서 간단하게 해 볼 수 있도록..
      2. 모바일이나 로컬 앱으로도 해볼 수 있도록
      3. 워드나 구글독스 애드온 버전을 만들어서 활용할 수 있도록...
3. 깃허브에 코드를 올린다.
   1. 공유 받아서 만든 것이니 나도 공유해서 미려하나마 기여한다.
   2. 피드백을 받아서 개선한다.
4. 에필로그
   1. 교훈과 의미를 정리한다.
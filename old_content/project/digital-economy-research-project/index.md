---
# Documentation: https://sourcethemes.com/academic/docs/managing-content/

title: "Digital Economy Research Tech Tree"
summary: "디지털 경제 리서치 테크 트리 정리"
authors: []
tags: []
categories: []
date: 2020-02-11T11:22:12+09:00
diagram: true

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

### My own Digital Research Tech-tree ver 0.2(Draft, Feb, 2020)

- References : [과거 보고서](https://academic.naver.com/search.naver?query=%EA%B9%80%EA%B1%B4%EC%9A%B0+LG%EA%B2%BD%EC%A0%9C%EC%97%B0%EA%B5%AC%EC%9B%90&field=0&sort=2&searchType=1&refineType=exist&docType=&thesisLv=&journalLv=&access=&year=&category=&journal=&source=)

```mermaid
graph TD;
  Gunn-->경제;
  Gunn-->금융;
  Gunn-->기술-->디지털기술-->비트코인;
  경제-->경제통합_EU,남북경제-->제도;
  경제-->일자리정책-->제도;
  경제-->서비스산업-->제도;
  제도-->혁신-->디지털경제;
  디지털기술-->제도;
  디지털기술-->플랫폼_네트워크-->디지털경제;
  디지털기술-->인공지능_SW-->디지털경제;
  디지털기술-->데이터-->디지털경제;
  금융-->화폐-->비트코인;
  금융-->금융시장;
  비트코인-->핀테크;
  금융시장-->은행-->핀테크;
  핀테크-->디지털경제;
  디지털경제-->디지털무역-->BEPS;
  디지털무역-->테크기업_독과점;
  디지털경제-->경쟁/반독점-->테크기업_독과점;
  경쟁/반독점-->디지털카르텔;
  디지털경제-->노동/자동화-->인공지능_자동화;
  노동/자동화-->공유경제;
  디지털경제-->산업;
  산업-->아마존효과;
  산업-->공유경제;
  공유경제-->플랫폼노동;
  공유경제-->모빌리티;
  아마존효과-->모빌리티;
 ```
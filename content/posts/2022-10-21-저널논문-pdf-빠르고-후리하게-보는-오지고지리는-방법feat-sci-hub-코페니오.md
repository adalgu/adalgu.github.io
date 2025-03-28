---
author: Gunn Kim
date: '2022-10-21T00:00:00.000+09:00'
draft: true
keywords: &id001
- Tip
lastmod: '2025-03-21T02:44:00.000Z'
notion_id: ef2812a8-1dc3-4d47-84fc-bc3d4a655ccf
slug: paper-pdf-scihub-kopernio
tags: *id001
title: 저널논문 PDF 빠르고 후리하게 보는 오지고지리는 방법(feat. Sci-hub, 코페니오)
---


![](https://prod-files-secure.s3.us-west-2.amazonaws.com/94f51666-273a-443d-bf89-42827b5b6876/ce2e2ad6-7132-4ec7-b83c-4724b884077b/Untitled.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466YJJ53DHQ%2F20250328%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20250328T102940Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEPL%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJGMEQCIBMkWykK2lMKd3fw53nI2Nf3IBoTMvNJDxl72%2B1VEZUPAiBxFzXJrxi%2Fsp%2FYuDj3MxjUKmEUqBkcGQpBsTcghqbV7yr%2FAwhbEAAaDDYzNzQyMzE4MzgwNSIMiKb400W83XA4wklJKtwD1R5qL06N2OsOab1GE0PtSKh%2BHRkF9LkzmjCoSrGLPMhp21YLmWLW%2Bcki%2F5YhHooFivoKtYwPnksunQtAZ%2BMfJMTbJIa1sqLGhGrM4skVFyVCQq39o8hlvFToHe4QWq2p4gFNuNiIrrNwO6BfJ99nNo2YoiyCIj9ZkRHdpG3DRKspRyFkHRX7Au1Pr40B7kfNR87rHf%2B6%2FHVW%2B4X1Jl13%2FCx0hC9VOCqws9N3ehiNxJCMCojYvajv9f8T2ykJ7zvjAAnCTY9sX%2BOLnmjJ%2BtjVmuwfZVET2DFhdLbtnFbUyFfSZoFk1%2Fy7L7jRZ0dtX1rsjvtBz4dB9UfJ2xU2AmV1WQ8n28Y7%2BReExcv%2FOQca1TOKab0tWhCWaTgTrTuaNt61lqHbc97W84qivolCGqFH5Dzek7oebvbzb7yCVozmrp%2FVr%2Bhdtn0qFIt15j3A%2FkwptJuI94w%2BJMqAzbhQNjk%2F%2FdSKX%2F2LKqgtQ5%2F0s8k46M%2BqQdsyei4pzioeW6g%2BDUSw5ov5amTeyie3H2wIyqCTkIKqX%2BGJDG4f6QUEuBjzxcjp4i2wrMNeegrhywf9PBi9XtZ2MxYyBWiKVvnQ4bL8xCN2fP7d2TN6S30KZNquhAd91YMknl1%2BmPzfcxgwqduZvwY6pgG5yOH6RKLR5P3gMVyXhDRnn9rBLpnnvywYo%2FUMT%2FpofZ1gMQVKdgQyJhNYEKYzd%2FLnwtzAtKD4auOSkFPfCcEmruut3oQlPSO8sG%2BpEsHJv5memG5IRy9gDH2IeS1R%2FZ473YuvqYjVXG5ZdvcltQdq3FK0GpJvC%2FkkDmszHsmlPx9OkckafeXO6ljoX4wCL1ye25Wbw7JGu8n%2FT%2BpKX4uJgGkh2BxA&X-Amz-Signature=9cf9b2a6eda395fbe2ac8d322b7a738077f63b6f56e46ffca61ced37b01835e7&X-Amz-SignedHeaders=host&x-id=GetObject)

<details>
<summary>'오지고 지지다'라는 것의 의미는 위와 같다</summary>

</details>


## 들어가며...

구글링으로 논문 검색하면 항상 걸리는 페이지 : ScienceDirect, Elsevier(엘스비어)...

자연스레 PayWall(지불장벽)에 좌절하게 된다. 돈을 낼만한 논문인지, 회사나 학교에서 접속 가능한 저널 DB인지 당장 알아내기 힘들 때, 이러한 지불장벽은 엄청난 심리적 압박으로 작용한다.

저널논문 뿐만 아니라 NBER Working Paper와 같은 것을 보려고 치면, 저자의 홈페이지에 계시되어 있는 논문도 결제의 압박이 다가오는 경우도 많다. NBER의 경우에는 개도국에서 접속하는 경우에만 무료로 다운로드 가능하다.

아래 예시를 보자. NBER에 게재된 하버드 비즈니스 스쿨의 Alberto Cavallo 교수의 아마존 효과에 대한 논문이다. 

- 이  논문은 2018년 잭슨홀 미팅에서 발표된 논문으로 미국 캔자스시티 연준(잭슨홀 미팅 주관)의 홈페이지에서 [공개]([https://www.kansascityfed.org/~/media/files/publicat/sympos/2018/papersandhandouts/825180810cavallopaper.pdf?la=en](https://www.kansascityfed.org/~/media/files/publicat/sympos/2018/papersandhandouts/825180810cavallopaper.pdf?la=en))하고 있다. 
- 저자의 홈페이지에서도 [공개]([https://www.hbs.edu/faculty/Publication Files/Cavallo_Alberto_J2_More Amazon Effects-Online Competition and Pricing Behaviors_61ab3273-d446-4dd5-9e71-469c54c46662.pdf](https://www.hbs.edu/faculty/Publication%20Files/Cavallo_Alberto_J2_More%20Amazon%20Effects-Online%20Competition%20and%20Pricing%20Behaviors_61ab3273-d446-4dd5-9e71-469c54c46662.pdf))하고 있다. 
- 그런데 NBER에서는 아래와 같이 개도국 접속자만 무료(아래 그림 빨간색 강조)라고 뜬다. 그쪽 정책이야 어쩔 수 없는 노릇이지만, 구글링으로 한번 더 하면 워킹페이퍼보다 더 최종 버전의 논문을 볼 수 있는 상황이라 다소 실효성 없는 정책이다.
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/94f51666-273a-443d-bf89-42827b5b6876/0d58c6aa-5d31-414c-865a-1761b6b5172b/Untitled.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB46654YZE3FM%2F20250328%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20250328T102940Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEPL%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJHMEUCIHMuU2BftyxJ57vHuEcFg5PhPy8ZEz0ZEKFk77jBFDHlAiEAo23O12q4rGVScAZ7OuKSapejA6Mf7yIStl8lonWeAvwq%2FwMIWxAAGgw2Mzc0MjMxODM4MDUiDG83vFs1uh%2FRO4t9XCrcA2Gzf7gp0vWAvYvLrZtAu2fPQTfKIAXhKxcgm81y8i%2BcNey4HgSlahkI6hOsn4OPT5ra%2Bp1NL%2BwGK6vVy5i71i2rTcAw5ZbxdmENjNpH9z7F7h6%2FnnbbSlD%2FL1G%2BfandVPJzPE7d7b%2FFexszbZyoQpFOip2X6dEPmzNFaRtvrrQEY5SmN%2BJzXr6ur7wAF6vU1nPThy%2FTrMPnRC5EDRUPyn4krdnoDw6p0fcT1sydkdkhciOgpnhi%2B2Mj3kOumTbXR4XJnDE8sSJSH6QsjE%2BNIxCC1ghfGeQtFCEMpGCfm%2Fg93krCKg4hSvVamEcvu%2BRCHUV18icUxB%2FL5Jj71M2%2FtLgXucT9vh%2F8iLILAwqamEYzOavHNQ69nf8JI4VIgTY8d1iWQ3P%2B2etZG6sq0q85EK%2FKQwlOzqbDjHzk0rpukQwFYtJc%2B4Nz0GMh1WpPOra6VW6rixcsY6bJDelWx%2Bdbz1cn4LqcfS4oDpyVyyLT83OqVPVwCAGAbpZP0XIf2hebQ%2BFmJ4K0DN8Wk4auf3y84uqNd43OEB%2FcGRzo%2BBExzCMYdUaO8buxOBsLwaNZzo0rh2eKqQHnwMkTFXKZoPPZ150iLStdR0V2b9UAp3IUrBrQaQyLZzR6JWtf90DfMI3pmb8GOqUB%2FZ3sD2Xumv7Hryotc5mD3u%2FHalAdg782H%2BdrNnLzsCl%2FeFFgK%2BTGkgVvt1WyaAA1Kwl7L6xJk3zOfKDx3Lvzx7L18n32SZmvcjeHuy%2FqLZjMbmSXBkeTFIX%2FW4GUbYps5zUDqnU0WfpK%2BWXKDim1zu76tr%2FNLwAlppDwJjtXJQw3HzXDM%2FdrvuQts9Vq0uDKSWVuVsnThYkPvkACbRK9blrg7ijn&X-Amz-Signature=d4724c7cb6801b3f1c50d04265442f8f4f37588e0f2e0492b875046a15fcac1e&X-Amz-SignedHeaders=host&x-id=GetObject)

- 팁 하나, VPN으로 우회 접속
- NBER과 같은 상황인 경우에는 VPN으로 개도국 프록시 서버로 우회하여 접속하면 바로 논문을 볼 수 있다. 학교에 적을 두고 있는 사람의 경우 학교 프로시 서버를 거쳐서 저널 웹사이트에 접속하기도 한다. 도서관에서 저널을 구독하는 경우 교내 IP에 대해서만 열람을 허용하는 정책때문이다.

## 1. 싸이헙(Sci-hub) 기본 사용법

서론이 길었다. 논문 PDF를 급하게 보고 싶은데, 시간과 돈이 없을 때 쓸수 있는 오지고 지린 꿀팁에 대해서 살펴보자.

바로 Sci-hub([https://sci-hub.tw/](https://sci-hub.tw/))을 이용하는 것이다. 싸이헙이라 읽는다.

참고로, 아래와 같은 법정 다툼이 있었다는 것은 인지하자. 

- 싸이헙을 저작권 침해로 고소한 [기사 하나]([http://www.bloter.net/archives/259652](http://www.bloter.net/archives/259652))
- “엘스비어가 이들 논문의 창작자가 아니라는 사실을 말씀드리고 싶다. 엘스비어 웹사이트에 등록된 모든 논문은 연구자들이 쓴 것이다. 연구자들은 엘스비어로부터 돈을 받지 않는다. 이는 창작자들이 팔린 만큼 돈을 받는 음악이나 영화 산업과는 완전히 다르다. (중략) 왜 연구자들은 (돈도 받지 않는데도) 자신들의 논문을 엘스비어에 제공할까? 그렇게 해야 하는 압력을 느끼기 때문이다. 왜냐하면 엘스비어는 소위 영향력 높은 저널의 소유자이기 때문이다. 연구자가 인지도를 얻기 위해서는 그 저널들에 게재됐다는 커리어를 만들 필요가 있어서다.” (싸이헙 창업자가 법원에 제출한 문서)

싸이헙 기본 사용법은 아래와 같이 간단하다.

아래 형식으로 [sci-hub.tw/](http://sci-hub.tw/)에 이어서 [논문주소]를 주소창 입력하면 바로 논문 pdf를 띄워준다.

- `http://sci-hub.tw/[논문주소]`
- 예시 1 : 논문의 주소가 "[https://www.nber.org/papers/w25138](https://sci-hub.tw/https://www.nber.org/papers/w25138)"일 경우, 아래를 주소창에 입력!
- [https://sci-hub.tw/https://www.nber.org/papers/w25138](https://sci-hub.tw/https://www.nber.org/papers/w25138)
- 예시 2 : 논문의 주소가 "[https://www.sciencedirect.com/science/article/pii/S0040162516302244](https://sci-hub.tw/https://www.sciencedirect.com/science/article/pii/S0040162516302244)"일 경우, 아래를 주소창에 입력!
- [https://sci-hub.tw/https://www.sciencedirect.com/science/article/pii/S0040162516302244](https://sci-hub.tw/https://www.sciencedirect.com/science/article/pii/S0040162516302244)

## 2. 북마크 신공으로 싸이헙 논문 바로 보기

Sci-hub을 원클릭으로 간편하게 사용하는 방법도 있다. 자바스크립트를 북마크로 등록해서 간편하게 논문을 볼 수 있는 방법이다. 


북마크로 싸이헙을 이용하는 방법은 아래와 같다.

북마크를 하나 만들자. 

- 아무 웹사이트에나 가서 북마크 추가를 하고, 아래와 같이 수정하면 된다.
- 이름: Sci-hub
- URL: 아래 자바스크립트를 그대로 복사해서 붙여넣자.
- `javascript:(function(){window.location='`[`https://sci-hub.tw/'+location.href`](https://sci-hub.tw/%27+location.href)`})();`

이 방법은 싸이헙 기본 사용법을 원클릭으로 해결해주는 방법이다.

논문 사이트가 나타나거든, 위에서 만든 Sci-hub 북마크를 클릭하자!

그러면 Sci-hub에서 해당 논문을 자동으로 검색해서 PDF를 띄워준다!


*북마크 신공 출처는 아래를 보고, 기존에 자바스크립트를 이용하여 북마크를 만든 방법을 결합한 것이다.*

- 트위터에서 본 클리앙 글이다. *참 진짜 우연인게, 평소에 들어가지도 않는 트위터에 옛날 글을 찾으로 갔다가 우연히 추천 계정이 떠서 그냥 클릭해 봤더니, 아래 클리앙 글을 소개해줘서 클릭했더니 좋은 팁이 있었다.*~~*는 전설같은 에피소드.*~~

## 3. 크롬 확장프로그램으로 논문 PDF 찾기

싸이헙을 이용하지 않고도 비슷한 효과를 내는 방법이 있다.

Kopernio(코페니오)라는 크롬 확장프로그램이 그것이다. 이 프로그램은 개별 논문 페이지나 구글 스콜라 검색 등과 연계하여 이용 가능한 원문이 있으면 브라우저 좌측 하단에 PDF 다운 버튼이 뜨게 해준다.

사용 방법은 [https://kopernio.com/](https://kopernio.com/) 접속하거나 크롬 웹스토어에 바로 가서 코페니오 크롬 확장 프로그램을 무료로 추가하면 된다! 또는 아래 클릭하면 바로 설치 가능하다.


*위 꿀팁은 대구경북과기원 사서 웹페이지에서 퍼왔다. 사서들도 쓰는 방법이니 품질 보증! 기타 방법도 잘 소개주고 있으니 참고!*


## 나가며...

위 방법보다 더 오지고 지린 방법이 있으면 댓글로 남겨주길 바란다.


![](https://prod-files-secure.s3.us-west-2.amazonaws.com/94f51666-273a-443d-bf89-42827b5b6876/c4bbd7ff-719c-4a7d-b246-e4c765b69d30/Untitled.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466YJJ53DHQ%2F20250328%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20250328T102940Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEPL%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJGMEQCIBMkWykK2lMKd3fw53nI2Nf3IBoTMvNJDxl72%2B1VEZUPAiBxFzXJrxi%2Fsp%2FYuDj3MxjUKmEUqBkcGQpBsTcghqbV7yr%2FAwhbEAAaDDYzNzQyMzE4MzgwNSIMiKb400W83XA4wklJKtwD1R5qL06N2OsOab1GE0PtSKh%2BHRkF9LkzmjCoSrGLPMhp21YLmWLW%2Bcki%2F5YhHooFivoKtYwPnksunQtAZ%2BMfJMTbJIa1sqLGhGrM4skVFyVCQq39o8hlvFToHe4QWq2p4gFNuNiIrrNwO6BfJ99nNo2YoiyCIj9ZkRHdpG3DRKspRyFkHRX7Au1Pr40B7kfNR87rHf%2B6%2FHVW%2B4X1Jl13%2FCx0hC9VOCqws9N3ehiNxJCMCojYvajv9f8T2ykJ7zvjAAnCTY9sX%2BOLnmjJ%2BtjVmuwfZVET2DFhdLbtnFbUyFfSZoFk1%2Fy7L7jRZ0dtX1rsjvtBz4dB9UfJ2xU2AmV1WQ8n28Y7%2BReExcv%2FOQca1TOKab0tWhCWaTgTrTuaNt61lqHbc97W84qivolCGqFH5Dzek7oebvbzb7yCVozmrp%2FVr%2Bhdtn0qFIt15j3A%2FkwptJuI94w%2BJMqAzbhQNjk%2F%2FdSKX%2F2LKqgtQ5%2F0s8k46M%2BqQdsyei4pzioeW6g%2BDUSw5ov5amTeyie3H2wIyqCTkIKqX%2BGJDG4f6QUEuBjzxcjp4i2wrMNeegrhywf9PBi9XtZ2MxYyBWiKVvnQ4bL8xCN2fP7d2TN6S30KZNquhAd91YMknl1%2BmPzfcxgwqduZvwY6pgG5yOH6RKLR5P3gMVyXhDRnn9rBLpnnvywYo%2FUMT%2FpofZ1gMQVKdgQyJhNYEKYzd%2FLnwtzAtKD4auOSkFPfCcEmruut3oQlPSO8sG%2BpEsHJv5memG5IRy9gDH2IeS1R%2FZ473YuvqYjVXG5ZdvcltQdq3FK0GpJvC%2FkkDmszHsmlPx9OkckafeXO6ljoX4wCL1ye25Wbw7JGu8n%2FT%2BpKX4uJgGkh2BxA&X-Amz-Signature=3c1d6da95f1404b325451b46ce94683d8f1cb22656e109b0365ac4de48b5eb5c&X-Amz-SignedHeaders=host&x-id=GetObject)


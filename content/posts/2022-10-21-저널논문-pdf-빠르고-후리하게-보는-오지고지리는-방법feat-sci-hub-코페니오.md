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


![](https://prod-files-secure.s3.us-west-2.amazonaws.com/94f51666-273a-443d-bf89-42827b5b6876/ce2e2ad6-7132-4ec7-b83c-4724b884077b/Untitled.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466QV4ARVUS%2F20250327%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20250327T043241Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjENX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJHMEUCIDwyy%2FSEeBl39WououXaywZ6RFFoGUbpm1K3b5vc%2BzeuAiEAlNh8j%2BQ7mH8lX9aOpUPxnBmYtyjM9BqLS64xV4cwTYgq%2FwMIPRAAGgw2Mzc0MjMxODM4MDUiDKve5DFHtbMe4nN0JCrcA7ua5LdzO5h%2BL948eUUIgHV1yQdHK%2Biy1Z9UKSUYGdt8HPN4v1xSEcjH0fs8FuvCh5OXMwQ8%2FNbgaUsjo05yscmB8qVqrXAcJ71cg3aXt%2FvYigT5zmXSAwiMvedqgp%2BVyeYOVa7fTyd3yfrzU9et3TCyeDY4xPDgb%2BgiXF5cjCxylLfhbKJuwhdi7y4PbZkP%2FhCHaVgoDY7cs1m4OsBAmmGkRdf57%2FHIFkYVa5Q%2Bf4xnqiQffnWz4s%2FTVDY6Unt7HAo5NkMo8zQac%2BKMpL3wqCRh4Nylu6AdwVWFoj4csVq%2F%2FXVy%2FIUYQK6JwIdEi2T1LV9hSJebMJeVxyzWwasfYaHWRBcY4W1CmUby6xMZCE7NzV67VxQp%2BDavfI4dqTuiduPvQRYi7pwweTvloGewcPMaqoRbiPjGbUirua9cEHVhJrtJkwL8AhlLFO6S4Lus7WNP9LjSWttP9pYY%2BnIu3d5ClKE0og3TzCE2es0p2yS%2BXK%2BkrmVa6H6RIBG0p%2BU7mo%2Bm34qxjLwLiugSNbBIhhoPXLuAh7CFdk9Vglx51vCPAz0Bs56emztGcoFZC8fES1oonKXJFPxnaHHzv36VrD1aYa59SZUSNGjH8X18%2BjXYTP%2FZPaFULDwGx2r%2BMJGlk78GOqUB1ACzZhYtsjs8Z%2B%2BnCyN9xHXFhmEeTLP71KM5lYy5mlgruCPjLEV3cDlils9uNqFXhaok0z1yzJU1Okos5hwtpFdipy8TvHlmLrvFKILceaL7Qd4Mp%2FXfUd5DBRYw%2Fs4mo%2FTDINqdryyhbpgLIB52sTdGn3mgXj3rgBk4bPPmMYQqhuIQWH28vqjc1ZVg1RHDz2etTpZjoBuhU401ADi5DoAQzlrH&X-Amz-Signature=b6f32d8c1fb202e08087067794b96596b8d0f6830eca26fa2dd31a7984f3a733&X-Amz-SignedHeaders=host&x-id=GetObject)

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
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/94f51666-273a-443d-bf89-42827b5b6876/0d58c6aa-5d31-414c-865a-1761b6b5172b/Untitled.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466VZSGL6B4%2F20250327%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20250327T043242Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjENX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJHMEUCIQDPe92OXtIF7F9vN3cTeBJuhRJGMaPCLLR0eRxrOGjzTAIgaBpmWTUjQ8EP2eLzFCTUvlTjA%2FrPAq%2B1PwAzOf3lNU0q%2FwMIPRAAGgw2Mzc0MjMxODM4MDUiDHIAv%2BPx7GmQ1rQUeCrcA8B2lnF96a8Bi1mKBoXTUQ%2F8nChf85df4Jz3ECQ5AP6jrfcuIm%2FWebvP%2BIJDYyh2ocG13U5UXMnOLtVixrumje%2FjNDUS1u6zdcNcClPLIB8%2B1K%2BqvpAKJ5DMY%2FpvgM42ylzEH%2B7tN30pEepTbDjrmICLHm8%2BrL7sPjrWBBSXR7cTipiieH95arMKw2CLcHF6f93zl6LxNX68pEDOjr8z122m%2Fjl1mxE4Ycm1zKWbYi8psGuhQQpTcvNmBMO26onWxtX%2FN5qNATU8RuLNuL0SK4j%2BQPzKcUjLwhRA3KjokVat9rUygNXMr5luXXeOiJhMmq8zWASDbukaFVimQ9wUf%2Bc2hG2OMoBCK5Q%2FWHwi3t3YDavVl3x9a5heIDM6%2BMXUymauqjD4mhiUG9mjgyzDBJ6CyWA1JFbFiFte9FaOlOAS8Nk0bwyVjSE70IKQjTmhwJgh5S5KoLpkdWm5%2BiqZWV079fpxJQKibpnu4kLYiaD1c83t%2FnOtFNZobEObJAMerEUNn7qhLCf8mRXz0E9F6lZcfItMED6R39YSak2fSIn6nFARzSir50LKe%2BCpjRz7Oy9uuuu9wbPzL%2FLtNwYL%2B55CUyMi9mv5K0twpWzPv%2FF4ftDJkS0%2BoyfbIs05MPikk78GOqUBZsDszpXdIQQ4DajIddOtdpK2wVzffVyRJjgGrEfxky99UE9bVF34L2G%2FdI5%2Fyhgq2191Fc58nyoRu8SLhRxjZdD%2BD5bv00hua0sZhNYcgilYmvea6upBXWDPEq91hJXt%2BcJy9fwpx7B%2F7TaVK4cqfo1aSYkB%2B59awcT0O5HuN7aB4Cmrs0VmjF0jZt0h4Np43WKD%2Fof7dusBkzL1RdNxWrpqaoK2&X-Amz-Signature=098afb9ac4aafcd20e6a4f934550c1facfdb8cafa3eaab49a77674288d1bdee5&X-Amz-SignedHeaders=host&x-id=GetObject)

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


![](https://prod-files-secure.s3.us-west-2.amazonaws.com/94f51666-273a-443d-bf89-42827b5b6876/c4bbd7ff-719c-4a7d-b246-e4c765b69d30/Untitled.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466QV4ARVUS%2F20250327%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20250327T043241Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjENX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJHMEUCIDwyy%2FSEeBl39WououXaywZ6RFFoGUbpm1K3b5vc%2BzeuAiEAlNh8j%2BQ7mH8lX9aOpUPxnBmYtyjM9BqLS64xV4cwTYgq%2FwMIPRAAGgw2Mzc0MjMxODM4MDUiDKve5DFHtbMe4nN0JCrcA7ua5LdzO5h%2BL948eUUIgHV1yQdHK%2Biy1Z9UKSUYGdt8HPN4v1xSEcjH0fs8FuvCh5OXMwQ8%2FNbgaUsjo05yscmB8qVqrXAcJ71cg3aXt%2FvYigT5zmXSAwiMvedqgp%2BVyeYOVa7fTyd3yfrzU9et3TCyeDY4xPDgb%2BgiXF5cjCxylLfhbKJuwhdi7y4PbZkP%2FhCHaVgoDY7cs1m4OsBAmmGkRdf57%2FHIFkYVa5Q%2Bf4xnqiQffnWz4s%2FTVDY6Unt7HAo5NkMo8zQac%2BKMpL3wqCRh4Nylu6AdwVWFoj4csVq%2F%2FXVy%2FIUYQK6JwIdEi2T1LV9hSJebMJeVxyzWwasfYaHWRBcY4W1CmUby6xMZCE7NzV67VxQp%2BDavfI4dqTuiduPvQRYi7pwweTvloGewcPMaqoRbiPjGbUirua9cEHVhJrtJkwL8AhlLFO6S4Lus7WNP9LjSWttP9pYY%2BnIu3d5ClKE0og3TzCE2es0p2yS%2BXK%2BkrmVa6H6RIBG0p%2BU7mo%2Bm34qxjLwLiugSNbBIhhoPXLuAh7CFdk9Vglx51vCPAz0Bs56emztGcoFZC8fES1oonKXJFPxnaHHzv36VrD1aYa59SZUSNGjH8X18%2BjXYTP%2FZPaFULDwGx2r%2BMJGlk78GOqUB1ACzZhYtsjs8Z%2B%2BnCyN9xHXFhmEeTLP71KM5lYy5mlgruCPjLEV3cDlils9uNqFXhaok0z1yzJU1Okos5hwtpFdipy8TvHlmLrvFKILceaL7Qd4Mp%2FXfUd5DBRYw%2Fs4mo%2FTDINqdryyhbpgLIB52sTdGn3mgXj3rgBk4bPPmMYQqhuIQWH28vqjc1ZVg1RHDz2etTpZjoBuhU401ADi5DoAQzlrH&X-Amz-Signature=fd5da74ac486ef4d35301f5edd12e17fb7a6333fb1dfd524820b5006dfde4e3c&X-Amz-SignedHeaders=host&x-id=GetObject)


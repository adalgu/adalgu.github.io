---
# Documentation: https://sourcethemes.com/academic/docs/managing-content/

title: "[파이썬] 파이썬 코드를 블로그에 쉽고, 예쁘게 공유하기" #[카테고리] 제목은 간결하게
subtitle: "Colab으로 만들고, Gist로 저장하고, Hugo 숏코드로 부르기" #부제는 결과를 간략하게
summary: "파이썬 코드를 쉽게 만들고, 쉽게 저장하고, 쉽게 공유하고, 쉽게 보여주는 방법은 무엇일까? Colab+Gist" #섬머리는 포스트 리스트에 표시되며, 구글 검색에서도 표시됨.
authors: []
tags: [colab, gist, hugo, python] #태그는 이왕이면 소문자 영어로
categories: [python] #카테고리는 필수적으로 소문자 영어로
date: 2020-12-24T17:21:56+09:00
lastmod: 2020-12-24T17:21:56+09:00
featured: false
draft: false

# Featured image
# To use, add an image named `featured.jpg/png` to your page's folder.
# Focal points: Smart, Center, TopLeft, Top, TopRight, Left, Right, BottomLeft, Bottom, BottomRight.
image:
  caption: ""
  focal_point: ""
  preview_only: false

# Projects (optional).
#   Associate this post with one or more of your projects.
#   Simply enter your project's folder or file name without extension.
#   E.g. `projects = ["internal-project"]` references `content/project/deep-learning/index.md`.
#   Otherwise, set `projects = []`.
projects: []
---

### 언제? 왜? 필요한가?
- 데이터 분석을 하고 만든 코드를 휴고 블로그로 포스팅할 때,
- 파이썬 코드를 쉬우면서도, 예쁘게 공유하고 싶을 때,

{{< adfit >}}

### 어떻게?
1. Colab(코랩)으로 파이썬 코드를 만든다.
2. 만든 코드를 Gist에 저장한다.
3. Hugo shortcode를 이용하여 코드를 보여준다.
   - 휴고 숏코드는 숏코드를 넣는 기호 사이 : ```{{ < > }}```  
   - 기스트 속성을 넣는다 : ```gist USERNAME gist-ID ```
   - 예시 형태(괄호 공백 제거) :  ```{ { < gist myname ad8807jlasdlslasdjl22 > } }```
   - 자세한 설명은 [휴고 공식홈](https://gohugo.io/content-management/shortcodes/#gist) 참고.

### 일단 보자!
{{< gist adalgu 6819a0e82b09b1a7c0743190a01346b6 >}}

### 무엇이 장점인가?
1. 온라인으로 코드를 바로 작성할 수 있고(Colab),
2. Colab에서 Gist도 원클릭으로 저장이 가능하고(Gist),
3. 휴고 블로그에 숏코드로 쉽게 불러올 수 있으며(Hugo),
4. 온라인으로 코드를 바로 실행해 볼 수 있다. (```Open in Colab```로 바로 이동)
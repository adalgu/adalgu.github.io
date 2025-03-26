---
author: Gunn Kim
date: '2023-01-09'
draft: true
keywords: &id001
- Notion
lastmod: '2025-03-21T02:44:00.000Z'
notion_id: cb6c2e80-2e67-4704-b6a0-24002d0f7b31
slug: notion-api-easy-blog
tags: *id001
title: '[Notion] 노션 API를 이용한 블로그'
---


노션을 CMS(컨텐츠 매니지먼트 시스템)으로 사용하는 방법을 연구했었는데, 이를 강연으로 만들어 파는 것을 보았다.


딱, 내가 구현하고자 했던 것과 동일하다. 작년에 참고 했었던 글들은 대개 **Notion as a blog CMS였었다.**


원래는 아래와 같이 Notion을 이용한 Hugo 블로그였는데,

일단 작년에 일부 되는 것까지만 확인하고 중단했었다.


이유는 별도의 서버(node.js로 추측)를 이용해야 하는데, 상용이 아니다보니 중간중간 멈추는 문제.

그리고, 자바 스크립트를 이용해서 글을 fetch해오는 것이 생각보다 쉽지 않았다.(자바 스크립트 문법을 좀 더 공부해야 하는 문제)


그래서 일단 최근에 node.js를 공부해서 서버 구축은 마쳤는데,

그러는 사이 이런 강연을 보게 되었다.

# **📚사용할 기술 스택**

주로 사용할 기술 스택은 다음과 같아요.

- [React](https://ko.reactjs.org/)
- [Next.js](https://nextjs.org/)
- [Typescript](https://www.typescriptlang.org/)
- [Tailwind css](https://tailwindcss.com/)
- [Notion API](https://www.notion.so/ko-kr)
`html/css` 는 기본이겠죠?


사용할 기술 스택을 보니, 딱 프론트엔드 공부하기에 제격이었다.


그러다 강연자의 깃허브를 보니 해당 강연자료들을 친철하게 잘 올려놨다.


내가 하려고 했던 것이 헛된 프로젝트가 아니었음을 알게 되었고,

이 프로젝트를 스스로 완성하게 되면 배우게 되는 기술 스택들이 꽤 매력적으로 구성될 수 있음도 알게 되었다.


더해서, 그동안 netlfy를 간단한 정적 페이지 띄우기에 이용했었는데,

Vercel도 있다는 것을 알게 됨.

- The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme)
 from the creators of Next.js.

상세 커리큘럼

# **📰상세 커리큘럼**

### **1회차 – 프로젝트 셋업하기**

1. 개발 환경 설정하기(VSCode, Extensions)
1. 깃허브 레포 만들기
1. 노션 시작하기 및 api 등록하기
1. 프로젝트에 필요한 패키지들 설치하기
1. Vercel에 배포하기
과제) 취업에 도움되는 깃허브 꾸미기

### **2회차 – Tailwind CSS와 친해지기**

1. Next.js와 TailwindCSS 기초 설명
1. 반응형 디자인 구현하는 법
1. 블로그 헤더 만들기
1. 헤더 메뉴 만들기
1. 푸터 만들기
과제) 블로그 헤드 프로퍼티 추가하기

### **3회차 – Notion API로 게시글 리스트 가져오기**

1. 노션에 글 작성하기
1. Notion API를 이용해 데이터 가져오기
1. 블로그 메인 페이지 만들기
과제) 인터랙티브 애니메이션 추가하기

### **4회차 – Notion에 적은 문서 내용 보여주기**

1. 블로그 게시글 상세 페이지 만들기
1. 상세 페이지 세부 디자인하기
1. 노션 API의 한계와 고쳐 쓰기
1. 마법의 가루, ISR
과제) 이미지가 로딩 중임을 알려주기

### **5회차 – Notion API에 쿼리를 추가해 기타 페이지들 만들기**

1. 태그별 페이지 만들기
1. 페이지네이션 추가하기
1. 검색 페이지 만들기
1. 서버사이드에서 프리뷰 이미지 추가하기
과제) 중복된 서버 요청 캐싱하기

### **6회차 – 내 블로그 세상에 공개하기**

1. 내 프로필 페이지 만들기
1. 도메인 구매 및 vercel과 연결하기
1. 구글과 네이버 검색 엔진에 등록하기
1. 구글 애널리틱스 붙이기
과제) 게시글마다 댓글 시스템 붙이기



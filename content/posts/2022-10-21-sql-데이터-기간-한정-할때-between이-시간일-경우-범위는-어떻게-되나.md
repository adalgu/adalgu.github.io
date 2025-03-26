---
author: Gunn Kim
date: '2022-10-21T01:53:00.000+00:00'
draft: true
keywords: &id001
- python
lastmod: '2025-03-21T02:44:00.000Z'
notion_id: e68c9c53-a046-4914-80d6-fdb45198f74c
tags: *id001
title: '[SQL] 데이터 기간 한정 할때 between이 시간일 경우 범위는 어떻게 되나?'
---


10시에서 12시 사이에 발생한 데이터를 뽑는다고 할때,


SELECT *

FROM MYDB

WHERE hour between 10 and 12


하면 된다.


그런데, 이렇게 뽑은 데이터에는 12시 10분 데이터가 포함될 것인가?

12시 정각이 넘은 데이터는 빠지는가?


정답은? 포함된다.

다시 말해서, 12시 10분 데이터를 뽑기 위해서 WHERE hour between 10 and 13으로 하면 안된다.

그냥 WHERE hour between 10 and 12로 하면 됩니다.

마찬가지로 WHERE month between 10 and 12라고 하면, 10월 1일 데이터부터 12월 31일 데이터까지 뽑게된다.


가끔씩 헷갈려서 적어둠.

이상.


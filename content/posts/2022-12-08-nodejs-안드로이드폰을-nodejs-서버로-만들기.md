---
author: Gunn Kim
date: '2022-12-08'
draft: true
keywords: &id001
- Node.js
lastmod: '2025-03-21T02:44:00.000Z'
notion_id: a08d8d61-be32-4e07-9dab-548db6407849
tags: *id001
title: '[node.js] 안드로이드폰을 node.js 서버로 만들기'
---

1. 안드로이드폰에 termux를 설치한다.
1. 먼저, `apt-get update` 실행
1. 이어서, Node.js 설치
```javascript
업데이트 진행
$ apt update && apt upgrade

coreutils 설치
$ apt install coreutils

vim 설치
$ apt install vim

nodejs 설치
$ apt install nodejs

프로젝트 폴더 만들기(예: /myserver/)
mkdir myserver
cd myserver

package.json 파일 생성
$ npm init
```


1. Express 모듈 설치
Express 모듈 설치
$ npm install express --save

여기서 골치아픈 폴더 권한 문제 발생


결국, termux용 node.js(nodejs-lts) 재설치 필요([참고](https://github.com/npm/cli/issues/5114))

$ pkg uninstall nodejs


$ pkg install nodejs-lts


새로운 nodejs가 설치되었으면, express 다시 설치

깔끔하게 설치 완료


1. 코드를 적을 index.js 파일 생성
$ touch index.js
$ vim index.js

```javascript
var express = require('express');
var app = express();
 
app.get('/', function(req, res) {
   res.send('Hello World! YoYo!');
});
 
app.listen(3000, function() {
   console.log('Example app listening on port 3000!');
});
```


1. 서버 실행
`node index.js`

'Example app listening on port 3000!’

1. 서버 접속
브라우저에서 “localhost:3000” 또는 안드로이드폰 “IP주소:3000” 입력

“Hello World! YoYo!”라고 뜨면 완성.


1. 외부 IP로 접속해 보자
- 크게 1) 공유기 포트포워딩 방법(ddns 사용)과 2) Ngrok 사용 방법
- 둘다 할만한데, 공유기 건들기가 귀찮으면,
- 2) Ngrok으로 가능

Termux용 Ngrok 설치 필요


```plain text
pkg update -y
pkg install git
git clone https://github.com/Yisus7u7/termux-ngrok

cd termux-ngrok
bash install.sh
```


1. Ngrok 백그라운드로 실행
이유 : Termux는 맥 터미널처럼 여러개 탭으로 실행이 불가능

- 즉, Ngrok를 실행시켜 놓고, Node.js를 실행해야 함.

방법 : `ngrok http 3000 > /dev/null &`

- 이렇게 입력하면, 백그라운드에서 ngrok 실행(termux 종료시 ngrok 연결 종료)

추가 : authtoken 물려서 실행하기

- ngrok에 무료 회원 가입하면 authtoken 발급됨. 이것을 ngrok 실행시 연결하면 8시간 이상 가동
- `ngrok http 3000 —authtoken [대괄호지우고받아온인증토큰입력] > /dev/null &` 
이렇게 하면 백그라운드에서 ngrok 실행됨.


1. Node.js 실행
Termux에서 바로 `node index.js` 실행


1. 브라우저로 접속
ngrok에서 생성한 주소로 접속하면 외부에서도 접속 가능한 것 확인


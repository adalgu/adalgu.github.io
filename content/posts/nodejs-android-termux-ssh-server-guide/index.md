---
author: Gunn Kim
cover:
  alt: '[node.js] 원격으로 안드로이드폰 서버(termux) 접속하기(SSH) 대표 이미지'
  hiddenInList: false
  hiddenInSingle: false
  image: https://app.notion.com/images/page-cover/met_william_morris_1877_willow.jpg
date: '2023-01-09'
description: Termux 앱을 통해 안드로이드 디바이스를 Node.js 서버로 만들고, SSH를 이용해 원격에서 접속하는 방법을 단계별로
  설명합니다. 저비용 서버 솔루션으로 활용할 수 있는 실용적인 가이드입니다.
draft: false
keywords: &id001
- Node.js
- Android
- SSH
- Termux
lastmod: '2025-06-22T04:00:00.000Z'
notion_id: 315062f5-aee1-4982-9baa-9b559310cddc
slug: "nodejs-android-termux-ssh-server-guide"
subtitle: Termux와 SSH를 활용해 안드로이드 폰을 원격 서버로 활용하기
summary: Termux 앱을 통해 안드로이드 디바이스를 Node.js 서버로 만들고, SSH를 이용해 원격에서 접속하는 방법을 단계별로 설명합니다.
  저비용 서버 솔루션으로 활용할 수 있는 실용적인 가이드입니다.
tags: *id001
title: '[node.js] 원격으로 안드로이드폰 서버(termux) 접속하기(SSH)'
---

앞에서 안드로이드폰을 node.js 서버로 만들기를 성공했다면, 이제는 개발이 편하게 SSH를 이용한 원격접속을 시도해 보자.


# **원격 접속(SSH)**

목적 : 서버(스마트폰)은 화면도 작고, 타자도 어려우니, 원격 PC에서 스마트폰을 접속하여 개발하는 목적


순서

1. 서버용 스마트폰에서 "Termux"를 실행

2. **openssh**를 설치

| `$ apt install openssh`   |
|---------------------------|

3. ssh용 공용 ID 키를 생성(yes치고 엔터 탁탁탁)

| `$ ssh-keygen`   |
|------------------|

4. openssh를 실행 (백그라운드에서 실행됨)

| `$ sshd`   |
|------------|

5. 계정 비밀번호를 설정합니다.(원격 접속시 사용할 암호 입력)

| `$ passwd`   |
|--------------|

6. 공유기에서 새로운 서버용 스마트폰의 포트포워드 규칙을 적용시킵니다. 

- 포트포워드에서 외부포트와 내부포트 모두 8022로 하고 규칙 새로 만듦.

1. 원격 터미널(내 PC)에서 스마트폰으로 접속
`$ ssh -p 8022 [원격 접속 주소]`



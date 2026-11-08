---
author: Gunn Kim
date: '2025-08-09'
description: 의존성 역전 원칙을 변수 하드코딩과 함수 하드코딩의 비교를 통해 쉽게 설명합니다. 개발자라면 누구나 알고 있는 하드코딩 문제와
  연결해서 DIP를 이해해보세요.
draft: false
lastmod: '2025-09-02T20:24:00.000Z'
notion_id: 24a7522e-eb2f-804f-a1dc-e39c5c8a8e91
slug: "dependency-inversion-principle-hardcoding-explained"
subtitle: 하드코딩을 피하는 패턴으로 의존성 역전을 쉽게 이해하기
summary: 의존성 역전 원칙을 변수 하드코딩과 함수 하드코딩의 비교를 통해 쉽게 설명합니다. 개발자라면 누구나 알고 있는 하드코딩 문제와 연결해서
  DIP를 이해해보세요.
title: '의존성 역전 원칙 이해하기: 변수 하드코딩에서 함수 하드코딩까지'
---

# 의존성 역전 원칙 이해하기: 변수 하드코딩에서 함수 하드코딩까지

“의존성 역전”이라는 용어를 처음 들었을 때 많은 개발자들이 혼란스러워합니다. 하지만 사실 우리가 이미 잘 알고 있는 개념과 정확히 같은 패턴입니다. 바로 **하드코딩을 피하는 것**입니다.

## 변수 하드코딩 vs 설정파일: 우리가 이미 아는 패턴

### 나쁜 예시: 변수 하드코딩

```javascript
function 파일읽기() {
  return readFile("/Users/myname/project/data.txt");  // 하드코딩!
}

function 데이터베이스연결() {
  return connect("mysql://localhost:3306/mydb");      // 하드코딩!
}

```

이렇게 하면 무엇이 문제일까요?

- 개발/운영 환경이 다르면? 코드를 수정해야 합니다
- 다른 사용자가 다른 경로를 사용하면? 코드를 수정해야 합니다
- MySQL에서 PostgreSQL로 바뀌면? 코드를 수정해야 합니다
### 좋은 예시: 설정파일 사용

```javascript
// config.json
{
  "filePath": "/Users/myname/project/data.txt",
  "databaseUrl": "mysql://localhost:3306/mydb"
}

// 유연한 코드
function 파일읽기(경로) {
  return readFile(경로);  // 유연함!
}

function 데이터베이스연결(url) {
  return connect(url);    // 유연함!
}

// 사용할 때
const config = readConfig();
파일읽기(config.filePath);
데이터베이스연결(config.databaseUrl);

```

이제 코드를 수정하지 않고도 설정파일만 바꾸면 됩니다!

## 함수 하드코딩: 같은 문제, 다른 영역

그런데 우리는 변수는 하드코딩하지 않으면서, 함수는 하드코딩하고 있었습니다.

### 나쁜 예시: 함수 하드코딩

```javascript
function 주문처리(주문정보) {
  // 함수가 하드코딩됨!
  이메일발송(주문정보.email);
  MySQL저장(주문정보);
}

```

이렇게 하면 무엇이 문제일까요?

- 이메일 대신 SMS로 바꾸고 싶으면? 코드를 수정해야 합니다
- MySQL 대신 MongoDB로 바꾸고 싶으면? 코드를 수정해야 합니다
- VIP 고객은 이메일, 일반 고객은 SMS를 보내고 싶으면? 코드를 수정해야 합니다
### 좋은 예시: 함수를 변수처럼 전달

```javascript
function 주문처리(주문정보, 알림함수, 저장함수) {
  알림함수(주문정보.contact);  // 유연함!
  저장함수(주문정보);          // 유연함!
}

// 다양한 구현체들
function 이메일발송(연락처) {
  console.log(`${연락처}로 이메일 발송`);
}

function SMS발송(연락처) {
  console.log(`${연락처}로 SMS 발송`);
}

function MySQL저장(데이터) {
  console.log(`MySQL에 저장: ${데이터.id}`);
}

function MongoDB저장(데이터) {
  console.log(`MongoDB에 저장: ${데이터.id}`);
}

// 사용할 때 - 마치 설정파일처럼!
주문처리(주문, 이메일발송, MySQL저장);    // 조합1
주문처리(주문, SMS발송, MongoDB저장);     // 조합2

```

## 의존성 역전 = 함수 하드코딩을 피하는 것

결국 의존성 역전이란 **함수를 변수처럼 취급하는 것**입니다.

### 전통적인 의존성

```plain text
고수준 함수 → 구체적인 저수준 함수 (하드코딩)

```

### 의존성 역전

```plain text
고수준 함수 → 함수 인터페이스 ← 구체적인 구현 함수

```

마치 이렇게 바뀌는 것과 같습니다:

### 변수 영역에서

```plain text
함수 → 하드코딩된 값     =>     함수 → 변수 → 설정파일의 값

```

### 함수 영역에서

```plain text
함수 → 하드코딩된 함수    =>     함수 → 함수변수 → 실제 구현 함수

```

## 껍데기와 내용의 분리

이 패턴의 핵심은 **“껍데기”와 “내용”을 분리**하는 것입니다.

```javascript
// 껍데기 (계약/인터페이스) - 어떤 모양인지만 정의
const 알림인터페이스 = {
  send: (메시지) => { /* 어떻게든 알림을 보낸다 */ }
}

// 내용 (구현체) - 실제로 어떻게 할지 정의
const 이메일알림 = {
  send: (메시지) => console.log(`이메일: ${메시지}`)
}

const SMS알림 = {
  send: (메시지) => console.log(`SMS: ${메시지}`)
}

// 주문처리는 껍데기만 알면 됨
function 주문처리(알림기) {
  알림기.send("주문완료!");  // 내용은 몰라도 됨
}

```

## 파이프라인 사고와의 연결

파이프라인에서 각 파이프의 **연결부 규격은 고정**하되, **파이프 내부 구현은 교체 가능**하게 만드는 것과 정확히 같습니다.

```plain text
[주문입력] → [주문처리] → [알림파이프] → [저장파이프]
                          ↑             ↑
                      이메일/SMS    MySQL/MongoDB
                      교체 가능      교체 가능

```

## Factory 패턴: 설정 기반 조립

마지막으로, 설정파일과 Factory 패턴을 결합하면 완전히 유연한 시스템을 만들 수 있습니다.

```javascript
// config.json
{
  "notification": "email",
  "database": "mysql"
}

// Factory - 설정에 따라 함수 조합
function 주문처리Factory(config) {
  const 알림함수 = config.notification === 'email' ? 이메일발송 : SMS발송;
  const 저장함수 = config.database === 'mysql' ? MySQL저장 : MongoDB저장;

  return (주문) => 주문처리(주문, 알림함수, 저장함수);
}

// 사용
const config = readConfig();
const 주문처리기 = 주문처리Factory(config);
주문처리기(주문정보);

```

## 마무리

의존성 역전은 새로운 개념이 아닙니다. 우리가 이미 변수 영역에서 하고 있던 **“하드코딩을 피하는 좋은 습관”**을 함수 영역으로 확장한 것뿐입니다.

- **변수 하드코딩 → 설정파일**: 데이터의 유연성
- **함수 하드코딩 → 의존성 주입**: 동작의 유연성
이렇게 이해하면 의존성 역전이 왜 필요하고, 어떻게 적용해야 하는지 훨씬 명확해집니다. 결국 더 유연하고 재사용 가능한 코드를 만들기 위한, 우리가 이미 알고 있는 패턴의 확장인 셈이죠.


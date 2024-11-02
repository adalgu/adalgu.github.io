---
date: '2024-06-03'
description: LangChain의 새로운 라이브러리 LangGraph를 소개합니다. LangGraph를 사용하여 멀티 에이전트 콜라보레이션을
  구현하고 S&P 500 지수 데이터를 검색하고 시각화하는 방법을 알아보세요.
draft: false
featured: true
lastmod: '2024-06-03T06:54:00.000Z'
tags:
- LangChain
- LangGraph
- LLM
- 멀티에이전트
title: 'LangGraph 사용법: 멀티 에이전트로 S&P 500 데이터 시각화하기'
---

# LangChain이 만든 멀티 에이전트 라이브러리 LangGraph를 알아보자

안녕하세요! 오늘은 최근에 출시된 LangChain의 새로운 라이브러리인 LangGraph에 대해 알아보겠습니다. 이 글에서는 LangGraph의 멀티 에이전트 콜라보레이션 기능을 살펴보고, 실제 예제를 통해 어떻게 동작하는지 알아보겠습니다. 이 글을 통해 LangGraph의 기본 개념부터 활용법까지 쉽게 따라할 수 있도록 설명드리겠습니다.

## LangGraph란 무엇인가?

LangGraph는 LangChain에서 만든 새로운 라이브러리로, 여러 에이전트가 협업하여 작업을 수행하는 기능을 제공합니다. 기존의 멀티 에이전트 시스템과 달리 LangGraph는 에이전트 간의 명확한 흐름도와 상태 관리를 지원하여 보다 체계적이고 효율적인 작업을 수행할 수 있게 해줍니다.

### LangGraph의 주요 기능



### LangGraph의 혁신적인 점

LangGraph는 기존의 멀티 에이전트 시스템보다 한층 더 발전된 기능을 제공합니다. 특히, 에이전트 간의 협업을 강화하고 작업의 효율성을 극대화하는 방식이 매우 혁신적입니다.

### LangGraph로 할 수 있는 일

LangGraph를 사용하면 여러 개의 '에이전트'가 서로 협력하여 다양한 작업을 자동으로 수행할 수 있습니다. 쉽게 이해할 수 있도록 몇 가지 예를 들어보겠습니다.

## LangGraph 사용 예제

이제 LangGraph를 사용하여 실제로 멀티 에이전트 콜라보레이션을 구현하는 예제를 보겠습니다. 예제에서는 S&P 500 지수 데이터를 검색하고, 이를 차트로 그리는 작업을 수행합니다.

### 1. 환경 설정 및 에이전트 생성

먼저 LangGraph를 사용하기 위해 필요한 환경을 설정하고 에이전트를 생성합니다.

### 2. 도구 정의

검색과 차트 생성을 위한 도구를 정의합니다.

### 3. 에이전트 상태 관리 및 노드 생성

에이전트의 상태를 관리하고, 작업을 수행할 노드를 생성합니다.

### 4. 멀티 에이전트 콜라보레이션 구현

리서치 에이전트와 차트 생성 에이전트를 정의하고, 각 에이전트가 협업하여 작업을 수행하는 흐름을 구현합니다.

### 5. 그래프 정의 및 실행

에이전트 간의 흐름을 정의하고, 그래프를 실행하여 작업을 수행합니다.

### 6. 결과 확인 및 시각화

수집된 데이터를 바탕으로 차트를 생성하고 결과를 확인합니다.

이렇게 해서 LangGraph를 사용하여 멀티 에이전트 콜라보레이션을 구현하고, 데이터를 검색하고 시각화하는 과정을 살펴보았습니다. LangGraph는 다양한 작업을 효율적으로 처리할 수 있는 강력한 도구이므로, 여러분들도 한번 사용해 보시길 추천드립니다.

## 결론

오늘은 LangChain에서 새로 출시한 LangGraph에 대해 알아보았습니다. LangGraph의 멀티 에이전트 콜라보레이션 기능을 통해 여러 작업을 체계적으로 처리할 수 있음을 확인했습니다. 앞으로도 LangGraph를 활용한 다양한 예제를 통해 더 많은 기능을 살펴보시길 바랍니다. 감사합니다.
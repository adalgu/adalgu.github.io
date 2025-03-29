---
author: Gunn Kim
date: '2024-02-22'
description: 이 글은 Streamlit 프레임워크를 활용해 파이썬으로 개발된 AI 기능이 탑재된 애플리케이션의 로그 데이터를 관리하고 분석하기
  위한 데이터베이스 통합의 중요성에 초점을 맞추고 있다. MongoDB와 PostgreSQL 사이의 선택 고민을 탐구하며, 강화학습에 적합한 구조화된
  데이터 축적을 위해 PostgreSQL을 선택한 과정을 소개한다. ElephantSQL을 통해 AWS 상에서 서비스로 제공되는 PostgreSQL의
  클라우드 기능을 강조하며, psycopg2 라이브러리를 사용해 PostgreSQL 데이터베이스에 연결하고 기본 데이터베이스 작업을 수행하는 방법을
  코드 스니펫과 함께 설명한다.
draft: true
keywords: &id001
- Tech
- ChatGPT
- python
- Web Dev
lastmod: '2025-03-21T02:44:00.000Z'
notion_id: b5e7ed83-08b0-47d0-ba23-977351c669ee
slug: Postgres-vs-MongoDB-Python-GenAI-App
subtitle: 'AI 기반 애플리케이션에서 데이터베이스 통합하기: PostgreSQL과 파이썬 사례 연구'
summary: 이 글은 Streamlit 프레임워크를 활용해 파이썬으로 개발된 AI 기능이 탑재된 애플리케이션의 로그 데이터를 관리하고 분석하기
  위한 데이터베이스 통합의 중요성에 초점을 맞추고 있다. MongoDB와 PostgreSQL 사이의 선택 고민을 탐구하며, 강화학습에 적합한 구조화된
  데이터 축적을 위해 PostgreSQL을 선택한 과정을 소개한다. ElephantSQL을 통해 AWS 상에서 서비스로 제공되는 PostgreSQL의
  클라우드 기능을 강조하며, psycopg2 라이브러리를 사용해 PostgreSQL 데이터베이스에 연결하고 기본 데이터베이스 작업을 수행하는 방법을
  코드 스니펫과 함께 설명한다.
tags: *id001
title: '**[ElephantSQL] PostgreSQL과 Python을 연동하는 방법: 기초부터 코드 예제까지**'
---

**PostgreSQL과 Python을 연동하는 방법: 기초부터 실습까지**

생성 AI 기술이 탑재된 현대 애플리케이션은 로그 데이터의 효율적인 관리와 분석을 위해 데이터베이스(DB) 연동의 중요성이 점점 증가하고 있다. 특히, 파이썬 언어로 개발된 애플리케이션에서는 사용자 인터페이스를 구축하기 위해 Streamlit 프레임워크를 주로 활용하는 추세다. 생성AI 프로젝트를 진행하면서 로그를 저장하기 위한 DB 선택을 고민하고, 실제 간략한 예시를 작성해 보았다.


# 1. 들어가며

### 데이터베이스 선택의 고민

애플리케이션 개발 초기 단계에서 가장 중요한 결정 중 하나는 적합한 데이터베이스를 선정하는 것이다. 이번 프로젝트에서는 MongoDB와 PostgreSQL이 후보군으로 올랐다. MongoDB는 NoSQL 데이터베이스의 대표주자로, 과거 프로젝트 경험 덕분에 개발자들에게 친숙하다. 클라우드 기반 서비스의 무료 이용 가능성은 MongoDB를 매력적인 옵션으로 만든다. 반면, PostgreSQL은 전통적인 SQL 데이터베이스의 강력한 기능을 제공하며, 최근에는 생성 AI 기술과의 통합 사례가 늘어나고 있는 추세다.


![](https://prod-files-secure.s3.us-west-2.amazonaws.com/94f51666-273a-443d-bf89-42827b5b6876/274558e5-f703-4399-8bca-f810e510ec31/Untitled.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466WQBG4IDS%2F20250329%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20250329T083046Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEAgaCXVzLXdlc3QtMiJHMEUCIQDQiooFaOvtOof119IplP4nK5%2FxP895q4fLf028dKq%2FAQIgGUI4g2mzuKqWSw1deaO8tVxeornYRv27QZBfxuOfZlMq%2FwMIcRAAGgw2Mzc0MjMxODM4MDUiDJ2QK%2FakDwhrAD1xMircA0ji5GmBafAefnLAmU7%2BLbN%2B%2FE3kLlMfyonGgz0r7ZN4ZgHcwR6lGoH8ythqLoUDOdf9bj7qRLtrnadLvjM5E%2FWZLx0DNgg6xZ%2BnAgCywuoOtLy3KZEQYm9n5QcuLwKQ7s9eSW9pClGBAqdCZ0SqUaMgp9vNmTmNU5jdFRnZXb3UkssQKZYzRfpzvLndrtKqIAOSt%2FfhuHFYV25nBySAxhpR%2BXpceSwhzm05hFMuy4FZKSguszYquySBU4eWNOSsFYEBnrwIBVzaZ%2F286ommUschpc7OrEgAd6PbUxq875gJ%2FIUkPJgEJ0DniiCtvuX382cmsnTJzS0njzAf14X%2Bx%2B9UNT843z5ZIOatUrfjm63lY4PNrWgFxkSL3B7WUpEP4TgBwkvOrVfqQGSbodJ4Ow5PwxJrQaqtkmzPw1XHiAAxKmYuEiP9nXZsDmVAgelqn9KDampbVGfDXkZr1h4XFI%2BzXh61sKWohcvUQqJkJ7OHg7Nh%2FO5yupp8XLQp%2FnjD8xPqEbhILq7Rq7yMkuSwndGniwZJGdsC4xECB16km9y4yEVBlqRHNWV67v4FU9Hd3wjpYTJm1MjZiQ0TDplaKrrHKEPNXKGDlf2mBF8S%2BsX9GhLrocbuMscHsbxwMNPFnr8GOqUB57MVP7dNjkBlULFPSBD1bM%2FOV9gXXafBuV0i3J%2B39SvQX3v2PcwUM8ZaVMv0cEZTuxhogme5QbPHlL74qcjBHvaIRhQ87K13eu2R3Ba4PWWJlnZiroKsBDH7LR1OETDLk6c41z7tF4wZX9OmTIw3yUaGPhfKQR7Ee5sw2UPD7L6E2z8UXPEek8mTN%2F1nIL%2B9LKJfLVGJjUD7BvdZLd0xLn9zcoC5&X-Amz-Signature=f90f35de02129ed4ca0c016f2be1d3ee8708ed0591387a4906503eb7747f1e5d&X-Amz-SignedHeaders=host&x-id=GetObject)

비록 MongoDB를 사용하여 로그 데이터를 관리하고, 필요에 따라 SQL 데이터베이스로 이전하는 방안도 고려 가능했지만, 프로젝트의 현재 요구 사항과 앱이 생성할 로그 데이터의 양을 고려했을 때, 어느 쪽을 선택해도 큰 문제가 없어 보였다. 그러나 최종적으로는 강화학습에 활용될 로그 데이터의 구조화와 축적의 중요성을 고려하여 PostgreSQL을 선택하기로 결정했다.

PostgreSQL은 강력하고 안정적인 오픈소스 관계형 데이터베이스 관리 시스템(RDBMS)입니다. 높은 확장성, 유연성, 보안성을 갖추고 있으며, 다양한 규모의 기업에서 사용되고 있습니다. 특히, 다음과 같은 특징은 데이터 기반 경제 시대에 기업들에게 큰 이점을 제공합니다.

- **낮은 총 소유 비용(TCO):** PostgreSQL은 오픈소스 소프트웨어이기 때문에 라이선스 비용이 발생하지 않습니다. 또한, 다양한 플랫폼에서 운영 가능하며, 관리 및 유지 보수가 용이하여 TCO를 크게 절감할 수 있습니다.
- **뛰어난 성능:** PostgreSQL은 멀티 코어 프로세서 및 고속 저장 장치를 활용하여 최상의 성능을 제공합니다. 또한, 다양한 데이터 유형을 지원하고, 복잡한 쿼리를 효율적으로 처리하여 데이터 분석 작업을 지원합니다.
- **높은 확장성:** PostgreSQL은 수 페타바이트의 데이터까지 확장 가능하며, 수백만 명의 동시 사용자를 지원합니다. 기업의 데이터가 증가하더라도 쉽게 확장하여 대응할 수 있습니다.
- **강력한 보안:** PostgreSQL은 다양한 보안 기능을 제공하여 데이터를 안전하게 보호합니다. 암호화, 접근 제어, 감사 추적 등의 기능을 통해 데이터 유출 및 침해를 방지할 수 있습니다.
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/94f51666-273a-443d-bf89-42827b5b6876/0714b38d-01fa-4c94-9c56-ca80167fa498/Untitled.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4664O2P4AJT%2F20250329%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20250329T083046Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEAgaCXVzLXdlc3QtMiJHMEUCIFXNNd0aI38N31LZQj%2FLqO9YmUq7tj9bIEWOY4aW%2B3X0AiEAxPYJaUINN3TZgJfPJdqq2XismVdArw3enWrr05EdhX0q%2FwMIcRAAGgw2Mzc0MjMxODM4MDUiDMphEcEQEQJmlBDAYSrcAwW5xfrVyrxeKKpZbvq1jxQ4DJzz7wo4W18swc6XeFyT0XY6wiPFNCc%2FjrnxcsjNpD2s1NIaGDxMDUWItkFbdXU4Y4j%2FeqzKPh85Af3BpLH9v0pBII0CvlxTNa0UWieOqy76Lh%2BhmtdgyaoM%2FpD5rY3vTzlrdTtPukmPwCoqi1WgkmqqwxtkcE7r0xu9kzXZS6GXn6zErKcXi2F8OjkiZvSO0gZm%2FE33oVqlsvx%2FyB0joVLYST09nEJ%2BDOF9PqsNtWSnG7L8H8fh2bAadMGbKbcHYmXbmki34xxNSKwl6vDdMHe%2BsXorEn5y3iuPoJfViZ08o4zvScNDQ0Kt%2BTL7DVBNXcNfsdbnDcQZGFbnhzUHmMIFoAPf9RK8HRkMQOFRWKp%2FhZm6oXIhGxOoLw2FcLL2VJ04jwLTshSmetkpQAd%2BB%2FvaGgKEE8WmDJY4%2FMFdn4fieSXUwmHLfeT1SNBKqqgPSciWXPT8x4UnND1DMxNJJyXkq2rQpwMVYATlpkYpDtSSnMRFDsIfcbefO8knjj8UgxfsC3lpD1xA0qG3gY1mvQfKgz6t9jM0VJ6docaDiSFPptMbnWclIdIsJ0oc1kA3sodd3piPLU1xVOZA%2FwjZD5UjEocwbv1tRNAwML3Fnr8GOqUBEJfWFrPQtUJuHE7wRJt8B445c0BGEG4qPYdKPBzzOVzXfmMfURNLQPvC%2FqDTvXTUXMNyE0vrKq%2B%2FzC%2F%2FZh%2BHfm4mnjYiJfPCK7VPR%2BthXBnq%2FqkmyowmWf9Y158frwJoAoRimLsWEJ0WviwgmjadFuegHoSWZ48cy71BCLfK%2BVJwqG5AzqNRwARA5RoauW%2BH9MhlZKiYcuAtxt%2BivILPHQXbxXX%2F&X-Amz-Signature=2322d3891fe5264cf41d9f4e8e5a995dae3b6f43e45a8a700ef28fe888444199&X-Amz-SignedHeaders=host&x-id=GetObject)


### 클라우드에서의 PostgreSQL 활용

PostgreSQL은 일반적으로 로컬 환경에서 설치하여 사용되지만, 최근에는 클라우드 서비스 형태로도 제공되는 추세다. 이러한 변화는 개발자들에게 더 큰 유연성과 편의성을 제공한다. 이번 프로젝트에서는 'ElephantSQL'이라는 서비스를 통해 PostgreSQL을 클라우드 환경에서 활용하기로 결정했다. ElephantSQL은 'PostgreSQL as a Service'라는 컨셉 아래, 몇 가지 간단한 설정만으로 데이터베이스를 쉽게 구축하고 사용할 수 있게 해준다. AWS 기반으로 운영되는 이 서비스는 개발자들에게 최대 20MB의 데이터 저장 공간을 무료로 제공한다.

![](https://prod-files-secure.s3.us-west-2.amazonaws.com/94f51666-273a-443d-bf89-42827b5b6876/cbf1c15e-91a6-4778-965c-386750619ba1/Untitled.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466WQBG4IDS%2F20250329%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20250329T083046Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEAgaCXVzLXdlc3QtMiJHMEUCIQDQiooFaOvtOof119IplP4nK5%2FxP895q4fLf028dKq%2FAQIgGUI4g2mzuKqWSw1deaO8tVxeornYRv27QZBfxuOfZlMq%2FwMIcRAAGgw2Mzc0MjMxODM4MDUiDJ2QK%2FakDwhrAD1xMircA0ji5GmBafAefnLAmU7%2BLbN%2B%2FE3kLlMfyonGgz0r7ZN4ZgHcwR6lGoH8ythqLoUDOdf9bj7qRLtrnadLvjM5E%2FWZLx0DNgg6xZ%2BnAgCywuoOtLy3KZEQYm9n5QcuLwKQ7s9eSW9pClGBAqdCZ0SqUaMgp9vNmTmNU5jdFRnZXb3UkssQKZYzRfpzvLndrtKqIAOSt%2FfhuHFYV25nBySAxhpR%2BXpceSwhzm05hFMuy4FZKSguszYquySBU4eWNOSsFYEBnrwIBVzaZ%2F286ommUschpc7OrEgAd6PbUxq875gJ%2FIUkPJgEJ0DniiCtvuX382cmsnTJzS0njzAf14X%2Bx%2B9UNT843z5ZIOatUrfjm63lY4PNrWgFxkSL3B7WUpEP4TgBwkvOrVfqQGSbodJ4Ow5PwxJrQaqtkmzPw1XHiAAxKmYuEiP9nXZsDmVAgelqn9KDampbVGfDXkZr1h4XFI%2BzXh61sKWohcvUQqJkJ7OHg7Nh%2FO5yupp8XLQp%2FnjD8xPqEbhILq7Rq7yMkuSwndGniwZJGdsC4xECB16km9y4yEVBlqRHNWV67v4FU9Hd3wjpYTJm1MjZiQ0TDplaKrrHKEPNXKGDlf2mBF8S%2BsX9GhLrocbuMscHsbxwMNPFnr8GOqUB57MVP7dNjkBlULFPSBD1bM%2FOV9gXXafBuV0i3J%2B39SvQX3v2PcwUM8ZaVMv0cEZTuxhogme5QbPHlL74qcjBHvaIRhQ87K13eu2R3Ba4PWWJlnZiroKsBDH7LR1OETDLk6c41z7tF4wZX9OmTIw3yUaGPhfKQR7Ee5sw2UPD7L6E2z8UXPEek8mTN%2F1nIL%2B9LKJfLVGJjUD7BvdZLd0xLn9zcoC5&X-Amz-Signature=c9612793d003117e9a9a923426f94bf4b1e0b803329031b389f9b52367979a40&X-Amz-SignedHeaders=host&x-id=GetObject)


# **2. 파이썬에서 PostgreSQL 사용 코드 설명**

psycopg2 라이브러리를 사용하면 Python 코드에서 PostgreSQL 데이터베이스에 쉽게 연결하고 작업할 수 있다.


**1. 라이브러리 불러오기**

```python
import psycopg2
```

PostgreSQL과 Python을 연결하는 `psycopg2` 라이브러리를 불러온다.


**2. 연결 문자열 설정**

```python
# 데이터베이스 연결 정보 설정
server='floppy.db.elephantsql.com'
dbname='User & Default database'
user='User & Default database'
password='Password'

conn_string = f"dbname={dbname} user={user} host={host} password={password}"
```

데이터베이스 이름, 사용자 이름, 호스트, 비밀번호를 변수에 저장하고, `f-string`을 사용하여 연결 문자열을 생성한다. 해당 정보들은 ElephantSQL에서 Instance를 생성한 이후에 확인할 수 있다.

![ElephantSQL에서 확인할 수 있는 DB세팅 정보](https://prod-files-secure.s3.us-west-2.amazonaws.com/94f51666-273a-443d-bf89-42827b5b6876/4c1c7fdd-c1db-48e0-8f05-e77688bac196/Untitled.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466WQBG4IDS%2F20250329%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20250329T083046Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEAgaCXVzLXdlc3QtMiJHMEUCIQDQiooFaOvtOof119IplP4nK5%2FxP895q4fLf028dKq%2FAQIgGUI4g2mzuKqWSw1deaO8tVxeornYRv27QZBfxuOfZlMq%2FwMIcRAAGgw2Mzc0MjMxODM4MDUiDJ2QK%2FakDwhrAD1xMircA0ji5GmBafAefnLAmU7%2BLbN%2B%2FE3kLlMfyonGgz0r7ZN4ZgHcwR6lGoH8ythqLoUDOdf9bj7qRLtrnadLvjM5E%2FWZLx0DNgg6xZ%2BnAgCywuoOtLy3KZEQYm9n5QcuLwKQ7s9eSW9pClGBAqdCZ0SqUaMgp9vNmTmNU5jdFRnZXb3UkssQKZYzRfpzvLndrtKqIAOSt%2FfhuHFYV25nBySAxhpR%2BXpceSwhzm05hFMuy4FZKSguszYquySBU4eWNOSsFYEBnrwIBVzaZ%2F286ommUschpc7OrEgAd6PbUxq875gJ%2FIUkPJgEJ0DniiCtvuX382cmsnTJzS0njzAf14X%2Bx%2B9UNT843z5ZIOatUrfjm63lY4PNrWgFxkSL3B7WUpEP4TgBwkvOrVfqQGSbodJ4Ow5PwxJrQaqtkmzPw1XHiAAxKmYuEiP9nXZsDmVAgelqn9KDampbVGfDXkZr1h4XFI%2BzXh61sKWohcvUQqJkJ7OHg7Nh%2FO5yupp8XLQp%2FnjD8xPqEbhILq7Rq7yMkuSwndGniwZJGdsC4xECB16km9y4yEVBlqRHNWV67v4FU9Hd3wjpYTJm1MjZiQ0TDplaKrrHKEPNXKGDlf2mBF8S%2BsX9GhLrocbuMscHsbxwMNPFnr8GOqUB57MVP7dNjkBlULFPSBD1bM%2FOV9gXXafBuV0i3J%2B39SvQX3v2PcwUM8ZaVMv0cEZTuxhogme5QbPHlL74qcjBHvaIRhQ87K13eu2R3Ba4PWWJlnZiroKsBDH7LR1OETDLk6c41z7tF4wZX9OmTIw3yUaGPhfKQR7Ee5sw2UPD7L6E2z8UXPEek8mTN%2F1nIL%2B9LKJfLVGJjUD7BvdZLd0xLn9zcoC5&X-Amz-Signature=e66ebd8710252173f082b70d8f0e03476afe98a9cef6ce93e6cbc3c961ef02ca&X-Amz-SignedHeaders=host&x-id=GetObject)


**3. 데이터베이스 연결**

```python
conn = psycopg2.connect(conn_string)
```

연결 문자열을 사용하여 PostgreSQL 데이터베이스에 연결한다.


**4. 커서 생성**

```plain text
cursor = conn.cursor()
```

데이터베이스 쿼리를 실행하고 결과를 처리하는 커서를 생성한다.


**5. 테이블 생성**

```plain text
create_table_query = '''
CREATE TABLE IF NOT EXISTS mytable (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    email VARCHAR(50)
)
'''

cursor.execute(create_table_query)
```

`mytable`이라는 이름의 테스트용 테이블을 생성하는 SQL 쿼리를 실행한다. 테이블은 `id`, `name`, `email` 컬럼으로 구성된다.


**6. 데이터 삽입**

```python
cursor.execute("INSERT INTO mytable (name, email) VALUES (%s, %s)", ("Alice", "alice@example.com"))
cursor.execute("INSERT INTO mytable (name, email) VALUES (%s, %s)", ("Bob", "bob@example.com"))
cursor.execute("INSERT INTO mytable (name, email) VALUES (%s, %s)", ("Charlie", "charlie@example.com"))
```

`INSERT` 쿼리를 사용하여 테이블에 데이터를 삽입한다. `%s` 플레이스홀더는 삽입될 값을 나타낸다.


**7. 변경사항 커밋**

```plain text
conn.commit()
```

데이터베이스에 변경사항을 저장한다.


**8. 데이터 조회**

```plain text
cursor.execute("SELECT id, name, email FROM mytable")
rows = cursor.fetchall()

for row in rows:
    print(f"ID: {row[0]}, Name: {row[1]}, Email: {row[2]}")
```

`SELECT` 쿼리를 사용하여 테이블에서 데이터를 조회한다. `fetchall()` 메서드를 사용하여 결과를 모두 가져온다.


**9. 커서 및 연결 종료**

```plain text
cursor.close()
conn.close()
```

사용 후에는 커서와 데이터베이스 연결을 종료하여 리소스를 해제한다.


# 3. 전체 코드 예시

이제 전체 코드를 통해 파이썬에서 PostgreSQL을 사용하는 과정을 확인할 수 있다. ElephantSQL에서 제공하는 데이터베이스 정보를 활용하여 연결 문자열을 구성하고, psycopg2 라이브러리를 통해 데이터베이스에 연결한다. 이후 테이블 생성, 데이터 삽입, 데이터 조회 및 처리, 그리고 마지막으로 커서 및 연결 종료까지의 전 과정을 아래 코드에서 볼 수 있다.

```javascript
import psycopg2

# 데이터베이스 연결 정보 설정
server='floppy.db.elephantsql.com' #elephatSQL에서 생성한 DB 정보 활용
dbname='User & Default database'   #elephatSQL에서 생성한 DB 정보 활용
user='User & Default database'     #elephatSQL에서 생성한 DB 정보 활용
password='Password'                #elephatSQL에서 생성한 DB 정보 활용

# 연결 문자열 생성: 데이터베이스 서버의 위치, 사용자 이름, 비밀번호 등을 포함
conn_string = f"dbname={dbname} user={user} host={server} password={password}"

# psycopg2를 사용하여 데이터베이스에 연결
conn = psycopg2.connect(conn_string)

# 데이터베이스 작업을 위한 커서 생성
cursor = conn.cursor()

# 'mytable'이라는 이름의 새 테이블을 생성하는 SQL 쿼리.
# 테이블에는 id(기본 키), 이름, 이메일 필드가 포함됩니다.
create_table_query = '''
CREATE TABLE IF NOT EXISTS mytable (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    email VARCHAR(50)
)
'''

# 생성한 SQL 쿼리를 실행하여 테이블 생성
cursor.execute(create_table_query)

# 'mytable' 테이블에 새로운 데이터를 삽입하는 SQL 쿼리 실행
# 여기서는 Alice, Bob, Charlie라는 세 명의 사용자를 추가합니다.
cursor.execute("INSERT INTO mytable (name, email) VALUES (%s, %s)", ("Alice", "alice@example.com"))
cursor.execute("INSERT INTO mytable (name, email) VALUES (%s, %s)", ("Bob", "bob@example.com"))
cursor.execute("INSERT INTO mytable (name, email) VALUES (%s, %s)", ("Charlie", "charlie@example.com"))

# 데이터베이스에 대한 변경사항(여기서는 데이터 삽입)을 커밋하여 확정
conn.commit()

# 'mytable' 테이블에서 모든 데이터를 선택하는 SQL 쿼리 실행
cursor.execute("SELECT id, name, email FROM mytable")

# 실행한 쿼리의 결과를 모두 가져오기
rows = cursor.fetchall()

# 가져온 결과를 반복하여 출력
# 각 행의 ID, 이름, 이메일을 출력합니다.
for row in rows:
    print(f"ID: {row[0]}, Name: {row[1]}, Email: {row[2]}")

# 사용한 커서와 데이터베이스 연결 종료
cursor.close()
conn.close()
```



[끝]



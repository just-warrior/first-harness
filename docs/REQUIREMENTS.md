# 프로젝트: Jira 관리자용 계산기 (Jira Admin Calculator)

## 1. 개요 (Objective)
Jira 관리자(Manage Apps) 화면 좌측 메뉴에 위치하여, 관리 작업 중 즉시 사용 가능한 표준 사칙연산 계산기를 제공한다.
Jira DC Version 은 10.3.4 이다.

## 2. 기능 요구사항 (Functional Requirements)
- **표준 연산:** 0-9 숫자 및 사칙연산(+, -, *, /), 초기화(C), 결과(=) 버튼 제공.
- **UI 형태:** 별도의 페이지 이동 없이 사이드바 메뉴 클릭 시 관리 화면 본문에 계산기 인터페이스 출력.
- **연산 이력:** 현재 세션 동안 수행한 계산 결과 리스트 표시 (최대 5개).

## 3. 기술 사양 (Technical Specifications) - **핵심 제약 조건**

### 3.1 진입점 및 라우팅 (Routing)
- **위치:** `admin_plugins_menu` 섹션 내 `web-item` (Jira 관리 -> 앱 관리 좌측 사이드바)
- **뷰 렌더링:** `CalculatorAction.java` (Webwork1 Action)의 `doDefault()` 메서드가 뷰(`calculator.vm`)를 반환한다.

### 3.2 프론트엔드 UI/UX (Frontend UI)
- **레이아웃 기술:** CSS Grid를 사용하여 윈도우 기본 계산기와 동일한 격자 구조(Grid Layout)로 버튼을 배치한다. 버튼이 일렬로 늘어서지 않도록 CSS 클래스로 강제한다.
- **디자인 시스템:** AUI(Atlassian User Interface)의 버튼 스타일(`aui-button`)과 폼(`text`) 스타일을 적용하되, 레이아웃 배치는 CSS Grid를 우선한다.
- **이력 저장:** 브라우저 내의 JavaScript 배열(메모리)을 사용하여 최대 5개의 최근 연산 기록(예: "5 + 3 = 8")을 저장하고 화면 패널에 표시한다.

### 3.3 백엔드 연산 로직 (Backend REST API)
- **연산 주체:** 클라이언트(JS)에서 직접 계산하지 않고, 버튼 클릭 시 입력값을 추출하여 **Java REST API (JAX-RS)** 로 전송(AJAX 호출)한다.
- **REST API 명세:**
  - Endpoint: `/rest/calculator/1.0/calculate`
  - Method: `POST` (또는 GET)
  - Request/Response: JSON 포맷 통신.
- **안정성:** 백엔드 Java 코드에서 0으로 나누기(Divide by Zero) 예외 처리 및 숫자 포맷 검증 로직을 반드시 포함한다.

## 4. 해결해야 할 버그 및 개선 과제 (Bug Fix & Improvements)
- **기존 증상:** 메뉴 접속 시 UI가 일렬로 늘어져 사용이 불편하며, 계산 로직이 전혀 동작하지 않음.
- **개선 목표:** 위 3.2항의 CSS Grid를 적용하여 UI를 보편적인 계산기 모양으로 재구성하고, 3.3항의 REST API를 새로 생성하여 프론트엔드 연동을 통해 사칙연산이 완벽하게 동작하도록 수정한다.

## 5. 파일 매니페스트 (File Manifest) - **필수 준수**
> 아래 목록은 생성해야 할 파일의 **정확한 경로**입니다. 파일명, 패키지 구조, 디렉터리를 임의로 변경하지 마세요.

| # | 파일 경로 (workspace 기준) | 용도 |
|---|---|---|
| 1 | `jira-calculator-plugin/pom.xml` | Maven 빌드 설정 (Jira DC 10.3.4, AMPS, Spring Scanner 3.x) |
| 2 | `jira-calculator-plugin/src/main/resources/atlassian-plugin.xml` | 플러그인 모듈 선언 (web-item, web-resource, webwork1, rest) |
| 3 | `jira-calculator-plugin/src/main/resources/jira-calculator-plugin.properties` | i18n 메시지 프로퍼티 |
| 4 | `jira-calculator-plugin/src/main/java/com/example/jiracalculator/action/CalculatorAction.java` | WebWork1 뷰 라우터 (JiraWebActionSupport 상속) |
| 5 | `jira-calculator-plugin/src/main/java/com/example/jiracalculator/rest/CalculatorResource.java` | JAX-RS REST API (/rest/calculator/1.0/calculate) |
| 6 | `jira-calculator-plugin/src/main/resources/templates/calculator/calculator.vm` | Velocity 템플릿 (CSS Grid 계산기 UI) |
| 7 | `jira-calculator-plugin/src/main/resources/templates/calculator/error.vm` | 에러 페이지 Velocity 템플릿 |
| 8 | `jira-calculator-plugin/src/main/resources/css/jira-calculator-plugin.css` | CSS Grid 레이아웃 스타일 |
| 9 | `jira-calculator-plugin/src/main/resources/js/jira-calculator-plugin.js` | JS AJAX 연동 및 이력 관리 로직 |

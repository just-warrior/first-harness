# 프로젝트: Jira 관리자용 계산기 (Jira Admin Calculator)

## 1. 개요 (Objective)
Jira 관리자(Manage Apps) 화면 좌측 메뉴에 위치하여, 관리 작업 중 즉시 사용 가능한 표준 사칙연산 계산기를 제공한다.
Jira DC Version 은 10.3.4 이다.

## 2. 기능 요구사항 (Functional Requirements)
- **표준 연산:** 0-9 숫자 및 사칙연산(+, -, *, /), 초기화(C), 결과(=) 버튼 제공.
- **UI 형태:** 별도의 페이지 이동 없이 사이드바 메뉴 클릭 시 관리 화면 본문에 계산기 인터페이스 출력.
- **연산 이력:** 현재 세션 동안 수행한 계산 결과 리스트 표시 (최대 5개).

## 3. 기술 사양 (Technical Specs)
- **진입점 (Entry Point):** - Section: `admin_plugins_menu` (Jira 관리 -> 앱 관리 좌측 사이드바)
    - Module: `web-item` 및 `webwork1` Action 사용.
- **프론트엔드:** AUI(Atlassian User Interface) Forms 및 Buttons 활용.
- **백엔드:** `CalculatorAction.java`에서 기본적인 뷰 렌더링 처리.
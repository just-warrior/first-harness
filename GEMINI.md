# Jira Admin Calculator Plugin - Comprehensive Development & Self-Healing Guide

This project is an Atlassian Jira Data Center (v10.3.4) plugin providing a standard calculator in the "Manage Apps" administration section. It follows the P2 architecture and is managed by a micro-batching harness (`harness.py`).

## 🛠 Harness Execution Protocol (하네스 실행 프로토콜)

Claude는 자동화된 하네스 환경에서 동작하므로 다음 규칙을 엄격히 준수해야 합니다:
1. **상태 파일 처리:** `ERROR_REPORT.md`, `FIX_HISTORY.md`, `TASKS.md` 등 하네스가 관리하는 상태 파일은 **읽기 전용**입니다. 분석 용도로만 사용하고 직접 수정하지 마십시오.
2. **범위 준수:** 하네스가 할당한 마이크로 배치 범위 내에서만 작업을 수행하고, 불필요한 파일 수정이나 과도한 확장을 지양하십시오.
3. **완료 보고:** 모든 작업(수정 및 빌드 확인)이 완료되면 터미널에 변경 사항을 요약 보고하고, 반드시 `CHAPTER COMPLETE` 메시지를 출력하여 세션을 종료하십시오.

## 🚑 Self-Healing Workflow (자가 치유 워크플로우)

빌드 실패, 런타임 에러 또는 테스트 실패 시 다음 5단계를 강제로 수행하여 문제를 해결하십시오:

1.  **Analyze (분석):** `ERROR_REPORT.md` 또는 터미널의 Stack Trace를 끝까지 읽어 에러의 근본 원인(Root Cause)을 파악하십시오.
2.  **Review History (이력 조회):** `FIX_HISTORY.md`를 읽어 과거에 시도했던 수정 사항과 실패 원인을 확인하여 동일한 실수를 반복하지 마십시오.
3.  **Hypothesize (가설 수립):** 수집된 정보를 바탕으로 에러 원인을 특정하십시오 (예: OSGi Import 누락, WebWork 라우팅 미설정 등).
4.  **Fix (수정):** 최소한의 코드를 수정하여 문제를 해결하십시오. 수정 시 `pom.xml`의 버전을 항상 `0.0.1`씩 증가시켜 빌드 구분을 명확히 하십시오.
5.  **Verify (검증):** `atlas-mvn clean package`를 실행하여 컴파일 및 패키징 성공 여부를 확인하십시오.

## 🔍 Error Analysis Patterns (주요 에러 분석 가이드)

### 1. OSGi & Dependency Issues
*   **Missing Requirement (Unresolved Package):** `pom.xml`의 `<Import-Package>` 섹션에 해당 패키지가 누락되었거나 버전이 맞지 않는 경우입니다.
    *   **주의:** `version="*"` 표기는 OSGi 컨테이너에서 파싱 에러를 유발하므로 절대 사용하지 마십시오.
    *   **Jira 10.3.4 제약:** `jakarta.*` 패키지는 export되지 않으므로 반드시 `javax.*` (예: `javax.ws.rs`)를 사용해야 합니다.
*   **ClassNotFoundException:** 런타임에 클래스를 찾지 못하는 경우, `pom.xml`에 의존성이 `provided` 스코프로 적절히 설정되었는지 확인하십시오.

### 2. WebWork1 (Action) Issues
*   **INPUT/SUCCESS Constant Errors:** `JiraWebActionSupport` 상속 시 `webwork.action` 패키지를 `Import-Package`에 명시해야 상수를 인식할 수 있습니다.
*   **Routing (404/Empty Page):** `atlassian-plugin.xml`의 `web-item` 링크는 반드시 `!default.jspa` suffix를 사용하여 `doDefault()` 메서드를 호출해야 합니다.

### 3. UI & Styling (CSS Grid)
*   **Layout Broken:** 계산기 버튼에 `aui-button` 클래스를 사용하면 AUI 기본 스타일이 CSS Grid 설정을 덮어씁니다.
    *   **해결:** 버튼에는 커스텀 클래스(예: `calc-btn`)만 사용하고, CSS에서 `!important`를 사용하여 레이아웃 속성을 강제하십시오.

## 🏗 Project Core Context

### Technologies
*   **Backend:** Java 11, WebWork1, JAX-RS (REST API), Spring Scanner 3.0.0.
*   **Frontend:** Velocity (.vm), CSS Grid, Atlassian User Interface (AUI), jQuery.
*   **Build:** Atlassian SDK (AMPS 9.1.1).

### Key Commands (Executed in `workspace/jira-calculator-plugin`)
*   **Build & Package:** `atlas-mvn clean package`
*   **Run Instance:** `atlas-run`
*   **Unit Tests:** `atlas-mvn test`

### Essential Files
*   `pom.xml`: Dependency & OSGi configuration.
*   `src/main/resources/atlassian-plugin.xml`: Plugin descriptors (Action, REST, Resources).
*   `src/main/java/com/example/jiracalculator/rest/CalculatorResource.java`: Arithmetic logic.
*   `src/main/resources/css/jira-calculator-plugin.css`: Grid layout styles.
*   `src/main/resources/js/jira-calculator-plugin.js`: AJAX & UI logic.

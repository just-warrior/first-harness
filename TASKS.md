# Tasks

## Chapter 1: 프로젝트 초기화

| # | Task | Status |
|---|------|--------|
| 1 | `atlas-create-jira-plugin`으로 프로젝트 스캐폴딩 생성 (workspace/jira-calculator-plugin) | ✅ Done |
| 1 | `atlas-mvn compile` BUILD SUCCESS 확인 | ✅ Done |

## Chapter 2: Webwork Action & Admin UI

| # | Task | Status |
|---|------|--------|
| 1 | CalculatorAction.java 작성 (JiraWebActionSupport 상속) | ✅ Done |
| 2 | pom.xml 의존성 설정 (Java 17, junit 4.13.2, mockito-core 4.11.0) | ✅ Done |
| 3 | atlassian-plugin.xml 모듈 선언 (web-section, web-item, webwork1) | ✅ Done |
| 4 | Velocity 템플릿 작성 (calculator.vm, error.vm) | ✅ Done |
| 5 | i18n 프로퍼티 등록 | ✅ Done |

## Chapter 5: CalculatorAction.java 구현

| # | Task | Status |
|---|------|--------|
| 5 | CalculatorAction.java 구현 (expression, result, history 필드 / expression 기반 / doExecute() 빈 expression → SUCCESS) | ✅ Done |
| 5 | pom.xml 버전: 1.0.0-SNAPSHOT → 1.0.1-SNAPSHOT | ✅ Done |
| 5 | `atlas-mvn compile` BUILD SUCCESS 확인 | ✅ Done |

## Chapter 6: CSS

| # | Task | Status |
|---|------|--------|
| 6 | calculator.css 스타일 작성 (AUI 호환, Live Preview 패널, 폼 필드) | ✅ Done |

## Chapter 7: Resource Descriptor

| # | Task | Status |
|---|------|--------|
| 7 | 리소스 디스크립터 등록 (web-resource: aui-core 의존성 추가, 이미지 개별 등록) | ✅ Done |

## Chapter 8: AUI 스타일 적용 및 레이아웃 정돈

| # | Task | Status |
|---|------|--------|
| 8 | calculator.vm: calc-layout 2컬럼 flex 레이아웃 (calc-main + calc-history 나란히) | ✅ Done |
| 8 | CSS: !important 제거, .calc-grid .aui-button.calc-btn-* 고명세도 셀렉터 적용 | ✅ Done |
| 8 | CSS: .calc-history 패널 스타일 (background, border, padding) | ✅ Done |
| 8 | MyComponentWiredTest.java 삭제 (제거된 osgi-testrunner 의존성 잔재 — FIX-01) | ✅ Done |
| 8 | pom.xml 버전: 1.0.2-SNAPSHOT → 1.0.3-SNAPSHOT | ✅ Done |
| 8 | `atlas-mvn clean package -DskipTests` BUILD SUCCESS | ✅ Done |

## Chapter 9: 빌드 및 검증

| # | Task | Status |
|---|------|--------|
| 9 | `atlas-mvn clean package` 실행 → target/jira-calculator-plugin-1.0.3-SNAPSHOT.jar 생성 | ✅ Done |
| 9 | Tests run: 1, Failures: 0, Errors: 0, Skipped: 0 | ✅ Done |
| 9 | BUILD SUCCESS 확인 (CLAUDE.md Test Protocol 준수) | ✅ Done |

## Chapter 10: 문서화 및 세션 컨텍스트 업데이트

| # | Task | Status |
|---|------|--------|
| 10 | README.md 작성 (아키텍처, 빌드, 테스트, 표준 체크리스트) | ✅ Done |
| 10 | TASKS.md Chapter 10 항목 추가 | ✅ Done |
| 10 | SESSION_CONTEXT.md Chapter 10 완료 반영 | ✅ Done |

## Chapter 3: WebWork Action 등록

| # | Task | Status |
|---|------|--------|
| 3 | atlassian-plugin.xml webwork1 Action 등록 (CalculatorAction alias, success/input/error 뷰 매핑) | ✅ Done |
| 3 | CalculatorAction.java 스켈레톤 생성 (JiraWebActionSupport 상속, doDefault/doExecute) | ✅ Done |

## Chapter 3-3: web-item 등록 (재실행, 2026-04-23)

| # | Task | Status |
|---|------|--------|
| 3 | atlassian-plugin.xml web-item 등록: section=admin_plugins_menu, weight=200, link=!default.jspa | ✅ Done |

## Chapter 4: webwork1 Action 등록 (2026-04-23)

| # | Task | Status |
|---|------|--------|
| 4 | atlassian-plugin.xml webwork1 Action 등록: key=calculator-webwork, alias=CalculatorAction, class=com.example.jiracalculator.action.CalculatorAction | ✅ Done |
| 4 | 뷰 매핑: success/input → calculator.vm, error → error.vm | ✅ Done |
| 4 | `atlas-mvn compile` BUILD SUCCESS 확인 | ✅ Done |

## Chapter 7: JavaScript 계산 로직 구현 (2026-04-23)

| # | Task | Status |
|---|------|--------|
| 7 | jira-calculator-plugin.js: 재귀하강 파서, 히스토리 FIFO(5), 연속계산, 에러처리 | ✅ Done |
| 7 | jira-calculator-plugin.css: CSS Grid 4컬럼, tall/wide 버튼 span, 색상 | ✅ Done |
| 7 | pom.xml 버전: 1.0.1-SNAPSHOT → 1.0.2-SNAPSHOT | ✅ Done |
| 7 | `atlas-mvn compile` BUILD SUCCESS (1 js, 1 css compressed) | ✅ Done |

## Notes
- `atlas-mvn compile` BUILD SUCCESS (2026-04-23, Jira 10.3.4 / Java 17)
- SKILLS.md 표준 준수: Skill 2 (jakarta.inject), Skill 3 (atlassian-plugin.xml 모듈), Skill 4 (atlas-mvn compile)
- PITFALL-01 준수: web-item link=/secure/CalculatorAction!default.jspa
- pom.xml 버전: 1.0.0-SNAPSHOT, jira.version: 10.3.4 (REQUIREMENTS.md 기준)

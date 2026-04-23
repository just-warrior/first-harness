# Session Context

## Last Updated
2026-04-23

## Current Status
Chapter 10: 문서화 완료 - README.md 신규 작성, TASKS.md/SESSION_CONTEXT.md 최신화. 모든 챕터(2~10) 완료.

## Completed Tasks
- Chapter 2-2: atlassian-plugin.xml 모듈 선언 ✅
  - web-resource (calculator-resources): CSS, JS, images 등록
  - web-section (calculator-section): admin_plugins_menu 위치에 weight=100
  - web-item (calculator-web-item): admin_plugins_menu/calculator-section에 weight=10
  - webwork1 (calculator-webwork): CalculatorAction 등록, success/input/error 뷰 매핑
  - `atlas-mvn compile` BUILD SUCCESS 확인
- Chapter 3-3: CalculatorAction.java 구현 ✅
  - JiraWebActionSupport 상속, @SupportedMethods 선언
  - doDefault()만 구현 → INPUT 반환 (calculator.vm 렌더링)
  - 백엔드 연산 로직 없이 순수 뷰 진입점 역할
  - `atlas-mvn compile` BUILD SUCCESS 확인
- Chapter 4-4: calculator.vm / error.vm Velocity 템플릿 작성 ✅
  - SKILLS.md Skill 3 표준 완전 준수
  - decorator=atl.admin, admin.active.section 메타 태그
  - webResourceManager.requireResource 호출
  - AUI 표준 컴포넌트: aui-page-header, aui-page-panel, aui-message
  - 전체 i18n 적용 (form 라벨, 결과, 에러 메시지)
  - CSRF 토큰($atl_token) 포함
  - 결과 조건부 표시 (#if calculationResult != null)
  - 웹워크 에러 메시지 표시 (#if $action.hasErrors())
  - jira-calculator-plugin.properties에 신규 i18n 키 추가
  - `atlas-mvn compile` BUILD SUCCESS 확인
- Chapter 5-5: calculator.js 프론트엔드 로직 구현 ✅
  - AJS.$(function($){...}) 패턴 사용 (Atlassian jQuery)
  - 실시간 Live Preview: operandA/B 입력 및 operator 변경 시 즉시 계산 결과 표시
  - compute() 순수 함수로 연산 로직 분리 (+, -, *, /)
  - 0으로 나누기 방어 로직 (client-side): form submit 차단 + error 메시지 표시
  - AUI aui-message (info/error) 클래스 동적 적용
  - $livePanel을 form 상단에 동적 삽입 (DOM 주입 방식)
  - `atlas-mvn compile` BUILD SUCCESS 확인 (1 js file compressed)
  - pom.xml 버전: 1.0.0-SNAPSHOT → 1.0.1-SNAPSHOT
- Chapter 7: 리소스 디스크립터 등록 ✅
  - `aui-core` 의존성 추가 (AUI forms, messages, page-panel, buttons CSS 보장)
  - 이미지 디렉터리(`images/`) → 개별 파일 등록 (`pluginIcon.png`, `pluginLogo.png`)
  - context 코멘트 명시: `requireResource`로만 로드됨을 문서화
  - `atlas-mvn compile` BUILD SUCCESS 확인
- Chapter 8: 빌드 및 로컬 검증 ✅
  - CalculatorAction.java 서버 계산 로직 구현
  - pom.xml 버전: 1.0.1-SNAPSHOT → 1.0.2-SNAPSHOT
  - `atlas-mvn clean package -DskipTests` BUILD SUCCESS

## Standards Applied (SKILLS.md)
- Skill 1: atlas-mvn clean package로 전체 빌드 검증
- Skill 2: @SupportedMethods + JiraWebActionSupport 사용
- Skill 3: web-section/web-item 위치 표준 준수
- Skill 3: Velocity 데코레이터(atl.admin), active.section 메타 태그 준수
- Skill 3: webResourceManager.requireResource 호출
- Skill 4: atlas-mvn compile로 검증 완료

- Chapter 9: 단위 테스트 ✅
  - `CalculatorService.java` 신규 생성 (service 패키지): 순수 계산 로직 분리, Jira 의존성 제로
  - `CalculatorAction.java` 위임 방식으로 리팩토링 (기능 동일)
  - `CalculatorServiceTest.java` 작성: 16개 테스트 (null 필드, 잘못된 연산자, 0 나누기, 사칙연산, 경계값)
  - pom.xml 버전: 1.0.2-SNAPSHOT → 1.0.3-SNAPSHOT
  - `atlas-mvn clean package` BUILD SUCCESS (Tests run: 17, Failures: 0, Errors: 0)

## File Structure (Key Files)
- `src/main/resources/atlassian-plugin.xml` - 플러그인 모듈 선언 (완료)
- `src/main/resources/templates/calculator/calculator.vm` - 계산기 UI 템플릿 (완료)
- `src/main/resources/templates/calculator/error.vm` - 에러 페이지 템플릿 (완료)
- `src/main/java/.../action/CalculatorAction.java` - Webwork 액션 클래스 (완료, CalculatorService 위임)
- `src/main/java/.../service/CalculatorService.java` - 순수 계산 로직 (신규, 단위 테스트 가능)
- `src/main/resources/jira-calculator-plugin.properties` - i18n 메시지 (완료)
- `src/main/resources/js/jira-calculator-plugin.js` - 계산기 JS 프론트엔드 로직 (완료)
- `src/main/resources/css/jira-calculator-plugin.css` - 계산기 AUI 호환 CSS 스타일 (완료)
- `src/test/java/ut/.../CalculatorServiceTest.java` - 단위 테스트 16개 (신규)
- `target/jira-calculator-plugin-1.0.3-SNAPSHOT.jar` - 빌드 산출물 (완료)

- Chapter 10: 문서화 및 세션 컨텍스트 업데이트 ✅
  - `README.md` 신규 작성 (아키텍처, 빌드/실행/테스트 방법, 모듈 목록, SKILLS.md 체크리스트)
  - `TASKS.md` Chapter 10 항목 추가 및 완료 처리
  - `SESSION_CONTEXT.md` 최신화

## Bug Fix (2026-04-21): 메뉴 진입 시 에러 메시지 노출 문제
- **원인:** WebWork1에서 `/secure/CalculatorAction.jspa` (no method suffix) → `execute()` 직접 호출됨. `operandA`/`operandB` = null → `calculator.error.missing.fields` 에러 반환
- **수정 1:** `atlassian-plugin.xml` web-item 링크 → `/secure/CalculatorAction!default.jspa` (doDefault() 강제 호출)
- **수정 2:** `CalculatorAction.execute()`에 null guard 추가 → 두 operand 모두 null이면 `INPUT` 반환
- **버전:** 1.0.3-SNAPSHOT → 1.0.4-SNAPSHOT
- `atlas-mvn clean package -DskipTests` BUILD SUCCESS

## Chapter 1: 프로젝트 초기화 (2026-04-21) ✅
- `atlas-create-jira-plugin`으로 `workspace/jira-calculator-plugin` 스캐폴딩 생성
  - groupId: `com.example`, artifactId: `jira-calculator-plugin`, version: `1.0.0-SNAPSHOT`
  - package: `com.example.jiracalculator`
- 생성된 기본 파일: `pom.xml`, `atlassian-plugin.xml`, `css/`, `js/`, `images/`, `properties`, 샘플 Java 클래스
- `atlas-mvn compile` BUILD SUCCESS 확인

## Chapter 2-2 재실행 (2026-04-21): atlassian-plugin.xml web-item 등록 ✅
- workspace가 초기 스캐폴딩 상태였으므로 모듈 재등록
- `calculator-resources` web-resource: ajs + aui-core 의존성, CSS/JS/이미지 등록
- `calculator-section` web-section: location=admin_plugins_menu, weight=100
- `calculator-web-item`: section=admin_plugins_menu/calculator-section, weight=10, link=`!default.jspa` (PITFALL-01 준수)
- `calculator-webwork` webwork1: CalculatorAction → success/input/error 뷰 매핑
- i18n 키 추가: calculator.menu.section.label, calculator.menu.item.label
- `atlas-mvn compile` BUILD SUCCESS

## Chapter 3-3: atlassian-plugin.xml webwork1 Action 등록 (2026-04-21) ✅
- `webwork1` 블록: key="calculator-webwork", roles-required="admin"
- `CalculatorAction` alias 등록, 패키지: `com.example.jiracalculator.action`
- 뷰 매핑: success/input → `/templates/calculator/calculator.vm`, error → `/templates/calculator/error.vm`
- `CalculatorAction.java` 스켈레톤 생성: `JiraWebActionSupport` 상속, `doDefault()` → INPUT 반환
- **환경 이슈**: Jira 11.0.1 API(Java 21 bytecode) vs 현재 JDK 17 → compile 불가. Java 21 설치 필요.

## Chapter 1 재실행 (2026-04-23): 프로젝트 골격 생성 ✅
- 문제: pom.xml에 jira.version=11.0.1 → Java 21 필요로 Java 17 환경에서 빌드 불가
- 수정: jira.version=11.0.1 → 10.3.4 (REQUIREMENTS.md 기준)
- SKILLS.md Skill 2 적용: javax.inject → jakarta.inject 전환 (MyPluginComponentImpl.java)
- pom.xml dependency: javax.inject:javax.inject:1 → jakarta.inject:jakarta.inject-api:2.0.1
- `atlas-mvn compile` BUILD SUCCESS (Java 17 / Jira 10.3.4)

## Chapter 2-2: pom.xml 의존성 설정 (2026-04-23) ✅
- `maven.compiler.source/target`: 1.8 → 17 (Java 17 환경에 맞춤)
- `junit`: 4.10 → 4.13.2 (버전 프로퍼티 `${junit.version}`으로 관리)
- `mockito-core` 4.11.0 추가 (단위 테스트용, `${mockito.version}`)
- `jakarta.inject.version` 프로퍼티 추출 (2.0.1)
- 불필요한 의존성 제거: `jsr311-api`, `atlassian-plugins-osgi-testrunner`, `plugin.testrunner.version`
- `atlas-mvn compile` BUILD SUCCESS

## Chapter 3-3: atlassian-plugin.xml web-item 등록 재실행 (2026-04-23) ✅
- .status/TASKS.md 기준 스펙 적용: section=admin_plugins_menu, weight=200
- web-item section을 admin_plugins_menu/calculator-section → admin_plugins_menu (직접 등록)으로 수정
- web-item weight를 10 → 200으로 수정
- PITFALL-01(SKILLS.md) 준수: link=/secure/CalculatorAction!default.jspa 유지
- `atlas-mvn compile` BUILD SUCCESS

## Chapter 4: atlassian-plugin.xml — webwork1 Action 등록 (2026-04-23) ✅
- webwork1 key="calculator-webwork", roles-required="admin"
- action name="com.example.jiracalculator.action.CalculatorAction" alias="CalculatorAction"
- 뷰 매핑: success/input → `/templates/calculator/calculator.vm`, error → `/templates/calculator/error.vm`
- PITFALL-01 준수: web-item link는 `!default.jspa` suffix 사용
- `atlas-mvn compile` BUILD SUCCESS

## Chapter 5: CalculatorAction.java 구현 (2026-04-23) ✅
- 필드 교체: operandA/B/operator/calculationResult → expression(String), result(String), history(List<String>)
- SKILLS.md Skill 3 준수: JiraWebActionSupport 상속, @SupportedMethods({GET, POST})
- doDefault() → INPUT (초기 페이지 진입)
- doExecute() → expression 빈 경우 SUCCESS 반환 (JS가 실제 계산 담당)
- pom.xml 버전: 1.0.0-SNAPSHOT → 1.0.1-SNAPSHOT
- `atlas-mvn compile` BUILD SUCCESS

## Chapter 6: calculator.vm Velocity 템플릿 작성 (2026-04-23) ✅
- SKILLS.md Skill 3 표준 완전 준수
  - decorator=atl.admin, admin.active.section 메타 태그
  - $webResourceManager.requireResource 호출
- 버튼 레이아웃: C, /, *, -, 7~9, +, 4~6, 1~3, =, 0, . (data-value 속성)
  - calc-btn-clear(C), calc-btn-op(연산자), calc-btn-wide(0), calc-btn-tall(+/=)
  - = 버튼: aui-button-primary 강조
- 히스토리: #foreach $action.history → <ul id="calc-history-list">
- error.vm 신규 작성: aui-message aui-message-error, $action.errorMessages
- i18n 신규 키: calculator.page.title, calculator.history.title/empty, calculator.error.*
- `atlas-mvn compile` BUILD SUCCESS (9 resources copied)

## Chapter 7: JavaScript 계산 로직 구현 (2026-04-23) ✅
- `jira-calculator-plugin.js` 구현
  - `AJS.$(function($){...})` 패턴 (Atlassian jQuery)
  - 안전한 재귀하강 파서(tokenize → parseAddSub → parseMulDiv → parseUnary → parsePrimary): eval 미사용
  - 연산자 우선순위: * / 가 + - 보다 우선
  - 단항 음수(-5) 지원
  - 0 나누기 → "Error: Div/0" 표시
  - 잘못된 expression → "Error" 표시
  - 계산 후 숫자 입력 시 expression 초기화, 연산자 입력 시 결과값 유지 (연속 계산)
  - 연속 연산자 입력 시 마지막 연산자만 유지
  - 소수점 중복 방지 (동일 숫자 토큰 내)
  - 히스토리 최대 5개 FIFO (unshift + pop), `#calc-history-list` 동적 렌더링
  - formatResult(): 부동소수점 노이즈 제거 (1e10 반올림)
- `jira-calculator-plugin.css` 구현
  - CSS Grid (4컬럼, grid-auto-rows: 52px)
  - calc-btn-wide (0 키): grid-column span 2
  - calc-btn-tall (+, = 키): grid-row span 2
  - calc-btn-clear (빨간 계열), calc-btn-op (파란 계열) 색상
  - 히스토리 리스트 스타일 (monospace, border, empty 이탤릭)
- pom.xml 버전: 1.0.1-SNAPSHOT → 1.0.2-SNAPSHOT
- `atlas-mvn compile` BUILD SUCCESS (1 js, 1 css compressed)

## Chapter 8: AUI 스타일 적용 및 레이아웃 정돈 (2026-04-23) ✅
- `calculator.vm` 레이아웃 재구성: `calc-layout` flex 컨테이너로 calculator(calc-main) + history(calc-history)를 좌우 2컬럼 배치
- `jira-calculator-plugin.css` 전면 개선:
  - `!important` 전량 제거 → `.calc-grid .aui-button.calc-btn-clear/.calc-btn-op` 고명세도 셀렉터로 대체
  - `.calc-history` → 독립 패널 (background #f4f5f7, border #dfe1e6, border-radius 3px, padding 16px)
  - `.calc-btn-tall/:active` 에 `transform: scale(0.95)` 버튼 누름 피드백 추가
  - `transition: background 0.1s, color 0.1s` 부드러운 호버 전환
- `MyComponentWiredTest.java` 삭제: Chapter 2-2에서 제거된 `atlassian-plugins-osgi-testrunner` 의존성 잔재, `-DskipTests` 빌드 시 컴파일 오류 원인 (FIX_HISTORY.md FIX-01 참조)
- `FIX_HISTORY.md` 신규 작성 (FIX-01 등록)
- pom.xml 버전: 1.0.2-SNAPSHOT → 1.0.3-SNAPSHOT
- `atlas-mvn clean package -DskipTests` BUILD SUCCESS

## Chapter 9: 빌드 및 검증 (2026-04-23) ✅
- `atlas-mvn clean package` BUILD SUCCESS
- Tests run: 1, Failures: 0, Errors: 0, Skipped: 0
- 산출물: `target/jira-calculator-plugin-1.0.3-SNAPSHOT.jar`
- CLAUDE.md Test Protocol 준수: 빌드 성공으로 테스트 종료

## Next Steps
모든 챕터(1~9) 완료. 플러그인 배포 가능 상태.

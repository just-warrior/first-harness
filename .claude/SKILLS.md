# 🛠 Atlassian SDK Expert Skill (Jira 10+)

이 문서는 Jira Data Center 10+ 개발을 위한 고도화된 스킬 세트입니다. Claude는 작업을 시작하기 전에 반드시 이 파일을 `cat`으로 읽고 모든 규칙을 내부 메모리에 로드해야 합니다.

## 🗂 Skill 1: Plugin Lifecycle Management
- **Command Set**: `atlas-create-jira-plugin`, `atlas-mvn clean package`, `atlas-run`, `atlas-debug`.
- **Standard**: 모든 빌드는 `atlas-mvn`을 사용하며, 환경 변수 충돌 방지를 위해 `workspace` 디렉터리 내에서 실행함.

## 🏗 Skill 2: Spring Scanner 3.x & Jakarta EE
- **Annotations**: `@Named` (Component), `@Inject` (Autowired), `@ComponentImport` (Jira API).
- **Package 규칙 (Jira 10 기준 — 실증 확인)**:
  - **JAX-RS REST API** (`@Path`, `@POST`, `@GET` 등): `javax.ws.rs.*` 사용 ✅
  - **DI 어노테이션**: REST 리소스에 `@Named` 사용 금지 ❌ — `jakarta.inject`도 OSGi 미충족. `<rest>` 모듈 디스크립터가 패키지 스캔으로 직접 등록하므로 불필요.
  - **결론**: 이 Jira 10.3.4 인스턴스는 `jakarta.*` 패키지를 전혀 export하지 않음 (`jakarta.ws.rs`, `jakarta.inject` 모두 확인)
- **Rules**: `plugin-context.xml` 내의 스캐닝 태그 사용 금지. 전적으로 Java Annotation 방식을 따름.

## 🎨 Skill 3: Web-UI & Integration (Standard)
- **Webwork Action (Java)**:
    - `JiraWebActionSupport` 상속 및 `@SupportedMethods({RequestMethod.GET, RequestMethod.POST})` 선언 필수.
- **Web Fragments (atlassian-plugin.xml)**:
    - **관리자 메뉴 위치**: `admin_plugins_menu`.
    - **커스텀 섹션**: `<web-section key="calculator-section" location="admin_plugins_menu" weight="100">`.
    - **메뉴 아이템**: `<web-item key="calculator-web-item" section="admin_plugins_menu/calculator-section" weight="10">`.
- **Velocity & Decoration (Jira 10 Standard)**:
    - **데코레이터 적용**: `<head>` 내부에 `<meta name="decorator" content="atl.admin"/>` 설정.
    - **활성 메뉴 표시**: `<meta name="admin.active.section" content="admin_plugins_menu/calculator-section"/>` (좌측 메뉴 강조 유지).
    - **리소스 로드**: `$webResourceManager.requireResource("${atlassian.plugin.key}:calculator-resources")`.

## 🔍 Skill 4: Validation & Self-Healing
- **Verification**: 코드 작성 후 반드시 `atlas-mvn compile`로 문법 및 의존성 검증.
- **Troubleshooting**: `ERROR_REPORT.md` 발생 시 `FIX_HISTORY.md`를 읽어 실패한 패턴을 배제하고 새 대안 제시.

## ⚠️ Known Pitfalls

### [PITFALL-01] WebWork1 URL 라우팅 — `!default` 누락

**증상:** 플러그인 메뉴를 클릭하자마자(GET 요청) 에러 메시지 또는 빈 결과가 표시된다.

**원인:**
Jira WebWork1은 URL suffix로 호출할 메서드를 결정한다.

| URL 형태 | 실제 호출 메서드 | 용도 |
|---|---|---|
| `/secure/XxxAction.jspa` | `execute()` | 폼 제출(POST) 결과 처리 |
| `/secure/XxxAction!default.jspa` | `doDefault()` | 초기 페이지 진입(GET) |
| `/secure/XxxAction!input.jspa` | `doInput()` 등 | 커스텀 메서드 |

suffix 없이 링크를 걸면 GET 요청도 `execute()`로 진입하고, 파라미터가 null인 상태에서 비즈니스 로직이 실행되어 에러가 발생한다.

**올바른 패턴:**

```xml
<!-- 잘못된 예 -->
<link linkId="my-link">/secure/MyAction.jspa</link>

<!-- 올바른 예: 초기 진입점에는 반드시 !default -->
<link linkId="my-link">/secure/MyAction!default.jspa</link>
```

```java
@Override
public String doDefault() throws Exception {
    return INPUT; // GET 진입 → 빈 폼 표시
}

@Override
public String execute() throws Exception {
    if (requiredParam == null) { return INPUT; } // null guard 필수
    // 실제 비즈니스 로직
    return SUCCESS;
}
```

**WebWork Action 작성 체크리스트:**
- [ ] `web-item` 링크가 초기 진입이라면 `!default.jspa` suffix를 사용했는가?
- [ ] `doDefault()`와 `execute()`의 역할이 명확히 분리되어 있는가?
- [ ] `execute()`에 필수 파라미터 null guard가 있는가?
- [ ] `@SupportedMethods`에 GET/POST 모두 선언했는가?

---

### [PITFALL-02] OSGi Import-Package — `version="*"` 사용 금지

**증상:** UPM 설치 시 번들이 생성되지 않고 아래 예외가 발생한다.
```
java.lang.IllegalArgumentException: invalid range "*": invalid version "*": non-numeric "*"
```

**원인:**
Felix OSGi 컨테이너는 `Import-Package` 버전 범위에 숫자형 표기만 허용한다.  
`version="*"` 는 파싱 단계에서 `NumberFormatException` 을 일으켜 번들 생성 자체가 실패한다.

| 표기 | 허용 여부 | 의미 |
|---|---|---|
| `version="*"` | ❌ 불가 | OSGi 스펙 외 표기 |
| `version="0.0.0"` | ✅ 가능 | 0.0.0 이상 모든 버전 |
| `version="[1.0,2.0)"` | ✅ 가능 | 1.0 이상 2.0 미만 |
| 버전 생략 | ✅ 가능 | 버전 제약 없음 (권장) |

**올바른 패턴:**

```xml
<!-- 잘못된 예 -->
<Import-Package>
    jakarta.ws.rs;version="*",
    com.atlassian.jira.web.action;version="*",
    *
</Import-Package>

<!-- 올바른 예: 버전 제약이 필요 없으면 패키지명만 작성 -->
<Import-Package>
    jakarta.ws.rs,
    com.atlassian.jira.web.action,
    *
</Import-Package>
```

**체크리스트:**
- [ ] `Import-Package` 항목에 `version="*"` 가 없는가?
- [ ] 버전 범위가 필요하면 `version="0.0.0"` 또는 `version="[x.y,z.w)"` 형식을 사용했는가?

---

### [PITFALL-03] JAX-RS 네임스페이스 — `jakarta.ws.rs` vs `javax.ws.rs`

**증상:** 플러그인이 설치되었으나 활성화 실패하며 아래 예외가 발생한다.
```
missing requirement [com.example.jira-calculator-plugin] osgi.wiring.package;
(osgi.wiring.package=jakarta.ws.rs)
Unresolved requirements: [[...] osgi.wiring.package; (osgi.wiring.package=jakarta.ws.rs)]
```

**원인:**
Jira 10.x의 REST 모듈(`atlassian-rest-common`)은 **Jersey 2.x** 기반이며, OSGi 컨테이너는 `javax.ws.rs`만 export한다.  
`jakarta.ws.rs`(Jersey 3.x / Jakarta EE 9+)는 컨테이너에 패키지가 존재하지 않는다.

| 영역 | 올바른 패키지 | 잘못된 패키지 |
|------|-------------|------------|
| JAX-RS 어노테이션 (`@Path`, `@POST` 등) | `javax.ws.rs.*` ✅ | `jakarta.ws.rs.*` ❌ |
| DI 어노테이션 (`@Named` on REST resource) | 사용하지 않음 ✅ | `jakarta.inject.*` ❌ `javax.inject.*` ❌ |

**올바른 패턴:**

```java
// ✅ JAX-RS는 javax
import javax.ws.rs.Path;
import javax.ws.rs.POST;
import javax.ws.rs.core.Response;

// ✅ DI는 jakarta
import jakarta.inject.Named;

@Named
@Path("/calculate")
public class CalculatorResource { ... }
```

```xml
<!-- pom.xml: JAX-RS 의존성 -->
<dependency>
    <groupId>javax.ws.rs</groupId>
    <artifactId>javax.ws.rs-api</artifactId>
    <version>2.1.1</version>
    <scope>provided</scope>
</dependency>

<!-- Import-Package -->
<Import-Package>
    javax.ws.rs,
    javax.ws.rs.core,
    jakarta.inject,
    *
</Import-Package>
```

**체크리스트:**
- [ ] JAX-RS 어노테이션이 `javax.ws.rs`를 import하는가? (`jakarta.ws.rs` 아님)
- [ ] REST 리소스 클래스에 `@Named` 어노테이션이 없는가?
- [ ] pom.xml 의존성이 `javax.ws.rs:javax.ws.rs-api:2.1.1`인가?
- [ ] pom.xml에 `jakarta.inject-api` 의존성이 없는가?
- [ ] Import-Package에 `jakarta.inject`가 없는가?

---

### [PITFALL-04] WebWork Action — `webwork.action` OSGi Import 누락

**증상:** 플러그인 설치 후 활성화는 되나, 관리자 페이지 접근 시 아래 예외 발생.
```
java.lang.Error: Unresolved compilation problems:
    The hierarchy of the type CalculatorAction is inconsistent
    The type webwork.action.ActionSupport cannot be resolved.
    It is indirectly referenced from required type com.atlassian.jira.web.action.JiraWebActionSupport
    INPUT cannot be resolved to a variable
    SUCCESS cannot be resolved to a variable
```

**원인:**
`JiraWebActionSupport`는 내부적으로 `webwork.action.ActionSupport`를 상속한다.  
OSGi는 직접 import한 패키지뿐 아니라 **클래스 계층에서 간접 참조되는 패키지**도 bundle에서 resolve할 수 있어야 한다.  
`Import-Package`에 `webwork.action`이 없으면 JVM이 `INPUT`, `SUCCESS` 상수와 부모 클래스를 찾지 못해 런타임 에러가 발생한다.

**올바른 패턴:**

```xml
<!-- pom.xml dependencies — webwork 필수 포함 (컴파일용) -->
<dependency>
    <groupId>opensymphony</groupId>
    <artifactId>webwork</artifactId>
    <version>1.4-atlassian-30</version>
    <scope>provided</scope>
</dependency>

<!-- pom.xml Import-Package — webwork.action 필수 포함 (런타임용) -->
<Import-Package>
    com.atlassian.jira.web.action,
    webwork.action,
    *
</Import-Package>
```

**체크리스트:**
- [ ] `pom.xml`의 `dependencies` 섹션에 `opensymphony:webwork`가 추가되었는가?
- [ ] `JiraWebActionSupport`를 상속하는 Action 클래스가 있다면 `webwork.action`이 Import-Package에 포함되어 있는가?
- [ ] `INPUT`, `SUCCESS` 상수가 컴파일 오류 없이 인식되는가?

---

## 🔄 Workflow: Task Execution
1. `TASKS.md`에서 현재 챕터 확인.
2. `workspace` 내의 기존 파일 상태를 `ls -R` 및 `cat`으로 확인.
3. 위 Skill 규칙(특히 UI 확장점 및 데코레이터 설정)에 따라 코드 작성.
4. `atlas-mvn` 빌드를 통해 결과 검증.

## 🏗 Skill 6: OSGi Dependency Injection (The P2 Way)
- **Component Import**: Jira 코어가 제공하는 빈(예: `UserManager`, `ProjectManager`)을 서비스 클래스에서 주입받으려면 반드시 생성자 파라미터에 `@ComponentImport`를 붙여야 합니다.
- **Rules**: `pom.xml`의 `maven-jira-plugin` 설정 중 `<Import-Package>`에 해당 API 패키지가 포함되어 있는지 반드시 확인하십시오.

## 🏢 Skill 7: Modern Injection Rules
- **Standard**: 모든 비즈니스 로직(Service/Component)은 `@Named`와 생성자 주입(`@Inject`)을 사용하십시오.
- **Exception**: `JiraWebActionSupport`를 상속받는 Webwork Action 클래스는 Jira 프레임워크가 인스턴스화하므로, 내부 로직에서 필요 시 `ComponentAccessor`를 사용하여 의존성을 획득하십시오.

## 🛑 Skill 8: Jira 10 Strict Compatibility
- **Library Bans**: Google Guava(`com.google.common.*`)와 Joda-time(`org.joda.time.*`) 사용을 엄격히 금지합니다.
- **Standards**: 반드시 Java 11/17 표준 라이브러리(`java.util.stream`, `java.time.*`)를 사용하십시오.
- **Jakarta 금지 (Jira 10.3.4)**: 이 인스턴스는 `jakarta.*` 패키지를 **전혀** export하지 않는다. JAX-RS는 `javax.ws.rs`, DI는 사용하지 않음. `jakarta.*` import 자체를 금지.

## 🧪 Skill 9: Wired Integration Tests (it.*)
- **Location**: 통합 테스트는 `src/test/java/it/` 패키지에 작성합니다.
- **Runner**: 클래스 상단에 `@RunWith(AtlassianPluginsTestRunner.class)`를 선언하여 OSGi 컨테이너 환경에서 테스트를 실행하십시오.

## 🎨 Skill 10: Atlassian User Interface (AUI) Strict Rules
   2 UI를 구성할 때는 절대 임의의 HTML/CSS를 발명하지 말고, 반드시 아래 AUI 표준 클래스를 사용해야 합니다.
   3 - **페이지 레이아웃**: `<section id="content" role="main"><header class="aui-page-header">...</header><div
     class="aui-page-panel">...</div></section>`
   4 - **폼 및 입력**: `<form class="aui">`, `<input class="text" type="text">`
   5 - **버튼**: `<button class="aui-button aui-button-primary">Submit</button>`

## ⚡ Skill 11: Front-end Event Handling & Scoping
- **Inline Handlers 금지**: HTML/Velocity 템플릿 내부에 `onclick="..."` 등의 인라인 이벤트 핸들러를 절대 사용하지 마십시오. JS가 IIFE(즉시 실행 함수)로 캡슐화될 경우 전역 스코프를 찾지 못해 `ReferenceError`가 발생합니다.
- **Event Delegation 사용**: 버튼 등 동적 요소의 이벤트는 `data-*` 속성을 활용하고, JavaScript 파일 내부에서 `AJS.$` (jQuery)를 이용한 이벤트 위임(Event Delegation) 방식으로 바인딩하십시오.
  - *예시 (HTML)*: `<button class="calc-btn" data-action="clear">C</button>` ← **`aui-button` 클래스 없음** (PITFALL-05 참조)
  - *예시 (JS)*: `AJS.$('.calc-grid').on('click', '.calc-btn', function(e) { ... });`

---

### [PITFALL-05] CSS Grid 버튼에 `aui-button` 클래스 적용 금지

**증상:** CSS Grid(`display: grid`)로 구성한 계산기 버튼들이 격자 구조를 무시하고 일렬로 늘어서거나, 버튼 크기·색상이 커스텀 CSS 대신 AUI 기본 스타일로 렌더링된다.

**원인:**
AUI의 `.aui-button` 클래스는 `display: inline-flex`, 고정 padding, border, background-color 등을 자체 스타일시트에 지정한다.  
이 규칙들은 플러그인 CSS보다 **로딩 순서상 나중에 적용**되거나 **선택자 특이도(specificity)가 높아** 커스텀 Grid 레이아웃 및 색상을 덮어쓴다.

| 클래스 조합 | 결과 |
|---|---|
| `aui-button` + CSS Grid 컨테이너 | ❌ 버튼이 일렬로 늘어서거나 AUI 색으로 고정됨 |
| 커스텀 클래스만 + `!important` | ✅ CSS Grid 정상 작동, 커스텀 색상 적용 |

**올바른 패턴:**

```html
<!-- ❌ 잘못된 예: aui-button 클래스가 Grid 레이아웃을 방해함 -->
<button class="aui-button aui-button-primary calc-btn calc-btn-operator" data-action="operator" data-value="/">÷</button>

<!-- ✅ 올바른 예: 커스텀 클래스만 사용, CSS에서 !important로 AUI 오버라이드 -->
<button class="calc-btn calc-btn-operator" data-action="operator" data-value="/">÷</button>
```

```css
/* CSS에서 핵심 레이아웃 속성에 !important 적용 */
.calc-grid {
    display: grid !important;
    grid-template-columns: repeat(4, 1fr) !important;
}
.calc-grid .calc-btn {
    display: flex !important;
    width: 100% !important;
    margin: 0 !important;
    border: none !important;
}
```

**체크리스트:**
- [ ] CSS Grid 컨테이너 내부 버튼에 `aui-button` 또는 `aui-button-primary` 클래스가 없는가?
- [ ] `.calc-grid`에 `display: grid !important`가 선언되어 있는가?
- [ ] `.calc-grid .calc-btn`에 `width: 100% !important`, `margin: 0 !important`가 선언되어 있는가?
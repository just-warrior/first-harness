# 🛠 Atlassian SDK Expert Skill (Jira 10+)

이 문서는 Jira Data Center 10+ 개발을 위한 고도화된 스킬 세트입니다. Claude는 작업을 시작하기 전에 반드시 이 파일을 `cat`으로 읽고 모든 규칙을 내부 메모리에 로드해야 합니다.

## 🗂 Skill 1: Plugin Lifecycle Management
- **Command Set**: `atlas-create-jira-plugin`, `atlas-mvn clean package`, `atlas-run`, `atlas-debug`.
- **Standard**: 모든 빌드는 `atlas-mvn`을 사용하며, 환경 변수 충돌 방지를 위해 `workspace` 디렉터리 내에서 실행함.

## 🏗 Skill 2: Spring Scanner 3.x & Jakarta EE
- **Annotations**: `@Named` (Component), `@Inject` (Autowired), `@ComponentImport` (Jira API).
- **Package**: `javax.*`가 아닌 `jakarta.*` 패키지를 사용해야 함 (Jira 10 기준).
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

## 🔄 Workflow: Task Execution
1. `TASKS.md`에서 현재 챕터 확인.
2. `workspace` 내의 기존 파일 상태를 `ls -R` 및 `cat`으로 확인.
3. 위 Skill 규칙(특히 UI 확장점 및 데코레이터 설정)에 따라 코드 작성.
4. `atlas-mvn` 빌드를 통해 결과 검증.

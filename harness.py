import subprocess
import os
import json
import re
import datetime
import hashlib
import shutil
import time


class SmartOrchestrator:
    """
    Plan Once, Execute Consistently (POEC) 하네스 v5.
    v5 개선:
    - P0: subprocess 에러 핸들링 + 타임아웃
    - P0: 챕터별 린트 검증 (SKILLS.md 규칙 위반 자동 탐지)
    - P0: 빌드 검증 챕터 하네스 직접 실행 (LLM 불필요)
    - P0: 챕터 간 파일 수정 범위 제한 지시
    - P1: 이전 챕터 요약 주입 (챕터 간 일관성)
    - (v4 기능 모두 포함)
    """

    MAX_RETRIES = 2
    SUBPROCESS_TIMEOUT = 600  # 10분
    EXCLUDE_DIRS = ("target", ".osgi-plugins", ".idea")

    # 챕터별 린트 규칙: (파일 확장자, 탐지 문자열, 위반 설명)
    LINT_RULES = [
        (".java", "import jakarta.", "jakarta.* 패키지 사용 금지 (Skill 8, PITFALL-03)"),
        (".xml", 'version="*"', 'Import-Package version="*" 사용 금지 (PITFALL-02)'),
        (".vm", "onclick=", "인라인 onclick 핸들러 사용 금지 (Skill 11)"),
        (".java", "import com.atlassian.jira.web.action.SupportedMethods",
         "SupportedMethods 패키지 오류 — com.atlassian.jira.security.request.SupportedMethods 사용 (PITFALL-07)"),
        (".java", "import com.atlassian.jira.web.action.RequestMethod",
         "RequestMethod 패키지 오류 — com.atlassian.jira.security.request.RequestMethod 사용 (PITFALL-07)"),
    ]

    def __init__(self):
        self.base_dir = os.getcwd()
        self.workspace_dir = os.path.join(self.base_dir, "workspace")
        self.status_dir = os.path.join(self.base_dir, ".status")
        self.archive_root = os.path.join(self.base_dir, "archive")

        self.spec_file = os.path.join(self.base_dir, "docs/REQUIREMENTS.md")
        self.task_file = os.path.join(self.status_dir, "TASKS.md")
        self.log_file = os.path.join(self.status_dir, "SESSION_CONTEXT.md")
        self.info_file = os.path.join(self.status_dir, "project_info.json")
        self.plan_lock_file = os.path.join(self.status_dir, "PLAN_LOCK.json")
        self.skill_file = os.path.join(self.base_dir, ".claude/SKILLS.md")
        self.fix_history_file = os.path.join(self.base_dir, "FIX_HISTORY.md")

        for d in [self.workspace_dir, self.status_dir, self.archive_root]:
            if not os.path.exists(d):
                os.makedirs(d)

    # ------------------------------------------------------------------
    # 유틸리티
    # ------------------------------------------------------------------
    def get_file_hash(self):
        """P1: REQUIREMENTS.md + SKILLS.md 복합 해시 (가이드라인 변경도 감지)"""
        content = b""
        for path in [self.spec_file, self.skill_file]:
            if os.path.exists(path):
                with open(path, "rb") as f:
                    content += f.read()
        return hashlib.md5(content).hexdigest()

    def archive_current(self):
        """현재 워크스페이스와 상태를 아카이브로 이동하고 초기화"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = os.path.join(self.archive_root, timestamp)
        os.makedirs(archive_path)
        print(f"📦 [Archive] 기존 프로젝트 백업 중: {archive_path}")

        if os.path.exists(self.workspace_dir):
            shutil.move(self.workspace_dir, os.path.join(archive_path, "workspace"))
            os.makedirs(self.workspace_dir)

        status_backup = os.path.join(archive_path, ".status")
        os.makedirs(status_backup)
        for f in os.listdir(self.status_dir):
            if f != "project_info.json":
                shutil.move(
                    os.path.join(self.status_dir, f),
                    os.path.join(status_backup, f),
                )

    # ------------------------------------------------------------------
    # Workspace 상태 주입 — 이전 챕터 결과를 다음 챕터에 전달
    # ------------------------------------------------------------------
    def get_workspace_manifest(self, chapter_info=None):
        """
        P2: chapter_info가 있으면 관련 파일만 전체 내용(30줄), 나머지는 경로 목록만 표시.
        대형 프로젝트에서 토큰 폭증 방지.
        """
        manifest = "# CURRENT WORKSPACE STATE (이전 챕터에서 생성된 파일들)\n"
        manifest += "> 아래 파일들은 이미 존재합니다. 이 파일들과 일관성을 유지하세요.\n\n"

        related_basenames = set()
        if chapter_info:
            for f in chapter_info.get("expected_files", []):
                related_basenames.add(os.path.basename(f))

        detailed_entries = []
        listed_paths = []

        for root, dirs, files in os.walk(self.workspace_dir):
            dirs[:] = [d for d in dirs if d not in ("target", ".osgi-plugins", ".idea")]
            for fname in sorted(files):
                if fname.endswith((".class", ".jar", ".iml", ".DS_Store")):
                    continue
                filepath = os.path.join(root, fname)
                rel = os.path.relpath(filepath, self.workspace_dir)
                if not chapter_info or fname in related_basenames:
                    detailed_entries.append((rel, filepath))
                else:
                    listed_paths.append(rel)

        for rel, filepath in detailed_entries:
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as fh:
                    lines = fh.readlines()[:30]
                manifest += f"## {rel}\n```\n{''.join(lines)}```\n\n"
            except Exception:
                pass

        if listed_paths:
            manifest += "## 기타 파일 목록 (참조용 — 일관성 유지)\n"
            for p in listed_paths:
                manifest += f"- {p}\n"
            manifest += "\n"

        if not detailed_entries and not listed_paths:
            manifest += "_아직 생성된 파일이 없습니다._\n"

        return manifest

    # ------------------------------------------------------------------
    # PLAN LOCK
    # ------------------------------------------------------------------
    def load_locked_plan(self):
        if os.path.exists(self.plan_lock_file):
            with open(self.plan_lock_file, "r", encoding="utf-8") as f:
                plan = json.load(f)
            print(f"🔒 [Plan Lock] 기존 잠긴 계획 로드 ({len(plan['chapters'])}개 챕터)")
            return plan
        return None

    def save_locked_plan(self, chapters, req_hash):
        plan = {
            "created_at": datetime.datetime.now().isoformat(),
            "req_hash": req_hash,
            "chapters": chapters,
        }
        with open(self.plan_lock_file, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        print(f"🔒 [Plan Lock] 계획 잠금 완료 ({len(chapters)}개 챕터) → {self.plan_lock_file}")

    def generate_plan_from_requirements(self):
        print("🧠 [Plan] AI가 설계서를 분석하여 작업 계획을 생성 중...")

        with open(self.spec_file, "r", encoding="utf-8") as f:
            spec = f.read()

        skills = ""
        if os.path.exists(self.skill_file):
            with open(self.skill_file, "r", encoding="utf-8") as f:
                skills = f.read()

        # P2: FIX_HISTORY.md가 있으면 플랜 프롬프트에 주입 (반복 실수 방지)
        fix_history_section = ""
        if os.path.exists(self.fix_history_file):
            with open(self.fix_history_file, "r", encoding="utf-8") as f:
                fix_history = f.read().strip()
            if fix_history:
                fix_history_section = f"\n\n[알려진 실패 패턴 — 반드시 회피]\n{fix_history}"

        prompt = f"""당신은 시니어 아틀라시안 플러그인 개발자입니다.
아래 설계서를 분석하여 개발 작업을 챕터 단위로 분해하세요.

[설계서]
{spec}

[기술 가이드]
{skills}{fix_history_section}

[출력 규칙 - 반드시 준수]
1. 결과는 반드시 아래 JSON 스키마의 배열로만 답변하세요. JSON 외 텍스트는 절대 포함하지 마세요.
2. 각 챕터는 하나의 논리적 단위 (예: 프로젝트 골격, 백엔드 액션, REST API, 프론트엔드 UI, 프론트엔드 로직, 빌드 검증)
3. 마지막 챕터는 반드시 "빌드 검증" 챕터여야 합니다.
4. expected_files에는 workspace 기준 상대 경로를 정확히 기재하세요.
5. 설계서에 '파일 매니페스트' 섹션이 있다면, 그 경로를 그대로 사용하세요.
6. 파일 매니페스트의 모든 파일을 빠짐없이 expected_files에 배분하세요. 누락된 파일이 하나라도 있으면 안 됩니다.
7. 프론트엔드 파일(.css, .js, Velocity 템플릿 .vm)은 반드시 독립된 별도 챕터(예: "프론트엔드 UI 구현")로 분리하세요. 다른 챕터(백엔드, 프로젝트 골격 등)에 합치지 마세요.
8. 각 챕터의 description에는 REQUIREMENTS.md의 해당 섹션(예: 3.2)을 명시적으로 인용하여 구체적인 구현 지시를 포함하세요.

[JSON 스키마]
```json
[
  {{
    "chapter": "챕터 이름 (한글)",
    "task": "수행할 작업 요약 (한 줄)",
    "description": "상세 설명 (LLM이 코드 생성 시 참고할 구체적 지시사항)",
    "expected_files": ["생성할 파일의 상대 경로 목록"]
  }}
]
```

JSON 배열만 출력하세요:"""

        try:
            result = subprocess.run(
                ["claude", "-p", prompt],
                capture_output=True, text=True, cwd=self.base_dir,
                timeout=self.SUBPROCESS_TIMEOUT,
            )
        except FileNotFoundError:
            print("❌ 'claude' CLI를 찾을 수 없습니다. PATH를 확인하세요.")
            return None
        except subprocess.TimeoutExpired:
            print("❌ AI 응답 타임아웃. 네트워크를 확인하세요.")
            return None

        match = re.search(r'\[\s*\{.*\}\s*\]', result.stdout, re.DOTALL)
        if not match:
            print("❌ AI 계획 생성 실패: JSON 파싱 불가")
            print(f"   원본 출력 (처음 500자): {result.stdout[:500]}")
            return None

        try:
            chapters = json.loads(match.group())
        except json.JSONDecodeError as e:
            print(f"❌ JSON 디코딩 실패: {e}")
            return None

        for ch in chapters:
            if not all(k in ch for k in ("chapter", "task", "description")):
                print(f"❌ 필수 키 누락: {ch}")
                return None
            if "expected_files" not in ch:
                ch["expected_files"] = []

        print(f"✅ AI 계획 생성 완료: {len(chapters)}개 챕터")
        chapters = self._validate_and_fix_plan_coverage(chapters)
        print(f"✅ 커버리지 보정 완료: {len(chapters)}개 챕터")
        for i, ch in enumerate(chapters):
            print(f"   Chapter {i+1}: {ch['chapter']} ({len(ch['expected_files'])}개 파일)")

        return chapters

    def analyze_intent(self, curr_hash):
        """P3: 동일 해시면 캐시된 의도 재사용, 새 해시면 LLM 호출 후 캐시 저장"""
        if os.path.exists(self.info_file):
            with open(self.info_file, "r") as f:
                info = json.load(f)
            cached = info.get("intent_cache", {})
            if cached.get("hash") == curr_hash:
                print(f"🔒 [Intent Cache] 캐시된 의도 재사용: {cached['intent']}")
                return cached["intent"]

        print("🔍 설계 변경 감지! AI가 의도를 분석 중입니다...")
        with open(self.spec_file, "r", encoding="utf-8") as f:
            spec = f.read()

        prompt = f"""설계서(REQUIREMENTS.md)가 변경되었습니다. 현재 워크스페이스의 코드와 비교하여 판단하세요.

[새로운 설계서]
{spec}

1. NEW: 완전히 다른 새로운 플러그인 프로젝트를 시작함.
2. INCREMENTAL: 기존 플러그인에 새로운 기능을 추가하거나 기존 로직을 수정함.

반드시 'INTENT: [NEW/INCREMENTAL]' 형식으로 답변을 시작하고 이유를 짧게 적으세요."""

        try:
            result = subprocess.run(
                ["claude", "-p", prompt],
                capture_output=True, text=True,
                timeout=self.SUBPROCESS_TIMEOUT,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("⚠️ AI 의도 분석 실패. INCREMENTAL로 기본 처리합니다.")
            return "INCREMENTAL"
        intent = "INCREMENTAL"
        if result.stdout and "INTENT: NEW" in result.stdout.upper():
            intent = "NEW"
        print(f"🤖 AI 판단 결과: {intent}")

        info = {}
        if os.path.exists(self.info_file):
            with open(self.info_file, "r") as f:
                info = json.load(f)
        info["intent_cache"] = {"hash": curr_hash, "intent": intent}
        with open(self.info_file, "w") as f:
            json.dump(info, f)

        return intent

    # ------------------------------------------------------------------
    # 태스크 파일 생성
    # ------------------------------------------------------------------
    def write_tasks_from_plan(self, chapters, completed_chapters=None):
        if completed_chapters is None:
            completed_chapters = set()

        with open(self.task_file, "w", encoding="utf-8") as f:
            f.write("# Project Task List\n\n")
            for i, ch in enumerate(chapters):
                num = i + 1
                status = "[x]" if num in completed_chapters else "[ ]"
                f.write(f"- {status} **Chapter {num}: {ch['chapter']}** - {ch['task']}\n")
                f.write(f"  - *Description*: {ch['description']}\n")
                if ch.get("expected_files"):
                    f.write(f"  - *Expected Files*: {', '.join(ch['expected_files'])}\n")

        print(f"📋 TASKS.md 생성 완료 ({len(chapters)}개 챕터)")

    # ------------------------------------------------------------------
    # 챕터 실행
    # ------------------------------------------------------------------
    def execute_chapter(self, chapter_num, chapter_info, retry_count=0, failure_context=None):
        chapter_name = chapter_info["chapter"]
        tasks = chapter_info["task"]
        description = chapter_info["description"]
        expected_files = chapter_info.get("expected_files", [])

        # 1. 정적 컨텍스트
        static_context = "# PROJECT STANDARDS & GUIDELINES\n"
        for path in [self.spec_file, self.skill_file, os.path.join(self.base_dir, ".claude/CLAUDE.md")]:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    static_context += f"\n## {os.path.basename(path)}\n{f.read()}\n"

        # 2. P2: 현재 챕터 관련 파일만 전체 내용, 나머지는 경로 목록
        workspace_state = self.get_workspace_manifest(chapter_info)

        # 3. P4: 이전 챕터 실행 결과 주입 (챕터 간 일관성)
        chapter_summaries = self._get_chapter_summaries(chapter_num)

        # 4. P0: 재시도 시 실패 원인 주입
        failure_section = ""
        if failure_context:
            failure_section = f"""
[이전 시도 실패 원인 — 반드시 해결 후 재시도]
{failure_context}
"""

        files_instruction = ', '.join(expected_files) if expected_files else '빌드 검증만 수행'
        lean_prompt = f"""{static_context}

{workspace_state}
{chapter_summaries}
{failure_section}
# CURRENT GOAL: Chapter {chapter_num} - {chapter_name}
당신은 위 가이드라인을 완벽히 숙지한 시니어 개발자입니다.
현재 `workspace`에서 다음 작업을 수행하세요.

[TASK]
{tasks}

[DETAILED DESCRIPTION]
{description}

[EXPECTED FILES TO CREATE/MODIFY]
{files_instruction}

[INSTRUCTION]
- 모든 작업은 `workspace` 폴더 내에서 이루어져야 합니다.
- REQUIREMENTS.md에 '파일 매니페스트' 섹션이 있다면 명시된 파일 경로를 정확히 따르세요.
- 위 CURRENT WORKSPACE STATE에 나열된 기존 파일과 일관성을 유지하세요 (import 경로, 패키지명, 클래스명 등).
- 기존 파일을 수정할 때는 원래 구조를 유지하면서 필요한 부분만 변경하세요.
- ⚠️ 이번 챕터의 EXPECTED FILES에 명시된 파일만 생성/수정하세요. 다른 챕터의 파일은 수정하지 마세요.
- 작업이 끝나면 어떤 파일이 어떻게 변경되었는지 요약하고 반드시 'CHAPTER COMPLETE'라고 명시하세요.
"""
        retry_tag = f" (재시도 {retry_count}/{self.MAX_RETRIES})" if retry_count > 0 else ""
        print(f"🚀 [Chapter {chapter_num}] 실행 중: {chapter_name}{retry_tag}")

        process = subprocess.Popen(
            ["claude", "--dangerously-skip-permissions", "-p", lean_prompt],
            cwd=self.base_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        full_output = []
        try:
            for line in process.stdout:
                print(line, end="")
                full_output.append(line)
            process.wait(timeout=self.SUBPROCESS_TIMEOUT)
        except subprocess.TimeoutExpired:
            process.kill()
            print(f"\n❌ [Chapter {chapter_num}] 타임아웃 발생 (작업 중단)")
            return None
        
        output_text = "".join(full_output)

        # P0: 실패 원인 수집 후 재시도 프롬프트에 주입
        failure_reasons = []

        if "CHAPTER COMPLETE" not in output_text.upper():
            failure_reasons.append(
                "'CHAPTER COMPLETE' 문자열이 출력에 없음 — 작업 완료 후 반드시 'CHAPTER COMPLETE'를 출력하세요."
            )

        missing = self._check_expected_files(expected_files)
        if missing:
            failure_reasons.append(
                f"다음 파일이 workspace에 존재하지 않음 — 반드시 생성하세요: {missing}"
            )

        # P0 v5: 린트 검증 — SKILLS.md 규칙 위반 자동 탐지
        lint_violations = self._lint_chapter_output(expected_files)
        if lint_violations:
            for v in lint_violations:
                print(f"🔍 [Lint] {v}")
            failure_reasons.extend(lint_violations)

        if failure_reasons:
            if retry_count < self.MAX_RETRIES:
                print(f"⚠️ [Chapter {chapter_num}] 실패 원인: {'; '.join(failure_reasons)}")
                print(f"🔄 재시도합니다... ({retry_count + 1}/{self.MAX_RETRIES})")
                return self.execute_chapter(
                    chapter_num, chapter_info,
                    retry_count + 1,
                    failure_context="\n".join(f"- {r}" for r in failure_reasons),
                )
            else:
                if "CHAPTER COMPLETE" not in output_text.upper():
                    print(f"❌ [Chapter {chapter_num}] 최대 재시도 초과. 건너뜁니다.")
                    return None
                print(f"❌ [Chapter {chapter_num}] 최대 재시도 초과. 린트 위반 또는 파일 누락 상태로 계속합니다.")

        return output_text

    def _check_expected_files(self, expected_files):
        """P1: basename이 아닌 full-path suffix 매칭으로 누락 파일 탐지"""
        missing = []
        for rel_path in expected_files:
            norm_rel = rel_path.replace(os.sep, "/")
            found = False
            if os.path.exists(os.path.join(self.workspace_dir, rel_path)):
                found = True
            if not found:
                for root, dirs, files in os.walk(self.workspace_dir):
                    dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS]
                    for fname in files:
                        full = os.path.join(root, fname)
                        rel_full = os.path.relpath(full, self.workspace_dir).replace(os.sep, "/")
                        if rel_full.endswith(norm_rel):
                            found = True
                            break
                    if found:
                        break
            if not found:
                missing.append(rel_path)
        return missing

    def _lint_chapter_output(self, expected_files):
        """P0 v5: 생성된 파일에서 SKILLS.md 규칙 위반 패턴을 grep으로 탐지"""
        violations = []
        for rel_path in expected_files:
            filepath = os.path.join(self.workspace_dir, rel_path)
            if not os.path.exists(filepath):
                continue
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue

            ext = os.path.splitext(rel_path)[1]

            # 범용 린트 규칙
            for rule_ext, pattern, desc in self.LINT_RULES:
                if ext == rule_ext and pattern in content:
                    violations.append(f"{rel_path}: {desc}")

            # Action 전용: JiraWebActionSupport 상속 클래스에 @Component/@Named 조합 금지 (PITFALL-08)
            if ext == ".java":
                if "extends JiraWebActionSupport" in content and (
                    "@Component" in content or "@Named" in content
                ):
                    violations.append(
                        f"{rel_path}: JiraWebActionSupport 상속 클래스에 @Component/@Named 금지 "
                        f"— ConfigurationClassParser OSGi 클래스 로딩 실패 유발 (PITFALL-08). "
                        f"plugin-context.xml에 <bean> 직접 선언 사용"
                    )

            # pom.xml 전용: version="*" in Import-Package (PITFALL-02)
            if rel_path.endswith("pom.xml") and 'version="*"' in content:
                violations.append(f"{rel_path}: Import-Package version=\"*\" 사용 금지 (PITFALL-02)")

        if violations:
            print(f"⚠️ [Lint] {len(violations)}개 규칙 위반 감지")
        return violations

    # ------------------------------------------------------------------
    # Plan Coverage
    # ------------------------------------------------------------------
    def _parse_manifest_files(self):
        if not os.path.exists(self.spec_file):
            return []
        with open(self.spec_file, "r", encoding="utf-8") as f:
            content = f.read()
        return re.findall(r"`(jira-calculator-plugin/[^`]+)`", content)

    def _validate_and_fix_plan_coverage(self, chapters):
        """P1: basename이 아닌 suffix 매칭으로 커버리지 검증 (오탐 방지)"""
        manifest_files = self._parse_manifest_files()
        if not manifest_files:
            return chapters

        def is_covered(manifest_path, chapter_files):
            norm_mf = manifest_path.replace(os.sep, "/")
            for cf in chapter_files:
                norm_cf = cf.replace(os.sep, "/")
                if norm_mf.endswith(norm_cf) or norm_cf.endswith(norm_mf):
                    return True
            return False

        missing = [
            mf for mf in manifest_files
            if not any(is_covered(mf, ch.get("expected_files", [])) for ch in chapters)
        ]
        if not missing:
            return chapters

        print(f"⚠️ [Plan Coverage] 미배분 파일 감지: {missing}")

        frontend_exts = {".css", ".js", ".vm"}
        frontend_missing = [f for f in missing if os.path.splitext(f)[1] in frontend_exts]

        if frontend_missing:
            fe_chapter = next(
                (ch for ch in chapters
                 if any(kw in ch["chapter"].lower() for kw in ("프론트", "frontend", "ui"))),
                None,
            )
            if fe_chapter:
                fe_chapter["expected_files"] = list(
                    set(fe_chapter.get("expected_files", []) + frontend_missing)
                )
                print(f"✅ [Plan Coverage] '{fe_chapter['chapter']}' 챕터에 {frontend_missing} 추가")
            else:
                new_chapter = {
                    "chapter": "프론트엔드 UI 구현",
                    "task": "CSS Grid 레이아웃 및 JS AJAX 연동 구현",
                    "description": (
                        "REQUIREMENTS.md 3.2절 기준: CSS Grid로 계산기 버튼 격자 배치, "
                        "AUI 버튼 스타일 적용(aui-button), JS 배열로 최대 5개 이력 관리. "
                        "인라인 핸들러 금지 — data-* 속성 + AJS.$ 이벤트 위임 방식 사용(SKILLS.md Skill 11)."
                    ),
                    "expected_files": frontend_missing,
                }
                insert_idx = max(0, len(chapters) - 1)
                chapters.insert(insert_idx, new_chapter)
                print(f"✅ [Plan Coverage] 프론트엔드 챕터 자동 생성: {frontend_missing}")

        return chapters

    # ------------------------------------------------------------------
    # 로그
    # ------------------------------------------------------------------
    def log_progress(self, chapter_num, chapter_name, output, elapsed_seconds=None):
        """P3: 실행 시간 포함 로깅"""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        files_match = re.findall(
            r"(?:Created|Updated|Modified|Edited|Saved|Wrote to|Created file|Overwriting)"
            r"[\s:]*[`\"']?([^\s\n`\"']+\.\w{1,10})",
            output, re.IGNORECASE,
        )
        if files_match:
            unique_files = list(set([os.path.basename(f.strip("`'\"")) for f in files_match]))
            summary = f"변경 파일: {', '.join(unique_files[:8])}"
        else:
            recent = self._get_recently_modified_files(minutes=5)
            summary = f"변경 파일 (타임스탬프): {', '.join(recent[:8])}" if recent else "작업 완료"

        time_str = f" ({elapsed_seconds:.1f}s)" if elapsed_seconds is not None else ""
        with open(self.log_file, "a", encoding="utf-8") as log:
            log.write(
                f"\n### ✅ [Chapter {chapter_num}] {chapter_name} ({now}){time_str}\n- {summary}\n"
            )

    def _get_recently_modified_files(self, minutes=5):
        cutoff = datetime.datetime.now().timestamp() - (minutes * 60)
        recent = []
        for root, dirs, files in os.walk(self.workspace_dir):
            dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS]
            for fname in files:
                filepath = os.path.join(root, fname)
                try:
                    if os.path.getmtime(filepath) > cutoff:
                        recent.append(os.path.relpath(filepath, self.workspace_dir))
                except OSError:
                    pass
        return sorted(recent)

    def update_status(self, chapter_num):
        with open(self.task_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open(self.task_file, "w", encoding="utf-8") as f:
            for line in lines:
                if f"**Chapter {chapter_num}:" in line:
                    f.write(line.replace("[ ]", "[x]"))
                else:
                    f.write(line)

    # ------------------------------------------------------------------
    # 빌드 검증 (하네스 직접 실행 — LLM 불필요)
    # ------------------------------------------------------------------
    def execute_build_verification(self):
        """P0 v5: 빌드 검증을 하네스가 직접 수행하여 토큰 절약"""
        # workspace 하위에서 pom.xml이 있는 프로젝트 디렉터리 탐색
        build_dir = None
        for entry in os.listdir(self.workspace_dir):
            candidate = os.path.join(self.workspace_dir, entry)
            if os.path.isdir(candidate) and os.path.exists(os.path.join(candidate, "pom.xml")):
                build_dir = candidate
                break

        if not build_dir:
            print("❌ [Build] pom.xml이 있는 프로젝트 디렉터리를 찾을 수 없습니다.")
            return None

        # plugin-context.xml 존재 여부 확인 — 없으면 "Plugin has no container" 런타임 오류 발생 (PITFALL-06)
        plugin_context_found = False
        for root, dirs, files in os.walk(build_dir):
            dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS]
            if "plugin-context.xml" in files:
                plugin_context_found = True
                break
        if not plugin_context_found:
            print("❌ [Build] META-INF/spring/plugin-context.xml 누락 — 빌드 전 복원 필요 (PITFALL-06)")
            return None

        print(f"🔨 [Build] 빌드 실행: {build_dir}")
        try:
            result = subprocess.run(
                ["atlas-mvn", "clean", "package", "-q"],
                cwd=build_dir,
                capture_output=True, text=True,
                timeout=self.SUBPROCESS_TIMEOUT,
            )
        except FileNotFoundError:
            print("❌ 'atlas-mvn' 명령을 찾을 수 없습니다. Atlassian SDK를 확인하세요.")
            return None
        except subprocess.TimeoutExpired:
            print("❌ 빌드 타임아웃.")
            return None

        output = result.stdout + result.stderr
        if result.returncode == 0:
            print("✅ [Build] BUILD SUCCESS")
            return f"BUILD SUCCESS\nCHAPTER COMPLETE\n{output[-1000:]}"
        else:
            print(f"❌ [Build] BUILD FAILURE (exit code: {result.returncode})")
            print(output[-2000:])
            return None

    def _get_chapter_summaries(self, up_to_chapter):
        """P4 v5: 이전 챕터 실행 결과를 주입하여 챕터 간 일관성 유지"""
        if not os.path.exists(self.log_file):
            return ""
        with open(self.log_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            return ""
        return f"\n# 이전 챕터 실행 결과 (참고용 — 이 파일들은 이미 완성됨, 수정 금지)\n{content}\n"

    # ------------------------------------------------------------------
    # 메인 실행 루프
    # ------------------------------------------------------------------
    def run(self):
        curr_hash = self.get_file_hash()
        info = {}
        if os.path.exists(self.info_file):
            with open(self.info_file, "r") as f:
                info = json.load(f)

        old_hash = info.get("req_hash")
        locked_plan = self.load_locked_plan()

        # ── Case 1: 신규 프로젝트 ──
        if not old_hash:
            print("🆕 신규 프로젝트 설계를 시작합니다...")
            if locked_plan and locked_plan.get("req_hash") == curr_hash:
                chapters = locked_plan["chapters"]
                print("🔒 기존 PLAN_LOCK 재사용 (동일 설계서)")
            else:
                chapters = self.generate_plan_from_requirements()
                if not chapters:
                    print("❌ 계획 생성 실패. 종료합니다.")
                    return
                self.save_locked_plan(chapters, curr_hash)

            self.write_tasks_from_plan(chapters)
            info["req_hash"] = curr_hash
            with open(self.info_file, "w") as f:
                json.dump(info, f)

        # ── Case 2: REQUIREMENTS.md 또는 SKILLS.md 변경됨 ──
        elif old_hash != curr_hash:
            intent = self.analyze_intent(curr_hash)
            if intent == "NEW":
                # P0: 플랜 생성 성공 후 아카이브 (실패 시 기존 워크스페이스 보존)
                chapters = self.generate_plan_from_requirements()
                if not chapters:
                    print("❌ 계획 생성 실패. 기존 워크스페이스는 보존됩니다.")
                    return
                self.archive_current()
                if os.path.exists(self.plan_lock_file):
                    os.remove(self.plan_lock_file)
                self.save_locked_plan(chapters, curr_hash)
                self.write_tasks_from_plan(chapters)
            else:
                # INCREMENTAL: 기존 완료 상태 보존
                completed_chapters = set()
                if os.path.exists(self.task_file):
                    with open(self.task_file, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.startswith("- [x]"):
                                m = re.search(r"\*\*Chapter (\d+):", line)
                                if m:
                                    completed_chapters.add(int(m.group(1)))

                if os.path.exists(self.plan_lock_file):
                    os.remove(self.plan_lock_file)

                chapters = self.generate_plan_from_requirements()
                if not chapters:
                    print("❌ 계획 생성 실패. 종료합니다.")
                    return
                self.save_locked_plan(chapters, curr_hash)
                self.write_tasks_from_plan(chapters, completed_chapters)

            info["req_hash"] = curr_hash
            with open(self.info_file, "w") as f:
                json.dump(info, f)

        # ── Case 3: 변경 없음 ──
        else:
            if locked_plan:
                chapters = locked_plan["chapters"]
            else:
                print("⚠️ PLAN_LOCK이 없습니다. 설계서에서 새 계획을 생성합니다.")
                chapters = self.generate_plan_from_requirements()
                if not chapters:
                    print("❌ 계획 생성 실패. 종료합니다.")
                    return
                self.save_locked_plan(chapters, curr_hash)
                self.write_tasks_from_plan(chapters)

        # ── 미완료 챕터 수집 및 실행 ──
        if not os.path.exists(self.plan_lock_file):
            print("❌ PLAN_LOCK이 없어 실행할 수 없습니다.")
            return

        with open(self.plan_lock_file, "r", encoding="utf-8") as f:
            plan = json.load(f)
        chapters = plan["chapters"]

        pending = []
        if os.path.exists(self.task_file):
            with open(self.task_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("- [ ]"):
                        m = re.search(r"\*\*Chapter (\d+):", line)
                        if m:
                            c_num = int(m.group(1))
                            if 1 <= c_num <= len(chapters):
                                pending.append((c_num, chapters[c_num - 1]))

        if not pending:
            print("✅ 모든 챕터가 완료되었습니다. 실행할 작업이 없습니다.")
            return

        print(f"📌 미완료 챕터 {len(pending)}개 실행 시작")

        for c_num, chapter_info in sorted(pending, key=lambda x: x[0]):
            start = time.time()

            # P0 v5: 빌드 검증 챕터는 하네스가 직접 실행 (LLM 토큰 절약)
            is_build_chapter = any(
                kw in chapter_info["chapter"].lower()
                for kw in ("빌드 검증", "build verification", "빌드검증")
            )
            if is_build_chapter:
                output = self.execute_build_verification()
            else:
                output = self.execute_chapter(c_num, chapter_info)

            elapsed = time.time() - start
            if output:
                self.update_status(c_num)
                self.log_progress(c_num, chapter_info["chapter"], output, elapsed_seconds=elapsed)
                print(f"✅ [Chapter {c_num}] 완료: {chapter_info['chapter']} ({elapsed:.1f}s)")
            else:
                print(f"⚠️ [Chapter {c_num}] 실행 중 오류 발생. 중단합니다.")
                break

        print("\n🏁 하네스 실행 완료")


if __name__ == "__main__":
    harness = SmartOrchestrator()
    harness.run()

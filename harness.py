import subprocess
import os
import json
import re
import datetime
import hashlib
import shutil


class SmartOrchestrator:
    """
    Plan Once, Execute Consistently (POEC) 하네스 v3.
    - 첫 실행: LLM이 REQUIREMENTS.md를 분석 → 구조화된 계획 생성 → PLAN_LOCK.json에 잠금
    - 이후 실행: Lock된 계획을 그대로 재사용 (LLM 재호출 없음 → 일관성 보장)
    - REQUIREMENTS.md 변경 시: Lock 삭제 → 새 계획 생성
    """

    MAX_RETRIES = 2

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

        for d in [self.workspace_dir, self.status_dir, self.archive_root]:
            if not os.path.exists(d):
                os.makedirs(d)

    # ------------------------------------------------------------------
    # 유틸리티
    # ------------------------------------------------------------------
    def get_file_hash(self, path):
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

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
    def get_workspace_manifest(self):
        """workspace 내 모든 소스 파일의 경로와 첫 30줄을 수집"""
        manifest = "# CURRENT WORKSPACE STATE (이전 챕터에서 생성된 파일들)\n"
        manifest += "> 아래 파일들은 이미 존재합니다. 이 파일들과 일관성을 유지하세요.\n\n"
        file_count = 0
        for root, dirs, files in os.walk(self.workspace_dir):
            dirs[:] = [d for d in dirs if d not in ("target", ".osgi-plugins", ".idea")]
            for fname in sorted(files):
                if fname.endswith((".class", ".jar", ".iml", ".DS_Store")):
                    continue
                filepath = os.path.join(root, fname)
                rel = os.path.relpath(filepath, self.workspace_dir)
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as fh:
                        lines = fh.readlines()[:30]
                    manifest += f"## {rel}\n```\n{''.join(lines)}```\n\n"
                    file_count += 1
                except Exception:
                    pass
        if file_count == 0:
            manifest += "_아직 생성된 파일이 없습니다._\n"
        return manifest

    # ------------------------------------------------------------------
    # PLAN LOCK: LLM이 한 번 생성한 계획을 잠그고 재사용
    # ------------------------------------------------------------------
    def load_locked_plan(self):
        """PLAN_LOCK.json이 존재하면 잠긴 계획을 반환, 없으면 None"""
        if os.path.exists(self.plan_lock_file):
            with open(self.plan_lock_file, "r", encoding="utf-8") as f:
                plan = json.load(f)
            print(f"🔒 [Plan Lock] 기존 잠긴 계획 로드 ({len(plan['chapters'])}개 챕터)")
            return plan
        return None

    def save_locked_plan(self, chapters, req_hash):
        """생성된 계획을 PLAN_LOCK.json에 저장하여 잠금"""
        plan = {
            "created_at": datetime.datetime.now().isoformat(),
            "req_hash": req_hash,
            "chapters": chapters,
        }
        with open(self.plan_lock_file, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        print(f"🔒 [Plan Lock] 계획 잠금 완료 ({len(chapters)}개 챕터) → {self.plan_lock_file}")

    def generate_plan_from_requirements(self):
        """
        LLM이 REQUIREMENTS.md를 분석하여 구조화된 작업 계획을 생성.
        어떤 프로젝트든 유연하게 대응하되, 출력 스키마를 강제하여 일관성을 확보.
        """
        print("🧠 [Plan] AI가 설계서를 분석하여 작업 계획을 생성 중...")

        with open(self.spec_file, "r", encoding="utf-8") as f:
            spec = f.read()

        # 스킬 파일 내용도 함께 전달
        skills = ""
        if os.path.exists(self.skill_file):
            with open(self.skill_file, "r", encoding="utf-8") as f:
                skills = f.read()

        prompt = f"""당신은 시니어 아틀라시안 플러그인 개발자입니다.
아래 설계서를 분석하여 개발 작업을 챕터 단위로 분해하세요.

[설계서]
{spec}

[기술 가이드]
{skills}

[출력 규칙 - 반드시 준수]
1. 결과는 반드시 아래 JSON 스키마의 배열로만 답변하세요. JSON 외 텍스트는 절대 포함하지 마세요.
2. 각 챕터는 하나의 논리적 단위 (예: 프로젝트 골격, 백엔드 액션, REST API, 프론트엔드 UI, 프론트엔드 로직, 빌드 검증)
3. 마지막 챕터는 반드시 "빌드 검증" 챕터여야 합니다.
4. expected_files에는 workspace 기준 상대 경로를 정확히 기재하세요.
5. 설계서에 '파일 매니페스트' 섹션이 있다면, 그 경로를 그대로 사용하세요.

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

        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True, text=True, cwd=self.base_dir,
        )

        # JSON 추출
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

        # 기본 검증
        for ch in chapters:
            if not all(k in ch for k in ("chapter", "task", "description")):
                print(f"❌ 필수 키 누락: {ch}")
                return None
            if "expected_files" not in ch:
                ch["expected_files"] = []

        print(f"✅ AI 계획 생성 완료: {len(chapters)}개 챕터")
        for i, ch in enumerate(chapters):
            print(f"   Chapter {i+1}: {ch['chapter']} ({len(ch['expected_files'])}개 파일)")

        return chapters

    def analyze_intent(self):
        """설계 변경의 의도를 분석 (NEW vs INCREMENTAL)"""
        print("🔍 설계 변경 감지! AI가 의도를 분석 중입니다...")
        with open(self.spec_file, "r", encoding="utf-8") as f:
            spec = f.read()

        prompt = f"""설계서(REQUIREMENTS.md)가 변경되었습니다. 현재 워크스페이스의 코드와 비교하여 판단하세요.

[새로운 설계서]
{spec}

1. NEW: 완전히 다른 새로운 플러그인 프로젝트를 시작함.
2. INCREMENTAL: 기존 플러그인에 새로운 기능을 추가하거나 기존 로직을 수정함.

반드시 'INTENT: [NEW/INCREMENTAL]' 형식으로 답변을 시작하고 이유를 짧게 적으세요."""

        result = subprocess.run(["claude", "-p", prompt], capture_output=True, text=True)
        intent = "INCREMENTAL"
        if result.stdout and "INTENT: NEW" in result.stdout.upper():
            intent = "NEW"
        print(f"🤖 AI 판단 결과: {intent}")
        return intent

    # ------------------------------------------------------------------
    # 태스크 파일 생성 (PLAN_LOCK 기반)
    # ------------------------------------------------------------------
    def write_tasks_from_plan(self, chapters, completed_chapters=None):
        """잠긴 계획(chapters)을 기반으로 TASKS.md 생성"""
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
    # 챕터 실행 — Workspace 상태 주입 + 검증 강화
    # ------------------------------------------------------------------
    def execute_chapter(self, chapter_num, chapter_info, retry_count=0):
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

        # 2. 이전 챕터 결과물 주입
        workspace_state = self.get_workspace_manifest()

        # 3. 프롬프트
        lean_prompt = f"""{static_context}

{workspace_state}

# CURRENT GOAL: Chapter {chapter_num} - {chapter_name}
당신은 위 가이드라인을 완벽히 숙지한 시니어 개발자입니다.
현재 `workspace`에서 다음 작업을 수행하세요.

[TASK]
{tasks}

[DETAILED DESCRIPTION]
{description}

[EXPECTED FILES TO CREATE/MODIFY]
{', '.join(expected_files) if expected_files else '빌드 검증만 수행'}

[INSTRUCTION]
- 모든 작업은 `workspace` 폴더 내에서 이루어져야 합니다.
- REQUIREMENTS.md에 '파일 매니페스트' 섹션이 있다면 명시된 파일 경로를 정확히 따르세요.
- 위 CURRENT WORKSPACE STATE에 나열된 기존 파일과 일관성을 유지하세요 (import 경로, 패키지명, 클래스명 등).
- 기존 파일을 수정할 때는 원래 구조를 유지하면서 필요한 부분만 변경하세요.
- 작업이 끝나면 어떤 파일이 어떻게 변경되었는지 요약하고 반드시 'CHAPTER COMPLETE'라고 명시하세요.
"""
        retry_tag = f" (재시도 {retry_count}/{self.MAX_RETRIES})" if retry_count > 0 else ""
        print(f"🚀 [Chapter {chapter_num}] 실행 중: {chapter_name}{retry_tag}")

        process = subprocess.Popen(
            ["claude", "--dangerously-skip-permissions", "-p", lean_prompt],
            cwd=self.base_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        full_output = []
        for line in process.stdout:
            print(line, end="")
            full_output.append(line)
        process.wait()
        output_text = "".join(full_output)

        # 검증 1: CHAPTER COMPLETE 확인
        if "CHAPTER COMPLETE" not in output_text.upper():
            print(f"⚠️ [Chapter {chapter_num}] 'CHAPTER COMPLETE' 미감지")
            if retry_count < self.MAX_RETRIES:
                print(f"🔄 재시도합니다... ({retry_count + 1}/{self.MAX_RETRIES})")
                return self.execute_chapter(chapter_num, chapter_info, retry_count + 1)
            else:
                print(f"❌ [Chapter {chapter_num}] 최대 재시도 초과. 건너뜁니다.")
                return None

        # 검증 2: 필수 파일 존재 확인
        missing = self._check_expected_files(expected_files)
        if missing:
            print(f"⚠️ [Chapter {chapter_num}] 필수 파일 누락: {missing}")
            if retry_count < self.MAX_RETRIES:
                print(f"🔄 누락 파일 생성을 위해 재시도합니다... ({retry_count + 1}/{self.MAX_RETRIES})")
                return self.execute_chapter(chapter_num, chapter_info, retry_count + 1)
            else:
                print(f"❌ [Chapter {chapter_num}] 최대 재시도 초과. 현재 상태로 계속합니다.")

        return output_text

    def _check_expected_files(self, expected_files):
        """expected_files 중 workspace 내에 존재하지 않는 파일 목록 반환"""
        missing = []
        for rel_path in expected_files:
            found = False
            # 직접 경로
            if os.path.exists(os.path.join(self.workspace_dir, rel_path)):
                found = True
            # basename으로 검색 (프로젝트 하위 디렉토리 대응)
            if not found:
                for root, dirs, files in os.walk(self.workspace_dir):
                    dirs[:] = [d for d in dirs if d not in ("target", ".osgi-plugins")]
                    if os.path.basename(rel_path) in files:
                        found = True
                        break
            if not found:
                missing.append(rel_path)
        return missing

    # ------------------------------------------------------------------
    # 로그
    # ------------------------------------------------------------------
    def log_progress(self, chapter_num, chapter_name, output):
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

        with open(self.log_file, "a", encoding="utf-8") as log:
            log.write(f"\n### ✅ [Chapter {chapter_num}] {chapter_name} ({now})\n- {summary}\n")

    def _get_recently_modified_files(self, minutes=5):
        cutoff = datetime.datetime.now().timestamp() - (minutes * 60)
        recent = []
        for root, dirs, files in os.walk(self.workspace_dir):
            dirs[:] = [d for d in dirs if d not in ("target", ".osgi-plugins")]
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
    # 메인 실행 루프
    # ------------------------------------------------------------------
    def run(self):
        curr_hash = self.get_file_hash(self.spec_file)
        info = {}
        if os.path.exists(self.info_file):
            with open(self.info_file, "r") as f:
                info = json.load(f)

        old_hash = info.get("req_hash")
        locked_plan = self.load_locked_plan()

        # ── Case 1: 신규 프로젝트 (해시 없음) ──
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

        # ── Case 2: REQUIREMENTS.md 변경됨 ──
        elif old_hash != curr_hash:
            intent = self.analyze_intent()
            if intent == "NEW":
                self.archive_current()
                # Lock 파일도 삭제
                if os.path.exists(self.plan_lock_file):
                    os.remove(self.plan_lock_file)

                chapters = self.generate_plan_from_requirements()
                if not chapters:
                    print("❌ 계획 생성 실패. 종료합니다.")
                    return
                self.save_locked_plan(chapters, curr_hash)
                self.write_tasks_from_plan(chapters)
            else:
                # INCREMENTAL: 기존 완료 상태 보존, Lock 갱신
                completed_chapters = set()
                if os.path.exists(self.task_file):
                    with open(self.task_file, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.startswith("- [x]"):
                                m = re.search(r"\*\*Chapter (\d+):", line)
                                if m:
                                    completed_chapters.add(int(m.group(1)))

                # Lock 삭제 후 새 계획 생성
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

        # ── Case 3: 변경 없음 — Lock된 계획으로 미완료 챕터 실행 ──
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
            output = self.execute_chapter(c_num, chapter_info)
            if output:
                self.update_status(c_num)
                self.log_progress(c_num, chapter_info["chapter"], output)
                print(f"✅ [Chapter {c_num}] 완료: {chapter_info['chapter']}")
            else:
                print(f"⚠️ [Chapter {c_num}] 실행 중 오류 발생. 중단합니다.")
                break

        print("\n🏁 하네스 실행 완료")


if __name__ == "__main__":
    harness = SmartOrchestrator()
    harness.run()

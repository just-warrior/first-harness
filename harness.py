import subprocess
import os
import json
import re
import datetime
import hashlib
import shutil

class SmartOrchestrator:
    """ 설계 변경 감지 및 신규/증분 작업을 자동 판별하는 지능형 하네스 """

    def __init__(self):
        self.base_dir = os.getcwd()
        self.workspace_dir = os.path.join(self.base_dir, "workspace")
        self.status_dir = os.path.join(self.base_dir, ".status")
        self.archive_root = os.path.join(self.base_dir, "archive")
        
        self.spec_file = os.path.join(self.base_dir, "docs/REQUIREMENTS.md")
        self.task_file = os.path.join(self.status_dir, "TASKS.md")
        self.log_file = os.path.join(self.status_dir, "SESSION_CONTEXT.md")
        self.info_file = os.path.join(self.status_dir, "project_info.json")
        self.skill_file = os.path.join(self.base_dir, ".claude/SKILLS.md")
        
        # 필수 디렉토리 생성
        for d in [self.workspace_dir, self.status_dir, self.archive_root]:
            if not os.path.exists(d): os.makedirs(d)

    def get_file_hash(self, path):
        if not os.path.exists(path): return None
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    def archive_current(self):
        """ 현재 워크스페이스와 상태를 아카이브로 이동하고 초기화 """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = os.path.join(self.archive_root, timestamp)
        os.makedirs(archive_path)
        
        print(f"📦 [Archive] 기존 프로젝트 백업 중: {archive_path}")
        
        # 파일 이동 (workspace 및 .status 내의 핵심 파일들)
        if os.path.exists(self.workspace_dir):
            shutil.move(self.workspace_dir, os.path.join(archive_path, "workspace"))
            os.makedirs(self.workspace_dir) # 다시 생성
            
        # .status 파일들은 복사 후 삭제 (현재 프로세스가 점유 중일 수 있음)
        status_backup = os.path.join(archive_path, ".status")
        os.makedirs(status_backup)
        for f in os.listdir(self.status_dir):
            if f != "project_info.json": # 정보 파일 제외
                shutil.move(os.path.join(self.status_dir, f), os.path.join(status_backup, f))

    def analyze_intent(self):
        """ Claude에게 설계 변경의 의도를 물어봅니다 (NEW vs INCREMENTAL) """
        print("🔍 설계 변경 감지! AI가 의도를 분석 중입니다...")
        
        prompt = f"""
설계서(REQUIREMENTS.md)가 변경되었습니다. 현재 워크스페이스의 코드와 비교하여 다음 중 하나로 판단하세요.

1. NEW: 완전히 다른 새로운 플러그인 프로젝트를 시작함.
2. INCREMENTAL: 기존 플러그인에 새로운 기능을 추가하거나 기존 로직을 수정함.

반드시 'INTENT: [NEW/INCREMENTAL]' 형식으로 답변을 시작하고 이유를 짧게 적으세요.
"""
        result = subprocess.run(["claude", "-p", prompt], capture_output=True, text=True)
        intent = "INCREMENTAL"
        if "INTENT: NEW" in result.stdout.upper():
            intent = "NEW"
        
        print(f"🤖 AI 판단 결과: {intent}")
        return intent

    def plan_tasks(self, mode="NEW"):
        """ 로드맵 수립 (신규 또는 증분 업데이트) """
        with open(self.spec_file, "r", encoding="utf-8") as f:
            spec = f.read()
            
        existing_tasks = ""
        if mode == "INCREMENTAL" and os.path.exists(self.task_file):
            with open(self.task_file, "r", encoding="utf-8") as f:
                existing_tasks = f.read()

        prompt = f"""
당신은 시니어 아틀라시안 개발자입니다. 설계서를 분석하여 작업을 JSON 리스트로 쪼개주세요.
[Mode] {mode} (NEW: 초기화 후 생성, INCREMENTAL: 기존 작업에 추가/수정)

[기존 작업 현황]
{existing_tasks if existing_tasks else "없음"}

[최신 설계서]
{spec}

결과는 반드시 JSON list 형식으로만 답변하세요. (키: chapter, task, description)
INCREMENTAL 모드인 경우, 이미 완료된 챕터 번호 이후부터 새로운 작업을 추가하거나 필요한 경우 기존 작업을 수정하세요.
"""
        result = subprocess.run(["claude", "-p", prompt], capture_output=True, text=True)
        match = re.search(r'\[\s*\{.*\}\s*\]', result.stdout, re.DOTALL)
        if not match: return False

        tasks = json.loads(match.group())
        with open(self.task_file, "w", encoding="utf-8") as f:
            f.write("# Project Task List\n\n")
            for i, t in enumerate(tasks):
                # 기존에 완료된 항목인지 대략적으로 판단 (단순 구현)
                status = "[ ]"
                if mode == "INCREMENTAL" and f"**Chapter {i+1}:" in existing_tasks and "[x]" in existing_tasks.split(f"**Chapter {i+1}:")[1].split("\n")[0]:
                    status = "[x]"
                
                f.write(f"- {status} **Chapter {i+1}: {t['chapter']}** - {t['task']}\n")
                f.write(f"  - *Description*: {t['description']}\n")
        return True

    def execute_task(self, chapter, task, description):
        lean_prompt = f"""
[GOAL] Chapter {chapter}: {task}
[DETAIL] {description}
[INSTRUCTION] `{self.skill_file}`을 읽고 표준을 준수하여 `workspace`에서 작업을 수행하세요.
"""
        print(f"🚀 [Chapter {chapter}] 실행 중: {task}")
        process = subprocess.Popen(
            ["claude", "--dangerously-skip-permissions", "-p", lean_prompt],
            cwd=self.base_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        
        full_output = []
        for line in process.stdout:
            print(line, end="")
            full_output.append(line)
        process.wait()
        return "".join(full_output)

    def log_progress(self, chapter, task, output):
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        summary = "작업 완료"
        files_match = re.findall(r"(?:Created|Updated|Modified) file:?\s*([^\s\n`]+)", output)
        if files_match:
            summary = f"변경 파일: {', '.join(list(set(files_match))[:5])}"

        with open(self.log_file, "a", encoding="utf-8") as log:
            log.write(f"\n### ✅ [Chapter {chapter}] {task} ({now})\n- {summary}\n")

    def update_status(self, chapter_num):
        with open(self.task_file, "r", encoding="utf-8") as f: lines = f.readlines()
        with open(self.task_file, "w", encoding="utf-8") as f:
            for line in lines:
                if f"**Chapter {chapter_num}:" in line: f.write(line.replace("[ ]", "[x]"))
                else: f.write(line)

    def run(self):
        curr_hash = self.get_file_hash(self.spec_file)
        info = {}
        if os.path.exists(self.info_file):
            with open(self.info_file, "r") as f: info = json.load(f)
        
        old_hash = info.get("req_hash")
        
        if not old_hash:
            print("🆕 신규 프로젝트 설계를 시작합니다...")
            if self.plan_tasks("NEW"):
                info["req_hash"] = curr_hash
                with open(self.info_file, "w") as f: json.dump(info, f)
        elif old_hash != curr_hash:
            intent = self.analyze_intent()
            if intent == "NEW":
                self.archive_current()
                self.plan_tasks("NEW")
            else:
                self.plan_tasks("INCREMENTAL")
            info["req_hash"] = curr_hash
            with open(self.info_file, "w") as f: json.dump(info, f)

        # 작업 루프
        with open(self.task_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("- [ ]"):
                    match = re.search(r"\*\*Chapter (\d+): (.*?)\*\* - (.*)", line)
                    if match:
                        c_num, c_name, t_detail = match.groups()
                        output = self.execute_task(c_num, c_name, t_detail)
                        if output:
                            self.update_status(c_num)
                            self.log_progress(c_num, c_name, output)
                        else: break

if __name__ == "__main__":
    harness = SmartOrchestrator()
    harness.run()

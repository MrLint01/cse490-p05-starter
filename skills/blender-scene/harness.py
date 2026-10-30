import glob
import json
import os
import re
import requests
from dotenv import load_dotenv
import subprocess
import sys

load_dotenv()
GATEWAY_URL = os.getenv("LITELLM_BASE_URL")
GATEWAY_KEY = os.getenv("LITELLM_API_KEY")

SYSTEM_PROMPT = """You can use these tools in the project:
- read_file: {"command": "read_file", "path": "untangle/README.md"}
- write_file: {"command": "write_file", "path": "hello.py", "content": "print('hi')"}
- execute_file: {"command": "execute_file", "path": "hello.py", "args": ["--name", "world"]}

When you use a tool, reply with only the JSON object and nothing else. For all other replies, answer in plain text. Do not wrap plain text in JSON."""

TOOL_FIELDS = {
    "read_file": {"path": str},
    "write_file": {"path": str, "content": str},
    "execute_file": {"path": str, "args": list},
}

HOOK_ALWAYS_ALLOWED_WRITES = {"PLAN.md", "profile.json"}

def parse_tool_request(reply):
    # Return the parsed request if the reply is a valid tool command, else None.
    try:
        data = json.loads(reply)
    except json.JSONDecodeError:
        return None

    if not isinstance(data, dict):
        return None
    command = data.get("command")
    if not isinstance(command, str) or command not in TOOL_FIELDS:
        return None
    for name, kind in TOOL_FIELDS[command].items():
        if not isinstance(data.get(name), kind):
            return None
    if command == "execute_file" and not all(isinstance(a, str) for a in data["args"]):
        return None
    return data

def call_model(context):
    messages = context
    
    response = requests.post(
        f"{GATEWAY_URL}/v1/chat/completions",
        headers={"Authorization": f"Bearer {GATEWAY_KEY}"},
                json={"model": "external/haiku-5-5", "messages": messages, "max_tokens": 8192},
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    choice = data["choices"][0]
    message = choice["message"]

    print("finish_reason:", choice.get("finish_reason"))
    print("content:", repr(message.get("content")))
    print("tool_calls:", message.get("tool_calls"))
    print("refusal:", message.get("refusal"))

    if choice.get("finish_reason") == "length":
        print("error: response was truncated (finish_reason=length), so it was not run or saved.")
        return None

    return message["content"]

# def call_model(context):
#     return "placeholder reply"

def parse_read_file(reply):
    # Return the parsed request if the reply is a valid read_file command, else None.
    try:
        data = json.loads(reply)
    except json.JSONDecodeError:
        return None

    if not isinstance(data, dict):
        return None
    if data.get("command") != "read_file":
        return None
    if not isinstance(data.get("path"), str):
        return None
    return data

def read_project_file(path):
    # Read a file relative to the harness folder. Return the contents or an error message.
    root = os.path.dirname(os.path.abspath(__file__))
    full = os.path.realpath(os.path.join(root, path))
    if os.path.commonpath([root, full]) != root:
        return f"error: {path} is outside the project folder"
    try:
        with open(full, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"error: file not found: {path}"
    except (OSError, UnicodeDecodeError) as e:
        return f"error: could not read {path}: {e}"

def confirm(description):
    # Show what will happen and wait for the student to type "yes".
    print(description)
    answer = input("Type yes to continue: ")
    return answer.strip() == "yes"

def resolve_project_path(path):
    # Return the absolute path inside the harness folder, or None if it escapes.
    root = os.path.dirname(os.path.abspath(__file__))
    full = os.path.realpath(os.path.join(root, path))
    if os.path.commonpath([root, full]) != root:
        return None
    return full

def write_project_file(path, content):
    # Write content to a file inside the project after the student confirms.
    full = resolve_project_path(path)
    if full is None:
        return f"error: {path} is outside the project folder"

    print(f"write_file {path} with this content:\n---\n{content}\n---")
    if not confirm(f"Write {len(content)} characters to {path}?"):
        return f"cancelled: write to {path} was not approved"

    try:
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as e:
        return f"error: could not write {path}: {e}"
    return f"wrote {len(content)} characters to {path}"

def execute_file(path, args=None):
    # Run a Python file inside the project after the student confirms. Return stdout, stderr, and exit code.
    full = resolve_project_path(path)
    if full is None:
        return f"error: {path} is outside the project folder"

    args = args or []
    command = [sys.executable, full] + [str(a) for a in args]
    print(f"execute_file: {' '.join(command)}")
    if not confirm(f"Run {path} with arguments {args}?"):
        return f"cancelled: execution of {path} was not approved"

    try:
        result = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return f"error: {path} timed out after 60 seconds"
    except OSError as e:
        return f"error: could not run {path}: {e}"

    return (
        f"exit code: {result.returncode}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )

def run_check():
    # Run the command stored in CHECK from the project root, if CHECK exists. Return a report or None.
    root = os.path.dirname(os.path.abspath(__file__))
    check_path = os.path.join(root, "CHECK")
    if not os.path.isfile(check_path):
        return None
    try:
        with open(check_path, encoding="utf-8") as f:
            command = f.read().strip()
    except OSError as e:
        return f"error: could not read CHECK: {e}"
    if not command:
        return None

    try:
        result = subprocess.run(
            command, shell=True, cwd=root, capture_output=True, text=True, timeout=60
        )
    except subprocess.TimeoutExpired:
        return f"error: CHECK command timed out after 60 seconds: {command}"
    except OSError as e:
        return f"error: could not run CHECK command: {e}"

    return (
        f"CHECK command: {command}\n"
        f"exit code: {result.returncode}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )

def load_system_prompt():
    # Read systemprompt.md from the harness folder. Called once at startup.
    root = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(root, "systemprompt.md"), encoding="utf-8") as f:
        return f.read()

def load_skill_summaries():
    # Read name and description lines from each skills/*/SKILL.md front matter. Called once at startup.
    root = os.path.dirname(os.path.abspath(__file__))
    summaries = []
    for path in sorted(glob.glob(os.path.join(root, "skills", "*", "SKILL.md"))):
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
        if not lines or lines[0].strip() != "---":
            continue
        for line in lines[1:]:
            if line.strip() == "---":
                break
            if line.startswith(("name:", "description:")):
                summaries.append(line.strip())
    return "\n".join(summaries)

def load_skills():
    # Read each skills/*/SKILL.md once at startup. Keep name, description, and full text.
    root = os.path.dirname(os.path.abspath(__file__))
    skills = []
    for path in sorted(glob.glob(os.path.join(root, "skills", "*", "SKILL.md"))):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        meta = {}
        lines = text.splitlines()
        if lines and lines[0].strip() == "---":
            for line in lines[1:]:
                if line.strip() == "---":
                    break
                if line.startswith(("name:", "description:")):
                    key, _, value = line.partition(":")
                    meta[key.strip()] = value.strip()
        skills.append({
            "name": meta.get("name", ""),
            "description": meta.get("description", ""),
            "text": text,
        })
    return skills

CODE_WORDS = {"code", "program", "software", "app", "script", "module"}
CODE_VERBS = {"fix", "add", "change", "build", "improve"}
SOURCE_FILE = re.compile(r"\b[\w.-]+\.(?:py|js|jsx|ts|tsx|java|c|cpp|h|hpp|cs|go|rs|rb|php|swift|kt|scala|sh|sql)\b")

def matching_skills(user, skills):
    # Return the skills whose description matches this user message. Used for this turn only.
    text = user.casefold()
    words = set(re.findall(r"[a-z0-9]+", text))
    starts_plan = re.match(r"^\s*/plan(\s|$)", text) is not None
    asks_code = bool(words & CODE_VERBS) and (
        bool(words & CODE_WORDS) or SOURCE_FILE.search(text) is not None
    )
    asks_pass = re.search(r"\bmake\b.*\bpass\b.*\b(?:score|tests?)\b", text) is not None

    matches = []
    for skill in skills:
        desc = skill["description"].casefold()
        if "starts with /plan" in desc and starts_plan:
            matches.append(skill)
        elif "asks to fix, add, change, build or improve code" in desc and asks_code:
            matches.append(skill)
        elif "make a program pass its score or tests" in desc and asks_pass:
            matches.append(skill)
    return matches

def run_tool(request):
    # Route a validated tool request to its function and return the result string.
    command = request["command"]
    if command == "read_file":
        return read_project_file(request["path"])
    if command == "write_file":
        return write_project_file(request["path"], request["content"])
    if command == "execute_file":
        return execute_file(request["path"], request["args"])
    return f"error: unknown command {command}"

skills = load_skills()
skill_index = "\n".join(
    f"Skill: {s['name']}\nDescription: {s['description']}"
    for s in skills
)
context = [{"role": "system", "content": load_system_prompt() + "\n\n" + skill_index + "\n\n" + SYSTEM_PROMPT}]

while True:
    user = input(">>> ")
    approved = (user == "approve")
    context.append({"role": "user", "content": user})

    # Matching skill text is sent with this turn's model calls only. It is not saved in context.
    turn_context = [
        {"role": "system", "content": f"Skill: {s['name']}\n{s['text']}"}
        for s in matching_skills(user, skills)
    ]

    while True:
        reply = call_model(context + turn_context)
        if reply is None:
            break
        context.append({"role": "assistant", "content": reply})
        request = parse_tool_request(reply)
        if request is None:
            if reply.lstrip().startswith("{"):
                context.append({
                    "role": "user",
                    "content": (
                        "Invalid tool request. Return exactly one JSON object "
                        "matching a supported tool, with no surrounding text."
                    ),
                })
                continue
            print(reply)
            break
        print(f"[{request['command']} request: {request['path']}]")

        if (
            request["command"] == "write_file"
            and not approved
            and os.path.normpath(request["path"]) not in HOOK_ALWAYS_ALLOWED_WRITES
        ):
            print("[write_file blocked: waiting for approve]")
            context.append({"role": "user", "content": "harness: waiting for approve"})
            break

        result = run_tool(request)
        context.append({
            "role": "user",
            "content": f"Result of {request['command']} {request['path']}:\n{result}",
        })

        if request["command"] == "write_file":
            check_report = run_check()
            if check_report is not None:
                print(check_report)
                context.append({"role": "user", "content": check_report})

import asyncio
import glob
import json
import os
import re
import requests
from dotenv import load_dotenv
import subprocess
import sys

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

load_dotenv()
PURPLE_BASE_URL = os.getenv(
    "PURPLE_BASE_URL", "https://apim-n1ai-usw2-065882797.azure-api.net/openai/v1"
).rstrip("/")
PURPLE_API_KEY = os.getenv("PURPLE_API_KEY")
PURPLE_MODEL = os.getenv("PURPLE_MODEL", "DeepSeek-V4.1-Flash")

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

def parse_tool_request(reply, blender_tools=None):
    # Return the parsed request if the reply is a valid tool command, else None.
    try:
        data = json.loads(reply)
    except json.JSONDecodeError:
        return None

    if not isinstance(data, dict):
        return None
    command = data.get("command")
    if not isinstance(command, str):
        return None
    if command in (blender_tools or {}):
        return data if isinstance(data.get("arguments"), dict) else None
    if command not in TOOL_FIELDS:
        return None
    for name, kind in TOOL_FIELDS[command].items():
        if not isinstance(data.get(name), kind):
            return None
    if command == "execute_file" and not all(isinstance(a, str) for a in data["args"]):
        return None
    return data

def call_model(context):
    if not PURPLE_API_KEY:
        raise RuntimeError("Set PURPLE_API_KEY in your environment before running the harness.")
    messages = context

    response = requests.post(
        f"{PURPLE_BASE_URL}/chat/completions",
        headers={"api-key": PURPLE_API_KEY},
        json={"model": PURPLE_MODEL, "messages": messages, "max_tokens": 8192},
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

    asks_scene = bool(words & {"plan", "add", "build", "create", "make", "animate", "render", "import", "show"}) and bool(
        words & {"blender", "scene", "3d", "animation", "torus", "cube", "sphere", "cylinder", "cone", "mesh", "camera", "lamp"}
    )

    matches = []
    for skill in skills:
        desc = skill["description"].casefold()
        if skill["name"] == "blender-scene" and asks_scene:
            matches.append(skill)
        elif "starts with /plan" in desc and starts_plan:
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

TRACE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trace.jsonl")


def append_trace(entry):
    with open(TRACE_PATH, "a", encoding="utf-8") as trace:
        trace.write(json.dumps(entry) + "\n")


def tool_result_message(command, target, result, result_data):
    prefix = f"Result of {command} {target}:\n"
    parts = result_data.get("content", []) if isinstance(result_data, dict) else []
    if not any(part.get("type") == "image" for part in parts):
        return {"role": "user", "content": prefix + result}

    # The harness uses user messages for tool replies; these accept image_url parts.
    content = [{"type": "text", "text": prefix}]
    if result_data.get("is_error"):
        content.append({"type": "text", "text": "Tool reported an error."})
    for part in parts:
        if part.get("type") == "image":
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{part['mime_type']};base64,{part['data']}"},
            })
        elif part.get("type") == "text":
            content.append({"type": "text", "text": part["text"]})
        else:
            content.append({"type": "text", "text": json.dumps(part)})
    return {"role": "user", "content": content}


async def run_chat(session, blender_tools):
    # Keep the existing JSON-command protocol for both local and MCP tools.
    blender_prompt = (
        'Blender tools use {"command": "tool_name", "arguments": {...}}. '
        'Available Blender tools (name, description, input_schema):\n'
        + json.dumps(list(blender_tools.values()))
    )
    skills = load_skills()
    skill_index = "\n".join(
        f"Skill: {s['name']}\nDescription: {s['description']}"
        for s in skills
    )
    context = [{"role": "system", "content": load_system_prompt() + "\n\n" + skill_index + "\n\n" + SYSTEM_PROMPT + "\n\n" + blender_prompt}]

    while True:
        user = await asyncio.to_thread(input, ">>> ")
        approved = (user == "approve")
        context.append({"role": "user", "content": user})

        # Matching skill text is sent with this turn's model calls only. It is not saved in context.
        turn_context = [
            {"role": "system", "content": f"Skill: {s['name']}\n{s['text']}"}
            for s in matching_skills(user, skills)
        ]

        while True:
            reply = await asyncio.to_thread(call_model, context + turn_context)
            if reply is None:
                break
            context.append({"role": "assistant", "content": reply})
            request = parse_tool_request(reply, blender_tools)
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
            target = request.get("path", request.get("arguments", {}))
            print(f"[{request['command']} request: {target}]")

            if (
                request["command"] == "write_file"
                and not approved
                and os.path.normpath(request["path"]) not in HOOK_ALWAYS_ALLOWED_WRITES
            ):
                print("[write_file blocked: waiting for approve]")
                context.append({"role": "user", "content": "harness: waiting for approve"})
                break

            append_trace({"type": "tool_call", "command": request["command"], "request": request})
            if request["command"] in blender_tools:
                try:
                    reply_result = await session.call_tool(request["command"], request["arguments"])
                    result_data = reply_result.model_dump(mode="json")
                    result = json.dumps(result_data)
                except Exception as e:
                    result_data = {"is_error": True, "error": str(e)}
                    result = json.dumps(result_data)
            else:
                result = await asyncio.to_thread(run_tool, request)
                result_data = result
            append_trace({"type": "tool_result", "command": request["command"], "result": result_data})
            context.append(tool_result_message(request["command"], target, result, result_data))

            if request["command"] == "write_file":
                check_report = await asyncio.to_thread(run_check)
                if check_report is not None:
                    print(check_report)
                    context.append({"role": "user", "content": check_report})


async def main():
    server = StdioServerParameters(
        command="uvx",
        args=["blender-mcp==1.9.1"],
        env={
            **os.environ,
            "BLENDER_MCP_SAFE_MODE": "1",
            "BLENDER_MCP_DISABLE_TELEMETRY": "true",
            "BLENDER_HOST": "localhost",
            "BLENDER_PORT": "9876",
        },
    )
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            blender_tools = {}
            cursor = None
            while True:
                listing = await session.list_tools(
                    params=types.PaginatedRequestParams(cursor=cursor) if cursor else None
                )
                for tool in listing.tools:
                    blender_tools[tool.name] = {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.input_schema,
                    }
                cursor = listing.next_cursor
                if not cursor:
                    break
            with open(TRACE_PATH, "w", encoding="utf-8") as trace:
                trace.write(json.dumps({"type": "blender_tools", "tools": list(blender_tools)}) + "\n")
            await run_chat(session, blender_tools)


if __name__ == "__main__":
    asyncio.run(main())

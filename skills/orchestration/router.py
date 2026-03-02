#!/usr/bin/env python3
"""
router.py - OpenPango real router for managing sub-agents.
Provides basic multi-agent session management, task appending, and execution via Gemini CLI.
"""
import argparse
import json
import uuid
import sys
import time
import subprocess
import threading
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
SKILLS_DIR = BASE_DIR / "skills"
STORAGE_FILE = Path(__file__).parent / "openpango_storage.json"
OUTPUTS_DIR = Path(__file__).parent / "outputs"

VALID_AGENTS = {"Researcher", "Planner", "Coder", "Designer"}

def load_storage():
    if STORAGE_FILE.exists():
        try:
            with open(STORAGE_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"sessions": {}}
    return {"sessions": {}}

def save_storage(data):
    with open(STORAGE_FILE, "w") as f:
        json.dump(data, f, indent=4)

def spawn_session(agent_type):
    if agent_type not in VALID_AGENTS:
        print(f"Error: Invalid agent type '{agent_type}'.", file=sys.stderr)
        sys.exit(1)
        
    session_id = str(uuid.uuid4())
    data = load_storage()
    data["sessions"][session_id] = {
        "agent_type": agent_type,
        "status": "idle",
        "task": None,
        "output_file": None,
        "created_at": time.time(),
        "started_at": None,
        "completed_at": None
    }
    save_storage(data)
    print(json.dumps({"session_id": session_id, "agent_type": agent_type, "status": "idle"}))

def execute_agent_task(session_id, agent_type, task_payload):
    data = load_storage()
    
    agent_dir = SKILLS_DIR / agent_type.lower()
    identity_file = agent_dir / "workspace/IDENTITY.md"
    soul_file = agent_dir / "workspace/SOUL.md"
    
    identity = identity_file.read_text() if identity_file.exists() else f"You are the {agent_type} agent."
    soul = soul_file.read_text() if soul_file.exists() else "Do your job."
    
    prompt = f"""
{identity}

{soul}

=== TASK ===
{task_payload}
===========

Execute this task strictly as your assigned role. You are running in a headless environment. Output your final response clearly.
"""
    
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUTS_DIR / f"{agent_type}-{session_id[:8]}.txt"
    
    # We use gemini CLI with --prompt to run the agent headlessly
    cmd = ["gemini", "--prompt", prompt]
    if agent_type == "Coder":
        # Coder needs yolo mode to actually write files!
        cmd.append("--yolo")
        cmd.append("--approval-mode")
        cmd.append("yolo")
        
    try:
        result = subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=True, text=True)
        with open(output_path, "w") as f:
            f.write(result.stdout)
            if result.stderr:
                f.write("\n\n--- STDERR ---\n")
                f.write(result.stderr)
    except Exception as e:
        with open(output_path, "w") as f:
            f.write(f"Failed to execute gemini CLI: {str(e)}")

    # Update state
    data = load_storage()
    if session_id in data["sessions"]:
        data["sessions"][session_id]["status"] = "completed"
        data["sessions"][session_id]["completed_at"] = time.time()
        data["sessions"][session_id]["output_file"] = str(output_path)
        save_storage(data)

def append_task(session_id, task_payload):
    data = load_storage()
    if session_id not in data["sessions"]:
        print(f"Error: Session '{session_id}' not found.", file=sys.stderr)
        sys.exit(1)
        
    session = data["sessions"][session_id]
    if session["status"] == "running":
        print(f"Error: Session '{session_id}' is already running.", file=sys.stderr)
        sys.exit(1)
        
    session["task"] = task_payload
    session["status"] = "running"
    session["started_at"] = time.time()
    save_storage(data)
    
    # Start execution in a background thread so 'append' returns immediately
    thread = threading.Thread(target=execute_agent_task, args=(session_id, session["agent_type"], task_payload))
    thread.daemon = True
    thread.start()
    
    print(json.dumps({"session_id": session_id, "message": "Task appended and execution started.", "status": "running"}))

def check_status(session_id):
    data = load_storage()
    if session_id not in data["sessions"]:
        print(f"Error: Session '{session_id}' not found.", file=sys.stderr)
        sys.exit(1)
    session = data["sessions"][session_id]
    print(json.dumps({"session_id": session_id, "status": session["status"]}))

def retrieve_output(session_id):
    data = load_storage()
    if session_id not in data["sessions"]:
        print(f"Error: Session '{session_id}' not found.", file=sys.stderr)
        sys.exit(1)
        
    session = data["sessions"][session_id]
    if session["status"] != "completed":
        print(f"Error: Session not completed. Status: {session['status']}", file=sys.stderr)
        sys.exit(1)
        
    output_path = Path(session["output_file"])
    if output_path.exists():
        print(json.dumps({
            "session_id": session_id,
            "status": "completed",
            "output_file": str(output_path),
            "content": output_path.read_text()
        }))
    else:
        print(f"Error: Output file {output_path} missing.", file=sys.stderr)
        sys.exit(1)

def wait_for_completion(session_id, timeout):
    deadline = time.monotonic() + timeout
    print(f"Waiting for session {session_id} to complete...", file=sys.stderr)
    while time.monotonic() < deadline:
        data = load_storage()
        if session_id not in data["sessions"]:
            print(f"Error: Session '{session_id}' not found.", file=sys.stderr)
            sys.exit(1)
        if data["sessions"][session_id]["status"] == "completed":
            print(f"Session {session_id} completed.", file=sys.stderr)
            retrieve_output(session_id)
            return
        time.sleep(2.0)
    print(f"TIMEOUT: Session did not complete within {timeout}s.", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    spawn_parser = subparsers.add_parser("spawn")
    spawn_parser.add_argument("agent_type")
    append_parser = subparsers.add_parser("append")
    append_parser.add_argument("session_id")
    append_parser.add_argument("task_payload")
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("session_id")
    output_parser = subparsers.add_parser("output")
    output_parser.add_argument("session_id")
    wait_parser = subparsers.add_parser("wait")
    wait_parser.add_argument("session_id")
    wait_parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()

    if args.command == "spawn": spawn_session(args.agent_type)
    elif args.command == "append": append_task(args.session_id, args.task_payload)
    elif args.command == "status": check_status(args.session_id)
    elif args.command == "output": retrieve_output(args.session_id)
    elif args.command == "wait": wait_for_completion(args.session_id, args.timeout)

#!/usr/bin/env python3
"""
skill_updater.py - Self-Improvement Skill Updater for OpenClaw.
Allows agents to safely propose updates to their own skills by creating a new
Git branch and committing the changes, requiring manual operator approval to merge.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

def run_cmd(cmd, check=True):
    try:
        result = subprocess.run(cmd, check=check, text=True, capture_output=True)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout.strip(), e.stderr.strip()

def main():
    parser = argparse.ArgumentParser(description="Safely update agent skills via Git branches.")
    parser.add_argument("--target-file", required=True, help="The path to the file to update (e.g., orchestration/SKILL.md).")
    parser.add_argument("--content-file", required=True, help="Path to a temporary file containing the new content.")
    parser.add_argument("--message", required=True, help="Commit message explaining the improvement.")
    
    args = parser.parse_args()

    # 1. Validate paths
    current_dir = Path.cwd().resolve()
    target_path = Path(args.target_file).resolve()
    content_path = Path(args.content_file).resolve()

    if not target_path.is_relative_to(current_dir):
        print(json.dumps({"status": "error", "message": "Target file must be within the current project directory."}))
        sys.exit(1)

    if not content_path.exists():
        print(json.dumps({"status": "error", "message": f"Content file not found: {args.content_file}"}))
        sys.exit(1)

    # 2. Check Git status
    code, stdout, stderr = run_cmd(["git", "rev-parse", "--is-inside-work-tree"], check=False)
    if code != 0:
        print(json.dumps({"status": "error", "message": "Not a git repository. Cannot safely propose changes without version control."}))
        sys.exit(1)

    # Ensure working tree is clean to avoid branch switching issues
    code, stdout, stderr = run_cmd(["git", "status", "--porcelain"])
    if stdout:
        print(json.dumps({"status": "error", "message": "Git working directory is not clean. Please commit or stash changes before proposing agent updates."}))
        sys.exit(1)

    # 3. Create branch and apply changes
    original_branch_code, original_branch, _ = run_cmd(["git", "branch", "--show-current"])
    if not original_branch:
        original_branch = "main" # Fallback if detached HEAD, though risky.

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    branch_name = f"agent-updates-{timestamp}"

    # Checkout new branch
    code, _, err = run_cmd(["git", "checkout", "-b", branch_name])
    if code != 0:
        print(json.dumps({"status": "error", "message": f"Failed to create branch: {err}"}))
        sys.exit(1)

    try:
        # Overwrite the file
        new_content = content_path.read_text(encoding="utf-8")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(new_content, encoding="utf-8")

        # Commit
        run_cmd(["git", "add", str(target_path)])
        code, out, err = run_cmd(["git", "commit", "-m", args.message])
        
        if code != 0:
            raise Exception(f"Commit failed: {err}")

    except Exception as e:
        # Rollback on error
        run_cmd(["git", "checkout", original_branch])
        run_cmd(["git", "branch", "-D", branch_name])
        print(json.dumps({"status": "error", "message": str(e)}))
        sys.exit(1)

    # 4. Switch back to original branch
    run_cmd(["git", "checkout", original_branch])

    print(json.dumps({
        "status": "success",
        "action": "propose_update",
        "target_file": str(target_path.relative_to(current_dir)),
        "branch": branch_name,
        "message": f"Successfully proposed update. Please manually review and merge the '{branch_name}' branch."
    }))

if __name__ == "__main__":
    main()

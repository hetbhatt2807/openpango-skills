#!/usr/bin/env python3
"""
memory_manager.py - OpenClaw Beads Architecture Memory Manager.
Uses an event-sourced JSONL file as truth and a local SQLite database as a read-cache.
"""
import argparse
import json
import sqlite3
import uuid
import sys
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / ".beads_data"
JSONL_FILE = DATA_DIR / "events.jsonl"
DB_FILE = DATA_DIR / "read_cache.sqlite"


def init_db(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            status TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dependencies (
            task_id TEXT,
            depends_on_id TEXT,
            PRIMARY KEY (task_id, depends_on_id),
            FOREIGN KEY (task_id) REFERENCES tasks(id),
            FOREIGN KEY (depends_on_id) REFERENCES tasks(id)
        )
    ''')
    conn.commit()


def sync_read_cache():
    """Rebuild SQLite read-cache from the JSONL event log."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    init_db(conn)
    cursor = conn.cursor()

    cursor.execute('DELETE FROM dependencies')
    cursor.execute('DELETE FROM tasks')

    if JSONL_FILE.exists():
        with open(JSONL_FILE, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                    etype = event.get('type')

                    if etype == 'create_task':
                        cursor.execute('''
                            INSERT INTO tasks (id, title, description, status, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (event['id'], event['title'], event['description'], 'todo', event['timestamp'], event['timestamp']))
                    elif etype == 'update_status':
                        cursor.execute('''
                            UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?
                        ''', (event['status'], event['timestamp'], event['id']))
                    elif etype == 'link_dependency':
                        cursor.execute('''
                            INSERT OR IGNORE INTO dependencies (task_id, depends_on_id)
                            VALUES (?, ?)
                        ''', (event['task_id'], event['depends_on_id']))
                except Exception as e:
                    print(f"Error parsing event line: {e}", file=sys.stderr)

    conn.commit()
    return conn


def append_event(event):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    event['timestamp'] = datetime.now(timezone.utc).isoformat()
    with open(JSONL_FILE, 'a') as f:
        f.write(json.dumps(event) + "\n")


def _task_exists(conn, task_id):
    """Check if a task exists in the read cache."""
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM tasks WHERE id = ?', (task_id,))
    return cursor.fetchone() is not None


def create_task(title, description):
    task_id = str(uuid.uuid4())
    event = {
        'type': 'create_task',
        'id': task_id,
        'title': title,
        'description': description
    }
    append_event(event)
    conn = sync_read_cache()
    conn.close()
    print(json.dumps({"task_id": task_id, "status": "todo", "message": "Task created successfully."}))


def update_status(task_id, status):
    conn = sync_read_cache()
    if not _task_exists(conn, task_id):
        conn.close()
        print(f"Error: Task '{task_id}' not found.", file=sys.stderr)
        sys.exit(1)
    conn.close()

    event = {
        'type': 'update_status',
        'id': task_id,
        'status': status
    }
    append_event(event)
    conn = sync_read_cache()
    conn.close()
    print(json.dumps({"task_id": task_id, "status": status, "message": "Task status updated."}))


def link_dependency(task_id, depends_on_id):
    conn = sync_read_cache()
    missing = []
    if not _task_exists(conn, task_id):
        missing.append(task_id)
    if not _task_exists(conn, depends_on_id):
        missing.append(depends_on_id)
    conn.close()

    if missing:
        print(f"Error: Task(s) not found: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    if task_id == depends_on_id:
        print("Error: A task cannot depend on itself.", file=sys.stderr)
        sys.exit(1)

    event = {
        'type': 'link_dependency',
        'task_id': task_id,
        'depends_on_id': depends_on_id
    }
    append_event(event)
    conn = sync_read_cache()
    conn.close()
    print(json.dumps({
        "task_id": task_id,
        "depends_on_id": depends_on_id,
        "message": f"Task {task_id} now depends on {depends_on_id}."
    }))


def get_ready_tasks():
    conn = sync_read_cache()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, title, description, status
        FROM tasks t
        WHERE status = 'todo'
        AND NOT EXISTS (
            SELECT 1 FROM dependencies d
            JOIN tasks parent ON d.depends_on_id = parent.id
            WHERE d.task_id = t.id AND parent.status != 'done'
        )
    ''')
    rows = cursor.fetchall()
    conn.close()
    tasks = [{"id": r[0], "title": r[1], "description": r[2], "status": r[3]} for r in rows]
    print(json.dumps({"ready_tasks": tasks, "count": len(tasks)}))


def list_tasks():
    """List all tasks with their status and dependency info."""
    conn = sync_read_cache()
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, description, status, created_at, updated_at FROM tasks ORDER BY created_at')
    rows = cursor.fetchall()

    tasks = []
    for r in rows:
        # Fetch dependencies for this task
        cursor.execute('SELECT depends_on_id FROM dependencies WHERE task_id = ?', (r[0],))
        deps = [d[0] for d in cursor.fetchall()]
        # Fetch tasks that depend on this one
        cursor.execute('SELECT task_id FROM dependencies WHERE depends_on_id = ?', (r[0],))
        blocks = [b[0] for b in cursor.fetchall()]
        tasks.append({
            "id": r[0], "title": r[1], "description": r[2],
            "status": r[3], "created_at": r[4], "updated_at": r[5],
            "depends_on": deps, "blocks": blocks
        })
    conn.close()
    print(json.dumps({"tasks": tasks, "count": len(tasks)}, indent=2))


def get_task(task_id):
    """Get full details for a single task."""
    conn = sync_read_cache()
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, description, status, created_at, updated_at FROM tasks WHERE id = ?', (task_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        print(f"Error: Task '{task_id}' not found.", file=sys.stderr)
        sys.exit(1)

    cursor.execute('SELECT depends_on_id FROM dependencies WHERE task_id = ?', (task_id,))
    deps = [d[0] for d in cursor.fetchall()]
    cursor.execute('SELECT task_id FROM dependencies WHERE depends_on_id = ?', (task_id,))
    blocks = [b[0] for b in cursor.fetchall()]
    conn.close()

    print(json.dumps({
        "id": row[0], "title": row[1], "description": row[2],
        "status": row[3], "created_at": row[4], "updated_at": row[5],
        "depends_on": deps, "blocks": blocks
    }, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Memory Manager - Beads Architecture")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_create = subparsers.add_parser('create_task', help="Create a new task")
    parser_create.add_argument('title', type=str, help="Task title")
    parser_create.add_argument('description', type=str, help="Task description")

    parser_update = subparsers.add_parser('update_status', help="Update task status")
    parser_update.add_argument('task_id', type=str, help="UUID of the task")
    parser_update.add_argument('status', type=str, choices=['todo', 'in_progress', 'blocked', 'done'], help="New status")

    parser_link = subparsers.add_parser('link_dependency', help="Link task to dependency")
    parser_link.add_argument('task_id', type=str, help="UUID of the blocked task")
    parser_link.add_argument('depends_on_id', type=str, help="UUID of the blocking task")

    subparsers.add_parser('get_ready_tasks', help="Get tasks ready to work on (todo + unblocked)")

    subparsers.add_parser('list_tasks', help="List all tasks with status and dependencies")

    parser_get = subparsers.add_parser('get_task', help="Get full details for a single task")
    parser_get.add_argument('task_id', type=str, help="UUID of the task")

    args = parser.parse_args()

    if args.command == 'create_task':
        create_task(args.title, args.description)
    elif args.command == 'update_status':
        update_status(args.task_id, args.status)
    elif args.command == 'link_dependency':
        link_dependency(args.task_id, args.depends_on_id)
    elif args.command == 'get_ready_tasks':
        get_ready_tasks()
    elif args.command == 'list_tasks':
        list_tasks()
    elif args.command == 'get_task':
        get_task(args.task_id)


if __name__ == '__main__':
    main()

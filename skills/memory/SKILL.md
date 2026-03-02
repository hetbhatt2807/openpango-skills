---
name: memory
description: "A distributed, Git-backed graph issue tracker using a local SQLite read-cache."
user-invocable: true
metadata: {"openclaw":{"emoji":"🧠","skillKey":"openpango-memory"}}
---

## Cross-Skill Integration

This skill integrates with the Openpango ecosystem:
- **Orchestration**: Tracks tasks using this memory skill.
- **Self-Improvement**: Can create tasks for tracking new learnings.
- **Persistent State**: Shared workspace files at `~/.openclaw/workspace/` (AGENTS.md, SOUL.md, TOOLS.md, .learnings/).
- **Real-time Coordination**: OpenClaw sessions API (sessions_send, sessions_spawn) referenced in orchestration SKILL.md.

# Beads Memory Architecture

You are interacting with the "Beads" memory architecture. This is a robust, event-sourced memory system designed for long-horizon task management in an OpenClaw AI environment.

## The Paradigm

- **Event-Sourced (Git-backed JSONL)**: Every state change (creating a task, updating status, linking dependencies) is appended as an immutable event in a JSONL file. This allows for seamless Git synchronization and conflict resolution without database locking.
- **SQLite Read-Cache**: To perform fast relational queries (like finding unblocked tasks), the system rebuilds a local SQLite database from the JSONL event log on each operation. You don't query the JSONL file manually.

## Workflow & Guidelines

1. **Break Down Complexity**: When given a large objective, break it down into atomic tasks using `create_task`.
2. **Map Dependencies**: Use `link_dependency` to model the graph. If Task A cannot be started before Task B, link them (`task_id`=A, `depends_on_id`=B).
3. **Find Work**: Always use `get_ready_tasks` to identify the next actionable items. A task is only "ready" if its status is `todo` and all of its dependencies are marked as `done`.
4. **Inspect State**: Use `list_tasks` to see everything, or `get_task {id}` for a single task's full details including what it depends on and what it blocks.
5. **Update State**: As work progresses, accurately reflect reality using `update_status`.
   - `in_progress`: When a sub-agent is actively working on it.
   - `blocked`: When an external factor prevents progress.
   - `done`: When work is complete and verified. (This will automatically unblock dependent tasks!).

## Example Workflow

All commands return JSON for easy parsing.

```bash
# 1. Create the foundational task
python3 skills/memory/memory_manager.py create_task "Setup DB" "Install and configure PostgreSQL"
# Output: {"task_id": "abc-123...", "status": "todo", "message": "Task created successfully."}

# 2. Create the dependent task
python3 skills/memory/memory_manager.py create_task "Build API" "Create REST endpoints"
# Output: {"task_id": "def-456...", "status": "todo", "message": "Task created successfully."}

# 3. Link them: API depends on DB (use the task_ids from above)
python3 skills/memory/memory_manager.py link_dependency def-456... abc-123...

# 4. Check ready tasks (Only "Setup DB" will appear — "Build API" is blocked)
python3 skills/memory/memory_manager.py get_ready_tasks

# 5. Finish DB task
python3 skills/memory/memory_manager.py update_status abc-123... done

# 6. Check ready tasks again ("Build API" is now unblocked and ready!)
python3 skills/memory/memory_manager.py get_ready_tasks

# 7. See the full picture
python3 skills/memory/memory_manager.py list_tasks
```

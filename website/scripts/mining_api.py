#!/usr/bin/env python3
"""
mining_api.py — JSON bridge for the mining pool dashboard.

Reads real data from the mining pool SQLite database and outputs JSON.
Used by the Next.js API route to serve data to the frontend.

Usage:
  python3 mining_api.py stats       # Pool stats + miner list
  python3 mining_api.py activity    # Recent task log entries
  python3 mining_api.py register    # Register seed miners (first-run)
"""

import json
import sys
import os

# Add skills to path so we can import the mining pool
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from skills.mining.mining_pool import MiningPool


def get_stats():
    pool = MiningPool()
    stats = pool.get_pool_stats()

    # Get all miners (any status)
    registry = pool.registry
    with __import__('sqlite3').connect(registry.db_path) as conn:
        conn.row_factory = __import__('sqlite3').Row
        miners = [dict(r) for r in conn.execute(
            "SELECT miner_id, name, model, price_per_request, status, "
            "trust_score, total_tasks, successful_tasks, total_earned, "
            "avg_response_ms, registered_at, last_seen FROM miners ORDER BY total_earned DESC"
        ).fetchall()]

    return {
        "stats": stats,
        "miners": miners,
    }


def get_activity():
    pool = MiningPool()
    import sqlite3
    with sqlite3.connect(pool.db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT t.task_id, t.miner_id, t.model, t.status, t.cost, "
            "t.response_ms, t.created_at, t.completed_at, m.name as miner_name "
            "FROM task_log t LEFT JOIN miners m ON t.miner_id = m.miner_id "
            "ORDER BY t.created_at DESC LIMIT 20"
        ).fetchall()
    return {"activity": [dict(r) for r in rows]}


def seed_miners():
    """Register some initial miners so the dashboard isn't empty."""
    pool = MiningPool()
    
    seeds = [
        ("gpt4-heavy", "GPT-4", "sk-demo-gpt4-key-000", 0.02),
        ("claude-fast", "Claude 3.5", "sk-demo-claude-key-000", 0.015),
        ("llama-local", "Llama 3", "sk-demo-llama-key-000", 0.005),
        ("mixtral-gpu", "Mixtral 8x7B", "sk-demo-mixtral-key-000", 0.008),
    ]

    registered = []
    for name, model, key, price in seeds:
        try:
            result = pool.register_miner(name=name, model=model, api_key=key, price_per_request=price)
            registered.append(result)
        except Exception as e:
            registered.append({"name": name, "error": str(e)})

    return {"registered": registered}


def run_demo_task():
    """Submit a demo task to generate real activity."""
    pool = MiningPool()
    try:
        result = pool.submit_task(
            prompt="Summarize the concept of autonomous agent economies in one paragraph.",
            strategy="cheapest",
            renter_id="dashboard-demo"
        )
        return {"task_result": result}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"

    if cmd == "stats":
        print(json.dumps(get_stats(), default=str))
    elif cmd == "activity":
        print(json.dumps(get_activity(), default=str))
    elif cmd == "register":
        print(json.dumps(seed_miners(), default=str))
    elif cmd == "task":
        print(json.dumps(run_demo_task(), default=str))
    else:
        print(json.dumps({"error": f"Unknown command: {cmd}"}))

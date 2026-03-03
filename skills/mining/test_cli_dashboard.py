"""
Tests for OpenPango CLI Dashboard — data loading and formatting helpers.
Run with:  pytest skills/mining/test_cli_dashboard.py -v
"""

from __future__ import annotations

import sqlite3
import datetime
import pytest

# Import module under test
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from skills.mining.cli_dashboard import (
    # DB helpers
    get_connection,
    _bootstrap_schema,
    # Data loaders
    load_miners,
    load_agents,
    load_recent_tasks,
    load_earnings_summary,
    load_earnings_series,
    load_system_health,
    insert_test_task,
    # Formatters
    status_color,
    colored_status,
    fmt_uptime,
    fmt_hashrate,
    health_bar_color,
    spark_line,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def db(tmp_path):
    """In-memory-style SQLite DB via a temp file."""
    db_path = str(tmp_path / "test_pool.db")
    conn = get_connection(db_path)
    yield conn
    conn.close()


def _seed_miner(conn, id="m1", name="TestMiner", status="online",
                hashrate=1500.0, uptime_sec=3600, wallet="0xABC"):
    conn.execute(
        "INSERT OR REPLACE INTO miners (id, name, status, hashrate, uptime_sec, wallet) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (id, name, status, hashrate, uptime_sec, wallet),
    )
    conn.commit()


def _seed_agent(conn, id="a1", miner_id="m1", name="Agent-1", status="running",
                task_count=5):
    conn.execute(
        "INSERT OR REPLACE INTO agents (id, miner_id, name, status, task_count) "
        "VALUES (?, ?, ?, ?, ?)",
        (id, miner_id, name, status, task_count),
    )
    conn.commit()


def _seed_task(conn, id="t1", agent_id="a1", description="do work",
               status="done", reward=0.05):
    now = datetime.datetime.utcnow().isoformat()
    conn.execute(
        "INSERT OR REPLACE INTO tasks (id, agent_id, description, status, created_at, reward) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (id, agent_id, description, status, now, reward),
    )
    conn.commit()


def _seed_earnings(conn, amounts: list[float], miner_id="m1"):
    now = datetime.datetime.utcnow().isoformat()
    for amt in amounts:
        conn.execute(
            "INSERT INTO earnings (miner_id, amount, recorded_at) VALUES (?, ?, ?)",
            (miner_id, amt, now),
        )
    conn.commit()


def _seed_health(conn, cpu=42.0, mem=55.0, disk=30.0, net_in=100.0, net_out=50.0):
    now = datetime.datetime.utcnow().isoformat()
    conn.execute(
        "INSERT INTO system_health (cpu_pct, mem_pct, disk_pct, net_in_kb, net_out_kb, recorded_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (cpu, mem, disk, net_in, net_out, now),
    )
    conn.commit()


# ── Schema tests ──────────────────────────────────────────────────────────────

class TestBootstrapSchema:
    def test_tables_created(self, db):
        tables = {
            row[0] for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        for expected in ("miners", "agents", "tasks", "earnings", "system_health"):
            assert expected in tables

    def test_idempotent(self, db):
        """Calling _bootstrap_schema twice must not raise."""
        _bootstrap_schema(db)
        _bootstrap_schema(db)


# ── Miner loading ─────────────────────────────────────────────────────────────

class TestLoadMiners:
    def test_empty(self, db):
        assert load_miners(db) == []

    def test_single_miner(self, db):
        _seed_miner(db, id="m1", name="Alpha", status="online")
        miners = load_miners(db)
        assert len(miners) == 1
        assert miners[0]["name"] == "Alpha"
        assert miners[0]["status"] == "online"

    def test_multiple_miners_sorted(self, db):
        _seed_miner(db, id="m2", name="Beta",  status="offline")
        _seed_miner(db, id="m1", name="Alpha", status="online")
        miners = load_miners(db)
        # online comes before offline
        assert miners[0]["status"] == "online"

    def test_fields_present(self, db):
        _seed_miner(db, hashrate=2500.0, uptime_sec=7200, wallet="0xDEAD")
        m = load_miners(db)[0]
        assert m["hashrate"] == 2500.0
        assert m["uptime_sec"] == 7200
        assert m["wallet"] == "0xDEAD"


# ── Agent loading ─────────────────────────────────────────────────────────────

class TestLoadAgents:
    def test_empty(self, db):
        assert load_agents(db) == []

    def test_agent_with_miner_join(self, db):
        _seed_miner(db, id="m1", name="MyMiner")
        _seed_agent(db, id="a1", miner_id="m1", name="Agent-X")
        agents = load_agents(db)
        assert len(agents) == 1
        assert agents[0]["name"] == "Agent-X"
        assert agents[0]["miner_name"] == "MyMiner"

    def test_agent_without_miner(self, db):
        _seed_agent(db, id="a1", miner_id=None, name="Orphan")
        agents = load_agents(db)
        assert agents[0]["miner_name"] is None


# ── Task loading ──────────────────────────────────────────────────────────────

class TestLoadRecentTasks:
    def test_empty(self, db):
        assert load_recent_tasks(db) == []

    def test_task_fields(self, db):
        _seed_task(db, id="t1", description="mine blocks", status="done", reward=0.1)
        tasks = load_recent_tasks(db)
        assert len(tasks) == 1
        t = tasks[0]
        assert t["description"] == "mine blocks"
        assert t["status"] == "done"
        assert abs(t["reward"] - 0.1) < 1e-9

    def test_limit_respected(self, db):
        for i in range(10):
            _seed_task(db, id=f"t{i}", description=f"task {i}")
        assert len(load_recent_tasks(db, limit=5)) == 5

    def test_order_newest_first(self, db):
        import time as _time
        for i in range(3):
            _time.sleep(0.01)
            _seed_task(db, id=f"tx{i}", description=f"task {i}")
        tasks = load_recent_tasks(db)
        # Most recently inserted is first
        assert tasks[0]["id"] == "tx2"


# ── Earnings ──────────────────────────────────────────────────────────────────

class TestLoadEarnings:
    def test_summary_empty(self, db):
        s = load_earnings_summary(db)
        assert s["total"] == 0

    def test_summary_total(self, db):
        _seed_earnings(db, [1.0, 2.5, 0.75])
        s = load_earnings_summary(db)
        assert abs(s["total"] - 4.25) < 1e-9

    def test_series_empty(self, db):
        assert load_earnings_series(db) == []

    def test_series_values(self, db):
        _seed_earnings(db, [0.1, 0.2, 0.3])
        series = load_earnings_series(db)
        assert len(series) == 3
        for v in series:
            assert isinstance(v, float)

    def test_series_limit(self, db):
        _seed_earnings(db, [float(i) for i in range(30)])
        assert len(load_earnings_series(db, limit=10)) == 10


# ── System health ─────────────────────────────────────────────────────────────

class TestLoadSystemHealth:
    def test_empty(self, db):
        assert load_system_health(db) is None

    def test_returns_latest(self, db):
        _seed_health(db, cpu=10.0)
        _seed_health(db, cpu=90.0)
        h = load_system_health(db)
        # Row with higher id (inserted later) should be returned
        assert h["cpu_pct"] == 90.0

    def test_all_fields(self, db):
        _seed_health(db, cpu=20.0, mem=40.0, disk=60.0, net_in=200.0, net_out=100.0)
        h = load_system_health(db)
        assert h["cpu_pct"]   == 20.0
        assert h["mem_pct"]   == 40.0
        assert h["disk_pct"]  == 60.0
        assert h["net_in_kb"] == 200.0
        assert h["net_out_kb"]== 100.0


# ── insert_test_task ──────────────────────────────────────────────────────────

class TestInsertTestTask:
    def test_returns_id(self, db):
        task_id = insert_test_task(db)
        assert task_id.startswith("test-")

    def test_persisted(self, db):
        task_id = insert_test_task(db)
        tasks = load_recent_tasks(db)
        ids = [t["id"] for t in tasks]
        assert task_id in ids

    def test_default_status_pending(self, db):
        task_id = insert_test_task(db)
        tasks = load_recent_tasks(db)
        task = next(t for t in tasks if t["id"] == task_id)
        assert task["status"] == "pending"

    def test_unique_ids(self, db):
        import time as _time
        ids = set()
        for _ in range(5):
            _time.sleep(0.01)
            ids.add(insert_test_task(db))
        assert len(ids) == 5


# ── Formatting helpers ────────────────────────────────────────────────────────

class TestStatusColor:
    @pytest.mark.parametrize("status,expected", [
        ("online",  "green"),
        ("running", "green"),
        ("done",    "green"),
        ("idle",    "yellow"),
        ("pending", "yellow"),
        ("offline", "dim"),
        ("error",   "red"),
        ("failed",  "red"),
        ("ONLINE",  "green"),   # case-insensitive
        ("unknown", "white"),
    ])
    def test_mapping(self, status, expected):
        assert status_color(status) == expected


class TestColoredStatus:
    def test_returns_rich_text(self, db):
        from rich.text import Text
        result = colored_status("online")
        assert isinstance(result, Text)

    def test_contains_status_text(self, db):
        result = colored_status("running")
        assert "RUNNING" in result.plain

    def test_offline_dim(self, db):
        result = colored_status("offline")
        assert "OFFLINE" in result.plain


class TestFmtUptime:
    @pytest.mark.parametrize("seconds,expected", [
        (0,     "0s"),
        (45,    "45s"),
        (60,    "1m 0s"),
        (90,    "1m 30s"),
        (3600,  "1h 0m"),
        (3661,  "1h 1m"),
        (86400, "24h 0m"),
    ])
    def test_format(self, seconds, expected):
        assert fmt_uptime(seconds) == expected


class TestFmtHashrate:
    @pytest.mark.parametrize("h,expected_contains", [
        (500.0,       "H/s"),
        (1500.0,      "KH/s"),
        (2_000_000.0, "MH/s"),
    ])
    def test_unit(self, h, expected_contains):
        assert expected_contains in fmt_hashrate(h)

    def test_mh_value(self):
        result = fmt_hashrate(2_500_000.0)
        assert "2.50" in result

    def test_kh_value(self):
        result = fmt_hashrate(3_000.0)
        assert "3.00" in result


class TestHealthBarColor:
    @pytest.mark.parametrize("pct,expected", [
        (0.0,   "green"),
        (59.9,  "green"),
        (60.0,  "yellow"),
        (84.9,  "yellow"),
        (85.0,  "red"),
        (100.0, "red"),
    ])
    def test_thresholds(self, pct, expected):
        assert health_bar_color(pct) == expected


class TestSparkLine:
    def test_empty(self):
        assert spark_line([]) == "no data"

    def test_length_matches(self):
        series = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = spark_line(series)
        assert len(result) == len(series)

    def test_all_same(self):
        result = spark_line([5.0, 5.0, 5.0])
        # all max → all '█'
        assert result == "███"

    def test_all_zero(self):
        result = spark_line([0.0, 0.0, 0.0])
        # all zero with max=0 → all space (index 0 of bars)
        assert result == "   "

    def test_only_block_chars(self):
        valid = set(" ▁▂▃▄▅▆▇█")
        for ch in spark_line([1.0, 3.0, 5.0, 2.0, 8.0]):
            assert ch in valid


# ── get_connection ────────────────────────────────────────────────────────────

class TestGetConnection:
    def test_creates_file(self, tmp_path):
        db_path = str(tmp_path / "sub" / "pool.db")
        conn = get_connection(db_path)
        conn.close()
        assert os.path.exists(db_path)

    def test_row_factory(self, tmp_path):
        db_path = str(tmp_path / "pool.db")
        conn = get_connection(db_path)
        # Row factory should allow dict access
        conn.execute("INSERT INTO miners (id, name) VALUES ('x', 'Test')")
        conn.commit()
        row = conn.execute("SELECT * FROM miners WHERE id='x'").fetchone()
        assert row["name"] == "Test"
        conn.close()

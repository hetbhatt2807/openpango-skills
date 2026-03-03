"""
OpenPango CLI Dashboard — Textual TUI
======================================
Live terminal dashboard for monitoring OpenPango mining pool operations.

Keyboard shortcuts:
  q  — Quit
  r  — Force refresh
  m  — Miner detail view
  t  — Submit test task
"""

from __future__ import annotations

import sqlite3
import os
import time
import datetime
from pathlib import Path
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.timer import Timer
from textual.widgets import Footer, Header, Label, Static
from rich.text import Text
from rich.table import Table

# ── DB helpers ───────────────────────────────────────────────────────────────

DEFAULT_DB_PATH = os.environ.get(
    "OPENPANGO_DB", str(Path.home() / ".openpango" / "mining_pool.db")
)


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Return a SQLite connection (creates DB + schema if absent)."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    _bootstrap_schema(conn)
    return conn


def _bootstrap_schema(conn: sqlite3.Connection) -> None:
    """Create tables if they don't already exist."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS miners (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            status      TEXT NOT NULL DEFAULT 'offline',
            hashrate    REAL DEFAULT 0.0,
            uptime_sec  INTEGER DEFAULT 0,
            last_seen   TEXT,
            wallet      TEXT
        );

        CREATE TABLE IF NOT EXISTS agents (
            id          TEXT PRIMARY KEY,
            miner_id    TEXT,
            name        TEXT NOT NULL,
            status      TEXT NOT NULL DEFAULT 'idle',
            task_count  INTEGER DEFAULT 0,
            started_at  TEXT
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id          TEXT PRIMARY KEY,
            agent_id    TEXT,
            description TEXT,
            status      TEXT NOT NULL DEFAULT 'pending',
            created_at  TEXT,
            finished_at TEXT,
            reward      REAL DEFAULT 0.0
        );

        CREATE TABLE IF NOT EXISTS earnings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            miner_id    TEXT,
            amount      REAL NOT NULL,
            currency    TEXT DEFAULT 'USDC',
            recorded_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS system_health (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            cpu_pct     REAL,
            mem_pct     REAL,
            disk_pct    REAL,
            net_in_kb   REAL,
            net_out_kb  REAL,
            recorded_at TEXT NOT NULL
        );
        """
    )
    conn.commit()


# ── Data-loading functions ───────────────────────────────────────────────────

def load_miners(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM miners ORDER BY status DESC, name ASC"
    ).fetchall()
    return [dict(r) for r in rows]


def load_agents(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT a.*, m.name AS miner_name FROM agents a "
        "LEFT JOIN miners m ON a.miner_id = m.id "
        "ORDER BY a.status DESC, a.name ASC"
    ).fetchall()
    return [dict(r) for r in rows]


def load_recent_tasks(conn: sqlite3.Connection, limit: int = 50) -> list[dict]:
    rows = conn.execute(
        "SELECT t.*, a.name AS agent_name FROM tasks t "
        "LEFT JOIN agents a ON t.agent_id = a.id "
        "ORDER BY t.created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def load_earnings_summary(conn: sqlite3.Connection) -> dict:
    row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total, "
        "       COALESCE(MAX(recorded_at), 'N/A') AS last_at "
        "FROM earnings"
    ).fetchone()
    return dict(row)


def load_earnings_series(conn: sqlite3.Connection, limit: int = 20) -> list[float]:
    rows = conn.execute(
        "SELECT amount FROM earnings ORDER BY recorded_at DESC LIMIT ?", (limit,)
    ).fetchall()
    values = [r["amount"] for r in rows]
    values.reverse()
    return values


def load_system_health(conn: sqlite3.Connection) -> dict | None:
    row = conn.execute(
        "SELECT * FROM system_health ORDER BY recorded_at DESC LIMIT 1"
    ).fetchone()
    return dict(row) if row else None


def insert_test_task(conn: sqlite3.Connection) -> str:
    """Insert a dummy test task and return its id."""
    task_id = f"test-{int(time.time())}"
    now = datetime.datetime.utcnow().isoformat()
    conn.execute(
        "INSERT INTO tasks (id, description, status, created_at, reward) "
        "VALUES (?, ?, ?, ?, ?)",
        (task_id, "CLI test task", "pending", now, 0.01),
    )
    conn.commit()
    return task_id


# ── Formatting helpers ───────────────────────────────────────────────────────

def status_color(status: str) -> str:
    mapping = {
        "online":  "green",
        "running": "green",
        "done":    "green",
        "idle":    "yellow",
        "pending": "yellow",
        "offline": "dim",
        "error":   "red",
        "failed":  "red",
    }
    return mapping.get(status.lower(), "white")


def colored_status(status: str) -> Text:
    color = status_color(status)
    dot = {"green": "●", "yellow": "◉", "red": "✖", "dim": "○"}.get(color, "·")
    t = Text()
    t.append(f"{dot} ", style=color)
    t.append(status.upper(), style=f"bold {color}")
    return t


def fmt_uptime(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}h {m}m"


def fmt_hashrate(h: float) -> str:
    if h >= 1_000_000:
        return f"{h / 1_000_000:.2f} MH/s"
    if h >= 1_000:
        return f"{h / 1_000:.2f} KH/s"
    return f"{h:.2f} H/s"


def health_bar_color(pct: float) -> str:
    if pct < 60:
        return "green"
    if pct < 85:
        return "yellow"
    return "red"


def spark_line(series: list[float]) -> str:
    """Render a unicode sparkline from a list of floats."""
    bars = " ▁▂▃▄▅▆▇█"
    if not series:
        return "no data"
    mx = max(series) or 1
    return "".join(bars[min(int(v / mx * 8), 8)] for v in series)


# ── Panels ───────────────────────────────────────────────────────────────────

class MinerStatusPanel(Static):
    """Shows active miners with hashrate, uptime, color-coded status."""

    DEFAULT_CSS = """
    MinerStatusPanel {
        height: 1fr;
        border: round $primary;
        padding: 0 1;
        overflow-y: auto;
    }
    """

    def __init__(self, conn: sqlite3.Connection, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.conn = conn

    def refresh_data(self) -> None:
        miners = load_miners(self.conn)
        table = Table(
            "ID", "Name", "Status", "Hashrate", "Uptime",
            show_header=True,
            header_style="bold cyan",
            expand=True,
            box=None,
        )
        for m in miners:
            table.add_row(
                m["id"][:8],
                m["name"],
                colored_status(m.get("status", "offline")),
                fmt_hashrate(m.get("hashrate") or 0),
                fmt_uptime(m.get("uptime_sec") or 0),
            )
        if not miners:
            table.add_row("—", "No miners registered", "", "", "")
        self.update(table)

    def on_mount(self) -> None:
        self.border_title = "⛏  Miner Status"
        self.refresh_data()


class TaskQueuePanel(Static):
    """Shows recent tasks with agent name, status, reward."""

    DEFAULT_CSS = """
    TaskQueuePanel {
        height: 1fr;
        border: round $accent;
        padding: 0 1;
        overflow-y: auto;
    }
    """

    def __init__(self, conn: sqlite3.Connection, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.conn = conn

    def refresh_data(self) -> None:
        tasks = load_recent_tasks(self.conn, limit=30)
        table = Table(
            "ID", "Agent", "Description", "Status", "Reward",
            show_header=True,
            header_style="bold magenta",
            expand=True,
            box=None,
        )
        for t in tasks:
            table.add_row(
                t["id"][:10],
                (t.get("agent_name") or "—")[:12],
                (t.get("description") or "")[:28],
                colored_status(t.get("status", "pending")),
                f"${t.get('reward', 0):.4f}",
            )
        if not tasks:
            table.add_row("—", "—", "No tasks yet", "", "")
        self.update(table)

    def on_mount(self) -> None:
        self.border_title = "📋  Task Queue"
        self.refresh_data()


class EarningsPanel(Static):
    """Shows total earnings + unicode sparkline history."""

    DEFAULT_CSS = """
    EarningsPanel {
        height: 1fr;
        border: round $success;
        padding: 0 1;
    }
    """

    def __init__(self, conn: sqlite3.Connection, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.conn = conn

    def refresh_data(self) -> None:
        summary = load_earnings_summary(self.conn)
        series = load_earnings_series(self.conn)
        total = summary.get("total", 0)
        last_at = summary.get("last_at", "N/A")

        content = Text()
        content.append("Total Earned\n", style="bold white")
        content.append(f"  ${total:.6f} USDC\n", style="bold green")
        content.append(f"  Last payment: {last_at}\n\n", style="dim")
        content.append("Earnings history:\n", style="bold cyan")
        content.append(f"  {spark_line(series)}\n", style="green")
        self.update(content)

    def on_mount(self) -> None:
        self.border_title = "💰  Earnings"
        self.refresh_data()


class SystemHealthPanel(Static):
    """Shows CPU / RAM / Disk / Network usage bars."""

    DEFAULT_CSS = """
    SystemHealthPanel {
        height: 1fr;
        border: round $warning;
        padding: 0 1;
    }
    """

    def __init__(self, conn: sqlite3.Connection, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.conn = conn

    def _bar(self, pct: float, width: int = 20) -> Text:
        filled = int(pct / 100 * width)
        color = health_bar_color(pct)
        t = Text()
        t.append("█" * filled, style=color)
        t.append("░" * (width - filled), style="dim")
        t.append(f" {pct:5.1f}%", style=f"bold {color}")
        return t

    def refresh_data(self) -> None:
        health = load_system_health(self.conn)
        if health is None:
            try:
                import psutil  # type: ignore
                health = {
                    "cpu_pct": psutil.cpu_percent(interval=0.1),
                    "mem_pct": psutil.virtual_memory().percent,
                    "disk_pct": psutil.disk_usage("/").percent,
                    "net_in_kb": 0.0,
                    "net_out_kb": 0.0,
                }
            except ImportError:
                health = {"cpu_pct": 0.0, "mem_pct": 0.0,
                          "disk_pct": 0.0, "net_in_kb": 0.0, "net_out_kb": 0.0}

        content = Text()
        content.append("CPU    ", style="bold white")
        content.append_text(self._bar(health.get("cpu_pct", 0)))
        content.append("\nRAM    ", style="bold white")
        content.append_text(self._bar(health.get("mem_pct", 0)))
        content.append("\nDisk   ", style="bold white")
        content.append_text(self._bar(health.get("disk_pct", 0)))
        content.append(
            f"\n\nNet ↓  {health.get('net_in_kb', 0):.1f} KB/s"
            f"   ↑  {health.get('net_out_kb', 0):.1f} KB/s",
            style="cyan",
        )
        self.update(content)

    def on_mount(self) -> None:
        self.border_title = "🖥  System Health"
        self.refresh_data()


# ── Miner detail modal ───────────────────────────────────────────────────────

class MinerDetailScreen(ModalScreen):
    """Full-detail modal for all registered miners."""

    DEFAULT_CSS = """
    MinerDetailScreen { align: center middle; }
    MinerDetailScreen > Container {
        width: 80;
        height: 26;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
        overflow-y: auto;
    }
    """

    BINDINGS = [Binding("escape,m", "dismiss", "Close")]

    def __init__(self, conn: sqlite3.Connection, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.conn = conn

    def compose(self) -> ComposeResult:
        with Container():
            yield Label("⛏  Miner Detail View  (press ESC to close)", id="modal-title")
            yield Static(id="detail-body")

    def on_mount(self) -> None:
        miners = load_miners(self.conn)
        agents = load_agents(self.conn)
        content = Text()
        for m in miners:
            content.append(f"\n  {m['name']} ({m['id'][:8]})\n", style="bold cyan")
            content.append("    Status:   ")
            content.append_text(colored_status(m.get("status", "offline")))
            content.append(f"\n    Hashrate: {fmt_hashrate(m.get('hashrate') or 0)}\n")
            content.append(f"    Uptime:   {fmt_uptime(m.get('uptime_sec') or 0)}\n")
            content.append(f"    Wallet:   {m.get('wallet') or 'N/A'}\n", style="dim")
            my_agents = [a for a in agents if a.get("miner_id") == m["id"]]
            if my_agents:
                content.append("    Agents:\n", style="bold")
                for a in my_agents:
                    style = "green" if a["status"] == "running" else "dim"
                    content.append(
                        f"      • {a['name']} — {a['status']} "
                        f"({a.get('task_count', 0)} tasks)\n",
                        style=style,
                    )
        if not miners:
            content.append("\n  No miners found in database.", style="dim")
        self.query_one("#detail-body", Static).update(content)


# ── Main App ─────────────────────────────────────────────────────────────────

class OpenPangoDashboard(App):
    """OpenPango CLI Dashboard — live TUI for mining pool monitoring."""

    TITLE = "OpenPango Mining Dashboard"
    SUB_TITLE = "q=quit  r=refresh  m=miners  t=test task"

    CSS = """
    Screen { layout: vertical; }
    #top-row    { layout: horizontal; height: 1fr; }
    #bottom-row { layout: horizontal; height: 1fr; }
    #status-bar { height: 1; background: $surface; color: $text-muted; padding: 0 1; }
    MinerStatusPanel  { width: 1fr; margin: 0 1 0 0; }
    TaskQueuePanel    { width: 1fr; }
    EarningsPanel     { width: 1fr; margin: 0 1 0 0; }
    SystemHealthPanel { width: 1fr; }
    """

    BINDINGS = [
        Binding("q", "quit",             "Quit"),
        Binding("r", "refresh",          "Refresh"),
        Binding("m", "miner_detail",     "Miner Detail"),
        Binding("t", "submit_test_task", "Submit Test Task"),
    ]

    _refresh_count: reactive[int] = reactive(0)

    def __init__(self, db_path: str = DEFAULT_DB_PATH, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.db_path = db_path
        self.conn = get_connection(db_path)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="top-row"):
            yield MinerStatusPanel(self.conn, id="miners")
            yield TaskQueuePanel(self.conn, id="tasks")
        with Container(id="bottom-row"):
            yield EarningsPanel(self.conn, id="earnings")
            yield SystemHealthPanel(self.conn, id="health")
        yield Static(id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        self._update_status("Dashboard started — auto-refresh every 5s")
        self._timer: Timer = self.set_interval(5, self._auto_refresh)

    # ── helpers ──

    def _update_status(self, msg: str) -> None:
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.query_one("#status-bar", Static).update(f"[{now}] {msg}")

    def _refresh_all(self) -> None:
        self.query_one("#miners",   MinerStatusPanel).refresh_data()
        self.query_one("#tasks",    TaskQueuePanel).refresh_data()
        self.query_one("#earnings", EarningsPanel).refresh_data()
        self.query_one("#health",   SystemHealthPanel).refresh_data()
        self._refresh_count += 1

    def _auto_refresh(self) -> None:
        self._refresh_all()
        self._update_status(f"Auto-refreshed (#{self._refresh_count})")

    # ── actions ──

    def action_refresh(self) -> None:
        self._refresh_all()
        self._update_status(f"Manual refresh (#{self._refresh_count})")

    def action_miner_detail(self) -> None:
        self.push_screen(MinerDetailScreen(self.conn))

    def action_submit_test_task(self) -> None:
        task_id = insert_test_task(self.conn)
        self.query_one("#tasks", TaskQueuePanel).refresh_data()
        self._update_status(f"Test task submitted: {task_id}")

    def action_quit(self) -> None:
        self.conn.close()
        self.exit()


# ── Entry-point ───────────────────────────────────────────────────────────────

def main(db_path: str = DEFAULT_DB_PATH) -> None:
    OpenPangoDashboard(db_path=db_path).run()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="OpenPango CLI Dashboard")
    parser.add_argument("--db", default=DEFAULT_DB_PATH,
                        help="Path to SQLite mining pool DB")
    args = parser.parse_args()
    main(db_path=args.db)

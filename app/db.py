# db.py
"""SQLite 数据库初始化与连接管理。"""
import sqlite3
import json
import os
from contextlib import contextmanager
from . import config


SCHEMA = """
CREATE TABLE IF NOT EXISTS sheets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS fields (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sheet_id    INTEGER NOT NULL,
    name        TEXT NOT NULL,
    type        TEXT NOT NULL DEFAULT 'text',  -- text / number / date / url / select
    sort_order  INTEGER NOT NULL DEFAULT 0,
    UNIQUE(sheet_id, name),
    FOREIGN KEY (sheet_id) REFERENCES sheets(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS rows (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sheet_id    INTEGER NOT NULL,
    data        TEXT NOT NULL,                  -- JSON: {字段名: 值}
    created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (sheet_id) REFERENCES sheets(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_rows_sheet      ON rows(sheet_id);
CREATE INDEX IF NOT EXISTS idx_rows_created    ON rows(created_at);
"""


# 初始 sheet 与字段
INITIAL_SHEETS = [
    {
        "name": "音舞热点",
        "fields": [
            {"name": "热点名称", "type": "text"},
            {"name": "日期", "type": "date"},
            {"name": "平台", "type": "select"},
            {"name": "点赞", "type": "number"},
            {"name": "相关视频数量", "type": "number"},
            {"name": "URL", "type": "url"},
        ],
    },
    {
        "name": "综艺热点",
        "fields": [
            {"name": "热点名称", "type": "text"},
            {"name": "日期", "type": "date"},
            {"name": "平台", "type": "select"},
            {"name": "点赞", "type": "number"},
            {"name": "相关视频数量", "type": "number"},
            {"name": "URL", "type": "url"},
        ],
    },
]


def _ensure_dir():
    d = os.path.dirname(config.DB_PATH)
    if d:
        os.makedirs(d, exist_ok=True)


@contextmanager
def get_conn():
    _ensure_dir()
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """初始化表结构 + 默认 sheet。"""
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        # 写入默认 sheet（如不存在）
        for idx, sh in enumerate(INITIAL_SHEETS):
            cur = conn.execute("SELECT id FROM sheets WHERE name = ?", (sh["name"],))
            row = cur.fetchone()
            if row:
                sheet_id = row["id"]
            else:
                cur = conn.execute(
                    "INSERT INTO sheets(name, sort_order) VALUES (?, ?)",
                    (sh["name"], idx),
                )
                sheet_id = cur.lastrowid
            for fi, f in enumerate(sh["fields"]):
                conn.execute(
                    "INSERT OR IGNORE INTO fields(sheet_id, name, type, sort_order) "
                    "VALUES (?, ?, ?, ?)",
                    (sheet_id, f["name"], f["type"], fi),
                )

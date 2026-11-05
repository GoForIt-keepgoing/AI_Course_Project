# -*- coding: utf-8 -*-
"""SQLite 存取层：连接、建表与常用查询。"""
from __future__ import annotations

import json
import os
import sqlite3

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(APP_DIR, "data")
DB_PATH = os.environ.get("AI4EN_DB_PATH") or os.path.join(DATA_DIR, "ai4en.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    grade TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('teacher', 'student', 'parent')),
    class_id INTEGER,
    child_id INTEGER
);
CREATE TABLE IF NOT EXISTS lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    grade TEXT NOT NULL,
    topic TEXT NOT NULL,
    vocab TEXT NOT NULL DEFAULT '[]',
    sentences TEXT NOT NULL DEFAULT '[]',
    duration INTEGER NOT NULL DEFAULT 40,
    notes TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'draft',
    source TEXT NOT NULL DEFAULT 'manual',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS plans (
    lesson_id INTEGER PRIMARY KEY,
    data TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'sample',
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS materials (
    lesson_id INTEGER NOT NULL,
    kind TEXT NOT NULL,
    data TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'sample',
    updated_at TEXT NOT NULL,
    PRIMARY KEY (lesson_id, kind)
);
CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER NOT NULL,
    kind TEXT NOT NULL,
    data TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'sample',
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS exercises (
    lesson_id INTEGER PRIMARY KEY,
    data TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'sample',
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER NOT NULL,
    class_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    instructions TEXT DEFAULT '',
    due_at TEXT DEFAULT '',
    allow_hints INTEGER NOT NULL DEFAULT 1,
    show_result TEXT NOT NULL DEFAULT 'immediately',
    status TEXT NOT NULL DEFAULT 'draft',
    snapshot TEXT NOT NULL DEFAULT '{}',
    student_count INTEGER NOT NULL DEFAULT 0,
    published_at TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'submitted',
    answers TEXT NOT NULL DEFAULT '{}',
    grading TEXT NOT NULL DEFAULT '{}',
    submitted_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (task_id, student_id)
);
CREATE TABLE IF NOT EXISTS revisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL,
    answers TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL,
    item_id TEXT NOT NULL,
    draft TEXT DEFAULT '',
    final TEXT DEFAULT '',
    level TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'draft',
    source TEXT NOT NULL DEFAULT 'rule',
    confirmed_at TEXT,
    UNIQUE (submission_id, item_id)
);
CREATE TABLE IF NOT EXISTS teaching_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER NOT NULL,
    task_id INTEGER,
    completed TEXT DEFAULT '',
    issues TEXT DEFAULT '',
    next_adjust TEXT DEFAULT '',
    source TEXT NOT NULL DEFAULT 'manual',
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER NOT NULL,
    task_id INTEGER,
    student_id INTEGER NOT NULL,
    kind TEXT NOT NULL DEFAULT 'independent',
    result TEXT NOT NULL DEFAULT '',
    note TEXT DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS dictations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER NOT NULL,
    words TEXT NOT NULL DEFAULT '[]',
    wrong TEXT NOT NULL DEFAULT '[]',
    note TEXT DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS gen_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER,
    kind TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT DEFAULT '',
    status TEXT NOT NULL,
    latency_ms INTEGER DEFAULT 0,
    error TEXT DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
"""


def connect():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init():
    conn = connect()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def query(sql, args=()):
    conn = connect()
    try:
        return [dict(r) for r in conn.execute(sql, args).fetchall()]
    finally:
        conn.close()


def query_one(sql, args=()):
    rows = query(sql, args)
    return rows[0] if rows else None


def execute(sql, args=()):
    conn = connect()
    try:
        cur = conn.execute(sql, args)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def loads(value, default=None):
    if not value:
        return default if default is not None else {}
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default if default is not None else {}


def dumps(value):
    return json.dumps(value, ensure_ascii=False)

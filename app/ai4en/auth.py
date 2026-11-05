# -*- coding: utf-8 -*-
"""登录、会话与权限校验。"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime

from . import db

SESSION_COOKIE = "ai4en_sid"
ITERATIONS = 60000


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), ITERATIONS)
    return "pbkdf2$" + salt + "$" + digest.hex()


def verify_password(password, stored):
    try:
        _, salt, _ = stored.split("$", 2)
    except ValueError:
        return False
    return hmac.compare_digest(hash_password(password, salt), stored)


def login(username, password):
    user = db.query_one("SELECT * FROM users WHERE username = ?", (username.strip(),))
    if not user or not verify_password(password, user["password"]):
        return None
    token = secrets.token_urlsafe(24)
    db.execute("INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)", (token, user["id"], now()))
    user.pop("password", None)
    return token, user


def logout(token):
    if token:
        db.execute("DELETE FROM sessions WHERE token = ?", (token,))


def user_by_token(token):
    if not token:
        return None
    row = db.query_one(
        "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.token = ?",
        (token,),
    )
    if row:
        row.pop("password", None)
    return row


def public_user(user):
    if not user:
        return None
    cls = db.query_one("SELECT name, grade FROM classes WHERE id = ?", (user.get("class_id"),)) if user.get("class_id") else None
    child = db.query_one("SELECT id, name FROM users WHERE id = ?", (user.get("child_id"),)) if user.get("child_id") else None
    return {
        "id": user["id"],
        "name": user["name"],
        "role": user["role"],
        "username": user["username"],
        "class_id": user.get("class_id"),
        "class_name": cls["name"] if cls else "",
        "grade": cls["grade"] if cls else "",
        "child_id": user.get("child_id"),
        "child_name": child["name"] if child else "",
    }

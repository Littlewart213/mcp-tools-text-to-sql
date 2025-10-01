"""Utility helpers for the text_to_sql demo environment.

The goal is to mirror the structure of the production helpers but keep
implementations lightweight so the examples can run without external
services.
"""
from __future__ import annotations

import pytz
import hashlib
from datetime import datetime
from typing import Optional


def create_current_date(timezone: str = "Asia/Jakarta") -> str:
    """Return the current date string formatted for presentations."""
    tz = pytz.timezone(timezone)
    return datetime.now(tz).strftime("%d %B %Y")


def create_sqlite_connection_string(db_path: str) -> str:
    """Build a SQLAlchemy-compatible SQLite URI from a file path."""
    return f"sqlite:///{db_path}"


def create_md5_id(text: str) -> str:
    """Generate a deterministic identifier to tag cacheable artifacts."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


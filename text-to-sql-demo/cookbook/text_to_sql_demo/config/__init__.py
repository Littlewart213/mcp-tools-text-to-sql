"""Configuration helpers for the cookbook demo."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DemoSettings:
    client: str
    connection_string: str
    metadata_dir: Path
    log_dir: Path


def load_settings(root: Path) -> DemoSettings:
    client = os.getenv("CLIENT", "demo")
    default_connection = f"sqlite:///{root / 'data' / 'sample.db'}"
    connection = os.getenv("CONNECTION_STRING") or os.getenv("CONNECTION_STRING_LEGACY", default_connection)
    metadata_dir = root / "data"
    log_dir = root / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    return DemoSettings(client=client, connection_string=connection, metadata_dir=metadata_dir, log_dir=log_dir)

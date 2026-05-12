"""Tests for AuditLogger (HMAC-SHA256 JSONL) [CRUX-MK]."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.audit_logger import AuditEntry, AuditLogger


def test_signed_entry_verifies():
    entry = AuditEntry(
        event_type="test_event",
        df_id="df-heylou-gemini-extension",
        timestamp_iso="2026-05-11T22:00:00Z",
        payload={"foo": "bar", "n": 42},
    ).signed("test-secret")
    assert entry.signature is not None
    assert entry.verify_signature("test-secret") is True
    assert entry.verify_signature("wrong-secret") is False


def test_log_appends_jsonl(tmp_path):
    audit = AuditLogger(audit_dir=str(tmp_path), df_id="df-heylou-gemini-extension")
    entry = audit.log("function_call", {"function": "search_hotels"}, target="gemini-function-calls")
    assert entry.signature is not None
    # File exists with at least one line
    files = list(tmp_path.glob("gemini-function-calls-*.jsonl"))
    assert len(files) == 1
    with files[0].open() as f:
        lines = [line.strip() for line in f if line.strip()]
    assert len(lines) >= 1
    parsed = json.loads(lines[-1])
    assert parsed["event_type"] == "function_call"
    assert parsed["payload"]["function"] == "search_hotels"
    assert "signature" in parsed


def test_read_recent_returns_last_n(tmp_path):
    audit = AuditLogger(audit_dir=str(tmp_path), df_id="df-heylou-gemini-extension")
    for i in range(5):
        audit.log(f"event_{i}", {"i": i}, target="gemini-function-calls")
    recent = audit.read_recent(target="gemini-function-calls", limit=3)
    assert len(recent) == 3
    assert recent[-1].payload["i"] == 4

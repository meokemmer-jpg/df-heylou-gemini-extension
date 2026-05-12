"""Tests for GeminiAuthHandler (K13 PAV) [CRUX-MK]."""

from __future__ import annotations

import os
import pytest

from src.auth_handler import AuthSource, GeminiAuthHandler, GeminiCredentials


def setup_function(_):
    for k in (
        "DF_HEYLOU_GEMINI_EXT_ENABLED",
        "GEMINI_API_KEY",
        "PHRONESIS_TICKET",
        "DF_HEYLOU_GEMINI_PHRONESIS_TICKET",
    ):
        os.environ.pop(k, None)


def test_sandbox_default_returns_fake_creds():
    handler = GeminiAuthHandler()
    creds = handler.get_credentials("hildesheim")
    assert creds.source == AuthSource.SANDBOX_FAKE
    assert creds.tenant_id == "hildesheim"
    assert handler.validate(creds) is True


def test_real_mode_without_api_key_returns_missing():
    os.environ["DF_HEYLOU_GEMINI_EXT_ENABLED"] = "true"
    handler = GeminiAuthHandler()
    creds = handler.get_credentials()
    assert creds.source == AuthSource.MISSING
    assert handler.validate(creds) is False


def test_real_mode_with_api_key_validates():
    os.environ["DF_HEYLOU_GEMINI_EXT_ENABLED"] = "true"
    os.environ["GEMINI_API_KEY"] = "fake-real-gemini-key-abc123"
    handler = GeminiAuthHandler()
    creds = handler.get_credentials()
    assert creds.source == AuthSource.ENV_VAR
    assert handler.validate(creds) is True


def test_phronesis_ticket_verification():
    handler = GeminiAuthHandler(sandbox_mode=False)
    assert handler.verify_phronesis_ticket() is False
    os.environ["PHRONESIS_TICKET"] = "PT-2026-W39-001"
    assert handler.verify_phronesis_ticket() is True


def test_k0_action_allowed_in_sandbox():
    handler = GeminiAuthHandler(sandbox_mode=True)
    assert handler.is_k0_action_allowed("book_direct") is True
    assert handler.is_k0_action_allowed("search_hotels") is True


def test_k0_action_denied_in_real_without_phronesis():
    handler = GeminiAuthHandler(sandbox_mode=False)
    assert handler.is_k0_action_allowed("book_direct") is False
    os.environ["PHRONESIS_TICKET"] = "PT-2026-W39-001"
    assert handler.is_k0_action_allowed("book_direct") is True

"""Tests for GeminiExtension dispatch [CRUX-MK]."""

from __future__ import annotations

import os
import pytest

from src.gemini_extension import (
    ExtensionProvenance,
    ExtensionResponse,
    GeminiExtension,
    K0_FUNCTIONS,
    VALID_FUNCTIONS,
)


def setup_function(_):
    # Ensure sandbox-mode default for every test
    for k in (
        "DF_HEYLOU_GEMINI_EXT_ENABLED",
        "PHRONESIS_TICKET",
        "DF_HEYLOU_GEMINI_PHRONESIS_TICKET",
    ):
        os.environ.pop(k, None)


def test_sandbox_mode_default():
    ext = GeminiExtension()
    assert ext.sandbox_mode is True
    assert ext.is_real_mode() is False


def test_unknown_function_returns_error():
    ext = GeminiExtension(sandbox_mode=True)
    resp = ext.handle_function_call({"name": "no_such_function", "args": {}})
    assert resp.success is False
    assert "unknown_function" in (resp.error or "")
    assert resp.provenance.mode == "error"


def test_search_hotels_mock_returns_canonical_shape():
    ext = GeminiExtension(sandbox_mode=True)
    resp = ext.handle_function_call(
        {
            "name": "search_hotels",
            "args": {
                "location": "Hildesheim",
                "dates": {"check_in": "2026-06-01", "check_out": "2026-06-03"},
            },
        }
    )
    assert resp.success is True
    assert resp.function_name == "search_hotels"
    assert "hotels" in resp.data
    assert isinstance(resp.data["hotels"], list)
    assert len(resp.data["hotels"]) >= 1
    assert resp.provenance.mode == "sandbox"
    assert resp.provenance.backend_used == "mock"


def test_get_rates_mock_three_room_types():
    ext = GeminiExtension(sandbox_mode=True)
    resp = ext.handle_function_call(
        {
            "name": "get_rates",
            "args": {
                "hotel_id": "hildesheim",
                "date_range": {"start": "2026-06-01", "end": "2026-06-03"},
            },
        }
    )
    assert resp.success is True
    assert len(resp.data["rates"]) == 3
    rooms = {r["room_type"] for r in resp.data["rates"]}
    assert rooms == {"standard", "superior", "suite"}


def test_book_direct_is_k0_relevant_in_sandbox_safe():
    ext = GeminiExtension(sandbox_mode=True)
    resp = ext.handle_function_call(
        {
            "name": "book_direct",
            "args": {
                "hotel_id": "hildesheim",
                "room_type": "standard",
                "guest": {"email": "test@example.org"},
                "dates": {"check_in": "2026-06-01", "check_out": "2026-06-03"},
            },
        }
    )
    assert resp.success is True
    assert resp.data["status"] == "confirmed"
    assert resp.data["k0_relevant"] is True
    assert resp.data["booking_id"].startswith("MOCK-gemini-")
    # In sandbox, mode must be sandbox (kein Real-API-Call)
    assert resp.provenance.mode == "sandbox"


def test_real_mode_requires_phronesis_ticket():
    # Without PHRONESIS_TICKET, is_real_mode must stay False
    os.environ["DF_HEYLOU_GEMINI_EXT_ENABLED"] = "true"
    ext = GeminiExtension()
    # ENV=true aber kein PHRONESIS_TICKET -> sandbox_mode=False BUT is_real_mode()=False
    assert ext.sandbox_mode is False
    assert ext.is_real_mode() is False
    os.environ.pop("DF_HEYLOU_GEMINI_EXT_ENABLED", None)


def test_provenance_envelope_has_required_fields():
    ext = GeminiExtension(sandbox_mode=True)
    resp = ext.handle_function_call(
        {"name": "optimize_revenue", "args": {"hotel_id": "munich"}}
    )
    p = resp.provenance
    assert isinstance(p, ExtensionProvenance)
    assert p.extension_id == "df-heylou-gemini-extension"
    assert p.provider == "gemini"
    assert p.function_name == "optimize_revenue"
    assert p.duration_s >= 0
    assert len(p.response_hash) == 64  # SHA256-hex


def test_k0_set_contains_book_direct():
    assert "book_direct" in K0_FUNCTIONS
    assert "search_hotels" not in K0_FUNCTIONS
    assert VALID_FUNCTIONS == {
        "search_hotels",
        "get_rates",
        "compare_otas",
        "book_direct",
        "optimize_revenue",
    }

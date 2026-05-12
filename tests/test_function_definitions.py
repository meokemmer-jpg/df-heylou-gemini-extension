"""Tests for HeyLou Function-Definitions (Gemini-Schema) [CRUX-MK]."""

from __future__ import annotations

from src.function_definitions import (
    HEYLOU_FUNCTION_DEFINITIONS,
    build_tool_payload,
    get_function_names,
    get_function_schema,
    is_k0_relevant,
)


def test_exactly_five_heylou_functions():
    names = get_function_names()
    assert len(names) == 5
    assert set(names) == {
        "search_hotels",
        "get_rates",
        "compare_otas",
        "book_direct",
        "optimize_revenue",
    }


def test_each_function_has_required_schema_fields():
    for fd in HEYLOU_FUNCTION_DEFINITIONS:
        assert "name" in fd
        assert "description" in fd
        assert "parameters" in fd
        assert fd["parameters"]["type"] == "object"
        assert "properties" in fd["parameters"]
        assert "required" in fd["parameters"]


def test_build_tool_payload_format():
    payload = build_tool_payload()
    assert "function_declarations" in payload
    assert payload["function_declarations"] is HEYLOU_FUNCTION_DEFINITIONS
    assert len(payload["function_declarations"]) == 5


def test_book_direct_is_k0_relevant():
    assert is_k0_relevant("book_direct") is True
    assert is_k0_relevant("search_hotels") is False
    assert is_k0_relevant("get_rates") is False
    assert is_k0_relevant("compare_otas") is False
    assert is_k0_relevant("optimize_revenue") is False


def test_get_function_schema_lookup():
    schema = get_function_schema("search_hotels")
    assert schema is not None
    assert schema["name"] == "search_hotels"
    assert "location" in schema["parameters"]["properties"]
    assert "dates" in schema["parameters"]["properties"]
    assert get_function_schema("nonexistent") is None

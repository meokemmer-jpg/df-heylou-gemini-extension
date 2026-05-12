"""HeyLou Function-Definitions fuer Gemini Function-Calling [CRUX-MK].

Schema-Format: Gemini-Function-Declarations (Google-AI-SDK JSON-Schema-Subset).
Pflicht: 5 HeyLou-Capabilities (search_hotels / get_rates / compare_otas / book_direct / optimize_revenue).

Gemini-Reference: https://ai.google.dev/gemini-api/docs/function-calling

[CRUX-MK]
"""

from __future__ import annotations

from typing import Any

# === HEYLOU FUNCTION DEFINITIONS (Gemini-Format) ===

HEYLOU_FUNCTION_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "search_hotels",
        "description": (
            "Search HeyLou Travel-Knowledge-Graph for hotels matching location, dates, and preferences. "
            "Read-only, idempotent. Returns list of hotels with availability + base-rates."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City or region (e.g. 'Hildesheim', 'Munich', 'Cape Coral FL').",
                },
                "dates": {
                    "type": "object",
                    "properties": {
                        "check_in": {"type": "string", "description": "ISO date YYYY-MM-DD"},
                        "check_out": {"type": "string", "description": "ISO date YYYY-MM-DD"},
                    },
                    "required": ["check_in", "check_out"],
                },
                "preferences": {
                    "type": "object",
                    "description": "Optional filters (room_type, max_price_eur, amenities).",
                    "properties": {
                        "room_type": {"type": "string"},
                        "max_price_eur": {"type": "number"},
                        "amenities": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
            "required": ["location", "dates"],
        },
    },
    {
        "name": "get_rates",
        "description": (
            "Fetch current rates from PMS/RMS backend (MEWS/Opera/Protel) for a hotel + date-range. "
            "Read-only. Returns per-room-type rates with availability."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "hotel_id": {"type": "string", "description": "HeyLou hotel-ID (e.g. 'hildesheim')."},
                "date_range": {
                    "type": "object",
                    "properties": {
                        "start": {"type": "string", "description": "ISO date"},
                        "end": {"type": "string", "description": "ISO date"},
                    },
                    "required": ["start", "end"],
                },
            },
            "required": ["hotel_id", "date_range"],
        },
    },
    {
        "name": "compare_otas",
        "description": (
            "Compare OTA-prices (Booking.com / Expedia / HRS) for a hotel + dates against Direct-Booking. "
            "Read-only. Returns spread + commission-delta."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "hotel_id": {"type": "string"},
                "dates": {
                    "type": "object",
                    "properties": {
                        "check_in": {"type": "string"},
                        "check_out": {"type": "string"},
                    },
                    "required": ["check_in", "check_out"],
                },
            },
            "required": ["hotel_id", "dates"],
        },
    },
    {
        "name": "book_direct",
        "description": (
            "Direct-Booking via HeyLou (commission-free). K_0-RELEVANT - requires PHRONESIS_TICKET in Real-Mode. "
            "Returns confirmed booking with booking_id."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "hotel_id": {"type": "string"},
                "room_type": {"type": "string"},
                "guest": {
                    "type": "object",
                    "properties": {
                        "email": {"type": "string"},
                        "first_name": {"type": "string"},
                        "last_name": {"type": "string"},
                    },
                    "required": ["email"],
                },
                "dates": {
                    "type": "object",
                    "properties": {
                        "check_in": {"type": "string"},
                        "check_out": {"type": "string"},
                    },
                    "required": ["check_in", "check_out"],
                },
            },
            "required": ["hotel_id", "room_type", "guest", "dates"],
        },
    },
    {
        "name": "optimize_revenue",
        "description": (
            "Run Revenue-Optimizer for a hotel (Hamilton/Lagrange/KKT pricing optimization). "
            "Returns recommended rate-changes per room-type. W40 Stub - currently mock-only."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "hotel_id": {"type": "string"},
            },
            "required": ["hotel_id"],
        },
    },
]


def build_tool_payload() -> dict[str, Any]:
    """Build Gemini tools payload from function-definitions.

    Gemini accepts tools as: {"function_declarations": [...]}
    """
    return {"function_declarations": HEYLOU_FUNCTION_DEFINITIONS}


def get_function_names() -> list[str]:
    """Return list of all 5 HeyLou function-names."""
    return [fd["name"] for fd in HEYLOU_FUNCTION_DEFINITIONS]


def get_function_schema(name: str) -> dict[str, Any] | None:
    """Lookup function-schema by name."""
    for fd in HEYLOU_FUNCTION_DEFINITIONS:
        if fd["name"] == name:
            return fd
    return None


def is_k0_relevant(name: str) -> bool:
    """K_0-Filter: book_direct triggers K_0-Gate."""
    return name in {"book_direct"}

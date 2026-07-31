"""HeyLou function definitions for Gemini function calling.

The module exposes the five Gemini tool declarations and a small deterministic
adapter that turns a user request into the concrete function call Gemini should
be allowed to make. Unsupported or adversarial requests fail closed instead of
falling back to an unrelated HeyLou capability.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import re
from typing import Any, Mapping


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
            "Returns recommended rate-changes per room-type."
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


MISSION_ID = "df-heylou-gemini-extension"

_HOTEL_IDS: dict[str, str] = {
    "hildesheim": "hildesheim",
    "munich": "munich",
    "muenchen": "munich",
    "cape coral": "cape-coral-fl",
    "cape coral fl": "cape-coral-fl",
}

_ROOM_TYPES = ("suite", "double", "single", "standard")
_BOOKING_WORDS = ("book", "booking", "reserve", "reservation", "direct")
_SEARCH_WORDS = ("search", "find", "show", "available", "availability", "hotel")
_RATE_WORDS = ("rate", "rates", "price", "prices", "availability")
_OTA_WORDS = ("ota", "booking.com", "expedia", "hrs", "compare", "commission")
_OPTIMIZE_WORDS = ("optimize", "revenue", "yield", "pricing", "kkt")
_ADVERSARIAL_WORDS = (
    "delete",
    "drop table",
    "exfiltrate",
    "ignore schema",
    "ignore tool",
    "bypass",
    "jailbreak",
    "system prompt",
    "unsupported_tool",
)


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: list[str]


@dataclass(frozen=True)
class RoutedFunctionCall:
    mission: str
    status: str
    function_call: dict[str, Any] | None
    k0_relevant: bool
    tool_payload: dict[str, Any]
    validation: dict[str, Any]
    discriminant: str


def build_tool_payload() -> dict[str, Any]:
    """Build Gemini tools payload from function definitions."""
    return {"function_declarations": HEYLOU_FUNCTION_DEFINITIONS}


def get_function_names() -> list[str]:
    """Return all HeyLou function names in declaration order."""
    return [fd["name"] for fd in HEYLOU_FUNCTION_DEFINITIONS]


def get_function_schema(name: str) -> dict[str, Any] | None:
    """Look up one Gemini function declaration by name."""
    for fd in HEYLOU_FUNCTION_DEFINITIONS:
        if fd["name"] == name:
            return fd
    return None


def is_k0_relevant(name: str) -> bool:
    """Return whether a function requires the K_0 gate."""
    return name == "book_direct"


def route_heylou_request(request: str | Mapping[str, Any]) -> dict[str, Any]:
    """Convert a user request into a validated Gemini function-call envelope.

    The function discriminates on the request content. It returns ``rejected``
    for unsupported or adversarial requests, and ``ready`` only when the
    selected call validates against the declared Gemini schema.
    """
    text = _request_text(request)
    lowered = text.lower()

    if not text.strip():
        return _rejected("empty_request", "request text is empty")

    if any(marker in lowered for marker in _ADVERSARIAL_WORDS):
        return _rejected("unsupported_or_adversarial", "request asks outside declared HeyLou tools")

    name = _select_function(lowered)
    if name is None:
        return _rejected("unsupported_intent", "no declared HeyLou function matches the request")

    try:
        args = _extract_arguments(name, text)
    except ValueError as exc:
        return _rejected(f"invalid_{name}", str(exc))
    validation = validate_function_call(name, args)
    if not validation.valid:
        return _rejected(f"invalid_{name}", "; ".join(validation.errors))

    call = {"name": name, "args": args}
    return asdict(
        RoutedFunctionCall(
            mission=MISSION_ID,
            status="ready",
            function_call=call,
            k0_relevant=is_k0_relevant(name),
            tool_payload={"function_declarations": [get_function_schema(name)]},
            validation=asdict(validation),
            discriminant=f"{name}:{_stable_arg_fingerprint(args)}",
        )
    )


def validate_function_call(name: str, args: Mapping[str, Any]) -> ValidationResult:
    """Validate call args against the required fields and simple schema types."""
    schema = get_function_schema(name)
    if schema is None:
        return ValidationResult(False, [f"unknown function: {name}"])

    errors = _validate_object(schema["parameters"], dict(args), path="args")
    return ValidationResult(not errors, errors)


def _request_text(request: str | Mapping[str, Any]) -> str:
    if isinstance(request, str):
        return request
    parts: list[str] = []
    for key in ("intent", "message", "prompt", "location", "hotel_id", "room_type", "email"):
        value = request.get(key)
        if isinstance(value, str):
            parts.append(value)
    return " ".join(parts)


def _select_function(lowered: str) -> str | None:
    if _contains_any(lowered, _OTA_WORDS):
        return "compare_otas"
    if _contains_any(lowered, _OPTIMIZE_WORDS):
        return "optimize_revenue"
    if _contains_any(lowered, _BOOKING_WORDS):
        return "book_direct"
    if "hotel_id" in lowered or _contains_any(lowered, _RATE_WORDS):
        return "get_rates"
    if _contains_any(lowered, _SEARCH_WORDS):
        return "search_hotels"
    return None


def _extract_arguments(name: str, text: str) -> dict[str, Any]:
    check_in, check_out = _extract_date_range(text)
    hotel_id = _extract_hotel_id(text)
    location = _extract_location(text)

    if name == "search_hotels":
        args: dict[str, Any] = {"location": location, "dates": {"check_in": check_in, "check_out": check_out}}
        room_type = _extract_room_type(text)
        if room_type:
            args["preferences"] = {"room_type": room_type}
        return args

    if name == "get_rates":
        return {"hotel_id": hotel_id, "date_range": {"start": check_in, "end": check_out}}

    if name == "compare_otas":
        return {"hotel_id": hotel_id, "dates": {"check_in": check_in, "check_out": check_out}}

    if name == "book_direct":
        return {
            "hotel_id": hotel_id,
            "room_type": _extract_room_type(text) or "standard",
            "guest": {"email": _extract_email(text)},
            "dates": {"check_in": check_in, "check_out": check_out},
        }

    if name == "optimize_revenue":
        return {"hotel_id": hotel_id}

    return {}


def _extract_date_range(text: str) -> tuple[str, str]:
    dates = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text)
    if len(dates) < 2:
        raise ValueError("request must include check-in and check-out ISO dates")
    check_in = _parse_iso_date(dates[0], "check_in")
    check_out = _parse_iso_date(dates[1], "check_out")
    if check_out <= check_in:
        raise ValueError("check_out must be after check_in")
    return check_in.isoformat(), check_out.isoformat()


def _extract_hotel_id(text: str) -> str:
    lowered = text.lower()
    explicit = re.search(r"\bhotel[_ -]?id[:= ]+([a-z0-9-]+)\b", lowered)
    if explicit:
        return explicit.group(1)
    for needle, hotel_id in _HOTEL_IDS.items():
        if needle in lowered:
            return hotel_id
    raise ValueError("request must identify a supported hotel")


def _extract_location(text: str) -> str:
    lowered = text.lower()
    for needle, hotel_id in _HOTEL_IDS.items():
        if needle in lowered:
            return hotel_id
    raise ValueError("request must identify a supported location")


def _extract_room_type(text: str) -> str | None:
    lowered = text.lower()
    for room_type in _ROOM_TYPES:
        if room_type in lowered:
            return room_type
    return None


def _extract_email(text: str) -> str:
    match = re.search(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", text, re.IGNORECASE)
    if not match:
        raise ValueError("direct booking requires a guest email")
    return match.group(0)


def _parse_iso_date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO date") from exc


def _validate_object(schema: Mapping[str, Any], value: Any, path: str) -> list[str]:
    if schema.get("type") != "object":
        return []
    if not isinstance(value, dict):
        return [f"{path} must be object"]

    errors: list[str] = []
    properties = schema.get("properties", {})
    for key in schema.get("required", []):
        if key not in value:
            errors.append(f"{path}.{key} is required")

    for key, item in value.items():
        if key not in properties:
            continue
        item_schema = properties[key]
        expected = item_schema.get("type")
        child_path = f"{path}.{key}"
        if expected == "object":
            errors.extend(_validate_object(item_schema, item, child_path))
        elif expected == "array":
            if not isinstance(item, list):
                errors.append(f"{child_path} must be array")
        elif expected == "number":
            if not isinstance(item, (int, float)) or isinstance(item, bool):
                errors.append(f"{child_path} must be number")
        elif expected == "string":
            if not isinstance(item, str) or not item:
                errors.append(f"{child_path} must be non-empty string")
    return errors


def _rejected(reason: str, message: str) -> dict[str, Any]:
    return asdict(
        RoutedFunctionCall(
            mission=MISSION_ID,
            status="rejected",
            function_call=None,
            k0_relevant=False,
            tool_payload=build_tool_payload(),
            validation={"valid": False, "errors": [message]},
            discriminant=f"rejected:{reason}",
        )
    )


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _stable_arg_fingerprint(args: Mapping[str, Any]) -> str:
    leaves: list[str] = []

    def walk(prefix: str, value: Any) -> None:
        if isinstance(value, Mapping):
            for key in sorted(value):
                walk(f"{prefix}.{key}" if prefix else str(key), value[key])
        else:
            leaves.append(f"{prefix}={value}")

    walk("", args)
    return "|".join(leaves)

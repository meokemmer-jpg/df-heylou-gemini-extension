"""Gemini-Extension fuer HeyLou [CRUX-MK].

Welle-39 LLM Sub-Funktion. Routet Gemini-functionCalls -> HeyLou-Backends.

Backends (Lazy-Imports, Mock-Fallback):
- df-heylou-travel-domain  -> search_hotels, book_direct
- df-pms-mews-adapter (W36) -> get_rates
- df-ota-* (W37)            -> compare_otas
- W40 Stub                  -> optimize_revenue

[CRUX-MK]
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

logger = logging.getLogger(__name__)

# === Constants ===

K0_FUNCTIONS = {"book_direct"}
VALID_FUNCTIONS = {
    "search_hotels",
    "get_rates",
    "compare_otas",
    "book_direct",
    "optimize_revenue",
}


@dataclass(frozen=True)
class ExtensionProvenance:
    """Provenance-Envelope fuer ExtensionResponse (K12)."""
    extension_id: str
    provider: str
    function_name: str
    timestamp_iso: str
    duration_s: float
    mode: str                    # real-api | sandbox | mock-fallback
    response_hash: str
    backend_used: str            # backend-DF-id or 'mock'
    phronesis_ticket: str | None = None
    schema_version: str = "v1.0"


@dataclass
class ExtensionResponse:
    """Pflicht-Response-Format fuer Function-Calls."""
    success: bool
    function_name: str
    data: dict
    provenance: ExtensionProvenance
    error: str | None = None


class GeminiExtension:
    """HeyLou-Extension fuer Gemini Function-Calling.

    Routet Gemini-functionCall-Parts an HeyLou-Backends.
    Sandbox-Default per ENV-Var DF_HEYLOU_GEMINI_EXT_ENABLED.
    """

    EXTENSION_ID = "df-heylou-gemini-extension"
    PROVIDER = "gemini"
    REAL_ENV_VAR = "DF_HEYLOU_GEMINI_EXT_ENABLED"

    def __init__(self, sandbox_mode: bool | None = None):
        if sandbox_mode is None:
            sandbox_mode = os.environ.get(self.REAL_ENV_VAR, "false") != "true"
        self.sandbox_mode = sandbox_mode
        self._handlers: dict[str, Callable[[dict], dict]] = {
            "search_hotels": self._handle_search_hotels,
            "get_rates": self._handle_get_rates,
            "compare_otas": self._handle_compare_otas,
            "book_direct": self._handle_book_direct,
            "optimize_revenue": self._handle_optimize_revenue,
        }

    # === Mode-Detection ===

    def is_real_mode(self) -> bool:
        if self.sandbox_mode:
            return False
        if not os.environ.get("PHRONESIS_TICKET") and not os.environ.get(
            "DF_HEYLOU_GEMINI_PHRONESIS_TICKET"
        ):
            return False
        return True

    def _is_k0_function(self, name: str) -> bool:
        return name in K0_FUNCTIONS

    # === Provenance-Helper ===

    def _build_provenance(
        self,
        function_name: str,
        duration_s: float,
        mode: str,
        backend: str,
        response_data: dict,
    ) -> ExtensionProvenance:
        import hashlib
        import json

        response_hash = hashlib.sha256(
            json.dumps(response_data, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        return ExtensionProvenance(
            extension_id=self.EXTENSION_ID,
            provider=self.PROVIDER,
            function_name=function_name,
            timestamp_iso=datetime.now(timezone.utc).isoformat(),
            duration_s=duration_s,
            mode=mode,
            response_hash=response_hash,
            backend_used=backend,
            phronesis_ticket=(
                os.environ.get("PHRONESIS_TICKET")
                or os.environ.get("DF_HEYLOU_GEMINI_PHRONESIS_TICKET")
            ),
        )

    # === Public-API ===

    def handle_function_call(self, function_call: dict) -> ExtensionResponse:
        """Dispatch entry-point.

        Args:
            function_call: dict with keys `name` (str) and `args` (dict).
                           This is the canonical-form aller Provider (Gemini liefert
                           per part.function_call das gleiche Schema).
        """
        start = time.time()
        name = function_call.get("name", "")
        args = function_call.get("args", {}) or {}

        # Validate
        if name not in VALID_FUNCTIONS:
            return ExtensionResponse(
                success=False,
                function_name=name,
                data={},
                provenance=self._build_provenance(
                    name, time.time() - start, "error", "none", {}
                ),
                error=f"unknown_function: {name}",
            )

        # K_0-Filter (book_direct)
        mode = "real-api" if self.is_real_mode() else "sandbox"
        if self._is_k0_function(name) and mode == "real-api":
            if not os.environ.get("PHRONESIS_TICKET") and not os.environ.get(
                "DF_HEYLOU_GEMINI_PHRONESIS_TICKET"
            ):
                # Defensive double-check (K13 PAV)
                mode = "sandbox"

        # Dispatch
        handler = self._handlers[name]
        try:
            data, backend = handler(args) if mode == "real-api" else self._mock_handler(name, args)
            return ExtensionResponse(
                success=True,
                function_name=name,
                data=data,
                provenance=self._build_provenance(
                    name, time.time() - start, mode, backend, data
                ),
            )
        except Exception as e:
            logger.error(f"[{self.PROVIDER}-extension] handle_function_call({name}) failed: {e}")
            return ExtensionResponse(
                success=False,
                function_name=name,
                data={},
                provenance=self._build_provenance(
                    name, time.time() - start, "error", "none", {}
                ),
                error=str(e)[:200],
            )

    # === Real-Backend-Handlers (Lazy-Import + Mock-Fallback) ===

    def _handle_search_hotels(self, args: dict) -> tuple[dict, str]:
        # Lazy-Import df-heylou-travel-domain backend
        try:
            # Pseudo-Wiring: backend not yet linked. Always fallback to mock for now.
            raise ImportError("df-heylou-travel-domain backend not yet wired (W40)")
        except Exception:
            return self._mock_handler("search_hotels", args)

    def _handle_get_rates(self, args: dict) -> tuple[dict, str]:
        try:
            raise ImportError("df-pms-mews-adapter backend not yet wired (W40)")
        except Exception:
            return self._mock_handler("get_rates", args)

    def _handle_compare_otas(self, args: dict) -> tuple[dict, str]:
        try:
            raise ImportError("df-ota-* backend not yet wired (W40)")
        except Exception:
            return self._mock_handler("compare_otas", args)

    def _handle_book_direct(self, args: dict) -> tuple[dict, str]:
        try:
            raise ImportError("df-heylou-travel-domain Direct-Booking not yet wired (W40)")
        except Exception:
            return self._mock_handler("book_direct", args)

    def _handle_optimize_revenue(self, args: dict) -> tuple[dict, str]:
        # W40 Stub - kein Real-Backend definiert
        return self._mock_handler("optimize_revenue", args)

    # === Mock-Defaults ===

    def _mock_handler(self, name: str, args: dict) -> tuple[dict, str]:
        if name == "search_hotels":
            return (
                {
                    "location": args.get("location", "unknown"),
                    "dates": args.get("dates", {}),
                    "hotels": [
                        {
                            "hotel_id": "hildesheim",
                            "name": "HeyLou Hildesheim",
                            "base_rate_eur": 89.0,
                            "available": True,
                        },
                        {
                            "hotel_id": "munich",
                            "name": "HeyLou Munich",
                            "base_rate_eur": 119.0,
                            "available": True,
                        },
                    ],
                    "mode": "sandbox",
                },
                "mock",
            )
        if name == "get_rates":
            return (
                {
                    "hotel_id": args.get("hotel_id", ""),
                    "date_range": args.get("date_range", {}),
                    "rates": [
                        {"room_type": "standard", "price_eur": 89.0, "available": 5},
                        {"room_type": "superior", "price_eur": 129.0, "available": 3},
                        {"room_type": "suite", "price_eur": 249.0, "available": 1},
                    ],
                    "mode": "sandbox",
                },
                "mock",
            )
        if name == "compare_otas":
            return (
                {
                    "hotel_id": args.get("hotel_id", ""),
                    "dates": args.get("dates", {}),
                    "comparison": [
                        {"channel": "direct", "price_eur": 89.0, "commission_pct": 0.0},
                        {"channel": "booking.com", "price_eur": 99.0, "commission_pct": 18.0},
                        {"channel": "expedia", "price_eur": 102.0, "commission_pct": 20.0},
                        {"channel": "hrs", "price_eur": 95.0, "commission_pct": 15.0},
                    ],
                    "best_direct_savings_eur": 13.0,
                    "mode": "sandbox",
                },
                "mock",
            )
        if name == "book_direct":
            booking_id = f"MOCK-{self.PROVIDER}-{uuid.uuid4().hex[:12]}"
            return (
                {
                    "booking_id": booking_id,
                    "hotel_id": args.get("hotel_id", ""),
                    "room_type": args.get("room_type", ""),
                    "guest_email": (args.get("guest") or {}).get("email", ""),
                    "dates": args.get("dates", {}),
                    "status": "confirmed",
                    "mode": "sandbox",
                    "k0_relevant": True,
                },
                "mock",
            )
        if name == "optimize_revenue":
            return (
                {
                    "hotel_id": args.get("hotel_id", ""),
                    "recommendations": [
                        {"room_type": "standard", "current_eur": 89.0, "recommended_eur": 94.0, "delta_pct": 5.6},
                        {"room_type": "superior", "current_eur": 129.0, "recommended_eur": 135.0, "delta_pct": 4.7},
                    ],
                    "expected_revenue_delta_pct": 4.2,
                    "mode": "sandbox-w40-stub",
                },
                "mock-w40-stub",
            )
        return ({"error": "no_mock"}, "mock")

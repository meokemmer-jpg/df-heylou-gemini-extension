"""Gemini-Auth-Handler fuer HeyLou-Extension [CRUX-MK].

Welle-39. User-OAuth (GEMINI_API_KEY) + Service-Identity-Token (DF_HEYLOU_GEMINI_HMAC_SECRET).
K13 Pre-Action-Verification: PHRONESIS_TICKET-Check vor K_0-Functions (book_direct).

[CRUX-MK]
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class AuthSource(str, Enum):
    """Where Credentials came from."""
    ENV_VAR = "env_var"
    SANDBOX_FAKE = "sandbox_fake"
    MISSING = "missing"


@dataclass(frozen=True)
class GeminiCredentials:
    """Gemini-API-Credentials envelope."""
    api_key: str
    source: AuthSource
    fetched_iso: str
    tenant_id: str = "hildesheim"
    phronesis_ticket: Optional[str] = None


class GeminiAuthHandler:
    """Gemini-Auth-Handler.

    Public-API:
    - get_credentials(tenant_id) -> GeminiCredentials
    - validate(creds) -> bool
    - verify_phronesis_ticket() -> bool      (K13)
    - is_k0_action_allowed(function_name) -> bool
    """

    K0_FUNCTIONS = {"book_direct"}

    def __init__(self, sandbox_mode: bool | None = None):
        if sandbox_mode is None:
            sandbox_mode = os.environ.get("DF_HEYLOU_GEMINI_EXT_ENABLED", "false") != "true"
        self.sandbox_mode = sandbox_mode

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def get_credentials(self, tenant_id: str = "hildesheim") -> GeminiCredentials:
        """Fetch credentials from ENV + tenant_id."""
        api_key = os.environ.get("GEMINI_API_KEY", "")
        phronesis = (
            os.environ.get("PHRONESIS_TICKET")
            or os.environ.get("DF_HEYLOU_GEMINI_PHRONESIS_TICKET")
        )

        if self.sandbox_mode:
            return GeminiCredentials(
                api_key=api_key or "sandbox-fake-gemini-key",
                source=AuthSource.SANDBOX_FAKE,
                fetched_iso=self._now_iso(),
                tenant_id=tenant_id,
                phronesis_ticket=phronesis,
            )

        if not api_key:
            return GeminiCredentials(
                api_key="",
                source=AuthSource.MISSING,
                fetched_iso=self._now_iso(),
                tenant_id=tenant_id,
                phronesis_ticket=phronesis,
            )

        return GeminiCredentials(
            api_key=api_key,
            source=AuthSource.ENV_VAR,
            fetched_iso=self._now_iso(),
            tenant_id=tenant_id,
            phronesis_ticket=phronesis,
        )

    def validate(self, creds: GeminiCredentials) -> bool:
        """Validate credentials structurally."""
        if self.sandbox_mode:
            return creds.source != AuthSource.MISSING or True  # sandbox accepts fake
        return creds.source == AuthSource.ENV_VAR and bool(creds.api_key)

    def verify_phronesis_ticket(self) -> bool:
        """K13 Pre-Action-Verification: PHRONESIS_TICKET present?"""
        ticket = (
            os.environ.get("PHRONESIS_TICKET")
            or os.environ.get("DF_HEYLOU_GEMINI_PHRONESIS_TICKET")
        )
        return bool(ticket and ticket.strip())

    def is_k0_action_allowed(self, function_name: str) -> bool:
        """K_0-Gate: allow only when (sandbox) OR (real + phronesis-ticket valid)."""
        if function_name not in self.K0_FUNCTIONS:
            return True  # not K_0
        if self.sandbox_mode:
            return True  # mock-only, safe
        return self.verify_phronesis_ticket()

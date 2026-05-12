"""df-heylou-gemini-extension [CRUX-MK].

Welle-39 LLM Sub-Funktion Extension: HeyLou als Sub-Funktion in Gemini Function-Calling.

LAZY-IMPORT-PATTERN.
"""

from __future__ import annotations

__version__ = "0.1.0-SKELETON"
__df_id__ = "df-heylou-gemini-extension"
__welle__ = "welle-39"
__provider__ = "gemini"


def get_extension():
    from src.gemini_extension import GeminiExtension
    return GeminiExtension


def get_function_definitions():
    from src.function_definitions import HEYLOU_FUNCTION_DEFINITIONS, build_tool_payload
    return HEYLOU_FUNCTION_DEFINITIONS, build_tool_payload


def get_auth_handler():
    from src.auth_handler import GeminiAuthHandler
    return GeminiAuthHandler


def get_orchestrator():
    from src.adapter_orchestrator import GeminiAdapterOrchestrator
    return GeminiAdapterOrchestrator


def get_audit_logger():
    from src.audit_logger import AuditLogger
    return AuditLogger


__all__ = [
    "__version__",
    "__df_id__",
    "__welle__",
    "__provider__",
    "get_extension",
    "get_function_definitions",
    "get_auth_handler",
    "get_orchestrator",
    "get_audit_logger",
]

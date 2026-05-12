"""Gemini-Adapter-Orchestrator [CRUX-MK].

LaunchAgent-Entry fuer Welle-39 HeyLou-Sub-Funktion-Extension Gemini.

Phasen:
1. auth   -> GeminiAuthHandler.get_credentials()
2. health -> Extension verifiziert function_definitions
3. sample -> 1x mock-function-call (search_hotels)
4. audit  -> AuditLogger persistiert alle Phases

Welle-39.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DF_ID = "df-heylou-gemini-extension"
PROVIDER = "gemini"


@dataclass
class LoopReport:
    loop_id: str
    df_id: str
    provider: str
    started_iso: str
    finished_iso: str
    sandbox_mode: bool
    final_status: str            # complete | partial | failed
    phases_passed: list = field(default_factory=list)
    phases_failed: list = field(default_factory=list)
    artifacts: dict = field(default_factory=dict)
    error: Optional[str] = None


class GeminiAdapterOrchestrator:
    DF_ID = DF_ID
    PROVIDER = PROVIDER

    def __init__(self, tenant_id: Optional[str] = None):
        self.tenant_id = tenant_id or os.environ.get(
            "DF_HEYLOU_GEMINI_TENANT_ID", "hildesheim"
        )
        self.sandbox_mode = (
            os.environ.get("DF_HEYLOU_GEMINI_EXT_ENABLED", "false") != "true"
        )
        from src.gemini_extension import GeminiExtension
        from src.auth_handler import GeminiAuthHandler
        from src.audit_logger import AuditLogger
        from src.function_definitions import get_function_names

        self.extension = GeminiExtension(sandbox_mode=self.sandbox_mode)
        self.auth = GeminiAuthHandler(sandbox_mode=self.sandbox_mode)
        self.audit = AuditLogger(df_id=self.DF_ID)
        self._get_function_names = get_function_names

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _persist_loop_report(self, report: LoopReport) -> Optional[Path]:
        try:
            reports_dir = Path("runs/loop-reports")
            reports_dir.mkdir(parents=True, exist_ok=True)
            file_path = reports_dir / f"loop-{report.loop_id}.json"
            with file_path.open("w", encoding="utf-8") as f:
                json.dump(asdict(report), f, indent=2, default=str)
            return file_path
        except Exception as e:
            logger.error(f"loop-report persist failed: {e}")
            return None

    def run(self, dry_run: bool = False) -> LoopReport:
        loop_id = str(uuid.uuid4())[:8]
        started = self._now_iso()
        report = LoopReport(
            loop_id=loop_id,
            df_id=self.DF_ID,
            provider=self.PROVIDER,
            started_iso=started,
            finished_iso="",
            sandbox_mode=self.sandbox_mode,
            final_status="failed",
        )

        # Phase 1: Auth
        try:
            creds = self.auth.get_credentials(self.tenant_id)
            if self.auth.validate(creds):
                report.phases_passed.append("auth")
                self.audit.log(
                    "auth_ok",
                    {
                        "tenant_id": self.tenant_id,
                        "source": creds.source.value,
                        "loop_id": loop_id,
                    },
                    target=f"{self.PROVIDER}-auth",
                )
            else:
                report.phases_failed.append("auth")
                self.audit.log(
                    "auth_failed",
                    {"tenant_id": self.tenant_id, "loop_id": loop_id},
                    target=f"{self.PROVIDER}-auth",
                )
        except Exception as e:
            report.phases_failed.append("auth")
            report.error = f"auth: {e}"
            logger.error(f"[orchestrator] auth phase failed: {e}")

        # Phase 2: Health (function_definitions count)
        try:
            names = self._get_function_names()
            report.artifacts["function_count"] = len(names)
            report.artifacts["functions"] = names
            if len(names) == 5:
                report.phases_passed.append("health")
            else:
                report.phases_failed.append("health")
        except Exception as e:
            report.phases_failed.append("health")
            logger.error(f"[orchestrator] health phase failed: {e}")

        # Phase 3: Sample (mock function-call)
        if not dry_run:
            try:
                sample_call = {
                    "name": "search_hotels",
                    "args": {
                        "location": "Hildesheim",
                        "dates": {"check_in": "2026-06-01", "check_out": "2026-06-03"},
                    },
                }
                resp = self.extension.handle_function_call(sample_call)
                report.artifacts["sample_function"] = sample_call["name"]
                report.artifacts["sample_success"] = resp.success
                report.artifacts["sample_mode"] = resp.provenance.mode
                if resp.success:
                    report.phases_passed.append("sample")
                    self.audit.log(
                        "sample_function_call_ok",
                        {
                            "function": sample_call["name"],
                            "mode": resp.provenance.mode,
                            "loop_id": loop_id,
                        },
                        target=f"{self.PROVIDER}-function-calls",
                    )
                else:
                    report.phases_failed.append("sample")
            except Exception as e:
                report.phases_failed.append("sample")
                logger.error(f"[orchestrator] sample phase failed: {e}")

        # Phase 4: Audit-Persist
        try:
            self.audit.log(
                "loop_complete",
                {
                    "loop_id": loop_id,
                    "phases_passed": report.phases_passed,
                    "phases_failed": report.phases_failed,
                    "sandbox_mode": self.sandbox_mode,
                    "provider": self.PROVIDER,
                },
                target=f"{self.PROVIDER}-function-calls",
            )
            report.phases_passed.append("audit_persist")
        except Exception as e:
            report.phases_failed.append("audit_persist")
            logger.error(f"[orchestrator] audit_persist failed: {e}")

        if not report.phases_failed:
            report.final_status = "complete"
        elif len(report.phases_passed) >= 2:
            report.final_status = "partial"
        else:
            report.final_status = "failed"

        report.finished_iso = self._now_iso()
        self._persist_loop_report(report)
        return report


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    orch = GeminiAdapterOrchestrator()
    report = orch.run()
    print(
        f"[{DF_ID}] loop_id={report.loop_id} status={report.final_status} "
        f"sandbox={report.sandbox_mode} provider={PROVIDER}"
    )
    sys.exit(0 if report.final_status in ("complete", "partial") else 1)


if __name__ == "__main__":
    main()

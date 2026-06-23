from __future__ import annotations

import json
import logging
import os
import ssl
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _load_dotenv(env_path: Path | None = None) -> None:
    """Load key=value pairs from a .env file into os.environ (no-op if missing).

    Existing environment variables are never overwritten, so values set in the
    shell or PyCharm run-configuration always take precedence.
    """
    path = env_path or Path(__file__).resolve().parent / ".env"
    if not path.is_file():
        return
    with path.open(encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and (key not in os.environ or not os.environ[key]):
                os.environ[key] = value


# Load .env on import so every entry point picks up credentials automatically.
_load_dotenv()


# ---------------------------------------------------------------------------
# Real SystemLink REST API reporter
#
# Environment variables:
#   SYSTEMLINK_URL          – base URL, e.g. https://localhost  (required)
#   SYSTEMLINK_API_KEY      – API key from HttpConfigurations   (required)
#   SYSTEMLINK_VERIFY_TLS   – "false" to skip TLS verification  (default true)
#   SYSTEMLINK_TIMEOUT_S    – HTTP timeout in seconds           (default 5.0)
#   SYSTEMLINK_PROGRAM_NAME – program name shown in Test Monitor (default FgenScopeTest)
#   SYSTEMLINK_OPERATOR     – operator name shown in Test Monitor (default localadmin)
#
# Asset name → SystemLink asset UUID map:
#   SYSTEMLINK_ASSET_MAP    – JSON-encoded dict, e.g.
#       '{"Scope1":"688779da-...","FGEN1":"e4489d58-..."}'
# ---------------------------------------------------------------------------

_DEFAULT_ASSET_MAP: Dict[str, str] = {
    "Scope1": "688779da-7fe5-497b-905a-5182144e94d2",
    "FGEN1": "e4489d58-a2e2-4ea5-a3eb-ecbc21de4b96",
}


class SystemLinkReporter:
    """Reports test run status and asset utilization to SystemLink REST APIs.

    Test Monitor API
    ----------------
    - Creates a result with status RUNNING when a suite starts.
    - Creates a step per test case (RUNNING → PASSED/FAILED).
    - Updates the result to PASSED/FAILED when the suite ends.

    Asset Performance Management API
    ---------------------------------
    - Updates each asset's ``properties`` to include ``inUseByRunId`` when
      acquired, and clears it when released.  This surfaces in the APM asset
      detail view and can drive custom dashboards.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        verify_tls: bool = True,
        timeout_s: float = 5.0,
        program_name: str = "FgenScopeTest",
        operator: str = "localadmin",
        asset_map: Optional[Dict[str, str]] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key.strip()
        self._verify_tls = verify_tls
        self._timeout_s = timeout_s
        self._program_name = program_name
        self._operator = operator
        self._asset_map: Dict[str, str] = asset_map or {}
        self._logger = logger or logging.getLogger(__name__)

        # In-flight state
        self._result_ids: Dict[str, str] = {}   # run_id → SystemLink result id
        self._step_start_times: Dict[str, str] = {}  # run_id:case_index → startedAt

    @classmethod
    def from_environment(cls, logger: Optional[logging.Logger] = None) -> "SystemLinkReporter":
        verify_tls = os.getenv("SYSTEMLINK_VERIFY_TLS", "true").strip().lower() not in {
            "0", "false", "no", "off",
        }
        try:
            timeout_s = float(os.getenv("SYSTEMLINK_TIMEOUT_S", "5.0"))
        except ValueError:
            timeout_s = 5.0

        asset_map = _DEFAULT_ASSET_MAP.copy()
        raw_map = os.getenv("SYSTEMLINK_ASSET_MAP", "").strip()
        if raw_map:
            try:
                asset_map.update(json.loads(raw_map))
            except Exception:
                pass

        return cls(
            base_url=os.getenv("SYSTEMLINK_URL", ""),
            api_key=os.getenv("SYSTEMLINK_API_KEY", ""),
            verify_tls=verify_tls,
            timeout_s=timeout_s,
            program_name=os.getenv("SYSTEMLINK_PROGRAM_NAME", "FgenScopeTest"),
            operator=os.getenv("SYSTEMLINK_OPERATOR", "localadmin"),
            asset_map=asset_map,
            logger=logger,
        )

    @property
    def enabled(self) -> bool:
        return bool(self._base_url and self._api_key)

    # ------------------------------------------------------------------
    # Public interface (called by test_scope_with_fgen.py)
    # ------------------------------------------------------------------

    def publish_test_run_status(self, run_id: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Create or update a Test Monitor result for this run."""
        if not self.enabled:
            return
        if status == "running":
            self._create_result(run_id, details or {})
        else:
            self._update_result(run_id, status, details or {})

    def publish_test_case_status(
        self,
        run_id: str,
        case_index: int,
        case_label: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Create or update a Test Monitor step for this test case."""
        if not self.enabled:
            return
        key = f"{run_id}:{case_index}"
        if status == "running":
            self._step_start_times[key] = _utc_iso_now()
        else:
            started_at = self._step_start_times.pop(key, _utc_iso_now())
            self._create_step(run_id, case_index, case_label, status, started_at, details or {})

    def publish_asset_utilization(
        self,
        asset_id: str,
        state: str,
        run_id: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update an asset's properties in APM to reflect in-use / available state."""
        if not self.enabled:
            return
        sl_asset_id = self._asset_map.get(asset_id)
        if not sl_asset_id:
            self._logger.debug("No SystemLink asset UUID mapped for '%s'; skipping APM update.", asset_id)
            return

        if state == "in_use":
            new_props = {"inUseByRunId": run_id, "inUseSince": _utc_iso_now()}
        else:
            new_props = {"inUseByRunId": "", "inUseSince": ""}

        self._update_asset_properties(sl_asset_id, asset_id, new_props)

    # ------------------------------------------------------------------
    # Test Monitor helpers
    # ------------------------------------------------------------------

    def _create_result(self, run_id: str, details: Dict[str, Any]) -> None:
        url = f"{self._base_url}/nitestmonitor/v2/results"
        payload = {
            "results": [
                {
                    "programName": self._program_name,
                    "status": {"statusType": "RUNNING", "statusName": "Running"},
                    "startedAt": _utc_iso_now(),
                    "operator": self._operator,
                    "keywords": ["FgenScope", "automated"],
                    "properties": {
                        "runId": run_id,
                        "scope": details.get("scope_resource", ""),
                        "fgen": details.get("fgen_resource", ""),
                        "mode": details.get("mode", "HARDWARE"),
                    },
                }
            ]
        }
        response_body = self._post_json(url, payload)
        if response_body:
            try:
                sl_id = response_body["results"][0]["id"]
                self._result_ids[run_id] = sl_id
                self._logger.info("SystemLink result created: id=%s run_id=%s", sl_id, run_id)
            except (KeyError, IndexError, TypeError) as exc:
                self._logger.warning("Could not parse result id from response: %s", exc)

    def _update_result(self, run_id: str, status: str, details: Dict[str, Any]) -> None:
        sl_id = self._result_ids.get(run_id)
        if not sl_id:
            self._logger.warning("No SystemLink result id found for run_id=%s; cannot update.", run_id)
            return

        sl_status_type = "PASSED" if status == "passed" else "FAILED"
        url = f"{self._base_url}/nitestmonitor/v2/update-results"
        payload = {
            "results": [
                {
                    "id": sl_id,
                    "status": {"statusType": sl_status_type, "statusName": sl_status_type.capitalize()},
                    "updatedAt": _utc_iso_now(),
                    "properties": {
                        "runId": run_id,
                        "passedCases": str(details.get("passed_cases", "")),
                        "failedCases": str(details.get("failed_cases", "")),
                    },
                }
            ],
        }
        self._post_json(url, payload)
        self._logger.info("SystemLink result updated: id=%s status=%s", sl_id, sl_status_type)

    def _create_step(
        self,
        run_id: str,
        case_index: int,
        case_label: str,
        status: str,
        started_at: str,
        details: Dict[str, Any],
    ) -> None:
        sl_id = self._result_ids.get(run_id)
        if not sl_id:
            return  # result not yet created; skip step

        sl_status_type = "PASSED" if status == "passed" else "FAILED"
        url = f"{self._base_url}/nitestmonitor/v2/steps"
        payload = {
            "steps": [
                {
                    "resultId": sl_id,
                    "name": f"{case_index:02d}. {case_label}",
                    "stepType": "NumericLimitTest",
                    "status": {"statusType": sl_status_type, "statusName": sl_status_type.capitalize()},
                    "startedAt": started_at,
                    "updatedAt": _utc_iso_now(),
                    "inputs": [
                        {"name": "rmsErrorPct", "value": str(details.get("rms_error_pct", "")), "units": "%"},
                        {"name": "freqErrorPct", "value": str(details.get("freq_error_pct", "")), "units": "%"},
                    ],
                }
            ]
        }
        self._post_json(url, payload)

    # ------------------------------------------------------------------
    # APM helpers
    # ------------------------------------------------------------------

    def _update_asset_properties(
        self, sl_asset_id: str, display_name: str, new_props: Dict[str, str]
    ) -> None:
        url = f"{self._base_url}/niapm/v1/update-assets"
        payload = {
            "assets": [
                {
                    "id": sl_asset_id,
                    "properties": new_props,
                }
            ]
        }
        self._post_json(url, payload)
        self._logger.info(
            "SystemLink APM asset '%s' updated: %s", display_name, new_props
        )

    # ------------------------------------------------------------------
    # HTTP transport
    # ------------------------------------------------------------------

    def _post_json(self, url: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        headers = {
            "Content-Type": "application/json",
            "x-ni-api-key": self._api_key,
        }
        request = Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        ssl_context: Optional[ssl.SSLContext] = None
        if url.lower().startswith("https://") and not self._verify_tls:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

        try:
            with urlopen(request, timeout=self._timeout_s, context=ssl_context) as response:
                body = response.read()
                if body:
                    return json.loads(body)
                return None
        except HTTPError as exc:
            body = exc.read().decode(errors="replace")
            self._logger.warning("SystemLink POST %s failed: %s %s – %s", url, exc.code, exc.reason, body[:200])
        except URLError as exc:
            self._logger.warning("SystemLink POST %s failed: %s", url, exc.reason)
        except Exception as exc:
            self._logger.warning("SystemLink POST %s failed: %s", url, exc)
        return None


def _utc_iso_now() -> str:
    # Emit RFC3339 UTC form with a trailing Z for broad API compatibility.
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")




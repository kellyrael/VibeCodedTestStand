"""Publishes test results to NI SystemLink TestMonitor service.

Converts CaseExecution results from test_scope_with_fgen.py into
TestMonitor Result and Step objects, then sends them to the SystemLink
TestMonitor API (nisystemlink-clients package).
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from typing import Dict, List, Optional

try:
    from nisystemlink.clients.testmonitor import TestMonitorClient
    from nisystemlink.clients.testmonitor.models import (
        CreateResultRequest,
        CreateStepRequest,
        Status,
        StatusType,
        StepData,
        Measurement,
        NamedValue,
    )
    _systemlink_import_error: Exception | None = None
except Exception as _e:
    TestMonitorClient = None  # type: ignore[assignment]
    _systemlink_import_error = _e


class SystemLinkReporter:
    """Publishes scope/FGEN test results to NI SystemLink TestMonitor."""

    def __init__(self, logger: logging.Logger, host: Optional[str] = None, port: Optional[int] = None):
        """Initialize reporter with optional custom SystemLink host/port.

        Args:
            logger: Logger for reporting errors/status
            host: SystemLink server hostname (default: auto-discover)
            port: SystemLink server port (default: auto-discover)

        Raises:
            RuntimeError: If nisystemlink-clients is not installed or couldn't be imported
        """
        if TestMonitorClient is None:
            raise RuntimeError(
                f"nisystemlink-clients is not installed. "
                f"Install via: pip install nisystemlink-clients. "
                f"Import error: {_systemlink_import_error}"
            )
        self.logger = logger
        self.host = host
        self.port = port
        self.client: Optional[TestMonitorClient] = None

    def connect(self) -> None:
        """Connect to SystemLink TestMonitor service.

        Handles SSL certificate verification for self-signed certificates commonly used
        in internal SystemLink instances.
        """
        try:
            self.logger.info("Connecting to SystemLink TestMonitor...")

            # Prefer an explicit CA bundle so requests can validate the SystemLink cert chain.
            bundle_path = os.environ.get("REQUESTS_CA_BUNDLE")
            if bundle_path and os.path.isfile(bundle_path):
                self.logger.info("Using REQUESTS_CA_BUNDLE: %s", bundle_path)
            else:
                if bundle_path:
                    self.logger.warning("REQUESTS_CA_BUNDLE is set but invalid: %s", bundle_path)
                project_root = Path(__file__).resolve().parent
                candidate_paths = [
                    project_root / "certs" / "systemlink-root-ca.pem",
                    project_root / "certs" / "systemlink-server.pem",
                ]
                selected_bundle: Optional[Path] = None
                for candidate in candidate_paths:
                    if candidate.is_file():
                        selected_bundle = candidate
                        break

                if selected_bundle is not None:
                    os.environ["REQUESTS_CA_BUNDLE"] = str(selected_bundle)
                    self.logger.info("Configured REQUESTS_CA_BUNDLE from workspace: %s", selected_bundle)
                else:
                    self.logger.warning(
                        "No CA bundle configured. Expected one of: %s",
                        ", ".join(str(path) for path in candidate_paths),
                    )

            # Create client using default secure TLS behavior.
            self.client = TestMonitorClient()
            self.logger.info("Connected to SystemLink TestMonitor.")

        except Exception as exc:
            self.logger.error("Failed to connect to SystemLink TestMonitor: %s", exc)
            raise

    def disconnect(self) -> None:
        """Disconnect from SystemLink TestMonitor service."""
        if self.client is not None:
            try:
                # TestMonitorClient doesn't require explicit close, but we can set it to None.
                self.client = None
                self.logger.info("Disconnected from SystemLink TestMonitor.")
            except Exception as exc:
                self.logger.warning("Error during SystemLink disconnect: %s", exc)

    def publish_test_suite_result(
        self,
        suite_name: str,
        scope_resource: str,
        fgen_resource: str,
        executions: List[object],  # List[CaseExecution]
        passed: bool = True,
    ) -> str:
        """Publish an entire test suite result to SystemLink.

        Args:
            suite_name: Name of the test suite (used as Result.program_name)
            scope_resource: Scope instrument resource name
            fgen_resource: FGEN instrument resource name
            executions: List of CaseExecution objects from test_scope_with_fgen
            passed: Overall pass/fail status

        Returns:
            Result ID from SystemLink

        Raises:
            RuntimeError: If not connected or publish fails
        """
        if self.client is None:
            raise RuntimeError("Not connected to SystemLink. Call connect() first.")

        try:
            # Determine overall status
            status_type = StatusType.PASSED if passed else StatusType.FAILED
            overall_status = Status(status_type=status_type)

            # Create the TestResult
            result_request = CreateResultRequest(
                program_name=suite_name,
                status=overall_status,
                started_at=datetime.now(timezone.utc),
                operator="automated_test",
                system_id=f"{scope_resource}_{fgen_resource}",
                keywords=["scope_fgen_validation"],
                properties={
                    "scope_resource": scope_resource,
                    "fgen_resource": fgen_resource,
                    "test_type": "waveform_validation",
                },
            )

            self.logger.info("Creating TestMonitor Result: %s", suite_name)
            result_response = self.client.create_results([result_request])

            # API response shape varies by nisystemlink-clients version.
            # Newer versions return CreateResultsPartialSuccess(results=[Result(...)]).
            result_id: Optional[str] = None
            response_id = getattr(result_response, "id", None)
            if isinstance(response_id, str) and response_id.strip():
                result_id = response_id.split(",")[0].strip()
            else:
                response_results = getattr(result_response, "results", None)
                if isinstance(response_results, list) and response_results:
                    first_result_id = getattr(response_results[0], "id", None)
                    if isinstance(first_result_id, str) and first_result_id.strip():
                        result_id = first_result_id.strip()

            if not result_id:
                failed_items = getattr(result_response, "failed", None)
                error_text = getattr(result_response, "error", None)
                raise RuntimeError(
                    f"Failed to create result: no id returned. failed={failed_items!r}, error={error_text!r}"
                )

            self.logger.info("Created TestMonitor Result ID: %s", result_id)

            # Create steps for each test case execution
            step_requests: List[CreateStepRequest] = []
            for idx, execution in enumerate(executions, start=1):
                case_label = getattr(execution, "case", None)
                if case_label:
                    case_label = getattr(case_label, "label", f"Case {idx}")
                else:
                    case_label = f"Case {idx}"

                # CaseExecution does not expose a top-level `passed` field.
                # Use explicit per-check flags to compute step status.
                passed_exec = bool(getattr(execution, "passed_rms", False) and getattr(execution, "passed_freq", False))
                case_status_type = StatusType.PASSED if passed_exec else StatusType.FAILED
                case_status = Status(status_type=case_status_type)

                # Build measurement output data for the step
                measurements = []
                measured_rms = getattr(getattr(execution, "result", None), "measured_rms", None)
                if measured_rms is not None:
                    measurements.append(
                        Measurement(
                            name="RMS",
                            measurement=str(measured_rms),
                            lowLimit=str(getattr(execution, "expected_rms_low", "")),
                            highLimit=str(getattr(execution, "expected_rms_high", "")),
                            units="V",
                            status="PASSED" if getattr(execution, "passed_rms", False) else "FAILED",
                        )
                    )

                freq_hz = getattr(execution, "measured_frequency_hz", None)
                if freq_hz is not None:
                    measurements.append(
                        Measurement(
                            name="Frequency",
                            measurement=str(freq_hz),
                            lowLimit=str(getattr(execution, "frequency_low_limit_hz", "")),
                            highLimit=str(getattr(execution, "frequency_high_limit_hz", "")),
                            units="Hz",
                            status="PASSED" if getattr(execution, "passed_freq", False) else "FAILED",
                        )
                    )

                step_data = StepData(text=f"Test case: {case_label}", parameters=measurements if measurements else None)

                step_request = CreateStepRequest(
                    step_id=str(uuid4()),
                    result_id=result_id,
                    name=case_label,
                    step_type="waveform_measurement",
                    status=case_status,
                    started_at=datetime.now(timezone.utc),
                    data=step_data,
                    properties={
                        "case_index": str(idx),
                        "waveform": getattr(execution.case.fgen_config if hasattr(execution, "case") else None, "waveform", "unknown"),
                    },
                )
                step_requests.append(step_request)

            if step_requests:
                self.logger.info("Creating %d TestMonitor Steps for Result %s", len(step_requests), result_id)
                steps_response = self.client.create_steps(step_requests)
                self.logger.info("Created TestMonitor Steps: %d", len(step_requests))

            return result_id

        except Exception as exc:
            self.logger.error("Failed to publish test suite result: %s", exc, exc_info=True)
            raise

    def close(self) -> None:
        """Alias for disconnect()."""
        self.disconnect()


def create_reporter(
    logger: Optional[logging.Logger] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> Optional[SystemLinkReporter]:
    """Factory function to create a SystemLinkReporter with fallback.

    Returns None if nisystemlink-clients is not installed, allowing graceful degradation.

    Args:
        logger: Logger instance (creates a default if None)
        host: Optional custom SystemLink host
        port: Optional custom SystemLink port

    Returns:
        SystemLinkReporter instance, or None if unavailable
    """
    if logger is None:
        logger = logging.getLogger("systemlink_reporter")

    if TestMonitorClient is None:
        logger.warning("nisystemlink-clients not installed; SystemLink reporting disabled.")
        return None

    try:
        return SystemLinkReporter(logger, host=host, port=port)
    except Exception as exc:
        logger.warning("Failed to initialize SystemLink reporter: %s (type: %s)", exc, type(exc).__name__)
        import traceback
        logger.debug("Full traceback: %s", traceback.format_exc())
        return None


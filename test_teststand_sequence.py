from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import teststand_sequence


class TestTestStandSequence(unittest.TestCase):
    def _fake_runtime(self) -> SimpleNamespace:
        fake_case = SimpleNamespace(
            label="Fake case",
            expected_rms_v=1.0,
            expected_pk_pk_v=2.0,
            fgen_config=SimpleNamespace(
                waveform="SINE",
                frequency=1000.0,
                amplitude=2.0,
                dc_offset=0.0,
            ),
        )
        return SimpleNamespace(
            scope_resource="Scope1",
            fgen_resource="FGEN1",
            mode_tag="HARDWARE",
            log_dir=Path("."),
            test_log_path=Path("logs/test_results.log"),
            limits=SimpleNamespace(
                rms_tolerance=0.12,
                freq_tolerance=0.02,
                max_rms_error_pct=12.0,
                max_freq_error_pct=2.0,
            ),
            cases=[fake_case],
            run_id="run-123",
            systemlink_reporter=Mock(),
        )

    def _fake_execution(self) -> Mock:
        execution = Mock()
        execution.as_dict.return_value = {
            "index": 1,
            "label": "Fake case",
            "measured_rms_v": 1.0,
            "measured_frequency_hz": 1000.0,
            "passed": True,
        }
        execution.result = SimpleNamespace(measured_rms=1.0, passed=True)
        execution.expected_rms_low = 0.88
        execution.expected_rms_high = 1.12
        execution.passed_rms = True
        execution.measured_frequency_hz = 1000.0
        execution.frequency_low_limit_hz = 980.0
        execution.frequency_high_limit_hz = 1020.0
        execution.passed_freq = True
        return execution

    def test_setup_sequence_hardware_context(self) -> None:
        with patch("teststand_sequence.create_suite_runtime", return_value=self._fake_runtime()):
            context = teststand_sequence.setup_sequence(log_dir=".")
            self.assertIn("handle", context)
            self.assertEqual(context["mode"], "HARDWARE")
            self.assertNotIn("simulate", context)
            self.assertEqual(context["case_count"], 1)

    def test_initialize_devices_rejects_simulation_kwarg(self) -> None:
        with self.assertRaises(ValueError):
            teststand_sequence.initialize_devices(simulate=True)

    def test_cleanup_sequence_idempotent(self) -> None:
        with patch("teststand_sequence.create_suite_runtime", return_value=self._fake_runtime()):
            context = teststand_sequence.setup_sequence(log_dir=".")
        handle = context["handle"]

        with patch("teststand_sequence.cleanup_suite_runtime") as cleanup_mock:
            cleanup = teststand_sequence.cleanup_sequence(handle)
            cleanup_mock.assert_called_once()
            self.assertTrue(cleanup["cleaned_up"])

        cleanup_again = teststand_sequence.cleanup_sequence(handle)
        self.assertFalse(cleanup_again["cleaned_up"])

    def test_run_main_reports_running_status(self) -> None:
        runtime = self._fake_runtime()
        fake_execution = self._fake_execution()
        with patch("teststand_sequence.create_suite_runtime", return_value=runtime):
            context = teststand_sequence.setup_sequence(log_dir=".")

        handle = context["handle"]
        try:
            with patch("teststand_sequence.execute_test_case", return_value=fake_execution):
                with patch("teststand_sequence.emit_suite_summary", return_value=0):
                    summary = teststand_sequence.run_main(handle)

            self.assertTrue(summary["passed"])
            runtime.systemlink_reporter.publish_test_run_status.assert_called_once()
            call_kwargs = runtime.systemlink_reporter.publish_test_run_status.call_args.kwargs
            self.assertEqual(call_kwargs["run_id"], "run-123")
            self.assertEqual(call_kwargs["status"], "running")
        finally:
            teststand_sequence._ACTIVE_RUNTIMES.pop(handle, None)



if __name__ == "__main__":
    unittest.main()


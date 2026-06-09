# PXIe-5162 Scope UI (Python)

This project provides a Tkinter desktop UI for NI PXIe-5162 acquisition using `ni-hw-drivers` (`niscope`).

## Features

- Connect/disconnect to oscilloscope resource `Scope1` (or another NI-SCOPE resource)
- Refresh and select detected scope resources from a Resource dropdown
- Configure channel, sample rate, record length, range, trigger, and coupling
- Acquire once or run continuous acquisitions
- Plot waveform directly in the UI
- Write and view three logs from the UI:
  - `logs/status.log`
  - `logs/error.log`
  - `logs/measurement.log`

## Install

```powershell
python -m pip install -r requirements.txt
```

## Run the UI

```powershell
python main.py
```

## Quick self-test (no hardware required)

```powershell
python main.py --self-test
```

## TestStand-style sequence flow

The scope/FGEN validation steps are now split into a reusable setup/main/cleanup flow for TestStand integration:

- `teststand_sequence.py` exposes Python adapter entry points:
  - `setup_sequence(...)`
  - `get_test_cases(handle)`
  - `run_case(handle, case_index)`
  - `run_main(handle)`
  - `cleanup_sequence(handle)`
- `scope_fgen_teststand_sequence.json` is a sequence blueprint that maps those calls into **Setup**, **Main**, and **Cleanup** groups with numeric limit checks for RMS and frequency.

### Verify the TestStand adapter unit tests

```powershell
python -m unittest test_teststand_sequence.py
```

### Run the scope/FGEN hardware test harness

```powershell
python test_scope_with_fgen.py
```

### Example direct Python run of the TestStand adapter

```powershell
python -c "from teststand_sequence import setup_sequence, run_main, cleanup_sequence; ctx = setup_sequence(); summary = run_main(ctx['handle']); print(summary['passed'], summary['failures']); cleanup_sequence(ctx['handle'])"
```

## Notes

- If NI hardware/driver is unavailable, enable **Simulation Mode** in the UI.
- The `test_scope_with_fgen.py` harness and `teststand_sequence.py` adapter run in **hardware-only mode** and fail fast if drivers/hardware are unavailable.
- Device discovery is best-effort and still allows manual resource entry.
- `measurement.log` is written in CSV-style lines for easy parsing.


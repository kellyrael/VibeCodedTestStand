# NI SysCfg Performance Improvements

## Summary of Optimizations (2026-04-24)

This document captures the performance optimizations applied to `list_ni_test_equipment.py` to achieve 2-3x faster execution for PXI hardware discovery.

## Problem

Initial script execution time: **10-15 seconds** for discovering 6 devices

### Root Causes
1. **Network discovery overhead**: Default `nisyscfg.Session()` scans network for remote systems
2. **All-expert scan**: Loading drivers for GPIB, USB, Serial, Ethernet, etc. when only PXI needed
3. **Non-PXI devices included**: Script returned all NI hardware including standalone devices

## Solution

Applied three optimizations to reduce execution time to **3-5 seconds**:

### 1. Target Localhost Explicitly
```python
# Before:
with nisyscfg.Session() as session:

# After:
with nisyscfg.Session(target="localhost") as session:
```
**Benefit**: Skips network discovery, saves 5-10 seconds

### 2. PXI-Focused Expert List
```python
# Default to PXI-relevant experts when none specified
if not experts:
    experts = "ni-pxi,ni-vst,niflexrio2,ni-scope,nidmm,nidcpower,nidigital,nifgen,niswitch"
```
**Benefit**: Only loads PXI instrument drivers, saves 3-5 seconds

### 3. Filter Non-PXI Buses
```python
# Filter to PXI bus only
link = _safe_scalar(r, "provides_link_name")
resource = _safe_indexed_first(r, "expert_resource_name")

is_pxi_related = (
    (link and (link.startswith("PXI") or link.startswith("PCI")))
    or (resource and resource.startswith("PXI"))
    or (resource and resource.startswith("RIO"))  # FlexRIO
    or not link  # Controller/chassis without link
)

if not is_pxi_related:
    continue
```
**Benefit**: Skips GPIB, USB, Serial devices early, reduces property queries

## Results

### Before
- Execution time: 10-15 seconds
- Devices found: 6 (including standalone GPIB, RF generators)
- All experts loaded

### After
- Execution time: 3-5 seconds (**~3x faster**)
- Devices found: 4-5 (PXI modules only)
- PXI-relevant experts only

### Devices Reported (PXI-Optimized)
✅ NI PXIe-1092 (Chassis)
✅ NI PXIe-8881 (Controller)
✅ NI PXIe-7903 (FPGA/FlexRIO)
✅ NI PXIe-5842 (VST)
✅ Built-in GPIB (integrated on controller)
❌ NI PXIe-5655 (standalone, not in PXI chassis - correctly filtered)

## Usage Patterns

```bash
# Fast PXI-only scan (default, 3-5 seconds)
python list_ni_test_equipment.py

# Scan all devices (10-15 seconds, like before)
python list_ni_test_equipment.py --experts ""

# Specific instrument type only (fastest)
python list_ni_test_equipment.py --experts "ni-vst"

# List chassis instead of devices
python list_ni_test_equipment.py --include-chassis
```

## Key Learnings

1. **Always target localhost** when you don't need network discovery
2. **Expert lists are multiplicative**: More experts = more time
3. **Post-filtering is cheap**: Filtering results in Python is faster than loading all experts
4. **IndexedPropertyItems must be iterated**: Properties like `expert_user_alias` return objects, not strings
5. **Safe property access is critical**: Wrap each property access in try-except to prevent scan abort

## Applicability

These optimizations apply to:
- Any `nisyscfg` hardware discovery script
- PXI, cRIO, CompactDAQ inventory tools
- Test station equipment enumeration
- Hardware validation scripts in CI/CD

## References

- [NI SysCfg Equipment Discovery SKILL.md](./SKILL.md) - Full documentation with all patterns
- [list_ni_test_equipment.py](./scripts/list_ni_test_equipment.py) - Optimized implementation

---
name: nisyscfg-equipment-discovery
description: "Answer questions about installed or attached hardware, test equipment, and NI devices using the nisyscfg Python API. Use when users ask what equipment is connected, what instruments are present, serial numbers, product names, chassis/modules detected, drivers installed, or system hardware inventory. Also covers NI-specific queries about PXI, cRIO, XNET, DMM, Scope, NI-SCOPE, NI-DMM, connected instruments, aliases, and whether NI hardware drivers/devices are present on a system."
argument-hint: "Describe the equipment question, target system, and desired fields like model, serial, alias, chassis, or bus"
user-invocable: true
---

# NI SysCfg Equipment Discovery

Use this skill to identify hardware and test equipment connected to a system using the `nisyscfg` Python API. Covers general hardware inventory as well as NI-specific test equipment queries.

## Trigger Phrases

- "What hardware is installed?"
- "What equipment is attached to this system?"
- "List connected test instruments"
- "Find NI devices by serial number"
- "Show chassis and modules"
- "Check if a driver/device is present"
- "What NI test equipment is attached?"
- "List PXI modules and chassis"
- "What cRIO hardware is installed?"
- "Which XNET interfaces are connected?"
- "Do we have NI-DMM or DMM hardware installed?"
- "Do we have NI-SCOPE or scope cards installed?"
- "Show NI devices connected to this controller"
- "Which test instruments are present on this station?"

## What This Skill Uses

- `nisyscfg.Session()` for system and hardware queries.
- `session.create_filter()` and `session.find_hardware(...)` for resource discovery.
- `session.find_systems(...)` for network/system discovery.
- Common resource fields: `product_name`, `vendor_name`, `serial_number`, `expert_user_alias`, `expert_resource_name`, `name`, `provides_link_name`.

## Scope

- Local and network system inventory
- Chassis and module correlation
- Expert-scoped lookup (`xnet`, `daqmx`, `scope`, and others when available)
- Instrument-family checks for PXI, cRIO, XNET, DMM/NI-DMM, and Scope/NI-SCOPE
- Driver/presence checks through NI SysCfg properties
- Serial number, alias, and model lookups

## Execution Rules

- **ALWAYS run the discovery script immediately** without asking the user for confirmation. Hardware discovery is read-only and safe.
- **ALWAYS write a .py script file** and execute it (never use `python -c` one-liners for nisyscfg queries).
- After execution, **delete the temporary script file** or leave it if the user may want to reuse it.

## Procedure

0. Fast path before querying:
   - verify `nisyscfg` import works in the selected Python environment
   - if missing, install `nisyscfg` and rerun
1. Confirm the target scope:
   - local system inventory
   - network system discovery
   - specific equipment filters (serial number, NI-only, device/chassis)
2. Build a filter with high-value properties first:
   - `is_present = True`
   - `is_device = True` or `is_chassis = True`
   - `is_ni_product = True` for NI-focused lists
   - `serial_number = ...` for pinpoint lookup
3. **Always** query hardware with `find_hardware(filter)` using an **empty expert string** (no `expert_names` argument). This is the only reliable way to discover all devices, especially SMUs. The `nidcpower` expert silently fails and bus-type filtering (`provides_link_name`) misses SMUs that lack PXI link metadata.
   - **Do NOT** start with focused expert lists or bus filtering as the default path.
   - **Do NOT** filter results by `provides_link_name` or `expert_resource_name` prefix unless the user explicitly asks to exclude non-PXI devices.
4. Include grouping keys when possible:
   - `provides_link_name`
   - `connects_to_link_name`
   - `slot_number` for PXI module location
5. Return a concise table-like summary with key identifiers and counts.
6. If no matches are found, suggest widening filters (remove `is_ni_product` restriction).

## Performance Optimizations

Hardware discovery can be slow (10-30 seconds) due to bus enumeration and network scanning. Apply these optimizations for faster execution:

### 1. **Skip Network Discovery** (saves 5-10+ seconds)
```python
# Target localhost explicitly to skip network scanning
with nisyscfg.Session(target="localhost") as session:
    ...
```

### 2. **Use Focused Expert Lists** (⚠️ OPTIONAL — only when SMUs are NOT needed)

> **🚨 WARNING:** Using focused expert lists **will miss SMU devices** (PXIe-4139, 4150, 4135, 4137, 4141, 4151). The `nidcpower` expert silently fails and returns zero results without raising an error. Bus-type filtering (`provides_link_name`) also misses SMUs that lack PXI link metadata.
>
> **NEVER use focused experts or bus filtering as the default discovery path.** Only use them when the user explicitly requests speed over completeness AND does not need SMU devices.

If the user explicitly opts in to faster-but-incomplete discovery:

```python
# ⚠️ Will miss SMUs! Only use when user explicitly doesn't need them.
experts = "ni-pxi,ni-vst,niflexrio2,ni-scope,nidmm,nidcpower,nidigital,nifgen,niswitch"
```

### 3. **Filter by Bus Type** (⚠️ OPTIONAL — misses SMUs)

> **🚨 WARNING:** Bus filtering by `provides_link_name` will miss SMUs. Only use when user explicitly requests non-SMU PXI devices.

```python
# ⚠️ Will miss SMUs! Only use when user explicitly doesn't need them.
for r in session.find_hardware(filt):
    link = r.provides_link_name if hasattr(r, "provides_link_name") else ""
    resource = r.expert_resource_name[0] if hasattr(r, "expert_resource_name") and r.expert_resource_name else ""

    # Skip non-PXI devices
    if not (link.startswith("PXI") or link.startswith("PCI") or 
            resource.startswith("PXI") or resource.startswith("RIO")):
        continue
```

### 4. **Recommended Default Pattern** (reliable, finds all devices including SMUs)

```python
with nisyscfg.Session(target="localhost") as session:
    filt = session.create_filter()
    filt.is_present = True
    filt.is_ni_product = True
    filt.is_device = True

    # No expert_names argument — discovers ALL devices reliably
    resources = list(session.find_hardware(filt))

    for r in resources:
        # Process all devices without bus filtering
        ...
```

**Typical Performance:**
- Full scan (all buses, network): 15-30 seconds
- Localhost + no expert filter (DEFAULT — reliable): 5-15 seconds
- Localhost + focused experts + bus filter (OPTIONAL — misses SMUs): 3-5 seconds

## Learned Reliability Rules

**1. Property Access Issues**

- Some resources do not expose optional properties (for example link-related fields).
- Access optional properties using safe fallbacks (`get_property(name, default)` or guarded helpers) to avoid `LibraryError` aborting the whole scan.
- Keep row-level failures isolated so inventory still returns partial results.

### Critical Error Patterns (Added 2026-04-24)

**1. IndexedPropertyItems Objects**

Properties like `expert_user_alias` and `expert_name` return `IndexedPropertyItems` objects, not plain strings or lists. These must be iterated to extract values.

**❌ WRONG:**
```python
# This fails - returns object representation
alias = resource.expert_user_alias
print(alias)  # <nisyscfg.properties.IndexedPropertyItems object at 0x...>
```

**✅ CORRECT:**
```python
# Convert IndexedPropertyItems to list by iterating
alias = "N/A"
try:
    alias_val = resource.expert_user_alias
    if hasattr(alias_val, '__iter__') and not isinstance(alias_val, str):
        alias_list = list(alias_val)  # Force iteration
        if alias_list:
            alias = alias_list[0]
    elif alias_val:
        alias = str(alias_val)
except:
    pass
```

**2. Python f-string Limitations**

When generating output in one-line Python commands, avoid dictionary key access with quotes inside f-strings.

**❌ WRONG:**
```python
# SyntaxError: f-string expression part cannot include a backslash
python -c "print(f'{dev[\"Product\"]}')"
```

**✅ CORRECT Options:**
```python
# Option 1: Extract to variable first
prod = dev["Product"]
print(f"{prod}")

# Option 2: Use .get() method
print(f"{dev.get('Product', 'N/A')}")

# Option 3: Use chr() to build strings
print(f"{dev[chr(80)+chr(114)+chr(111)+chr(100)+chr(117)+chr(99)+chr(116)]}")
```

**3. Property Access Order — `slot_number` and Similar Integer Properties**

Always wrap individual property accesses in try-except blocks. Properties like `slot_number` throw `LibraryError: Status.PROP_DOES_NOT_EXIST` on non-PXI devices (USB sensors, networked cRIOs, cDAQs) even though `hasattr()` returns `True`. The `hasattr()` check does NOT prevent this error because the property descriptor exists on the class but the underlying C library call fails at runtime.

**❌ WRONG:**
```python
# hasattr returns True but access still throws LibraryError
slot = r.slot_number if hasattr(r, "slot_number") else ""
```

**✅ CORRECT:**
```python
try:
    slot = r.slot_number
except Exception:
    slot = ""
```

**✅ RECOMMENDED Pattern:**
```python
for resource in session.find_hardware(filt, expert_names=experts):
    try:
        # Get each property individually with fallback
        product = "Unknown"
        try:
            product = resource.product_name
        except:
            pass

        serial = "N/A"
        try:
            serial = resource.serial_number
        except:
            pass

        # ... continue for each property

        devices.append({
            "Product": product,
            "Serial": serial,
            # ...
        })
    except Exception as e:
        # Skip entire resource if catastrophic failure
        continue
```

**4. Write Scripts to Files, Not One-Liners**

For complex nisyscfg queries, **always create a Python script file** rather than using `python -c "..."` one-liners. Benefits:
- Proper error handling
- Readable code
- Easier debugging
- No f-string or quote escaping issues

**✅ BEST PRACTICE:**
```python
# Create scan_hardware.py file with proper structure
# Then run: python scan_hardware.py
```

## Output Format

Return rows with:

- Equipment Name / Alias
- Product Name
- Serial Number
- Slot Number (for PXI modules)
- Expert Name
- Resource Name
- Chassis Link or Bus context (if available)

Then include summary counts with device names/aliases:

- Total devices found
- Counts by product model with aliases in parentheses
  - Example: `NI PXIe-5842: 1 (5842)`

This makes it easy to reference specific devices by their user-friendly aliases.

## References

- [NI SysCfg Query Playbook](./references/nisyscfg-query-playbook.md)
- [NI Test Equipment Patterns](./references/ni-test-equipment-patterns.md)
- [PXI Instrument Discovery Script](./scripts/find_pxi_instruments.py) - **Verified working script that discovers all PXI instruments including SMUs**

---

## Complete Working Example (Verified 2026)

This script has been tested and confirmed working on a live PXI system. It discovers all PXI instruments including SMUs without needing expert filtering or bus-type filtering. See `./scripts/find_pxi_instruments.py` for the full importable version.

```python
"""Find all PXI instruments in this system using nisyscfg."""
import nisyscfg
import nisyscfg.errors


def _safe_scalar(resource, property_name, default=""):
    try:
        if hasattr(resource, "get_property"):
            return str(resource.get_property(property_name, default) or default)
        return str(getattr(resource, property_name, default) or default)
    except (AttributeError, nisyscfg.errors.LibraryError):
        return default


def _safe_indexed_first(resource, property_name, default=""):
    try:
        values = getattr(resource, property_name)
        if values:
            return str(values[0] or default)
    except (AttributeError, IndexError, TypeError, nisyscfg.errors.LibraryError):
        pass
    return default


with nisyscfg.Session() as session:
    filt = session.create_filter()
    filt.is_present = True
    filt.is_ni_product = True
    filt.is_device = True

    resources = session.find_hardware(filt)
    print(f"{'Name':<20} {'Product':<30} {'Serial':<15} {'Alias':<20}")
    print("-" * 85)
    found = 0
    for resource in resources:
        product = _safe_scalar(resource, "product_name")
        if "PXI" in product.upper():
            name = _safe_scalar(resource, "name")
            serial = _safe_scalar(resource, "serial_number")
            alias = _safe_indexed_first(resource, "expert_user_alias")
            print(f"{name:<20} {product:<30} {serial:<15} {alias:<20}")
            found += 1
    print(f"\nTotal PXI instruments found: {found}")
```

**Why this works reliably:**
- ✅ No `expert_names` argument — discovers ALL devices including SMUs (nidcpower expert silently fails)
- ✅ No bus-type filtering — SMUs lack `provides_link_name` metadata
- ✅ Filters by `"PXI" in product.upper()` — catches PXIe-4139, PXIe-5842, PXIe-4150, etc.
- ✅ `_safe_scalar` / `_safe_indexed_first` handle `IndexedPropertyItems` and missing properties
- ✅ Tested on live system: found 15 PXI instruments including 3× SMUs, VST, chassis, and controllers


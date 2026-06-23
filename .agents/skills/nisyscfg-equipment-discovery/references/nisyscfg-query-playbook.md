# NI SysCfg Query Playbook

This playbook is based on usage patterns from `tkrebes/nisyscfg-python`.

## Install

```bash
pip install nisyscfg
```

## Minimal Hardware Inventory

```python
import nisyscfg

with nisyscfg.Session() as session:
    filt = session.create_filter()
    filt.is_present = True
    filt.is_ni_product = True
    filt.is_device = True

    for resource in session.find_hardware(filt):
        print(resource.name, resource.product_name, resource.serial_number)
```

## Common Filter Fields

- `is_present`
- `is_ni_product`
- `is_device`
- `is_chassis`
- `serial_number`
- `connects_to_link_name`

## Common Hardware Properties

- `name` (alias fallback behavior)
- `product_name`
- `vendor_name`
- `serial_number`
- `expert_name`
- `expert_user_alias`
- `expert_resource_name`
- `provides_link_name`

## Network/System Discovery

Use `find_systems(...)` when the user asks about systems on the network or installable targets.

## Expert-Scoped Queries

Use `expert_names="xnet"` or CSV/list when users ask about specific subsystems.

## Troubleshooting

0. Startup failures:
   - `ModuleNotFoundError: nisyscfg`: install dependency in active env and rerun.
1. Empty result set:
   - remove expert restriction
   - remove NI-only filter
   - verify `is_present` intent for simulated/offline devices
2. Property access issues:
   - fall back to `resource.get_property(name, default)` when optional properties vary by device.
   - catch `nisyscfg.errors.LibraryError` for optional fields and continue processing remaining resources.

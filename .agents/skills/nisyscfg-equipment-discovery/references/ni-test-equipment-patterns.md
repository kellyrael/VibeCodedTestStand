# NI Test Equipment Query Patterns

## Base Query For NI Devices

```python
import nisyscfg

with nisyscfg.Session() as session:
    filt = session.create_filter()
    filt.is_present = True
    filt.is_ni_product = True
    filt.is_device = True

    for r in session.find_hardware(filt):
        print(r.name, r.product_name, r.serial_number)
```

## Fast Startup Checklist

1. Validate environment has `nisyscfg` installed.
2. Run device inventory first (`is_device=True`) to confirm baseline visibility.
3. Run chassis inventory second (`is_chassis=True`) for topology context.

## Chassis Query

```python
with nisyscfg.Session() as session:
    filt = session.create_filter()
    filt.is_present = True
    filt.is_ni_product = True
    filt.is_chassis = True

    for chassis in session.find_hardware(filt):
        print(chassis.name, chassis.product_name, chassis.provides_link_name)
```

## Module-By-Chassis Pattern

Use `connects_to_link_name` to find modules attached to a known chassis link.

## Expert-Scoped Query

Set `expert_names="xnet"` or CSV expert names for subsystem-specific inventory.

## Frequently Useful Fields

- `name`
- `product_name`
- `serial_number`
- `vendor_name`
- `expert_name`
- `expert_user_alias`
- `expert_resource_name`
- `provides_link_name`
- `connects_to_link_name`

## No Results Checklist

1. Remove expert restriction.
2. Keep `is_present=True` only and retry.
3. Remove `is_device`/`is_chassis` split and test separately.

## Optional Property Safety

Some devices may raise `nisyscfg.errors.LibraryError` when reading optional properties. Use safe access wrappers and defaults so one missing property does not fail the full inventory run.

"""Find all PXI instruments in this system using nisyscfg.

This is the primary discovery script for the nisyscfg-equipment-discovery skill.
It queries all present NI devices and filters for PXI products by product name.

Usage:
    python find_pxi_instruments.py
"""
from __future__ import annotations

import nisyscfg
import nisyscfg.errors


def _safe_scalar(resource, property_name: str, default: str = "") -> str:
    """Return a scalar resource property without failing on unsupported properties."""
    try:
        if hasattr(resource, "get_property"):
            return str(resource.get_property(property_name, default) or default)
        return str(getattr(resource, property_name, default) or default)
    except (AttributeError, nisyscfg.errors.LibraryError):
        return default


def _safe_indexed_first(resource, property_name: str, default: str = "") -> str:
    """Return first indexed string property value when available."""
    try:
        values = getattr(resource, property_name)
        if values:
            return str(values[0] or default)
    except (AttributeError, IndexError, TypeError, nisyscfg.errors.LibraryError):
        pass
    return default


def find_pxi_instruments() -> list[dict[str, str]]:
    """Discover all PXI instruments on the local system.

    Returns a list of dicts with keys: name, product, serial, alias.
    """
    rows: list[dict[str, str]] = []
    with nisyscfg.Session() as session:
        filt = session.create_filter()
        filt.is_present = True
        filt.is_ni_product = True
        filt.is_device = True

        resources = session.find_hardware(filt)
        for resource in resources:
            product = _safe_scalar(resource, "product_name")
            if "PXI" in product.upper():
                rows.append(
                    {
                        "name": _safe_scalar(resource, "name"),
                        "product": product,
                        "serial": _safe_scalar(resource, "serial_number"),
                        "alias": _safe_indexed_first(resource, "expert_user_alias"),
                    }
                )
    return rows


def main() -> None:
    rows = find_pxi_instruments()
    if not rows:
        print("No PXI instruments found.")
        return

    print(f"{'Name':<20} {'Product':<30} {'Serial':<15} {'Alias':<20}")
    print("-" * 85)
    for row in rows:
        print(f"{row['name']:<20} {row['product']:<30} {row['serial']:<15} {row['alias']:<20}")
    print(f"\nTotal PXI instruments found: {len(rows)}")


if __name__ == "__main__":
    main()

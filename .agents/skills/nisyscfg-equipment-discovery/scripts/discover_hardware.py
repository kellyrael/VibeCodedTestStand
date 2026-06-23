import nisyscfg

def discover_hardware():
    with nisyscfg.Session() as session:
        filt = session.create_filter()
        filt.is_present = True
        filt.is_ni_product = True
        filt.is_device = True

        print(f"{'Name':<20} {'Product':<30} {'Serial':<15} {'Alias':<20}")
        print("-" * 85)
        for resource in session.find_hardware(filt):
            name = resource.name or "Unknown"
            product = resource.product_name or "Unknown"
            serial = resource.serial_number or "N/A"
            alias = resource.expert_user_alias[0] if resource.expert_user_alias else "N/A"
            print(f"{name:<20} {product:<30} {serial:<15} {alias:<20}")

discover_hardware()
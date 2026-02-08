def calculate_discount(orders_count: int) -> int:
    if orders_count < 3:
        return 5
    elif orders_count < 5:
        return 7
    else:
        return 10

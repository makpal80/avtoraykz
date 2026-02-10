def calculate_discount(orders_count: int) -> int:
    if orders_count == 1:
        return 3
    if orders_count == 2:
        return 4
    if orders_count == 3:
        return 5
    if orders_count == 4:
        return 7
    else:
        return 10

def calculate_discount(orders_count: int) -> int:
    if orders_count <= 1:
        return 3
    elif orders_count == 2:
        return 4
    elif orders_count == 3:
        return 5
    elif orders_count == 4:
        return 7
    else:
        return 10

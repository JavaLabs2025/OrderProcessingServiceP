from datetime import date
from typing import List, Callable, Optional
from src.shop.models import User, Item, PromoCode


class DiscountCalculator:
    # time_provider по умолчанию возвращает реальное "сегодня", но в тестах мы его подменим
    def __init__(self, time_provider: Callable[[], date] = date.today):
        self._time_provider = time_provider

    def calculate_discount(self, user: User, total_amount: float) -> float:
        if total_amount < 0:
            raise ValueError("Total amount cannot be negative")

        discount_percentage = 0.0

        if user.is_vip:
            discount_percentage += 0.10

        if total_amount >= 5000.0:
            discount_percentage += 0.05

        if discount_percentage > 0.15:
            discount_percentage = 0.15

        return total_amount - (total_amount * discount_percentage)

    def apply_promo_code(self, current_total: float, promo_code: Optional[PromoCode]) -> float:
        if not promo_code:
            return current_total

        today = self._time_provider()
        if today > promo_code.expiry_date:
            raise ValueError("Promo code expired")

        return max(0.0, current_total - promo_code.discount_amount)


class DeliveryCalculator:
    BASE_FEE = 200.0

    def calculate_delivery(self, items: List[Item], delivery_zone: str) -> float:
        if not items:
            return 0.0

        total_delivery = self.BASE_FEE

        if delivery_zone == "ZONE_2":
            total_delivery += 300.0
        elif delivery_zone == "ZONE_3":
            total_delivery += 500.0

        for item in items:
            if item.weight > 5.0:
                total_delivery += (item.weight - 5.0) * 50 * item.quantity
            if item.is_fragile:
                total_delivery += 150.0 * item.quantity

        return total_delivery

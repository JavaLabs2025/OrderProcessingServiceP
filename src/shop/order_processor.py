import uuid
from typing import List, Optional

from src.shop.pricing import DiscountCalculator, DeliveryCalculator
from src.shop.models import User, Item, Order, PromoCode, OrderStatus
from src.shop.interfaces import InventoryService, PaymentGateway


class OrderProcessor:
    def __init__(self,
                 inventory_service: InventoryService,
                 payment_gateway: PaymentGateway,
                 discount_calculator: DiscountCalculator,
                 delivery_calculator: DeliveryCalculator):
        self.inventory_service = inventory_service
        self.payment_gateway = payment_gateway
        self.discount_calculator = discount_calculator
        self.delivery_calculator = delivery_calculator

    def process_order(self, user: User, items: List[Item], delivery_zone: str,
                      promo_code: Optional[PromoCode] = None) -> Order:
        if not items:
            raise ValueError("Order must contain at least one item")

        # 1. Проверяем наличие
        raw_total = 0.0
        for item in items:
            if not self.inventory_service.in_stock(item.id, item.quantity):
                raise RuntimeError(f"Item {item.id} is out of stock")
            raw_total += item.price * item.quantity

        # 2. Скидки
        discounted_price = self.discount_calculator.calculate_discount(user, raw_total)
        price_after_promo = self.discount_calculator.apply_promo_code(discounted_price, promo_code)

        # 3. Доставка
        delivery_cost = self.delivery_calculator.calculate_delivery(items, delivery_zone)
        final_price = price_after_promo + delivery_cost

        # 4. Оплата (С механизмом Retry - 3 попытки)
        payment_success = False
        for attempt in range(3):
            try:
                payment_success = self.payment_gateway.charge(user, final_price)
                if payment_success:
                    break
            except Exception as e:
                if attempt == 2:
                    raise RuntimeError("Payment gateway unavailable after 3 attempts") from e

        if not payment_success:
            raise RuntimeError(f"Payment rejected for user {user.id}")

        # 5. Списываем товары
        for item in items:
            self.inventory_service.deduct_item(item.id, item.quantity)

        # 6. Формируем заказ
        order = Order(
            order_id=str(uuid.uuid4()),
            user=user,
            items=items,
            final_price=final_price,
            status=OrderStatus.PAID
        )
        return order

    def cancel_order(self, order: Order) -> None:
        if order.status == OrderStatus.SHIPPED:
            raise RuntimeError("Cannot cancel a shipped order")

        if order.status == OrderStatus.PAID:
            self.payment_gateway.refund(order.user, order.final_price)

        for item in order.items:
            self.inventory_service.return_item(item.id, item.quantity)

        order.status = OrderStatus.CANCELLED

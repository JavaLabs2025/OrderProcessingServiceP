from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import List, Optional


class OrderStatus(Enum):
    CREATED = "CREATED"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


@dataclass
class User:
    id: str
    is_vip: bool


@dataclass
class Item:
    id: str
    price: float
    quantity: int
    weight: float
    is_fragile: bool


@dataclass
class PromoCode:
    code: str
    discount_amount: float
    expiry_date: date


@dataclass
class Order:
    order_id: str
    user: User
    items: List[Item]
    final_price: float = 0.0
    status: OrderStatus = OrderStatus.CREATED

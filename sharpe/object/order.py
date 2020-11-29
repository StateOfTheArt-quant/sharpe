#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
from decimal import Decimal
import numpy as np
from datetime import datetime

from sharpe.const import ORDER_STATUS, ORDER_TYPE, SIDE, POSITION_EFFECT, POSITION_DIRECTION
from sharpe.utils import id_gen, decimal_rounding_floor, get_position_direction
from sharpe.utils.repr import property_repr, properties
from sharpe.context import Context

class Order(object):

    order_id_gen = id_gen(int(time.time()) * 10000)

    __repr__ = property_repr

    def __init__(self):
        self._order_id = None
        self._calendar_dt = None
        self._trading_dt = None
        self._quantity = None
        self._order_book_id = None
        self._side = None
        self._position_effect = None
        self._message = None
        self._filled_quantity = None
        self._status = None
        self._frozen_price = None
        self._type = None
        self._avg_price = None
        self._transaction_cost = None
        self._kwargs = None

    @staticmethod
    def _str_to_enum(enum_class, s):
        return enum_class.__members__[s]

    def get_state(self):
        return {
            'order_id': self._order_id,
            'secondary_order_id': self._secondary_order_id,
            'calendar_dt': self._calendar_dt,
            'trading_dt': self._trading_dt,
            'order_book_id': self._order_book_id,
            'quantity': self._quantity,
            'side': self._side,
            'position_effect': self._position_effect,
            'message': self._message,
            'filled_quantity': self._filled_quantity,
            'status': self._status,
            'frozen_price': self._frozen_price,
            'type': self._type,
            'transaction_cost': self._transaction_cost,
            'avg_price': self._avg_price,
            'kwargs': self._kwargs,
        }

    def set_state(self, d):
        self._order_id = d['order_id']
        if 'secondary_order_id' in d:
            self._secondary_order_id = d['secondary_order_id']
        self._calendar_dt = d['calendar_dt']
        self._trading_dt = d['trading_dt']
        self._order_book_id = d['order_book_id']
        self._quantity = d['quantity']
        self._side = SIDE[d["side"]]
        self._position_effect = POSITION_EFFECT[d["position_effect"]] if d["position_effect"] else None
        self._message = d['message']
        self._filled_quantity = d['filled_quantity']
        self._status = ORDER_STATUS[d["order_status"]]
        self._frozen_price = d['frozen_price']
        self._type = ORDER_TYPE[d["type"]]
        self._transaction_cost = d['transaction_cost']
        self._avg_price = d['avg_price']
        self._kwargs = d['kwargs']

    @classmethod
    def __from_create__(cls, order_book_id, quantity, side, style, position_effect, **kwargs):
        context = Context.get_instance()
        order = cls()
        order._order_id = next(order.order_id_gen)
        order._calendar_dt = context.calendar_dt
        order._trading_dt = context.trading_dt
        order._quantity = quantity
        order._order_book_id = order_book_id
        order._side = side
        order._position_effect = position_effect
        order._message = ""
        order._filled_quantity = 0
        order._status = ORDER_STATUS.PENDING_NEW
        if isinstance(style, LimitOrder):
            order._frozen_price = style.get_limit_price()
            order._type = ORDER_TYPE.LIMIT
        else:
            order._frozen_price = 0.
            order._type = ORDER_TYPE.MARKET
        order._avg_price = 0
        order._transaction_cost = 0
        order._kwargs = kwargs
        return order

    @property
    def order_id(self) -> int:
        """
        [int] the unique identifier
        """
        return self._order_id

    @property
    def trading_datetime(self) -> datetime:
        """
        the trading datetime of the order
        """
        return self._trading_dt

    @property
    def datetime(self) -> datetime:
        """
        the creation datetime of the order
        """
        return self._calendar_dt

    @property
    def quantity(self) ->datetime:
        """
        the quantity of the order
        """
        if np.isnan(self._quantity):
            raise RuntimeError("Quantity of order {} is not supposed to be nan.".format(self.order_id))
        return self._quantity

    @property
    def unfilled_quantity(self) -> int:
        """
        the unfilled quantity of order
        """
        return self.quantity - self.filled_quantity

    @property
    def order_book_id(self) -> str:
        """
        the unique code of the trading contract
        """
        return self._order_book_id

    @property
    def side(self) -> SIDE:
        """
        the side of the order
        """
        return self._side

    @property
    def position_effect(self) -> POSITION_EFFECT:
        """
        position effect of order (for future contract usage)
        """
        if self._position_effect is None:
            if self._side == SIDE.BUY:
                return POSITION_EFFECT.OPEN
            else:
                return POSITION_EFFECT.CLOSE
        return self._position_effect

    @property
    def position_direction(self) -> POSITION_DIRECTION:
        return get_position_direction(self._side, self._position_effect)

    @property
    def message(self) -> str:
        """
        message like why rejected
        """
        return self._message

    @property
    def filled_quantity(self) -> int:
        """
        the has beed filled part of the order
        """
        if np.isnan(self._filled_quantity):
            raise RuntimeError("Filled quantity of order {} is not supposed to be nan.".format(self.order_id))
        return self._filled_quantity

    @property
    def status(self) -> ORDER_STATUS:
        """
        the status of order
        """
        return self._status

    @property
    def price(self):
        """
        the price of the order in the context of the LIMIT order
        """
        return 0 if self.type == ORDER_TYPE.MARKET else self.frozen_price

    @property
    def type(self) -> ORDER_TYPE:
        """
        the type of order, LIMIT OR MARKET ORDER
        """
        return self._type

    @property
    def avg_price(self) -> float:
        """
        the average price of transaction of the order
        """
        return self._avg_price

    @property
    def transaction_cost(self) -> float:
        """
        transaction fee
        """
        return self._transaction_cost

    @property
    def frozen_price(self) -> float:
        """
        """
        if np.isnan(self._frozen_price):
            raise RuntimeError("Frozen price of order {} is not supposed to be nan.".format(self.order_id))
        return self._frozen_price

    @property
    def kwargs(self):
        return self._kwargs

    def is_final(self):
        return self._status not in {
            ORDER_STATUS.PENDING_NEW,
            ORDER_STATUS.ACTIVE,
            ORDER_STATUS.PENDING_CANCEL
        }

    def is_active(self):
        return self.status == ORDER_STATUS.ACTIVE

    def active(self):
        self._status = ORDER_STATUS.ACTIVE

    def set_pending_cancel(self):
        if not self.is_final():
            self._status = ORDER_STATUS.PENDING_CANCEL

    def fill(self, trade):
        quantity = trade.last_quantity
        assert self.filled_quantity + quantity <= self.quantity
        new_quantity = self._filled_quantity + quantity
        self._transaction_cost += trade.commission + trade.tax
        self._filled_quantity = new_quantity
        if self.unfilled_quantity == 0:
            self._status = ORDER_STATUS.FILLED
        if trade.position_effect != POSITION_EFFECT.MATCH:
            self._avg_price = (self._avg_price * self._filled_quantity + trade.last_price * quantity) / new_quantity

    def mark_rejected(self, reject_reason):
        if not self.is_final():
            self._message = reject_reason
            self._status = ORDER_STATUS.REJECTED
        
    def mark_cancelled(self, cancelled_reason, user_warn=True):
        if not self.is_final():
            self._message = cancelled_reason
            self._status = ORDER_STATUS.CANCELLED
            if user_warn:
                pass
                #user_system_log.warn(cancelled_reason)

    def set_frozen_price(self, value):
        self._frozen_price = value

    def set_secondary_order_id(self, secondary_order_id):
        self._secondary_order_id = str(secondary_order_id)

    def __simple_object__(self):
        return properties(self)


class OrderStyle(object):
    def get_limit_price(self):
        raise NotImplementedError


class MarketOrder(OrderStyle):
    __repr__ = ORDER_TYPE.MARKET.__repr__

    def get_limit_price(self):
        return None


class LimitOrder(OrderStyle):
    __repr__ = ORDER_TYPE.LIMIT.__repr__

    def __init__(self, limit_price):
        self.limit_price = float(limit_price)

    def get_limit_price(self):
        return self.limit_price

    def round_price(self, tick_size):
        if tick_size:
            with decimal_rounding_floor():
                limit_price_decimal = Decimal("{:.4f}".format(self.limit_price))
                tick_size_decimal = Decimal("{:.4f}".format(tick_size))
                self.limit_price = float((limit_price_decimal / tick_size_decimal).to_integral() * tick_size_decimal)
        else:
            pass
            #user_system_log.warn('Invalid tick size: {}'.format(tick_size))
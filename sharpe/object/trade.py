#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time

from sharpe.utils import id_gen, get_position_direction
from sharpe.utils.repr import property_repr, properties
from sharpe.core.context import Context
from sharpe.const import POSITION_EFFECT, SIDE


class Trade(object):

    __repr__ = property_repr

    trade_id_gen = id_gen(int(time.time()) * 10000)

    def __init__(self):
        self._calendar_dt = None
        self._trading_dt = None
        self._price = None
        self._amount = None
        self._order_id = None
        self._commission = None
        self._tax = None
        self._trade_id = None
        self._close_today_amount = None
        self._side = None
        self._position_effect = None
        self._order_book_id = None
        self._frozen_price = None

    @classmethod
    def __from_create__(
            cls, order_id, price, amount, side, position_effect, order_book_id, commission=0., tax=0.,
            trade_id=None, close_today_amount=0, frozen_price=0, calendar_dt=None, trading_dt=None
    ):

        trade = cls()
        trade_id = trade_id or next(trade.trade_id_gen)

        for value in (price, amount, commission, tax, frozen_price):
            if value != value:
                raise RuntimeError(
                    "price, amount, commission, tax and frozen_price of trade {trade_id} is not supposed to be nan, current_value is {price}, {amount}, {commission}, {tax}, {frozen_price}"
                .format(
                    trade_id=trade_id, price=price, amount=amount, commission=commission, tax=tax,
                    frozen_price=frozen_price
                ))

        context = Context.get_instance()
        trade._calendar_dt = calendar_dt or context.calendar_dt
        trade._trading_dt = trading_dt or context.trading_dt
        trade._price = price
        trade._amount = amount
        trade._order_id = order_id
        trade._commission = commission
        trade._tax = tax
        trade._trade_id = trade_id
        trade._close_today_amount = close_today_amount
        trade._side = side
        trade._position_effect = position_effect
        trade._order_book_id = order_book_id
        trade._frozen_price = frozen_price
        return trade

    order_book_id = property(lambda self: self._order_book_id)
    trading_datetime = property(lambda self: self._trading_dt)
    datetime = property(lambda self: self._calendar_dt)
    order_id = property(lambda self: self._order_id)
    last_price = property(lambda self: self._price)
    last_quantity = property(lambda self: self._amount)
    commission = property(lambda self: self._commission)
    tax = property(lambda self: self._tax)
    transaction_cost = property(lambda self: self.commission + self.tax)
    side = property(lambda self: self._side)
    position_effect = property(lambda self: self._position_effect or (
        POSITION_EFFECT.OPEN if self._side == SIDE.BUY else POSITION_EFFECT.CLOSE
    ))
    position_direction = property(lambda self: get_position_direction(self._side, self._position_effect))
    exec_id = property(lambda self: self._trade_id)
    frozen_price = property(lambda self: self._frozen_price)
    close_today_amount = property(lambda self: self._close_today_amount)

    def __simple_object__(self):
        return properties(self)
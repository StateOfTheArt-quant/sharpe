#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import six
import math
import numpy as np
from decimal import Decimal, getcontext
from itertools import chain
from typing import Dict, List, Optional, Union
from sharpe.core.context import Context
from sharpe.const import (DEFAULT_ACCOUNT_TYPE, ORDER_TYPE, POSITION_DIRECTION,
                           POSITION_EFFECT, SIDE)
from sharpe.object.order import LimitOrder, MarketOrder, Order, OrderStyle
from sharpe.utils import is_valid_price
from sharpe.mod.sys_account.position import Position
from sharpe.core.events import Event, EVENT
import pdb
KSH_MIN_AMOUNT = 200

def cal_style(price, style):
    if price is None and style is None:
        return MarketOrder()

    if style is not None:
        if not isinstance(style, OrderStyle):
            raise RuntimeError
        return style

    if isinstance(price, OrderStyle):
        # 为了 order_xxx('RB1710', 10, MarketOrder()) 这种写法
        if isinstance(price, LimitOrder):
            if np.isnan(price.get_limit_price()):
                raise RuntimeError("Limit order price should not be nan.")
        return price

    if np.isnan(price):
        raise RuntimeError(u"Limit order price should not be nan.")

    return LimitOrder(price)

def _get_account_position_ins(order_book_id):
    account = Context.get_instance().portfolio.accounts[DEFAULT_ACCOUNT_TYPE.STOCK]
    position = account.get_position(order_book_id, POSITION_DIRECTION.LONG)
    return account, position


def is_cash_enough(order, account, warn=True):
    order_cost = order.frozen_price*order.quantity #instrument.calc_cash_occupation(order.frozen_price, order.quantity, order.position_direction)
    order_cost += Context.get_instance().get_order_transaction_cost(order)
    if order_cost <= account.cash:
        return True
    if warn:
        print("Order Creation Failed: not enough money to buy {order_book_id}, needs {cost_money:.2f},"
              " cash {cash:.2f}").format(
                order_book_id=order.order_book_id,
                cost_money=order_cost,
                cash=account.cash,
            )
    return False

def _get_ksh_amount(amount):
    return 0 if abs(amount) < KSH_MIN_AMOUNT else amount // 1


def get_positions() -> List[Position]:
    """
    get all available positions，
    :example:
    ..  code-block:: python3
        [In] get_positions()
        [Out]
        [BookingPosition({'order_book_id': '000014.XSHE', 'quantity': 100, 'direction': POSITION_DIRECTION.LONG, 'old_quantity': 0, 'trading_pnl': 1.0, 'avg_price': 9.56, 'last_price': 0, 'position_pnl': 0.0}),
         BookingPosition({'order_book_id': '000010.XSHE', 'quantity': 100, 'direction': POSITION_DIRECTION.LONG, 'old_quantity': 0, 'trading_pnl': 0.0, 'avg_price': 3.09, 'last_price': 0, 'position_pnl': 0.0})]
    """
    portfolio = Context.get_instance().portfolio
    return portfolio.get_positions()

def get_position(order_book_id:str, direction:POSITION_DIRECTION=POSITION_DIRECTION.LONG) -> Position:

    """
    get the position object from one specific order_book_id，
    :param order_book_id: 
    :param direction:
    :example:
    ..  code-block:: python3
        [In] get_position('000014.XSHE','long_positions")
        [Out]
        [BookingPosition({'order_book_id': '000014.XSHE', 'quantity': 100, 'direction': POSITION_DIRECTION.LONG, 'old_quantity': 0, 'trading_pnl': 1.0, 'avg_price': 9.56, 'last_price': 0, 'position_pnl': 0.0})]
    """
    portfolio = Context.get_instance().portfolio
    return portfolio.get_position(order_book_id, direction)


def _submit_order(order_book_id, amount, side, position_effect, style, quantity, auto_switch_order_value):
    # param: amount: the target quantity of this order
    # param: quantity: the quantity of exist position of order_book_id
    context = Context.get_instance()
    if isinstance(style, LimitOrder):
        if not is_valid_price(style.get_limit_price()):
            raise RuntimeError((u"Limit order price should be positive"))
    price = context.get_last_price(order_book_id)
    if not is_valid_price(price):
        print("Order Creation Failed: [{order_book_id}] No market data").format(order_book_id=order_book_id)
        return
    round_lot = 100

    if side in [SIDE.BUY, side.SELL]:
        if not (side == SIDE.SELL and quantity == abs(amount)):
                # KSH can buy(sell) 201, 202 shares
                amount = int(Decimal(amount) / Decimal(round_lot)) * round_lot

    if amount == 0:
        print("Order Creation Failed: 0 order quantity, order_book_id={order_book_id}").format(order_book_id=order_book_id)
        return
    order = Order.__from_create__(order_book_id, abs(amount), side, style, position_effect)
    if order.type == ORDER_TYPE.MARKET:
        order.set_frozen_price(price)
    if side == SIDE.BUY and auto_switch_order_value:
        account, position = _get_account_position_ins(order_book_id)
        if not is_cash_enough(order, account):
            print("insufficient cash, use all remaining cash({}) to create order").format(account.cash)
            return _order_value(account, position, order_book_id, account.cash, style)
    return order

def _order_shares(order_book_id, amount, style, quantity, auto_switch_order_value):
    side, position_effect = (SIDE.BUY, POSITION_EFFECT.OPEN) if amount > 0 else (SIDE.SELL, POSITION_EFFECT.CLOSE)
    return _submit_order(order_book_id, amount, side, position_effect, style, quantity, auto_switch_order_value)


def _order_value(account, position, order_book_id, cash_amount, style):
    context = Context.get_instance()
    if cash_amount > 0:
        cash_amount = min(cash_amount, account.cash)
    if isinstance(style, LimitOrder):
        price = style.get_limit_price()
    else:
        price = context.get_last_price(order_book_id)
        if not is_valid_price(price):
            print("Order Creation Failed: [{order_book_id}] No market data").format(order_book_id=order_book_id)
            return

    amount = int(Decimal(cash_amount) / Decimal(price))

    round_lot = 100#int(ins.round_lot)
    if cash_amount > 0:
        amount = int(Decimal(amount) / Decimal(round_lot)) * round_lot
        while amount > 0:
            expected_transaction_cost = context.get_order_transaction_cost(Order.__from_create__(
                order_book_id, amount, SIDE.BUY, LimitOrder(price), POSITION_EFFECT.OPEN
            ))
            if amount * price + expected_transaction_cost <= cash_amount:
                break
            amount -= round_lot
        else:
            print("Order Creation Failed: 0 order quantity")
            return

    if amount < 0:
        amount = max(amount, -position.closable)

    return _order_shares(order_book_id, amount, style, position.quantity, auto_switch_order_value=False)

def order_value(order_book_id, cash_amount, price=None, style=None):
    account, position = _get_account_position_ins(order_book_id)
    return _order_value(account, position, order_book_id, cash_amount, cal_style(price, style))

def order_target_value(order_book_id, cash_amount, price=None, style=None):
    account, position = _get_account_position_ins(order_book_id)
    if cash_amount == 0:
        return _submit_order(order_book_id, position.closable, SIDE.SELL, POSITION_EFFECT.CLOSE, cal_style(price, style),
                             position.quantity, False)
    return _order_value(account, position, order_book_id, cash_amount - position.market_value, cal_style(price, style))

def order_percent(order_book_id, percent, price=None, style=None):
    account, position = _get_account_position_ins(order_book_id)
    return _order_value(account, position, order_book_id, account.total_value * percent, cal_style(price, style))

def order_target_percent(order_book_id, percent, price=None, style=None):
    account, position = _get_account_position_ins(order_book_id)
    if percent == 0:
        return _submit_order(order_book_id, position.closable, SIDE.SELL, POSITION_EFFECT.CLOSE, cal_style(price, style),
                             position.quantity, False)
    else:
        return _order_value(
            account, position, order_book_id, account.total_value * percent - position.market_value, cal_style(price, style)
        )


def order_target_weights(target_weights:Dict[str, float]) -> List[Order]:
    """
    make the account position to touch the target position
    :param target_weights: a dictionary contain the target weight of position
    :example:
    .. code-block:: python
        # adjust positions, to make the '000001.XSHE' to touch the target percent of account 10%
        # make the '000002.XSHE' to touch the target percent of account 15% 
        order_target_weights({
            '000001.XSHE': 0.1
            '000002.XSHE': 0.15
        })
    """

    total_percent = sum(six.itervalues(target_weights))
    if total_percent > 1 and not np.isclose(total_percent, 1):
        raise RuntimeError("total percent should be lower than 1, current: {}").format(total_percent)

    context = Context.get_instance()
    account = context.portfolio.accounts[DEFAULT_ACCOUNT_TYPE.STOCK]
    account_value = account.get_current_trading_dt_total_value()
    
    
    #
    target_quantities = {}
    for order_book_id, target_percent in target_weights.items():

        if target_percent < 0:
            raise RuntimeError("target percent of {} should between 0 and 1, current: {}".format(
                order_book_id, target_percent
            ))
        price = context.get_last_price(order_book_id)
        #print("trading_dt:{} current price: {}".format(context.trading_dt, price))
        if not is_valid_price(price):
            print("Order Creation Failed: [{order_book_id}] No market data".format(order_book_id=order_book_id))
            
            continue
        target_quantity = account_value * target_percent / price
        target_quantities[order_book_id] = int(round(target_quantity/100) * 100) #target_quantity#

    close_orders, open_orders = [], []
    current_quantities = {
        p.order_book_id: p.quantity for p in account.get_positions() if p.direction == POSITION_DIRECTION.LONG
    }
    for order_book_id, quantity in current_quantities.items():
        if order_book_id not in target_weights:
            close_orders.append(Order.__from_create__(
                order_book_id, quantity, SIDE.SELL, MarketOrder(), POSITION_EFFECT.CLOSE
            ))

    round_lot = 100
    for order_book_id, target_quantity in target_quantities.items():
        if order_book_id in current_quantities:
            delta_quantity = target_quantity - current_quantities[order_book_id]
        else:
            delta_quantity = target_quantity

        if delta_quantity >= round_lot:
            delta_quantity = math.floor(delta_quantity / round_lot) * round_lot
            open_orders.append(Order.__from_create__(
                order_book_id, delta_quantity, SIDE.BUY, MarketOrder(), POSITION_EFFECT.OPEN
            ))
        elif delta_quantity < -1:
            delta_quantity = math.floor(delta_quantity)
            close_orders.append(Order.__from_create__(
                order_book_id, abs(delta_quantity), SIDE.SELL, MarketOrder(), POSITION_EFFECT.CLOSE
            ))

    to_submit_orders = []
    for order in chain(close_orders, open_orders):
        #print("to submit order: {}".format(order))
        to_submit_orders.append(order)
    return to_submit_orders


def order_target_quantities(target_quantities:Dict[str, int]) -> List[Order]:
    """
    make the account position to touch the target quantities
    :param target_quantities: a dictionary contain the target quantities of position
    :example:
    .. code-block:: python
        # adjust positions, to make the '000001.XSHE' to touch the target quantities 800
        # make the '000002.XSHE' to touch the target quantities 400 
        order_target_quantities({
            '000001.XSHE': 800
            '000002.XSHE': 400
        })
    """

    context = Context.get_instance()
    account = context.portfolio.accounts[DEFAULT_ACCOUNT_TYPE.STOCK]

    close_orders, open_orders = [], []
    current_quantities = {
        p.order_book_id: p.quantity for p in account.get_positions() if p.direction == POSITION_DIRECTION.LONG
    }
    
    # close all position if the order_book_id not in the key list of target_quantities
    for order_book_id, quantity in current_quantities.items():
        if order_book_id not in target_quantities:
            close_orders.append(Order.__from_create__(
                order_book_id, quantity, SIDE.SELL, MarketOrder(), POSITION_EFFECT.CLOSE
            ))

    round_lot = 100
    for order_book_id, target_quantity in target_quantities.items():
        if order_book_id in current_quantities:
            delta_quantity = target_quantity - current_quantities[order_book_id]
        else:
            delta_quantity = target_quantity

        if delta_quantity >= round_lot:
            delta_quantity = math.floor(delta_quantity / round_lot) * round_lot
            open_orders.append(Order.__from_create__(
                order_book_id, delta_quantity, SIDE.BUY, MarketOrder(), POSITION_EFFECT.OPEN
            ))
        elif delta_quantity < -1:
            delta_quantity = math.floor(delta_quantity)
            close_orders.append(Order.__from_create__(
                order_book_id, abs(delta_quantity), SIDE.SELL, MarketOrder(), POSITION_EFFECT.CLOSE
            ))

    to_submit_orders = []
    for order in chain(close_orders, open_orders):
        #print("to submit order: {}".format(order))
        to_submit_orders.append(order)
    return to_submit_orders


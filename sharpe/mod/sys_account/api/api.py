#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import six
import math
import numpy as np
from itertools import chain
from typing import Dict, List, Optional, Union
from sharpe.context import Context
from sharpe.const import (DEFAULT_ACCOUNT_TYPE, ORDER_TYPE, POSITION_DIRECTION,
                           POSITION_EFFECT, SIDE)
from sharpe.object.order import LimitOrder, MarketOrder, Order, OrderStyle
from sharpe.utils import is_valid_price

def order_target_portfolio(target_portfolio:Dict[str, float]) -> List[Order]:
    """
    make the account position to touch the target postion
    :param target_portfolio: a dictionary contain the target weight of position
    :example:
    .. code-block:: python
        # adjust positions, to make the '000001.XSHE' to touch the target percent of account 10%
        # make the '000002.XSHE' to touch the target percent of account 15% 
        order_target_portfolio({
            '000001.XSHE': 0.1
            '000002.XSHE': 0.15
        })
    """

    total_percent = sum(six.itervalues(target_portfolio))
    if total_percent > 1 and not np.isclose(total_percent, 1):
        raise RuntimeError("total percent should be lower than 1, current: {}").format(total_percent)

    context = Context.get_instance()
    account = context.portfolio.accounts[DEFAULT_ACCOUNT_TYPE.STOCK]
    account_value = account.total_value
    target_quantities = {}
    for order_book_id, target_percent in target_portfolio.items():

        if target_percent < 0:
            raise RuntimeError("target percent of {} should between 0 and 1, current: {}".format(
                order_book_id, target_percent
            ))
        price = context.get_last_price(order_book_id)
        if not is_valid_price(price):
            print("Order Creation Failed: [{order_book_id}] No market data".format(order_book_id=order_book_id))
            
            continue
        target_quantities[order_book_id] = account_value * target_percent / price

    close_orders, open_orders = [], []
    current_quantities = {
        p.order_book_id: p.quantity for p in account.get_positions() if p.direction == POSITION_DIRECTION.LONG
    }
    for order_book_id, quantity in current_quantities.items():
        if order_book_id not in target_portfolio:
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
            to_submit_orders.append(order)
    return to_submit_orders


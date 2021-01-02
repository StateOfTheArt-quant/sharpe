#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
from decimal import getcontext, ROUND_FLOOR
from contextlib import contextmanager
from sharpe.const import (
    SIDE, POSITION_EFFECT, POSITION_DIRECTION
)


def is_valid_price(price):
    return not (price is None or np.isnan(price) or price <= 0)


def merge_dicts(*dict_args):
    result = {}
    for d in dict_args:
        result.update(d)
    return result


def id_gen(start=1):
    i = start
    while True:
        yield i
        i += 1

def get_position_direction(side, position_effect):
    if position_effect is None:
        return POSITION_DIRECTION.LONG
    if side == SIDE.CONVERT_STOCK:
        return POSITION_DIRECTION.LONG
    if (side == SIDE.BUY and position_effect == POSITION_EFFECT.OPEN) or (side == SIDE.SELL and position_effect in (
        POSITION_EFFECT.CLOSE, POSITION_EFFECT.CLOSE_TODAY, POSITION_EFFECT.EXERCISE
    )):
        return POSITION_DIRECTION.LONG
    return POSITION_DIRECTION.SHORT


@contextmanager
def decimal_rounding_floor():
    original_rounding_option = getcontext().rounding
    getcontext().rounding = ROUND_FLOOR
    yield
    getcontext().rounding = original_rounding_option

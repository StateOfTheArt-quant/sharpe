#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np

def calc_draw_down(bar_returns:list):
    bar_returns_np = np.array(bar_returns)
    net_value_np = (1+bar_returns_np).cumprod()
    expanding_max = np.maximum.accumulate(net_value_np)
    draw_down = (net_value_np - expanding_max)/expanding_max
    return draw_down

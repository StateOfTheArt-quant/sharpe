#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
np.random.seed(123)

from sharpe.utils.plot.plot_performance import plot_performance

trading_number = 10000
returns = np.random.random((trading_number,3))/100
date_index = pd.date_range(start="2020-01-01", periods=trading_number)
returns = pd.DataFrame(returns, columns=["a","b","c"], index=date_index)
cumulative_net_value = (returns + 1).cumprod()


output = plot_performance(cumulative_net_value)




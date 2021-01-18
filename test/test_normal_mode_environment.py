#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sharpe.utils.mock_data import create_toy_feature
from sharpe.data.data_source import DataSource
from sharpe.environment import TradingEnv

feature_df, price_s = create_toy_feature(order_book_ids_number=2, feature_number=3, random_seed=111)
data_source = DataSource(feature_df=feature_df, price_s=price_s)
    
env= TradingEnv(data_source=data_source, look_backward_window=2)
print('--------------------------------------------')
from sharpe.core.context import Context
print("current context \n",Context.get_instance().__dict__)
    
    
from sharpe.mod.sys_account.api import order_target_weights
to_submit_orders = order_target_weights({"000001.XSHE":0.5})
    
state, reward, is_done, info = env.step(action=to_submit_orders)
print(state, reward, is_done)
# to_submit_orders2 = order_target_portfolio({"000001.XSHE":0.2})
# state, reward, is_done, info = env.step(action=to_submit_orders2)
# print(state, reward, is_done)


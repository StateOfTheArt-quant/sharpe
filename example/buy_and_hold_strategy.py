#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from sharpe.utils.mock_data import create_toy_feature
from sharpe.data.data_source import DataSource
from sharpe.environment import TradingEnv
from sharpe.mod.sys_account.api import order_target_weights
import random
random.seed(111)

feature_df, price_s = create_toy_feature(order_book_ids_number=3, feature_number=3, start="2020-01-01", end="2020-05-11", random_seed=111)
data_source = DataSource(feature_df=feature_df, price_s=price_s)

env = TradingEnv(data_source=data_source,
                        look_backward_window=10,
                        mode='non-rl',
                        starting_cash={'STOCK': 1000000000},
                        commission_multiplier=0.5, #the default commission fee rate is 0.0005, charged bilaterally, commission_multiplier
                        min_commission=5,          #the minimum commission fee is 5
                        tax_multiplier=1)

state = env.reset()


def equal_weight_buy_and_hold_strategy(order_book_ids:list) -> dict:
    order_book_ids_num = len(order_book_ids)
    init_allocation = 1/order_book_ids_num
    target_weight_dict = {x:init_allocation for x in order_book_ids}
    return target_weight_dict

NOT_TRADE_FLAG = True

while True:
      print("the current trading_dt is: {}".format(env.trading_dt))
      #action = risk_parity_strategy(state)
      if NOT_TRADE_FLAG:
          order_book_ids = state.index.get_level_values(0).drop_duplicates()
          target_weight_dict = equal_weight_buy_and_hold_strategy(list(order_book_ids))
          action = order_target_weights(target_weight_dict)
          next_state, reward, done, info = env.step(action)
          
          NOT_TRADE_FLAG = False
      else:
          # the action can be set to None, means keep the previous position unchange and do nothing.
          next_state, reward, done, info = env.step(action=None)
      print("the reward of this action: {}".format(reward))
      print("the next state is \n {}".format(next_state))
      if done:
          break
      else:
          state = next_state
env.render(auto_open=False)


from sharpe.utils.risk import Risk, DAILY, WEEKLY
bar_returns = env._context.tracker.bar_returns
risk = Risk(bar_returns=bar_returns, period=DAILY)
performance = risk.performance() 
print(performance)

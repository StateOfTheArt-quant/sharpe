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
                        look_backward_window=5,
                        mode='rl',
                        starting_cash={'STOCK': 1000000000},
                        commission_multiplier=0, #the default commission fee rate is 0.0005, charged bilaterally, commission_multiplier
                        min_commission=0,          #the minimum commission fee is 5
                        tax_multiplier=0)

# ========================================== #
# data structure wrapper                     #
# ========================================== #
# see next post
from sharpe.utils.wrapper.numpy_wrapper import Numpy
wrapper_env = Numpy(env)

state = wrapper_env.reset()

print(state)
print(type(state))
# the data structure of state now is pd.DataFrame
while True:
      print("the current trading_dt is: {}".format(env.trading_dt))
      print("the current state: \n {}".format(state))
      # the action can be set to None, means keep the previous position unchange and do nothing.
      next_state, reward, done, info = wrapper_env.step(action=None)
      print("the reward of this action: {}".format(reward))
      print("the next state is \n {}".format(next_state))
      if done:
          break
      else:
          state = next_state



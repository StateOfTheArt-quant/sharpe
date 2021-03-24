#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
from sharpe.utils.mock_data import create_toy_feature
import time

feature_df, price_s = create_toy_feature(order_book_ids_number=500, feature_number=1, start="2020-01-01", end="2020-12-31", frequency="D", random_seed=123)
feature_df = feature_df.rename(columns={"feature_1":"prediction"})

from sharpe.data.data_source import DataSource
data_source = DataSource(feature_df=feature_df, price_s=price_s)


# ============================================= #
# step2: create trading environment             #
# ============================================= #
from sharpe.environment import TradingEnv
env = TradingEnv(data_source=data_source, look_backward_window=1)

#state =env.reset()

# ============================================================================ #
# step3: create your strategy(policy), a mapping from state to action          #
# ============================================================================ #
from sharpe.mod.sys_account.api import order_target_weights

def pick_stocks_by_prediction(state:pd.DataFrame, top_number=50) -> list:
    sorted_prediction = state["prediction"].sort_values(ascending=False)
    to_target = sorted_prediction[:top_number].droplevel(1)
    # equal weight
    
    target_weight = to_target.map(lambda x: 1/top_number) 
    target_weight_dict = target_weight.to_dict()
    print(target_weight_dict)
    #call in-built trade API function
    action = order_target_weights(target_weight_dict)
    return action


# =================================================================== #
# backtest bar-by-bar                                                 #
# =================================================================== #
start_time = time.time()

state = env.reset()
while True:
      print("the current trading_dt is: {}".format(env.trading_dt))
      action = pick_stocks_by_prediction(state)

      next_state, reward, done, info = env.step(action)
      print("the reward of this action: {}".format(reward))
      print("the next state is \n {}".format(next_state))
      if done:
          break
      else:
          state = next_state
env.render(auto_open=False)


# =============================================== #
# evaluate strategy performance                   #
# =============================================== #
from sharpe.utils.risk import Risk, WEEKLY

bar_returns = env._context.tracker.bar_returns
risk = Risk(bar_returns=bar_returns, period=WEEKLY)
performance = risk.performance() 
print(performance)
print("total time elapsed: {}".format(time.time() - start_time))
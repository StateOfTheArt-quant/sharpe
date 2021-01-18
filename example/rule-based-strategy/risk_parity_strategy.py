#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
(weekly frequency) risk-parity strategy backtest
"""
# ======================================== #
# step1: create your own data_source       #
# ======================================== #
# step 1.1: create your features and price(in this case, assume it's a weekly trading frequency strategy)
import pandas as pd
import numpy as np
np.random.seed(124)

# create toy price and your features you care about of your srategy
order_book_ids = ["stock1", "stock2", "stock3"]
start_date = "2020-01-01"
frequency = "W-FRI"
periods = 100

trading_datetime = pd.date_range(start=start_date, periods=periods, freq=frequency)
# the first level of multiindex should be instrument name, the second level should be trading datetime
multi_index = pd.MultiIndex.from_product([order_book_ids, trading_datetime],names=["order_book_id","datetime"])

price_list= []
for i in order_book_ids:
    start_price = np.random.randint(100)
    price = np.random.uniform(low = start_price, high = start_price+10, size = len(trading_datetime))
    price_list.append(price)    
price_all = np.hstack(price_list).round(decimals = 2)
price_s = pd.Series(price_all, index=multi_index, name='price')


feature_df = price_s.groupby("order_book_id").pct_change().dropna()
feature_df.name = "returns"
feature_df = feature_df.to_frame()


from sharpe.data.data_source import DataSource
data_source = DataSource(feature_df=feature_df, price_s=price_s)


# ============================================= #
# step2: create trading environment             #
# ============================================= #
from sharpe.environment import TradingEnv
env = TradingEnv(data_source=data_source, look_backward_window=20)

#state =env.reset()

# ============================================================================ #
# step3: create your strategy(policy), a mapping from state to action          #
# ============================================================================ #
from sharpe.mod.sys_account.api import order_target_weights

def risk_parity_strategy(state:pd.DataFrame) -> list:
    volatility = state["returns"].groupby(level=0).std()
    volatility_reverse = 1/volatility
    weight = volatility_reverse / volatility_reverse.sum()
    weight_dict = weight.to_dict()
    
    #call in-built trade API function
    action = order_target_weights(weight_dict)
    return action


# =================================================================== #
# backtest bar-by-bar                                                 #
# =================================================================== #
state = env.reset()
while True:
     print("the current trading_dt is: {}".format(env.trading_dt))
     action = risk_parity_strategy(state)

     next_state, reward, done, info = env.step(action)
     print("the reward of this action: {}".format(reward))
     print("the next state is \n {}".format(next_state))
     if done:
          break
     else:
          state = next_state
env.render()


# =============================================== #
# evaluate strategy performance                   #
# =============================================== #
from sharpe.utils.risk import Risk, WEEKLY

bar_returns = env._context.tracker.bar_returns
risk = Risk(bar_returns=bar_returns, period=WEEKLY)
performance = risk.performance() 
print(performance)






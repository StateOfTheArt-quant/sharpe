#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from sharpe.utils.mock_data import create_toy_feature
from sharpe.data.data_source import DataSource
from sharpe.environment import TradingEnv
import random
random.seed(111)

feature_df, price_s = create_toy_feature(order_book_ids_number=2, feature_number=3, start="2020-01-01", end="2020-01-11", random_seed=111)

print("feature_df: \n{}".format(feature_df))
print("price_s: \n{}".format(price_s))

data_source = DataSource(feature_df=feature_df, price_s=price_s)

look_backward_window = 2    
env= TradingEnv(data_source=data_source, look_backward_window=2)
print('--------------------------------------------')



# ============================================ #
# here sharpe just serve as a data replayer    #
# ============================================ #

state = env.reset()


while True:
    print("the current trading_dt is: {}".format(env.trading_dt))
    
    print("current state: \n{}".format(state))

    next_state, reward, done, info = env.step(action=None)
    
    print("the reward of this action: {}".format(reward))
    #print("the next state is \n {}".format(next_state))
    if done:
        break
    else:
        state = next_state

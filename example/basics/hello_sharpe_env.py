#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from sharpe.utils.mock_data import create_toy_feature
from sharpe.data.data_source import DataSource
from sharpe.environment import TradingEnv
from sharpe.mod.sys_account.api import order_target_weights
import random
random.seed(111)

feature_df, price_s = create_toy_feature(order_book_ids_number=2, feature_number=3, start="2020-01-01", end="2020-01-11", random_seed=111)
data_source = DataSource(feature_df=feature_df, price_s=price_s)

look_backward_window = 2    
starting_cash = {"STOCK":1000000, "FUTURE":10000}
env= TradingEnv(data_source=data_source, look_backward_window=2, starting_cash=starting_cash)
print('--------------------------------------------')

the_first_stock_id = data_source.get_available_order_book_ids()[0]



def your_strategy(state):
    """
    here is a random strategy, only trade the first stock with a random target percent
    """

    target_percent_of_postion =  round(random.uniform(0, 1), 2)
    # call trade API
    target_pososition_dict = {the_first_stock_id : target_percent_of_postion}
    print("the target portfolio is to be: {}".format(target_pososition_dict))
    # call trade API
    action = order_target_weights(target_pososition_dict)
    return action


state = env.reset()


# action = your_strategy(state)

# next_state, reward, done, info = env.step(action)


while True:
    print("the current trading_dt is: {}".format(env.trading_dt))
    action = your_strategy(state)
    print("my action is: \n {}".format(action))
    next_state, reward, done, info = env.step(action)
    
    print("the reward of this action: {}".format(reward))
    print("the next state is \n {}".format(next_state))
    if done:
        break
    else:
        state = next_state


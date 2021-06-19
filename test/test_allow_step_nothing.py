#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from sharpe.utils.mock_data import create_toy_feature
from sharpe.data.data_source import DataSource
from sharpe.environment import TradingEnv

from sharpe.const import POSITION_DIRECTION

feature_df, price_s = create_toy_feature(order_book_ids_number=1, feature_number=3, random_seed=111)
data_source = DataSource(feature_df=feature_df, price_s=price_s)

STOCK_INIT_CASH = 1000000
    
env= TradingEnv(data_source=data_source, look_backward_window=2, mode="non-rl", starting_cash= {"STOCK":STOCK_INIT_CASH},
                commission_multiplier=0,
                min_commission=0,
                tax_multiplier=0)

print('--------------------------------------------')
from sharpe.core.context import Context
#print("current context \n",Context.get_instance().__dict__)


print("------------the first trading date: {}--------------------------".format(env.trading_dt))
state = env.reset()
print("------------the first state: \n {}--------".format(state))
    
from sharpe.mod.sys_account.api import order_target_weights
order_book_id = "000001.XSHE"
target_weight = 0.5
to_submit_orders = order_target_weights({order_book_id:target_weight})
order = to_submit_orders[0]

trade_price = data_source.get_last_price(order_book_id="000001.XSHE", dt=env.trading_dt)
target_quantity = (STOCK_INIT_CASH * target_weight)/ trade_price
target_quantity = int(round(target_quantity/100) * 100)
assert target_quantity == order.quantity
    
state, reward, is_done, info = env.step(action=to_submit_orders)
print(state, reward, is_done)


portfolio = Context.get_instance().portfolio
account = portfolio.stock_account
position1 = account.get_position("000001.XSHE", POSITION_DIRECTION.LONG)
print(position1)
available_cash = account.cash

target_market_value = trade_price * target_quantity
assert target_market_value == position1.market_value

total_value = account.total_value 
target_reward = (total_value - STOCK_INIT_CASH)/STOCK_INIT_CASH
print(target_reward, reward)
assert target_reward ==  reward


print("------------the second trading date: {}--------------------------".format(env.trading_dt))
current_last_price = data_source.get_last_price(order_book_id="000001.XSHE", dt=env.trading_dt)
print("---------the action is None, means hold the previous position and do nothing---------------------")
state, reward, is_done, info = env.step(action=None)

# print(state, reward, is_done)
position2 = portfolio.get_position("000001.XSHE", POSITION_DIRECTION.LONG)
print(position2)
target_market_value = current_last_price * target_quantity
assert target_market_value == position2.market_value

target_total_value = target_market_value + available_cash
assert target_total_value == account.total_value

target_reward = (target_total_value - total_value)/total_value
print(target_reward, reward)
assert target_reward.round(4) == reward.round(4)

total_value = account.total_value

print("------------the third trading date: {}--------------------------".format(env.trading_dt))
current_last_price = data_source.get_last_price(order_book_id="000001.XSHE", dt=env.trading_dt)

state, reward, is_done, info = env.step(action=None)
# print(state, reward, is_done)
position3 = portfolio.get_position("000001.XSHE", POSITION_DIRECTION.LONG)
print(position3)
target_market_value = current_last_price * target_quantity
assert target_market_value == position3.market_value

target_total_value = target_market_value + available_cash
assert target_total_value == account.total_value

target_reward = (target_total_value - total_value)/total_value
print(target_reward, reward)
assert target_reward.round(4) == reward.round(4)


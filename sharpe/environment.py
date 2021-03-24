#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import gym
import pdb
import pandas as pd
from sharpe.mod.sys_simulation.event_source import SimulationEventSource
from sharpe.core.context import Context
from sharpe.core.events import Event, EVENT
from sharpe.core.executor import Executor, RLExecutor
from sharpe.mod.sys_account import Portfolio
from sharpe.core.strategy import Strategy
from sharpe.mod.sys_simulation.simulation_broker import SimulationBroker
from sharpe.mod.sys_transaction_cost.deciders import CNStockTransactionCostDecider
from sharpe.mod.sys_tracker.tracker import Tracker 
from sharpe.utils.plot.plot_performance import plot_performance

class TradingEnv(gym.Env):
    
    def __init__(self, data_source,
                 look_backward_window=1, 
                 mode="rl",
                 starting_cash = {"STOCK":1000000},
                 commission_multiplier=1,
                 min_commission=5,
                 tax_multiplier=1) -> None:
        
        self.look_backward_window = look_backward_window
        self.mode = mode
        self.starting_cash = starting_cash
        self.commission_multiplier = commission_multiplier
        self.min_commission = min_commission
        self.tax_multiplier = tax_multiplier
        
        self._context = Context(look_backward_window=look_backward_window)
        
        #set data_source
        self._context.set_data_source(data_source)
        
        #set event_source
        event_source = SimulationEventSource()
        self._context.set_event_source(event_source)
        
        #set broker
        broker = SimulationBroker(self._context)
        self._context.set_broker(broker)
        
        # transaction_cost decider
        transaction_cost_decider = CNStockTransactionCostDecider(commission_multiplier=commission_multiplier, min_commission=min_commission, tax_multiplier=tax_multiplier)
        self._context.set_transaction_cost_decider("CS", transaction_cost_decider)
        
        # setup account and portfolio
        portfolio = Portfolio(starting_cash=starting_cash, init_positions={})
        self._context.set_portfolio(portfolio)
        
        # setup a tracker to record key info
        tracker = Tracker(self._context)
        self._context.set_tracker(tracker)
        self._context.event_bus.publish_event(Event(EVENT.POST_SYSTEM_INIT))
        
        #setUP executor
        if mode == "rl":
            self._executor = RLExecutor(self._context)
        else:
            self._executor = Executor(self._context)
        
        # user strategy
        user_strategy = Strategy(self._context)
            
    def reset(self):
        state = Context.get_instance().history_bars()
        return state
    
    def step(self, action):
        
        reward, is_done, info = self._executor.send(action)
        #pdb.set_trace()
        next_state = Context.get_instance().history_bars()
        return next_state, reward, is_done, info
    
    @property
    def trading_dt(self):
        return self._context.trading_dt
    
    
    def render(self, auto_open=True):
        if self.mode == "rl":
            returns_list = self._context.tracker._portfolio_forward_bar_returns.copy()
            returns_list.insert(0,0)
        else:
            returns_list = self._context.tracker._portfolio_current_bar_returns.copy()
        #pdb.set_trace()
        index = self._context.availabel_trading_dts
        returns = pd.DataFrame(returns_list, index=index,columns=["unit_net_value"])
        unit_net_value = (returns + 1).cumprod()
            
        plot_performance(unit_net_value, auto_open=auto_open)
    
if __name__ == "__main__":
    from sharpe.utils.mock_data import create_toy_feature
    from sharpe.data.data_source import DataSource
    
    feature_df, price_s = create_toy_feature(order_book_ids_number=2, feature_number=3, random_seed=111)
    data_source = DataSource(feature_df=feature_df, price_s=price_s)
    
    env= TradingEnv(data_source=data_source, look_backward_window=2)
    print('--------------------------------------------')
    from sharpe.core.context import Context
    print("current context \n",Context.get_instance().__dict__)
    
    
    from sharpe.mod.sys_account.api.api import order_target_portfolio
    to_submit_orders = order_target_portfolio({"000001.XSHE":0.5})
    
    state, reward, is_done, info = env.step(action=to_submit_orders)
    print(state, reward, is_done)
    to_submit_orders2 = order_target_portfolio({"000001.XSHE":0.2})
    state, reward, is_done, info = env.step(action=to_submit_orders2)
    print(state, reward, is_done)
            
        
        
        
    
    
    
    
    
    
    
    
    
    
    
    
    
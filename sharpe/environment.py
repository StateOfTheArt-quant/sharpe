#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from sharpe.mod.sys_simulation.event_source import SimulationEventSource
from sharpe.core.context import Context
from sharpe.core.executor import Executor
from sharpe.mod.sys_account import Portfolio
from sharpe.core.strategy import Strategy

class TradingEnv(object):
    
    def __init__(self, data_source, look_backward_window=1) -> None:
        self._context = Context(look_backward_window=look_backward_window)
        
        #set data_source
        self._context.set_data_source(data_source)
        
        #set event_source
        event_source = SimulationEventSource()
        self._context.set_event_source(event_source)
        
        #
        mock_start_cash = {"STOCK":1000000, "FUTURE":10000}
        portfolio = Portfolio(starting_cash=mock_start_cash, init_positions={})
        self._context.set_portfolio(portfolio)
        
        #set broker
        self._executor = Executor(self._context)
        
        # user strategy
        user_strategy = Strategy(self._context)
            
    def reset():
        pass
    
    
    def step(self, action):
        
        state = Context.get_instance().history_bars()
        
        reward, is_done, info = self._executor.send(action)
        
        return state, reward, is_done, info
    
if __name__ == "__main__":
    from sharpe.utils.mock_data import create_toy_feature
    from sharpe.data.data_source import DataSource
    
    feature_df, price_s = create_toy_feature(order_book_ids_number=2, feature_number=3)
    data_source = DataSource(feature_df=feature_df, price_s=price_s)
    
    env= TradingEnv(data_source=data_source, look_backward_window=2)
    print('--------------------------------------------')
    from sharpe.core.context import Context
    print("current context \n",Context.get_instance().__dict__)
    
    
    from sharpe.mod.sys_account.api.api import order_target_portfolio
    to_submit_orders = order_target_portfolio({"000001.XSHE":0.5})
    
    env.step(action=to_submit_orders)
    
            
        
        
        
    
    
    
    
    
    
    
    
    
    
    
    
    
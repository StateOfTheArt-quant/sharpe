#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from sharpe.mod.events import EventBus

class Context(object):
    """serve as a global variable, prodiving context to different module"""
    
    _instance = None
    def __new__(cls, *args, **kwars):
        """make the Context class be a Singleton Pattern, that it says can be instanced only once"""
        if cls._instance is None:
            cls._instance = super(Context, cls).__new__(cls)
        return cls._instance
    
        
    def __init__(self, look_backward_window=2):
        Context._instance = self
        self.data_source = None
        self.broker = None
        self.event_bus = EventBus()
        self.event_source = None
        self.portfolio = None
        
        self.look_backward_window = look_backward_window
        self.calendar_dt = None  
        self.trading_dt = None  

    @classmethod
    def get_instance(cls):
        """
        return the created instance of Context
        """
        if Context._instance is None:
            raise RuntimeError(("Context has not been created. Please Use `Context.get_instance()` after sharpe init"))
        return Context._instance

    
    def set_data_source(self, data_source):
        self.data_source = data_source
    
    def set_event_source(self, event_source):
        self.event_source = event_source
    
    
    def get_last_price(self, order_book_id:str) -> float:
        return self.data_source(order_book_id = order_book_id, dt = self.trading_dt)
    
    def update_time(self, calendar_dt:datetime, trading_dt:datetime) -> None:
        self.calendar_dt = calendar_dt
        self.trading_dt = trading_dt
        
    def get_available_trading_dts(self):
        raw_availabel_trading_dts = self.data_source.get_available_trading_dts()
        self.availabel_trading_dts =  raw_availabel_trading_dts[self.look_backward_window-1:]
        return self.availabel_trading_dts
    
    def get_next_trading_dt(self):
        current_idx = self.availabel_trading_dts.searchsorted(self.trading_dt, side="left")
        return self.availabel_trading_dts[current_idx+1]

if __name__ == "__main__":
    from sharpe.utils.mock_data import create_toy_feature
    from sharpe.data.data_source import DataSource
    feature_df, price_s = create_toy_feature(order_book_ids_number=2, feature_number=3)
    data_source = DataSource(feature_df=feature_df, price_s=price_s)
    
    context = Context(look_backward_window=2)
    context.set_data_source(data_source)
    
    availabel_trading_dts = context.get_available_trading_dts()
    print(availabel_trading_dts)
    
    
    
    
    
    
    


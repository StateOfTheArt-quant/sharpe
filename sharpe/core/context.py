#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from sharpe.core.events import EventBus

class Context(object):
    """serve as a global variable, prodiving context to different module"""
    
    _instance = None
    #def __new__(cls, *args, **kwars):
    #    """make the Context class be a Singleton Pattern, that it says can be instanced only once"""
    #    if cls._instance is None:
    #        cls._instance = super(Context, cls).__new__(cls)
    #    return cls._instance
    
        
    def __init__(self, look_backward_window=2):
        Context._instance = self
        self.data_source = None
        self.broker = None
        self.event_bus = EventBus()
        self.event_source = None
        self.portfolio = None
        self._transaction_cost_decider_dict = {}
        
        self.look_backward_window = look_backward_window
        self.calendar_dt = None  
        self.trading_dt = None  
        self.frequency = None
        self.mode = None

    @classmethod
    def get_instance(cls):
        """
        return the created instance of Context
        """
        if Context._instance is None:
            raise RuntimeError(("Context has not been created. Please Use `Context.get_instance()` after sharpe init"))
        return Context._instance
    
    def set_mode(self, mode):
        self.mode = mode

    def set_data_source(self, data_source):
        self.data_source = data_source
    
    def set_event_source(self, event_source):
        self.event_source = event_source
    
    def set_broker(self, broker):
        self.broker = broker
    
    def set_portfolio(self, portfolio):
        self.portfolio = portfolio
    
    def set_tracker(self, tracker):
        self.tracker = tracker
    
    def get_last_price(self, order_book_id:str) -> float:
        return self.data_source.get_last_price(order_book_id = order_book_id, dt = self.trading_dt)
    
    
    def history_bars(self):
        return self.data_source.history_bars(dt=self.trading_dt, bar_count=self.look_backward_window)
    
    def update_time(self, calendar_dt:datetime, trading_dt:datetime) -> None:
        self.calendar_dt = calendar_dt
        self.trading_dt = trading_dt
        
    def get_available_trading_dts(self):
        raw_available_trading_dts = self.data_source.get_available_trading_dts()
        self.available_trading_dts =  raw_available_trading_dts[self.look_backward_window-1:]
        return self.available_trading_dts
    
    @property
    def available_order_book_ids(self):
        return self.data_source.get_available_order_book_ids()
    
    def get_next_trading_dt(self):
        current_idx = self.available_trading_dts.searchsorted(self.trading_dt, side="left")
        return self.available_trading_dts[current_idx+1]
    
    def get_account(self, order_book_id):
        return self.portfolio.get_account(order_book_id)
    
    def set_transaction_cost_decider(self, instrument_type, decider):
        self._transaction_cost_decider_dict[instrument_type] = decider

    def _get_transaction_cost_decider(self, order_book_id):
        instrument_type = self.data_source.instrument_type(order_book_id)
        try:
            return self._transaction_cost_decider_dict[instrument_type]
        except KeyError:
            raise NotImplementedError("No such transaction cost decider, order_book_id = {}".format(
                order_book_id
            ))
    def get_trade_tax(self, trade):
        return self._get_transaction_cost_decider(trade.order_book_id).get_trade_tax(trade)

    def get_trade_commission(self, trade):
        return self._get_transaction_cost_decider(trade.order_book_id).get_trade_commission(trade)
    
    def get_order_transaction_cost(self, order):
        return self._get_transaction_cost_decider(order.order_book_id).get_order_transaction_cost(order)
if __name__ == "__main__":
    from sharpe.utils.mock_data import create_toy_feature
    from sharpe.data.data_source import DataSource
    feature_df, price_s = create_toy_feature(order_book_ids_number=2, feature_number=3)
    data_source = DataSource(feature_df=feature_df, price_s=price_s)
    
    context = Context(look_backward_window=2)
    context.set_data_source(data_source)
    
    available_trading_dts = context.get_available_trading_dts()
    print(available_trading_dts)
    
    
    
    
    
    
    


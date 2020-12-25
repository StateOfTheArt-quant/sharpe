#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from copy import copy
from sharpe.core.events import Event, EVENT
import pdb

class Executor(object):
    
    EVENT_SPLIT_MAP = {
        EVENT.BEFORE_TRADING: (EVENT.PRE_BEFORE_TRADING, EVENT.BEFORE_TRADING, EVENT.POST_BEFORE_TRADING),
        EVENT.BAR: (EVENT.PRE_BAR, EVENT.BAR, EVENT.POST_BAR),
        EVENT.AFTER_TRADING: (EVENT.PRE_AFTER_TRADING, EVENT.AFTER_TRADING, EVENT.POST_AFTER_TRADING),
        EVENT.SETTLEMENT: (EVENT.PRE_SETTLEMENT, EVENT.SETTLEMENT, EVENT.POST_SETTLEMENT),
    }
    
    def __init__(self, context):
        self._context = context
        self._last_before_trading = None
        self.available_trading_dts = self._context.get_available_trading_dts()
        
        self._events_container = self._context.event_source.events(trading_dts = self.available_trading_dts) 
        #temp operation
        #self._context.trading_dt =  self.available_trading_dts[0]
        self._context.update_time(calendar_dt=self.available_trading_dts[0], trading_dt=self.available_trading_dts[0])
    
    def send(self, action):
        
        for event in self._events_container[self._context.trading_dt]:
            
            if event.event_type == EVENT.BAR:
                event.action = action
            self._split_and_publish(event)
 
        
        self._split_and_publish(Event(EVENT.SETTLEMENT))
        portfolio = self._context.portfolio
        reward = portfolio.daily_returns
        
        if self._context.trading_dt == self.available_trading_dts[-1]:
            is_done = True
        else:
            is_done = False
        info = {}
        
        if is_done:
            pass
        else:             
            next_trading_dt = self._context.get_next_trading_dt()
            self._context.update_time(calendar_dt=next_trading_dt, trading_dt=next_trading_dt)
        
        return reward, is_done, info
        
    
    def _split_and_publish(self, event):
        for event_type in self.EVENT_SPLIT_MAP[event.event_type]:
            e = copy(event)
            e.event_type = event_type
            self._context.event_bus.publish_event(e)


class RLExecutor(object):

    def __init__(self, context):
        self._context = context
        self._last_before_trading = None
        self.available_trading_dts = self._context.get_available_trading_dts()
        
        self._events_container = self._context.event_source._rl_events(trading_dts = self.available_trading_dts) 
        #temp operation
        self._context.update_time(calendar_dt=self.available_trading_dts[0], trading_dt=self.available_trading_dts[0])
    

    def send(self, action):
        
        for event in self._events_container[self._context.trading_dt]:
            
            if event.event_type == EVENT.BAR:
                event.action = action
            
            if event.event_type == EVENT.PRE_BEFORE_TRADING:
                self._context.update_time(calendar_dt=event.calendar_dt, trading_dt=event.trading_dt)
            self._context.event_bus.publish_event(event)
        
        tracker = self._context.tracker
        reward = tracker.reward
        
        if self._context.trading_dt == self.available_trading_dts[-1]:
            is_done = True
        else:
            is_done = False
        info = {}
        return reward, is_done, info




if __name__ == "__main__":
    from sharpe.utils.mock_data import create_toy_feature
    from sharpe.data.data_source import DataSource
    from sharpe.context import Context
    
    feature_df, price_s = create_toy_feature(order_book_ids_number=2, feature_number=3)
    data_source = DataSource(feature_df=feature_df, price_s=price_s)
    
    #
    context = Context(look_backward_window=2)
    context.set_data_source(data_source)
    
    #
    from sharpe.mod.event_source import SimulationEventSource
    default_event_source = SimulationEventSource() 
    context.set_event_source(default_event_source)
    
    executor = Executor(context)
    executor.send(action=0) 
    
    

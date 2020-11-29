#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from copy import copy
from sharpe.mod.events import Event, EVENT


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
        self._context.trading_dt =  self.available_trading_dts[0]
    
    def send(self, action):
        
        for event in self._events_container[self._context.trading_dt]:
            
            if event.event_type == EVENT.BAR:
                if self._ensure_before_trading(event):
                    event.action = action
                    self._split_and_publish(event)
            elif event.event_type == EVENT.BEFORE_TRADING:
                self._ensure_before_trading(event)
            elif event.event_type == EVENT.AFTER_TRADING:
                self._split_and_publish(event)
            else:
                self._env.event_bus.publish_event(event)
        
        self._split_and_publish(Event(EVENT.SETTLEMENT))
        #portfolio = Context.get_instance().get_portfolio()
        reward, is_done, info = 1,1,1,#portfolio.get_bar_info()
        return reward, is_done, info
    
    def _ensure_before_trading(self, event):
        # return True if before_trading won't run this time
        if self._last_before_trading == event.trading_dt:
            return True
        #if self._last_before_trading:
            # don't publish settlement on first date(time)
        #    self._split_and_publish(Event(EVENT.SETTLEMENT))
        self._last_before_trading = event.trading_dt
        self._split_and_publish(Event(EVENT.BEFORE_TRADING, calendar_dt=event.calendar_dt, trading_dt=event.trading_dt))
        return False    
    
    def _split_and_publish(self, event):
        if not hasattr(event, "trading_dt"):
            #FIXME
            try:
                next_trading_dt = self._context.get_next_trading_dt()
            except Exception as e:
                pass
            else:
                self._context.update_time(calendar_dt=next_trading_dt, trading_dt=next_trading_dt)
        for event_type in self.EVENT_SPLIT_MAP[event.event_type]:
            e = copy(event)
            e.event_type = event_type
            self._context.event_bus.publish_event(e)

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
    
    

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sharpe.core.context import Context
from sharpe.core.events import Event, EVENT

class SimulationEventSource(object):
    
    def __init__(self):
        pass
    
    def events(self, trading_dts):
        event_container = {}
        for trading_dt in trading_dts:
            
            events_within_bar = ( Event(EVENT.BEFORE_TRADING, calendar_dt=trading_dt, trading_dt=trading_dt),
                             Event(EVENT.BAR, calendar_dt=trading_dt, trading_dt=trading_dt),
                             Event(EVENT.AFTER_TRADING, calendar_dt=trading_dt, trading_dt=trading_dt)
                )
            #yield events_within_bar
            event_container[trading_dt] = events_within_bar
        return event_container
    
    
    def _rl_events(self, trading_dts):
        event_container = {}
        for i, trading_dt in enumerate(trading_dts[:-1]):
            events_within_bar = []
            
            events_within_bar.append(Event(EVENT.BAR, calendar_dt=trading_dt, trading_dt=trading_dt))
            events_within_bar.append(Event(EVENT.POST_BAR, calendar_dt=trading_dt, trading_dt=trading_dt))
            
            events_within_bar.append(Event(EVENT.PRE_AFTER_TRADING, calendar_dt=trading_dt, trading_dt=trading_dt))
            events_within_bar.append(Event(EVENT.AFTER_TRADING, calendar_dt=trading_dt, trading_dt=trading_dt))
            events_within_bar.append(Event(EVENT.POST_AFTER_TRADING, calendar_dt=trading_dt, trading_dt=trading_dt))
            
            events_within_bar.append(Event(EVENT.PRE_SETTLEMENT, calendar_dt=trading_dt, trading_dt=trading_dt))
            events_within_bar.append(Event(EVENT.SETTLEMENT, calendar_dt=trading_dt, trading_dt=trading_dt))
            events_within_bar.append(Event(EVENT.POST_SETTLEMENT, calendar_dt=trading_dt, trading_dt=trading_dt))
            
            next_trading_dt = trading_dts[i+1]
            
            events_within_bar.append(Event(EVENT.PRE_BEFORE_TRADING, calendar_dt=next_trading_dt, trading_dt=next_trading_dt))
            events_within_bar.append(Event(EVENT.BEFORE_TRADING, calendar_dt=next_trading_dt, trading_dt=next_trading_dt))
            events_within_bar.append(Event(EVENT.POST_BEFORE_TRADING, calendar_dt=next_trading_dt, trading_dt=next_trading_dt))
            
            events_within_bar.append(Event(EVENT.PRE_BAR, calendar_dt=next_trading_dt, trading_dt=next_trading_dt))
            event_container[trading_dt] = events_within_bar
        return event_container

if __name__ == "__main__":
    
    import pandas as pd
    trading_dts = pd.date_range(start="2020-01-01", end="2020-01-05")
    
    event_simulator = SimulationEventSource()
    normal_event_container = event_simulator.events(trading_dts)
    rl_event_container = event_simulator._rl_events(trading_dts)

    
    
    
    
    
    
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
#            yield events_within_bar
            event_container[trading_dt] = events_within_bar
        return event_container


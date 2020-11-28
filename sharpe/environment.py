#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from sharpe.mod.event_source import SimulationEventSource
from sharpe.context import Context
from sharpe.executor import Executor

class TradingEnv(object):
    
    def __init__(self, data_source, look_backward_window=1) -> None:
        self._context = Context(look_backward_window=look_backward_window)
        
        #set event_source
        event_source = SimulationEventSource()
        self._context.set_event_source(event_source)
        
        #set broker
        self._executor = Executor()
        
        
            
    def reset():
        pass
    
    
    def step(self, action):
        
        state = Context.get_instance().history_bars()
        
        reward, is_done, info = executor.send(action)
        
        return state, reward, is_done, info
    

            
        
        
        
    
    
    
    
    
    
    
    
    
    
    
    
    
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sharpe.core.events import EVENT

class Strategy(object):
    
    def __init__(self, context):
        self._context = context
        self._context.event_bus.add_listener(EVENT.BAR, self.handle_bar)
    
    
    
    def handle_bar(self, event):
        action = event.action
        if action is None:
            pass
        else:
            for order in action:
                self._context.broker.submit_order(order)

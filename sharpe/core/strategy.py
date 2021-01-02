#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sharpe.core.events import EVENT

class Strategy(object):
    
    def __init__(self, context):
        self._context = context
        self._context.event_bus.add_listener(EVENT.BAR, self.handle_bar)
    
    
    
    def handle_bar(self, event):
        to_submit_orders = event.action
        for order in to_submit_orders:
            self._context.broker.submit_order(order)

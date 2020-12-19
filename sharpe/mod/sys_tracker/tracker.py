#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numbers
from enum import Enum
from sharpe.core.events import EVENT
import pdb

class Tracker(object):
    
    def __init__(self, context):
        self._context = context
        self._orders = []
        self._trades = []
        self._portfolio_daily_returns = []
        self._portfolio_forward_reward = []
        
        
        self._rl_static_unit_net_value = 1
        
        self._context.event_bus.add_listener(EVENT.POST_SYSTEM_INIT, self._subscribe_events)
    
    def _subscribe_events(self, event):
        self._context.event_bus.add_listener(EVENT.TRADE, self._collect_trade)
        self._context.event_bus.add_listener(EVENT.ORDER_CREATION_PASS, self._collect_order)
        self._context.event_bus.add_listener(EVENT.POST_SETTLEMENT, self._collect_daily)        
        self._context.event_bus.add_listener(EVENT.PRE_BAR, self._calculate_forward_reward)
    
    def _collect_trade(self, event):
        self._trades.append(self._to_trade_record(event.trade))
    
    def _collect_order(self, event):
        self._orders.append(event.order)
    
    def _collect_daily(self, event):
        portfolio = self._context.portfolio
        self._portfolio_daily_returns.append(portfolio.daily_returns)
    
    def _calculate_forward_reward(self, event):
        self.reward = self.rl_unit_net_value / self.rl_static_unit_net_value - 1
        self._portfolio_forward_reward.append(self.reward)
        self._rl_static_unit_net_value = self.rl_unit_net_value
    
    @property
    def rl_static_unit_net_value(self):
        return self._rl_static_unit_net_value
    
    @property
    def rl_unit_net_value(self):
        portfolio = self._context.portfolio 
        return portfolio.total_value / portfolio.units
    
    
    @staticmethod
    def _safe_convert(value, ndigits=4):
        if isinstance(value, Enum):
            return value.name

        if isinstance(value, numbers.Real):
            return round(float(value), ndigits)

        return value
    
    def _to_trade_record(self, trade):
        return {
            'datetime': trade.datetime.strftime("%Y-%m-%d %H:%M:%S"),
            'trading_datetime': trade.trading_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            'order_book_id': trade.order_book_id,
            'symbol': trade.order_book_id,
            'side': self._safe_convert(trade.side),
            'position_effect': self._safe_convert(trade.position_effect),
            'exec_id': trade.exec_id,
            'tax': trade.tax,
            'commission': trade.commission,
            'last_quantity': trade.last_quantity,
            'last_price': self._safe_convert(trade.last_price),
            'order_id': trade.order_id,
            'transaction_cost': trade.transaction_cost,
        }
    
        
    

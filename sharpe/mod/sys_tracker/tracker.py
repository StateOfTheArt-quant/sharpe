#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import division
import numbers
import numpy as np
import pandas as pd
from enum import Enum
from sharpe.core.events import EVENT
from sharpe.mod.sys_tracker.performance import calc_draw_down
import pdb

class Tracker(object):
    
    def __init__(self, context):
        self._context = context
        self._orders = []
        self._trades = []
        self._total_portfolio = []
        self._total_forward_portfolio = []
        self._portfolio_current_bar_returns = []
        self._portfolio_forward_bar_returns = []
        self._portfolio_current_bar_pnl = []
        self._portfolio_forward_bar_pnl =[]
        self.trading_dt_list = []
        
        #extra performance stats
        self._returns_mean= []
        self._forward_bar_returns_mean = []
        
        self._unit_sharpe_ratio = []
        self._forward_bar_unit_sharpe_ratio = []
        
        self._draw_down = []
        self._forward_bar_draw_down = []
        
        self._max_draw_down = []
        self._forward_bar_max_draw_down = []
        
        
        self._rl_static_unit_net_value = 1
        self._rl_static_total_value = context.portfolio.total_value
        
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
        self._portfolio_current_bar_returns.append(portfolio.daily_returns)#
        self._portfolio_current_bar_pnl.append(portfolio.daily_pnl)
        #
        self._total_portfolio.append(self._to_portfolio_record(dt=self._context.trading_dt, portfolio=portfolio))
        
        #
        performance_dict = self._to_performance(self._portfolio_current_bar_returns)
        self._returns_mean.append(performance_dict["returns_mean"])
        self._unit_sharpe_ratio.append(performance_dict["unit_sharpe_ratio"])
        self._draw_down.append(performance_dict["current_draw_down"])
        self._max_draw_down.append(performance_dict["max_draw_down"])
        
    def _calculate_forward_reward(self, event):
        self.reward = self.rl_unit_net_value / self.rl_static_unit_net_value - 1
        self._portfolio_forward_bar_returns.append(self.reward)
                
        portfolio = self._context.portfolio
        self.pnl = portfolio.total_value - self._rl_static_total_value
        self._portfolio_forward_bar_pnl.append(self.pnl)
        #important here
        self._rl_static_unit_net_value = self.rl_unit_net_value
        self._rl_static_total_value = portfolio.total_value

        
        self._total_forward_portfolio.append(self._to_portfolio_record(dt=self._context.trading_dt, portfolio=portfolio))
        #
        performance_dict = self._to_performance(self._portfolio_forward_bar_returns)
        self._forward_bar_returns_mean.append(performance_dict["returns_mean"])
        self._forward_bar_unit_sharpe_ratio.append(performance_dict["unit_sharpe_ratio"])
        self._forward_bar_draw_down.append(performance_dict["current_draw_down"])
        self._forward_bar_max_draw_down.append(performance_dict["max_draw_down"])
        

    
    @property
    def rl_static_unit_net_value(self):
        return self._rl_static_unit_net_value
    
    @property
    def rl_unit_net_value(self):
        # after update_last_price
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
    
    def _to_portfolio_record(self, dt, portfolio):
        return {
            'datetime': dt,
            'cash': self._safe_convert(portfolio.cash),
            'total_value': self._safe_convert(portfolio.total_value),
            'market_value': self._safe_convert(portfolio.market_value),
            'unit_net_value': self._safe_convert(portfolio.unit_net_value, 6),
            'units': portfolio.units,
            'static_unit_net_value': self._safe_convert(portfolio.static_unit_net_value),
        }
    

        
    def _to_performance(self, returns):
        #
        _returns_mean = np.mean(returns)
        _returns_std = np.std(returns)
        _unit_sharpe_ratio = _returns_mean / (_returns_std + 1e-7)
        drawdown = calc_draw_down(returns)
        
        return {
            "returns_mean": _returns_mean,
            "unit_sharpe_ratio": _unit_sharpe_ratio,
            "current_draw_down": abs(drawdown[-1]),
            "max_draw_down": abs(drawdown.min())
        }
    
    @property
    def bar_returns(self) -> pd.Series:
        bar_returns_list = self._portfolio_forward_bar_returns 
        bar_reutrns_s = pd.Series(bar_returns_list, index=self._context.available_trading_dts[:len(bar_returns_list)])
        return bar_reutrns_s 

    

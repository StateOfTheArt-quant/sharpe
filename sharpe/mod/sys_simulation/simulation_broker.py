#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from functools import lru_cache
from sharpe.const import MATCHING_TYPE, INSTRUMENT_TYPE
from typing import Dict, List,Tuple, Optional, Union, Iterable
from sharpe.interface import AbstractBroker
from sharpe.const import POSITION_EFFECT, ORDER_STATUS
from sharpe.core.event import EVENT, Event
from sharpe.mod.sys_simulation.matcher import DefaultMatcher

class SimulationBroker(AbstractBroker):
    def __init__(self, context, mod_config):
        self._context = context
        self._mod_config = mod_config

        self._matchers = {} 

        self._match_immediately = mod_config.matching_type == MATCHING_TYPE.CURRENT_BAR_CLOSE

        self._open_orders = []  
        self._delayed_orders = []

        self._context.event_bus.add_listener(EVENT.BEFORE_TRADING, self.before_trading)
        # to match the unfilled order in the following bars
        self._context.event_bus.add_listener(EVENT.BAR, self.on_bar)
        self._context.event_bus.add_listener(EVENT.AFTER_TRADING, self.after_trading)
        self._context.event_bus.add_listener(EVENT.PRE_SETTLEMENT, self.pre_settlement)

    @lru_cache(1024)
    def _get_matcher(self, order_book_id):
        instrument_type = self._context.data_source.instrument_type(order_book_id)
        try:
            return self._matchers[instrument_type]
        except KeyError:
            return self._matchers.setdefault(instrument_type, DefaultMatcher(self._env, self._mod_config))

    def register_matcher(self, instrument_type, matcher):
        self._matchers[instrument_type] = matcher
    
    def get_open_orders(self, order_book_id=None):
        if order_book_id is None:
            return [order for account, order in self._open_orders]
        else:
            return [order for account, order in self._open_orders if order.order_book_id == order_book_id]

    def submit_order(self, order):
        if order.position_effect == POSITION_EFFECT.MATCH:
            raise TypeError("unsupported position_effect {}".format(order.position_effect))
        account = self._env.get_account(order.order_book_id)
        self._context.event_bus.publish_event(Event(EVENT.ORDER_PENDING_NEW, account=account, order=order))
        if order.is_final():
            return
            
        if self._context.frequency == '1d' and not self._match_immediately:
            self._delayed_orders.append((account, order))
            return
        self._open_orders.append((account, order))
        order.active()
        self._env.event_bus.publish_event(Event(EVENT.ORDER_CREATION_PASS, account=account, order=order))
        if self._match_immediately:
            self._match()

    def cancel_order(self, order):
        account = self._context.get_account(order.order_book_id)

        self._env.event_bus.publish_event(Event(EVENT.ORDER_PENDING_CANCEL, account=account, order=order))

        order.mark_cancelled("{order_id} order has been cancelled by user.".format(order_id=order.order_id))

        self._env.event_bus.publish_event(Event(EVENT.ORDER_CANCELLATION_PASS, account=account, order=order))

        try:
            self._open_orders.remove((account, order))
        except ValueError:
            try:
                self._delayed_orders.remove((account, order))
            except ValueError:
                pass

    def before_trading(self, _):
        for account, order in self._open_orders:
            order.active()
            self._env.event_bus.publish_event(Event(EVENT.ORDER_CREATION_PASS, account=account, order=order))

    def after_trading(self, __):
        for account, order in self._open_orders:
            order.mark_rejected("Order Rejected: {order_book_id} can not match. Market close.".format(
                order_book_id=order.order_book_id
            ))
            self._env.event_bus.publish_event(Event(EVENT.ORDER_UNSOLICITED_UPDATE, account=account, order=order))
        self._open_orders = self._delayed_orders
        self._delayed_orders = []

    def pre_settlement(self, __):
        for account, order in self._open_exercise_orders:
            self._get_matcher(order.order_book_id).match(account, order, False)

    def on_bar(self, _):
        for matcher in self._matchers.values():
            matcher.update()
        self._match()

    def _match(self, order_book_id=None):
        order_filter = None if order_book_id is None else lambda a_and_o: a_and_o[1].order_book_id == order_book_id
        for account, order in filter(order_filter, self._open_orders):
            self._get_matcher(order.order_book_id).match(account, order, open_auction=False)
        final_orders = [(a, o) for a, o in self._open_orders if o.is_final()]
        self._open_orders = [(a, o) for a, o in self._open_orders if not o.is_final()]

        for account, order in final_orders:
            if order.status == ORDER_STATUS.REJECTED or order.status == ORDER_STATUS.CANCELLED:
                self._env.event_bus.publish_event(Event(EVENT.ORDER_UNSOLICITED_UPDATE, account=account, order=order))
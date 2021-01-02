#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from enum import Enum
from collections import defaultdict


class Event(object):
    def __init__(self, event_type, **kwargs):
        self.__dict__ = kwargs
        self.event_type = event_type

    def __repr__(self):
        return ' '.join('{}:{}'.format(k, v) for k, v in self.__dict__.items())


class EventBus(object):
    def __init__(self):
        self._listeners = defaultdict(list)
        self._user_listeners = defaultdict(list)

    def add_listener(self, event_type, listener, user=False):
        (self._user_listeners if user else self._listeners)[event_type].append(listener)

    def prepend_listener(self, event_type, listener, user=False):
        (self._user_listeners if user else self._listeners)[event_type].insert(0, listener)

    def publish_event(self, event):
       
        for listener in self._listeners[event.event_type]:
            # if return True, then break, would not continue this event
            if listener(event):
                break

        for listener in self._user_listeners[event.event_type]:
            listener(event)


class EVENT(Enum):
    # post_system_init()
    POST_SYSTEM_INIT = 'post_system_init'

    # pre_before_trading()
    PRE_BEFORE_TRADING = 'pre_before_trading'
    # before_trading()
    BEFORE_TRADING = 'before_trading'
    # post_before_trading()
    POST_BEFORE_TRADING = 'post_before_trading'


    # pre_bar()
    PRE_BAR = 'pre_bar'
    # bar(bar_dict)
    BAR = 'bar'
    # post_bar()
    POST_BAR = 'post_bar'

    # pre_after_trading()
    PRE_AFTER_TRADING = 'pre_after_trading'
    # after_trading()
    AFTER_TRADING = 'after_trading'
    # post_after_trading()
    POST_AFTER_TRADING = 'post_after_trading'

    # pre_settlement()
    PRE_SETTLEMENT = 'pre_settlement'
    # settlement()
    SETTLEMENT = 'settlement'
    # post_settlement()
    POST_SETTLEMENT = 'post_settlement'

    # order_pending_new(account, order)
    ORDER_PENDING_NEW = 'order_pending_new'
    # order_creation_pass(account, order)
    ORDER_CREATION_PASS = 'order_creation_pass'
    # order_creation_reject(account, order)
    ORDER_CREATION_REJECT = 'order_creation_reject'
    # order_pending_cancel(account, order)
    # order_unsolicited_update(account, order)
    ORDER_UNSOLICITED_UPDATE = 'order_unsolicited_update'

    # trade(accout, trade, order)
    TRADE = 'trade'


def parse_event(event_str):
    return EVENT[event_str.upper()]


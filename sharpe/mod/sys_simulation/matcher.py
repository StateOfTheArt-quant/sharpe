#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from collections import defaultdict
from sharpe.const import MATCHING_TYPE, POSITION_EFFECT, SIDE, ORDER_TYPE
from sharpe.core.events import EVENT, Event
from sharpe.object.trade import Trade

class AbstractMatcher:
    def match(self, account, order, open_auction):
        raise NotImplementedError

    def update(self):
        raise NotImplementedError


class DefaultMatcher(AbstractMatcher):
    def __init__(self, context, mod_config):
        self._turnover = defaultdict(int)
        self._context = context 
        self._deal_price_decider = self._create_deal_price_decider(mod_config.matching_type)

    def _create_deal_price_decider(self, matching_type):
        decider_dict = {
            MATCHING_TYPE.CURRENT_BAR_CLOSE: self._current_bar_close_decider,
            MATCHING_TYPE.NEXT_BAR_OPEN: self._next_bar_open_decider,
        }
        return decider_dict[matching_type]
    
    def _current_bar_close_decider(self, order_book_id, _):
        try:
            return self._context.get_last_price(order_book_id)
        except (KeyError, TypeError):
            return 0
    
    def _next_bar_open_decider(self, order_book_id, _):
        try:
            return self._context.get_last_price(order_book_id)
        except (KeyError, TypeError):
            return 0
    
    SUPPORT_POSITION_EFFECTS = (POSITION_EFFECT.OPEN, POSITION_EFFECT.CLOSE, POSITION_EFFECT.CLOSE_TODAY)
    SUPPORT_SIDES = (SIDE.BUY, SIDE.SELL)

    def match(self, account, order, open_auction):

        if not (order.position_effect in self.SUPPORT_POSITION_EFFECTS and order.side in self.SUPPORT_SIDES):
            raise NotImplementedError
        order_book_id = order.order_book_id
        
        deal_price = self._deal_price_decider(order_book_id, order.side)
        fill = order.unfilled_quantity
        ct_amount = account.calc_close_today_amount(order_book_id, fill, order.position_direction)
        price = deal_price
        
        
        trade = Trade.__from_create__(
            order_id=order.order_id,
            price=price,
            amount=fill,
            side=order.side,
            position_effect=order.position_effect,
            order_book_id=order.order_book_id,
            frozen_price=order.frozen_price,
            close_today_amount=ct_amount
        )
        trade._commission = self._env.get_trade_commission(trade)
        trade._tax = self._env.get_trade_tax(trade)
        order.fill(trade)
        
        self._turnover[order.order_book_id] += fill

        self._context.event_bus.publish_event(Event(EVENT.TRADE, account=account, trade=trade, order=order))

        if order.type == ORDER_TYPE.MARKET and order.unfilled_quantity != 0:
            reason = "Order Cancelled: market order {order_book_id} volume {order_volume} is larger than 25% percent of current bar volume, fill {filled_volume} actually".format(
                order_book_id=order.order_book_id,
                order_volume=order.quantity,
                filled_volume=order.filled_quantity,
            )
            order.mark_cancelled(reason)

    def update(self):
        self._turnover.clear()
        
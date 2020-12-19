#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import defaultdict
from sharpe.core.context import Context
from sharpe.const import SIDE, HEDGE_TYPE, COMMISSION_TYPE, POSITION_EFFECT


class StockTransactionCostDecider(object):
    def __init__(self, commission_rate, commission_multiplier, min_commission):
        self.commission_rate = commission_rate
        self.commission_multiplier = commission_multiplier
        self.commission_map = defaultdict(lambda: min_commission)
        self.min_commission = min_commission

        self.context = Context.get_instance()

    def _get_order_commission(self, order_book_id, side, price, quantity):
        commission = price * quantity * self.commission_rate * self.commission_multiplier
        return max(commission, self.min_commission)

    def _get_tax(self, order_book_id, side, cost_money):
        raise NotImplementedError

    def get_trade_commission(self, trade):
        order_id = trade.order_id
        commission = self.commission_map[order_id]
        cost_commission = trade.last_price * trade.last_quantity * self.commission_rate * self.commission_multiplier
        if cost_commission > commission:
            if commission == self.min_commission:
                self.commission_map[order_id] = 0
                return cost_commission
            else:
                self.commission_map[order_id] = 0
                return cost_commission - commission
        else:
            if commission == self.min_commission:
                self.commission_map[order_id] -= cost_commission
                return commission
            else:
                self.commission_map[order_id] -= cost_commission
                return 0

    def get_trade_tax(self, trade):
        return self._get_tax(trade.order_book_id, trade.side, trade.last_price * trade.last_quantity)

    def get_order_transaction_cost(self, order):
        commission = self._get_order_commission(order.order_book_id, order.side, order.frozen_price, order.quantity)
        tax = self._get_tax(order.order_book_id, order.side, order.frozen_price * order.quantity)
        return tax + commission


class CNStockTransactionCostDecider(StockTransactionCostDecider):
    def __init__(self, commission_multiplier=1, min_commission=5, tax_multiplier=1):
        super(CNStockTransactionCostDecider, self).__init__(0.0008, commission_multiplier, min_commission)
        self.tax_rate = 0.001
        self.tax_multiplier = tax_multiplier

    def _get_tax(self, order_book_id, side, cost_money):
        instrument_type = Context.get_instance().data_source.instrument_type(order_book_id)
        if instrument_type != 'CS':
            return 0
        return cost_money * self.tax_rate * self.tax_multiplier if side == SIDE.SELL else 0



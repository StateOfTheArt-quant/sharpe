#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import six
import jsonpickle
import numpy as np
from itertools import chain
from typing import Dict, List,Tuple, Optional, Union

from sharpe.utils import merge_dicts
from sharpe.utils.repr import PropertyReprMeta
from sharpe.mod.events import EVENT
from sharpe.context import Context
from sharpe.const import DEFAULT_ACCOUNT_TYPE
from .account import Account

class Portfolio(object, metaclass=PropertyReprMeta):
    """
    a manager(set) manage all account with different major INSTRUMENT type according __instrument_types__
    """
    __repr_properties__ = (
        "total_value", "unit_net_value", "daily_pnl", "daily_returns", "total_returns", "annualized_returns", "accounts"
    )

    def __init__(self, starting_cash:Dict[str, float], init_positions:List[Tuple[str, int]]) -> None:
    
        self._static_unit_net_value = 1
        self._last_unit_net_value = 1

        account_args = {}
        for account_type, cash in starting_cash.items():
            account_args[account_type] = {"type": account_type, "total_cash": cash, "init_positions": {}}
        for order_book_id, quantity in init_positions:
            account_type = self.get_account_type(order_book_id)
            if account_type in account_args:
                account_args[account_type]["init_positions"][order_book_id] = quantity
                
        self._accounts = {account_type: Account(**args) for account_type, args in account_args.items()}
        self._units = sum(account.total_value for account in six.itervalues(self._accounts))

        self._register_event()

    def get_state(self):
        return jsonpickle.encode({
            'static_unit_net_value': self._static_unit_net_value,
            'last_unit_net_value': self._last_unit_net_value,
            'units': self._units,
            'accounts': {
                name: account.get_state() for name, account in self._accounts.items()
            }
        }).encode('utf-8')

    def set_state(self, state):
        state = state.decode('utf-8')
        value = jsonpickle.decode(state)
        self._static_unit_net_value = value['static_unit_net_value']
        self._last_unit_net_value = value.get('last_unit_net_value', self._static_unit_net_value)
        self._units = value['units']
        for k, v in value['accounts'].items():
            self._accounts[k].set_state(v)

    def get_positions(self):
        return list(chain(*(a.get_positions() for a in six.itervalues(self._accounts))))

    def get_position(self, order_book_id, direction):
        account = self._accounts[self.get_account_type(order_book_id)]
        return account.get_position(order_book_id, direction)

    @classmethod
    def get_account_type(cls, order_book_id):
        #instrument = Context.get_instance().data_source.instruments(order_book_id)
        #return instrument.account_type
        return DEFAULT_ACCOUNT_TYPE.STOCK.name

    def get_account(self, order_book_id):
        return self._accounts[self.get_account_type(order_book_id)]

    @property
    def accounts(self) -> Dict[DEFAULT_ACCOUNT_TYPE, Account]:
        """
        a dict contain different account        
        """
        return self._accounts

    @property
    def stock_account(self):
        """
        [StockAccount] 
        """
        return self._accounts.get(DEFAULT_ACCOUNT_TYPE.STOCK.name, None)

    @property
    def future_account(self):
        """
        [FutureAccount]
        """
        return self._accounts.get(DEFAULT_ACCOUNT_TYPE.FUTURE.name, None)


    @property
    def units(self) -> float:
        """
        """
        return self._units

    @property
    def unit_net_value(self) -> float:
        """
        [float] realtime net value
        """
        if self._units == 0:
            return np.nan
        return self.total_value / self._units

    @property
    def static_unit_net_value(self):
        """
        [float] the net value at the previous datestamp
        """
        return self._static_unit_net_value

    @property
    def daily_pnl(self):
        """
        [float] daily pnl
        """
        return sum(account.daily_pnl for account in six.itervalues(self._accounts))

    @property
    def daily_returns(self):
        """
        [float] the return of at current bar
        """
        return np.nan if self._static_unit_net_value == 0 else self.unit_net_value / self._static_unit_net_value - 1

    @property
    def total_returns(self):
        """
        [float] cumulative returns
        """
        return self.unit_net_value - 1

    @property
    def total_value(self):
        """
        [float] total value
        """
        return sum(account.total_value for account in six.itervalues(self._accounts))


    @property
    def positions(self):
        """
        [dict] dict contain all positions
        """
        return MixedPositions(self._accounts)

    @property
    def cash(self):
        """
        [float] available cash
        """
        return sum(account.cash for account in six.itervalues(self._accounts))

    @property
    def transaction_cost(self):
        """
        [float] transaction_cost and tax fee
        """
        return sum(account.transaction_cost for account in six.itervalues(self._accounts))

    @property
    def market_value(self):
        """
        [float] market value
        """
        return sum(account.market_value for account in six.itervalues(self._accounts))

    @property
    def pnl(self):
        """
        [float] profit and loss
        """
        return (self.unit_net_value - 1) * self.units

    @property
    def starting_cash(self):
        """
        [float] starting cash
        """
        return self.units

    @property
    def frozen_cash(self):
        """
        [float] frozen cash
        """
        return sum(account.frozen_cash for account in six.itervalues(self._accounts))

    def _pre_before_trading(self, _):
        if not np.isnan(self.unit_net_value):
            self._static_unit_net_value = self.unit_net_value
        else:
            self._static_unit_net_value = self._last_unit_net_value

    def _post_settlement(self, event):
        self._last_unit_net_value = self.unit_net_value

    def _register_event(self):
        event_bus = Context.get_instance().event_bus
        event_bus.prepend_listener(EVENT.PRE_BEFORE_TRADING, self._pre_before_trading)
        event_bus.prepend_listener(EVENT.POST_SETTLEMENT, self._post_settlement)
        
        
        
class MixedPositions(dict):

    def __init__(self, accounts):
        super(MixedPositions, self).__init__()
        self._accounts = accounts

    def __missing__(self, key):
        account_type = Portfolio.get_account_type(key)
        for a_type in self._accounts:
            if a_type == account_type:
                return self._accounts[a_type].positions[key]
        return None

    def __contains__(self, item):
        return item in self.keys()

    def __repr__(self):
        keys = []
        for account in six.itervalues(self._accounts):
            keys += account.positions.keys()
        return str(sorted(keys))

    def __len__(self):
        return sum(len(account.positions) for account in six.itervalues(self._accounts))

    def __iter__(self):
        keys = []
        for account in six.itervalues(self._accounts):
            keys += account.positions.keys()
        for key in sorted(keys):
            yield key

    def items(self):
        items = merge_dicts(*[account.positions.items() for account in six.itervalues(self._accounts)])
        for k in sorted(items.keys()):
            yield k, items[k]

    def keys(self):
        keys = []
        for account in six.itervalues(self._accounts):
            keys += list(account.positions.keys())
        return sorted(keys)
        
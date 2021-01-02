#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import date
from collections import UserDict
from sharpe.core.context import Context
from sharpe.utils import is_valid_price
from sharpe.utils.repr import property_repr, PropertyReprMeta
from sharpe.const import INSTRUMENT_TYPE, POSITION_DIRECTION, POSITION_EFFECT, INST_TYPE_IN_STOCK_ACCOUNT


def new_position_meta():

    type_map = {}

    class Meta(PropertyReprMeta):
        def __new__(mcs, *args, **kwargs):
            cls = super(Meta, mcs).__new__(mcs, *args, **kwargs)
            try:
                instrument_types = cls.__instrument_types__
            except AttributeError:
                pass
            else:
                for instrument_type in instrument_types:
                    type_map[instrument_type] = cls
            return cls

    return type_map, Meta


POSITION_TYPE_MAP, PositionMeta = new_position_meta()


class Position(object, metaclass=PositionMeta):

    __repr_properties__ = (
        "order_book_id", "direction", "quantity", "market_value", "trading_pnl", "position_pnl"
    )

    # istance Portfolio, but the instance will be StockPosition according the order_book_id instrument_types
    __instrument_types__ = []

    def __new__(cls, order_book_id, direction, init_quantity=0):
        if cls == Position:
            ins_type = INSTRUMENT_TYPE.CS #Context.get_instance().data_proxy.instruments(order_book_id).type
            try:
                position_cls = POSITION_TYPE_MAP[ins_type]
            except KeyError:
                raise NotImplementedError("")
            return position_cls.__new__(position_cls, order_book_id, direction, init_quantity)
        else:
            return object.__new__(cls)

    def __init__(self, order_book_id, direction, init_quantity=0):
        #self._context = Context.get_instance()

        self._order_book_id = order_book_id
        #self._instrument = self._env.data_proxy.instruments(order_book_id)
        self._direction = direction

        self._old_quantity = init_quantity
        self._logical_old_quantity = 0
        self._today_quantity = 0

        self._avg_price = 0
        self._trade_cost = 0
        self._transaction_cost = 0
        self._prev_close = None
        self._last_price = float("NaN")

        self._direction_factor = 1 if direction == POSITION_DIRECTION.LONG else -1

    @property
    def order_book_id(self):
        # type: () -> str
        return self._order_book_id

    @property
    def direction(self):
        # type: () -> POSITION_DIRECTION
        return self._direction

    @property
    def quantity(self):
        # type: () -> int
        return self._old_quantity + self._today_quantity

    @property
    def transaction_cost(self):
        # type: () -> float
        return self._transaction_cost

    @property
    def avg_price(self):
        # type: () -> float
        return self._avg_price

    @property
    def trading_pnl(self):
        # type: () -> float
        trade_quantity = self._today_quantity + (self._old_quantity - self._logical_old_quantity)
        if trade_quantity == 0:
            return 0
        return (trade_quantity * self.last_price - self._trade_cost) * self._direction_factor

    @property
    def position_pnl(self):
        # type: () -> float
        if self._logical_old_quantity == 0:
            return 0
        return self._logical_old_quantity * (self.last_price - self.prev_close) * self._direction_factor

    @property
    def pnl(self) -> float:
        """
        cumulative profit and loss(pnl)
        """
        if self.quantity == 0:
            return 0
        return (self.last_price - self.avg_price) * self.quantity * self._direction_factor

    @property
    def market_value(self):
        # type: () -> float
        return self.last_price * self.quantity if self.quantity != 0 else 0

    @property
    def margin(self):
        # type: () -> float
        return 0

    @property
    def equity(self):
        # type: () -> float
        return self.last_price * self.quantity if self.quantity != 0 else 0

    @property
    def prev_close(self):
        if not is_valid_price(self._prev_close):
            context = Context.get_instance()
            self._prev_close = context.data_source.get_prev_close(self._order_book_id, context.trading_dt)
        return self._prev_close

    @property
    def last_price(self):
        if self._last_price != self._last_price:
            context = Context.get_instance()
            self._last_price = context.get_last_price(self._order_book_id)
            if self._last_price != self._last_price:
                raise RuntimeError("last price of position {} is not supposed to be nan".format(self._order_book_id))
        return self._last_price

    @property
    def closable(self) -> int:
         
        """
        position quantity which can be closed
        """
        order_quantity = sum(o.unfilled_quantity for o in self._open_orders if o.position_effect in (
            POSITION_EFFECT.CLOSE, POSITION_EFFECT.CLOSE_TODAY, POSITION_EFFECT.EXERCISE
        ))
        return self.quantity - order_quantity

    @property
    def today_closable(self):
        # type: () -> int
        return self._today_quantity - sum(
            o.unfilled_quantity for o in self._open_orders if o.position_effect == POSITION_EFFECT.CLOSE_TODAY
        )

    def get_state(self):
        """"""
        return {
            "old_quantity": self._old_quantity,
            "logical_old_quantity": self._logical_old_quantity,
            "today_quantity": self._today_quantity,
            "avg_price": self._avg_price,
            "trade_cost": self._trade_cost,
            "transaction_cost": self._transaction_cost,
            "prev_close": self._prev_close
        }

    def set_state(self, state):
        """"""
        self._old_quantity = state.get("old_quantity", 0)
        self._logical_old_quantity = state.get("logical_old_quantity", self._old_quantity)
        self._today_quantity = state.get("today_quantity", 0)
        self._avg_price = state.get("avg_price", 0)
        self._trade_cost = state.get("trade_cost", 0)
        self._transaction_cost = state.get("transaction_cost", 0)
        self._prev_close = state.get("prev_close")

    def before_trading(self, trading_date):
        return 0

    def apply_trade(self, trade):
        self._transaction_cost += trade.transaction_cost
        if trade.position_effect == POSITION_EFFECT.OPEN:
            if self.quantity < 0:
                self._avg_price = trade.last_price if self.quantity + trade.last_quantity > 0 else 0
            else:
                cost = self.quantity * self._avg_price + trade.last_quantity * trade.last_price
                self._avg_price = cost / (self.quantity + trade.last_quantity)
            self._today_quantity += trade.last_quantity
            self._trade_cost += trade.last_price * trade.last_quantity
            return (-1 * trade.last_price * trade.last_quantity) - trade.transaction_cost
        elif trade.position_effect == POSITION_EFFECT.CLOSE:
            self._today_quantity -= max(trade.last_quantity - self._old_quantity, 0)
            self._old_quantity -= min(trade.last_quantity, self._old_quantity)
            self._trade_cost -= trade.last_price * trade.last_quantity
            return trade.last_price * trade.last_quantity - trade.transaction_cost
        else:
            raise NotImplementedError("{} does not support position effect {}".format(
                self.__class__.__name__, trade.position_effect
            ))

    def settlement(self, trading_date):
        self._old_quantity += self._today_quantity
        self._logical_old_quantity = self._old_quantity
        self._today_quantity = self._trade_cost = self._transaction_cost = self._non_closable = 0
        self._prev_close = self.last_price
        return 0

    def update_last_price(self, price):
        self._last_price = price

    def calc_close_today_amount(self, trade_amount):
        return 0

    @property
    def _open_orders(self):
        for order in Context.get_instance().broker.get_open_orders(self.order_book_id):
            if order.position_direction == self._direction:
                yield order



def _int_to_date(d):
    r, d = divmod(d, 100)
    y, m = divmod(r, 100)
    return date(year=y, month=m, day=d)


class StockPosition(Position):
    __repr_properties__ = (
        "order_book_id", "direction", "quantity", "market_value", "trading_pnl", "position_pnl"
    )
    __instrument_types__ = INST_TYPE_IN_STOCK_ACCOUNT

    dividend_reinvestment = False
    cash_return_by_stock_delisted = True
    t_plus_enabled = True

    def __init__(self, order_book_id, direction, init_quantity=0):
        super(StockPosition, self).__init__(order_book_id, direction, init_quantity)
        self._dividend_receivable = None
        self._pending_transform = None
        self._non_closable = 0

    @property
    def dividend_receivable(self):
        # type: () -> float
        """
        dividend_receivable
        """
        if self._dividend_receivable:
            return self._dividend_receivable[1]
        return 0

    @property
    def equity(self):
        # type: () -> float
        """"""
        return super(StockPosition, self).equity + self.dividend_receivable

    @property
    def closable(self):
        # type: () -> int
        order_quantity = sum(o.unfilled_quantity for o in self._open_orders if o.position_effect in (
            POSITION_EFFECT.CLOSE, POSITION_EFFECT.CLOSE_TODAY, POSITION_EFFECT.EXERCISE
        ))
        if self.t_plus_enabled:
            return self.quantity - order_quantity - self._non_closable
        return self.quantity - order_quantity

    def set_state(self, state):
        super(StockPosition, self).set_state(state)
        self._dividend_receivable = state.get("dividend_receivable")
        self._pending_transform = state.get("pending_transform")
        self._non_closable = state.get("non_closable", 0)

    def get_state(self):
        state = super(StockPosition, self).get_state()
        state.update({
            "dividend_receivable": self._dividend_receivable,
            "pending_transform": self._pending_transform,
            "non_closable": self._non_closable
        })
        return state

    def before_trading(self, trading_date):
        # type: (date) -> float
        if self.quantity == 0:
            return 0
        if self.direction != POSITION_DIRECTION.LONG:
            raise RuntimeError("direction of stock position {} is not supposed to be short".format(self._order_book_id))
        #data_proxy = Environment.get_instance().data_proxy
        #self._handle_dividend_book_closure(trading_date, data_proxy)
        #delta_cash = self._handle_dividend_payable(trading_date)
        #self._handle_split(trading_date, data_proxy)
        delta_cash = 0
        return delta_cash

    def apply_trade(self, trade) -> float:
        # return the cash change
        delta_cash = super(StockPosition, self).apply_trade(trade)
        if trade.position_effect == POSITION_EFFECT.OPEN and self._market_tplus >= 1:
            self._non_closable += trade.last_quantity
        return delta_cash

    def settlement(self, trading_date):
        # type: (date) -> float
        output = super(StockPosition, self).settlement(trading_date)
         
        if self.quantity == 0:
            return 0
        if self.direction != POSITION_DIRECTION.LONG:
            raise RuntimeError("direction of stock position {} is not supposed to be short".format(self._order_book_id))
        delta_cash = 0
        return delta_cash 
    @property
    def _market_tplus(self):
        return 0#self._instrument.market_tplus

    # def _handle_dividend_book_closure(self, trading_date, data_proxy):
    #     # type: (date, DataProxy) -> None
    #     last_date = data_proxy.get_previous_trading_date(trading_date)
    #     dividend = data_proxy.get_dividend_by_book_date(self._order_book_id, last_date)
    #     if dividend is None:
    #         return
    #     dividend_per_share = sum(dividend['dividend_cash_before_tax'] / dividend['round_lot'])
    #     if dividend_per_share != dividend_per_share:
    #         raise RuntimeError("Dividend per share of {} is not supposed to be nan.".format(self._order_book_id))
    #     self._avg_price -= dividend_per_share

    #     try:
    #         payable_date = _int_to_date(dividend["payable_date"][0])
    #     except ValueError:
    #         payable_date = _int_to_date(dividend["ex_dividend_date"][0])

    #     self._dividend_receivable = (payable_date, self.quantity * dividend_per_share)

    # def _handle_dividend_payable(self, trading_date):
    #     # type: (date) -> float
    #     # 返回总资金的变化量
    #     if not self._dividend_receivable:
    #         return 0
    #     payable_date, dividend_value = self._dividend_receivable
    #     if payable_date != trading_date:
    #         return 0
    #     self._dividend_receivable = None
    #     if self.dividend_reinvestment:
    #         last_price = self.last_price
    #         self.apply_trade(Trade.__from_create__(
    #             None, last_price, dividend_value / last_price, SIDE.BUY, POSITION_EFFECT.OPEN, self._order_book_id
    #         ))
    #         return 0
    #     else:
    #         return dividend_value

    # def _handle_split(self, trading_date, data_proxy):
    #     ratio = data_proxy.get_split_by_ex_date(self._order_book_id, trading_date)
    #     if ratio is None:
    #         return
    #     self._today_quantity = int(self._today_quantity * ratio)
    #     self._old_quantity = int(self._old_quantity * ratio)
    #     self._logical_old_quantity = int(self._logical_old_quantity * ratio)
    #     self._avg_price /= ratio
    #     self._prev_close /= ratio


class PositionProxyDict(UserDict):
    def __init__(self, positions):
        super(PositionProxyDict, self).__init__()
        self._positions = positions  

    def keys(self):
        return self._positions.keys()

    def __getitem__(self, order_book_id):
        position_type, position_proxy_type = self._get_position_types(order_book_id)
        if order_book_id not in self._positions:
            long = position_type(order_book_id, POSITION_DIRECTION.LONG)
            short = position_type(order_book_id, POSITION_DIRECTION.SHORT)
        else:
            positions = self._positions[order_book_id]
            long = positions[POSITION_DIRECTION.LONG]
            short = positions[POSITION_DIRECTION.SHORT]
        return position_proxy_type(long, short)

    def __contains__(self, item):
        return item in self._positions

    def __iter__(self):
        return iter(self._positions)

    def __len__(self):
        return len(self._positions)

    def __setitem__(self, key, value):
        raise TypeError("{} object does not support item assignment".format(self.__class__.__name__))

    def __delitem__(self, key):
        raise TypeError("{} object does not support item deletion".format(self.__class__.__name__))

    def __repr__(self):
        return repr({k: self[k] for k in self._positions.keys()})

if __name__ == "__main__":
    position = Position(order_book_id="000001.XSHE", direction=None)
    print(type(position))
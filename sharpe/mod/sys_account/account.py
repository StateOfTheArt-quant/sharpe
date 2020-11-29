#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import six
from itertools import chain
from typing import Dict, List,Tuple, Optional, Union, Iterable
from sharpe.const import POSITION_DIRECTION, POSITION_EFFECT
from sharpe.core.events import EVENT
from sharpe.core.context import Context

from sharpe.mod.sys_account.position import Position, PositionProxyDict

class Account:
    """
    Account whicn contain all positions and cash.
    """

    def __init__(self, type:str, total_cash:float, init_positions:Dict[str, int]={}) -> None:

        self._type = type
        self._total_cash = total_cash 

        self._positions = {}
        self._backward_trade_set = set()
        self._frozen_cash = 0

        self.register_event()

        for order_book_id, init_quantity in init_positions.items():
            position_direction = POSITION_DIRECTION.LONG if init_quantity > 0 else POSITION_DIRECTION.SHORT
            self._get_or_create_pos(order_book_id, position_direction, init_quantity)

    def __repr__(self):
        positions_repr = {}
        for order_book_id, positions in self._positions.items():
            for direction, position in positions.items():
                if position.quantity != 0:
                    positions_repr.setdefault(order_book_id, {})[direction.value] = position.quantity
        return "Account(cash={}, total_value={}, positions={})".format(
            self.cash, self.total_value, positions_repr
        )

    def register_event(self):
        event_bus = Context.get_instance().event_bus
        event_bus.add_listener(
            EVENT.TRADE, lambda e: self.apply_trade(e.trade, e.order) if e.account == self else None
        )
        event_bus.add_listener(EVENT.ORDER_PENDING_NEW, self._on_order_pending_new)
        event_bus.add_listener(EVENT.ORDER_CREATION_REJECT, self._on_order_unsolicited_update)
        event_bus.add_listener(EVENT.ORDER_UNSOLICITED_UPDATE, self._on_order_unsolicited_update)
        #event_bus.add_listener(EVENT.ORDER_CANCELLATION_PASS, self._on_order_unsolicited_update)

        event_bus.add_listener(EVENT.PRE_BEFORE_TRADING, self._on_before_trading)
        event_bus.add_listener(EVENT.SETTLEMENT, self._on_settlement)

        event_bus.prepend_listener(EVENT.BAR, self._update_last_price)
        
    def get_state(self):
        return {
            'positions': {
                order_book_id: {
                    POSITION_DIRECTION.LONG: positions[POSITION_DIRECTION.LONG].get_state(),
                    POSITION_DIRECTION.SHORT: positions[POSITION_DIRECTION.SHORT].get_state()
                } for order_book_id, positions in self._positions.items()
            },
            'frozen_cash': self._frozen_cash,
            "total_cash": self._total_cash,
            'backward_trade_set': list(self._backward_trade_set),
        }

    def set_state(self, state):
        self._frozen_cash = state['frozen_cash']
        self._backward_trade_set = set(state['backward_trade_set'])
        self._total_cash = state["total_cash"]

        self._positions.clear()
        for order_book_id, positions_state in state['positions'].items():
            for direction in POSITION_DIRECTION:
                position = self._get_or_create_pos(order_book_id, direction)
                if direction in positions_state.keys():
                    position.set_state(positions_state[direction])
                else:
                    position.set_state(positions_state[direction.lower()])

    def fast_forward(self, orders=None, trades=None):
        if trades:
            close_trades = []
            # process open trade first
            for trade in trades:
                if trade.exec_id in self._backward_trade_set:
                    continue
                if trade.position_effect == POSITION_EFFECT.OPEN:
                    self.apply_trade(trade)
                else:
                    close_trades.append(trade)
            # then process close trade
            for trade in close_trades:
                self.apply_trade(trade)

        # calculate Frozen Cash
        if orders:
            self._frozen_cash = sum(self._frozen_cash_of_order(order) for order in orders if order.is_active())

    def get_positions(self) -> Iterable[Position]:
       
        """
        get all position objects
        """
        return self._iter_pos()

    def get_position(self, order_book_id: str, direction:POSITION_DIRECTION) -> Position:

        """
        get the position with the specific order_book_id
        :param order_book_id: contract identifie
        :param direction: position direction
        """
        try:
            return self._positions[order_book_id][direction]
        except KeyError:
            return Position(order_book_id, direction)

    def calc_close_today_amount(self, order_book_id, trade_amount, position_direction):
        return self._get_or_create_pos(order_book_id, position_direction).calc_close_today_amount(trade_amount)

    @property
    def type(self):
        return self._type

    @property
    def positions(self):
        return PositionProxyDict(self._positions)

    @property
    def frozen_cash(self) -> float:

        """
        frozen cash
        """
        return self._frozen_cash

    @property
    def cash(self) -> float:
        """
        available cash
        """
        return self._total_cash - self.margin - self._frozen_cash

    @property
    def market_value(self) -> float:
        """
        [float] market value
        """
        return sum(p.market_value * (1 if p.direction == POSITION_DIRECTION.LONG else -1) for p in self._iter_pos())

    @property
    def transaction_cost(self):
        """
        total transaction cost and fee
        """
        return sum(p.transaction_cost for p in self._iter_pos())

    @property
    def margin(self):
        # type: () -> float
        """
        total margin
        """
        return sum(p.margin for p in self._iter_pos())

    @property
    def buy_margin(self):
        """
        buy margin
        """
        return sum(p.margin for p in self._iter_pos(POSITION_DIRECTION.LONG))

    @property
    def sell_margin(self):
        """
        sell margin
        """
        return sum(p.margin for p in self._iter_pos(POSITION_DIRECTION.SHORT))

    @property
    def daily_pnl(self):
        """
        daily pnl
        """
        return self.trading_pnl + self.position_pnl - self.transaction_cost

    @property
    def equity(self):
        """
        total equity value
        """
        return sum(p.equity for p in self._iter_pos())

    @property
    def total_value(self):
        """
        total value
        """
        return self._total_cash + self.equity

    @property
    def total_cash(self):
        # type: () -> float
        """
        total cash
        """
        return self._total_cash - self.margin

    @property
    def position_pnl(self):
        # type: () -> float
        """
        position pnl
        """
        return sum(p.position_pnl for p in self._iter_pos())

    @property
    def trading_pnl(self):
        # type: () -> float
        """
        trading pnl
        """
        return sum(p.trading_pnl for p in self._iter_pos())

    def _on_before_trading(self, _):
        trading_date = Context.get_instance().trading_dt.date()
        for position in self._iter_pos():
            self._total_cash += position.before_trading(trading_date)

    def _on_settlement(self, event):
        trading_date = Context.get_instance().trading_dt.date()

        for order_book_id, positions in list(self._positions.items()):
            for position in six.itervalues(positions):
                delta_cash = position.settlement(trading_date)
                self._total_cash += delta_cash

        for order_book_id, positions in list(self._positions.items()):
            if all(p.quantity == 0 and p.equity == 0 for p in six.itervalues(positions)):
                del self._positions[order_book_id]

        self._backward_trade_set.clear()

        # if total_value <= 0, forced_liquidation
        forced_liquidation = True#Environment.get_instance().config.base.forced_liquidation
        if self.total_value <= 0 and forced_liquidation:
            if self._positions:
                print("Trigger Forced Liquidation, current total_value is 0")
            self._positions.clear()
            self._total_cash = 0

    def _on_order_pending_new(self, event):
        if event.account != self:
            return
        order = event.order
        self._frozen_cash += self._frozen_cash_of_order(order)

    def _on_order_unsolicited_update(self, event):
        if event.account != self:
            return
        order = event.order
        if order.filled_quantity != 0:
            self._frozen_cash -= order.unfilled_quantity / order.quantity * self._frozen_cash_of_order(order)
        else:
            self._frozen_cash -= self._frozen_cash_of_order(event.order)

    def apply_trade(self, trade, order=None) -> None:

        if trade.exec_id in self._backward_trade_set:
            return
        order_book_id = trade.order_book_id
        if order and trade.position_effect != POSITION_EFFECT.MATCH:
            if trade.last_quantity != order.quantity:
                self._frozen_cash -= trade.last_quantity / order.quantity * self._frozen_cash_of_order(order)
            else:
                self._frozen_cash -= self._frozen_cash_of_order(order)
        if trade.position_effect == POSITION_EFFECT.MATCH:
            delta_cash = self._get_or_create_pos(
                order_book_id, POSITION_DIRECTION.LONG
            ).apply_trade(trade) + self._get_or_create_pos(
                order_book_id, POSITION_DIRECTION.SHORT
            ).apply_trade(trade)
            self._total_cash += delta_cash
        else:
            delta_cash = self._get_or_create_pos(order_book_id, trade.position_direction).apply_trade(trade)
            self._total_cash += delta_cash
        self._backward_trade_set.add(trade.exec_id)

    def _iter_pos(self, direction=None):
        # type: (Optional[POSITION_DIRECTION]) -> Iterable[Position]
        if direction:
            return (p[direction] for p in six.itervalues(self._positions))
        else:
            return chain(*[six.itervalues(p) for p in six.itervalues(self._positions)])

    def _get_or_create_pos(self, order_book_id, direction, init_quantity=0):
        # type: (str, Union[str, POSITION_DIRECTION], Optional[int]) -> Position
        if order_book_id not in self._positions:
            if direction == POSITION_DIRECTION.LONG:
                long_init_position, short_init_position = init_quantity, 0
            else:
                long_init_position, short_init_position = 0, init_quantity

            positions = self._positions.setdefault(order_book_id, {
                POSITION_DIRECTION.LONG: Position(order_book_id, POSITION_DIRECTION.LONG, long_init_position),
                POSITION_DIRECTION.SHORT: Position(order_book_id, POSITION_DIRECTION.SHORT, short_init_position)
            })
        else:
            positions = self._positions[order_book_id]
        return positions[direction]

    def _update_last_price(self, _):
        context = Context.get_instance()
        for order_book_id, positions in self._positions.items():
            price = context.get_last_price(order_book_id)
            if price == price:
                for position in six.itervalues(positions):
                    position.update_last_price(price)

    def _frozen_cash_of_order(self, order):
        #context = Context.get_instance()
        if order.position_effect == POSITION_EFFECT.OPEN:
            #instrument = context.data_source.instruments(order.order_book_id)
            order_cost = order.frozen_price*order.quantity #instrument.calc_cash_occupation(order.frozen_price, order.quantity, order.position_direction)
        else:
            order_cost = 0
        return order_cost + 5#context.get_order_transaction_cost(order) to fix

if __name__ == "__main__":
    account = Account(type="stock", total_cash=1000000)
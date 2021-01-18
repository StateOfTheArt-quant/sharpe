#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sharpe.utils.mock_data import create_toy_feature
from sharpe.data.data_source import DataSource
from sharpe.environment import TradingEnv
from sharpe.core.context import Context
from sharpe.mod.sys_account.api import order_target_weights
from sharpe.const import SIDE
import unittest
import pdb

class TestOneObjectImplmentCorrection(unittest.TestCase):
    
    def setUp(self):
        feature_df, price_s = create_toy_feature(order_book_ids_number=2, feature_number=3, start="2020-01-01", end="2020-01-11", random_seed=111)
        self.data_source = DataSource(feature_df=feature_df, price_s=price_s)
        
        self.order_book_ids  = self.data_source.get_available_order_book_ids() 
        
        
        self.look_backward_window = 2    
        
        self.starting_cash = {"STOCK":1000000, "FUTURE":10000}
        
        
        self.commission_rate = 0.0008
        self.tax_rate = 0.001
        
        self.commission_multiplier=1
        self.min_commission=5
        self.tax_multiplier=1
        
        self.env= TradingEnv(data_source=self.data_source,
                             look_backward_window=self.look_backward_window,
                             mode="rl",
                             starting_cash=self.starting_cash,
                             commission_multiplier=self.commission_multiplier,
                             min_commission=self.min_commission,
                             tax_multiplier=self.tax_multiplier)
        
        context = Context.get_instance()
        
        #stock account
        expect_market_value_stock = 0
        expect_cash_stock = self.starting_cash["STOCK"]
        expect_total_value_stock = expect_cash_stock + expect_market_value_stock
        
        #future account
        expect_market_value_future = 0
        expect_cash_future = self.starting_cash["FUTURE"]
        expect_total_value_future = expect_cash_future + expect_market_value_future
        self.expect_total_value_future = expect_total_value_future
        #portfolio
        expect_total_value = expect_total_value_stock + expect_total_value_future
        
        
        self.trading_dts = context.get_available_trading_dts()
        first_trading_dt = self.trading_dts[0]
        self.order_book_id = self.order_book_ids[0]
        
        
        to_submit_orders = order_target_weights({self.order_book_id:0.5})
        state, reward, is_done, info = self.env.step(action=to_submit_orders)
        
        
        
        order = to_submit_orders[0] 

        expect_deal_price = self.data_source.get_last_price(order_book_id = self.order_book_id , dt=first_trading_dt)
        expect_deal_money = expect_deal_price * order.quantity
 
        expect_commission_fee = expect_deal_money * self.commission_rate * self.commission_multiplier
        expect_tax = 0 # no tax rate when buy
        expect_transaction_cost = expect_commission_fee + expect_tax
        
        first_trade = context.tracker._trades[0]
        self.first_trade = first_trade
        self.assertEqual(first=first_trade["order_book_id"], second= self.order_book_id)
        self.assertEqual(first=first_trade["trading_datetime"], second = first_trading_dt.strftime("%Y-%m-%d %H:%M:%S"))
        self.assertEqual(first=first_trade["last_price"], second=expect_deal_price)
        self.assertEqual(first=first_trade["commission"], second=expect_commission_fee)
        self.assertEqual(first=first_trade["tax"], second=expect_tax)
        self.assertEqual(first=first_trade["transaction_cost"], second=expect_transaction_cost)
        
        # portfolio and accounts change after trading
        #stock account
        expect_market_value_stock = expect_deal_money
        expect_cash_stock = self.starting_cash["STOCK"] - expect_market_value_stock - expect_transaction_cost #502448.2768
        #expect_total_value_stock = expect_cash_stock + expect_market_value_stock
        
        #future account
        #expect_market_value_future = 0
        #expect_cash_future = self.starting_cash["FUTURE"]
        #expect_total_value_future = expect_cash_future + expect_market_value_future
        
        #portfolio
        #expect_total_value = expect_total_value_stock + expect_total_value_future
        
        
        # settlement on the next bar
        next_trading_dt = self.trading_dts[1]
        expect_settlement_price = self.data_source.get_last_price(order_book_id = self.order_book_id , dt=next_trading_dt)
        expect_market_value_stock_settlement = first_trade["last_quantity"] * expect_settlement_price
        self.expect_cash_stock_settlement = expect_cash_stock
        self.expect_total_value_stock_settlement = self.expect_cash_stock_settlement + expect_market_value_stock_settlement
        
        self.expect_total_value_future_settlement = expect_total_value_future
        
        self.expect_total_value_settlement = self.expect_total_value_stock_settlement + self.expect_total_value_future_settlement
        
        expect_reward = (self.expect_total_value_settlement - expect_total_value) / expect_total_value
        self.assertAlmostEqual(first=reward, second=expect_reward)
        
    def test_senond_step_sell(self):
        to_submit_orders = order_target_weights({self.order_book_id:0.2})
        state, reward, is_done, info = self.env.step(action=to_submit_orders)
        
        order = to_submit_orders[0]
        # this is a sell trade
        self.assertEqual(first=order.side, second=SIDE.SELL)
        #
        second_trading_dt = self.trading_dts[1]
        expect_deal_price = self.data_source.get_last_price(order_book_id = self.order_book_id , dt=second_trading_dt)
        expect_deal_money = expect_deal_price * order.quantity
     
        expect_commission_fee = expect_deal_money * self.commission_rate * self.commission_multiplier
        expect_tax = expect_deal_money * self.tax_rate * self.tax_multiplier # no tax rate when buy
        expect_transaction_cost = expect_commission_fee + expect_tax
        print("expect_transaction_cost: {}".format(expect_transaction_cost))
        second_trade = Context.get_instance().tracker._trades[1]
        print(second_trade)
        self.assertEqual(first=second_trade["order_book_id"], second= self.order_book_id)
        self.assertEqual(first=second_trade["trading_datetime"], second = second_trading_dt.strftime("%Y-%m-%d %H:%M:%S"))
        self.assertEqual(first=second_trade["last_price"], second=expect_deal_price)
        self.assertEqual(first=second_trade["commission"], second=expect_commission_fee)
        self.assertEqual(first=second_trade["tax"], second=expect_tax)
        self.assertEqual(first=second_trade["transaction_cost"], second=expect_transaction_cost)
        
        expect_cash_stock_settlement = self.expect_cash_stock_settlement + expect_deal_money -  expect_transaction_cost
        
        
        next_trading_dt = self.trading_dts[2]
        expect_settlement_price = self.data_source.get_last_price(order_book_id = self.order_book_id , dt=next_trading_dt)
        expect_remaining_market_value_stock_settlement = (self.first_trade["last_quantity"] - second_trade["last_quantity"]) * expect_settlement_price
        
        self.expect_total_value_stock_settlement = expect_cash_stock_settlement + expect_remaining_market_value_stock_settlement
        
        self.expect_total_value_future_settlement = self.expect_total_value_future
        
        expect_total_value_settlement = self.expect_total_value_stock_settlement + self.expect_total_value_future_settlement
        
        expect_reward = (expect_total_value_settlement - self.expect_total_value_settlement) / self.expect_total_value_settlement
        #pdb.set_trace()
        self.assertAlmostEqual(first=reward, second=expect_reward)
        
        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTest(TestOneObjectImplmentCorrection("test_senond_step_sell"))
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
    
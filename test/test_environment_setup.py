#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sharpe.utils.mock_data import create_toy_feature
from sharpe.data.data_source import DataSource
from sharpe.environment import TradingEnv
from sharpe.core.context import Context
import unittest


class TestOneObjectImplmentCorrection(unittest.TestCase):
    
    def setUp(self):
        feature_df, price_s = create_toy_feature(order_book_ids_number=2, feature_number=3, start="2020-01-01", end="2020-01-11", random_seed=111)
        self.data_source = DataSource(feature_df=feature_df, price_s=price_s)
        
        self.look_backward_window = 2    
        
        self.starting_cash = {"STOCK":1000000, "FUTURE":10000}
        
        self.env= TradingEnv(data_source=self.data_source, look_backward_window=self.look_backward_window, mode="rl", starting_cash=self.starting_cash)
    
    def test_portfolio_setup(self):
        portfolio = Context.get_instance().portfolio
        expected_total_value = sum(self.starting_cash.values())
        actual_total_value = portfolio.total_value
        self.assertEqual(actual_total_value, expected_total_value)
    
    def test_trading_dts_setup(self):
        #test available trading dts
        all_trading_dts = self.data_source.get_available_trading_dts()
        expected_available_trading_dts = all_trading_dts[self.look_backward_window-1:]
        actual_available_trading_dts = Context.get_instance().get_available_trading_dts()
        self.assertListEqual(list(actual_available_trading_dts), list(expected_available_trading_dts))
        
        
        #test the first trading dt
        expected_first_trading_dt = expected_available_trading_dts[0]
        actual_first_trading_dt = Context.get_instance().trading_dt
        self.assertEqual(actual_first_trading_dt, expected_first_trading_dt)
    
    
        order_book_ids = self.data_source.get_available_order_book_ids()
        
        expected_first_last_price = self.data_source.get_last_price(order_book_id=order_book_ids[0], dt=expected_first_trading_dt)
        actual_first_last_price = Context.get_instance().get_last_price(order_book_id=order_book_ids[0])
        self.assertEqual(actual_first_last_price, expected_first_last_price)
    
if __name__ == "__main__":
    unittest.main()        



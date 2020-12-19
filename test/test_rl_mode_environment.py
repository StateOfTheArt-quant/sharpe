#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sharpe.utils.mock_data import create_toy_feature
from sharpe.data.data_source import DataSource
from sharpe.environment import TradingEnv
import unittest


# class TestOneObjectImplmentCorrection(unittest.TestCase):
    
#     def setUp(self):
#         feature_df, price_s = create_toy_feature(order_book_ids_number=2, feature_number=3, start="2020-01-01", end="2020-01-11", random_seed=111)
#         data_source = DataSource(feature_df=feature_df, price_s=price_s)
        
#         look_backward_window = 2    
        
#         starting_cash = {"STOCK":1000000, "FUTURE":10000}
        
#         self.env= TradingEnv(data_source=data_source, look_backward_window=2, mode="rl", starting_cash=starting_cash)
#         print('--------------------------------------------')
#         from sharpe.core.context import Context
        
#         context = Context.get_instance()
#         print("current context \n",context.__dict__)
        
        
#         #test available trading dts
#         all_trading_dts = data_source.get_available_trading_dts()
#         expected_available_trading_dts = all_trading_dts[look_backward_window-1:]
#         actual_available_trading_dts = context.get_available_trading_dts()
#         self.assertEqual(actual_available_trading_dts, expected_available_trading_dts)
        
        
#         #test the first dt
#         expected_first_trading_dt = expected_available_trading_dts[0]
#         actual_first_trading_dt = context.trading_dt
#         self.assertEqual(actual_available_trading_dts, expected_available_trading_dts)
        
# # if __name__ == "__main__":
# #     unittest.main()        
        













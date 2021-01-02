#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
from sharpe.data.data_source import DataSource
from sharpe.utils.mock_data import create_toy_feature
import unittest


class TestDataSource(unittest.TestCase):
    def test_data_from_data_utils(self):
        feature_df, price_s = create_toy_feature(order_book_ids_number=2, feature_number=3, start="2020-01-01", end="2020-01-11",random_seed=555)
        print(price_s)
        data_source = DataSource(feature_df=feature_df, price_s=price_s)
    
        #availabel_dts
        availabel_dts = data_source.get_available_trading_dts()
        
        first_dt_expected = pd.Timestamp("2020-01-01")
        first_dt = availabel_dts[0] 
        self.assertEqual(first_dt, first_dt_expected)
        
        end_dt_expected = pd.Timestamp("2020-01-11")
        end_dt = availabel_dts[-1] 
        self.assertEqual(end_dt, end_dt_expected)

    
        #get_availabel_order_book_ids
        order_book_ids = data_source.get_available_order_book_ids()
        
        forth_dt_expected = pd.Timestamp("2020-01-04")
        forth_dt = availabel_dts[3]
        self.assertEqual(forth_dt, forth_dt_expected)
        
        #get state
        #state = data_source.history_bars(order_book_ids=order_book_ids, dt=availabel_dts[3], bar_count=2)
            
        #get last price
        last_price = data_source.get_last_price(order_book_id=order_book_ids[0], dt=forth_dt_expected)
        last_price_expected = 20.11
        self.assertEqual(last_price, last_price_expected)
    
if __name__ == "__main__":
    unittest.main()
    

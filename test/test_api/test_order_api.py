#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from sharpe.utils.mock_data import create_toy_feature
from sharpe.data.data_source import DataSource
from sharpe.environment import TradingEnv
from sharpe.const import POSITION_DIRECTION
from sharpe.mod.sys_account.api import order_target_quantities, get_position

import unittest


feature_df, price_s = create_toy_feature(order_book_ids_number=3, feature_number=3, random_seed=111)
data_source = DataSource(feature_df=feature_df, price_s=price_s)

all_order_book_ids = data_source.get_available_order_book_ids()
print(all_order_book_ids)

STOCK_INIT_CASH = 1000000
    
env= TradingEnv(data_source=data_source, look_backward_window=2, mode="non-rl", starting_cash= {"STOCK":STOCK_INIT_CASH},
                commission_multiplier=0,
                min_commission=0,
                tax_multiplier=0)


class TestOrderTargetQuantities(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def test_order_target_quantites(self):
        state = env.reset()
        target_quantities1 = {all_order_book_ids[0] : 500, all_order_book_ids[1]:600}
        to_submit_orders1 = order_target_quantities(target_quantities1)
        
        state, reward, is_done, info = env.step(action=to_submit_orders1)
        
        current_positions0 = get_position(all_order_book_ids[0], POSITION_DIRECTION.LONG)
        self.assertEqual(first=500, second=current_positions0.quantity)
        
        current_positions1 = get_position(all_order_book_ids[1], POSITION_DIRECTION.LONG)
        self.assertEqual(first=600, second=current_positions1.quantity)
        

        target_quantities2 = {all_order_book_ids[0] : 800, all_order_book_ids[1]:400}
        to_submit_orders2 = order_target_quantities(target_quantities2)


        state, reward, is_done, info = env.step(action=to_submit_orders2)
        current_positions0 = get_position(all_order_book_ids[0], POSITION_DIRECTION.LONG)
        self.assertEqual(first=800, second=current_positions0.quantity)

        current_positions1 = get_position(all_order_book_ids[1], POSITION_DIRECTION.LONG)
        self.assertEqual(first=400, second=current_positions1.quantity)
        
        
        target_quantities3 = {all_order_book_ids[0] : 200, all_order_book_ids[2]:300}
        to_submit_orders3 = order_target_quantities(target_quantities3)
        
        state, reward, is_done, info = env.step(action=to_submit_orders3)
        
        current_positions0 = get_position(all_order_book_ids[0], POSITION_DIRECTION.LONG)
        current_positions1 = get_position(all_order_book_ids[1], POSITION_DIRECTION.LONG)
        current_positions2 = get_position(all_order_book_ids[2], POSITION_DIRECTION.LONG)
        self.assertEqual(first=200, second=current_positions0.quantity)
        self.assertEqual(first=0, second=current_positions1.quantity)
        self.assertEqual(first=300, second=current_positions2.quantity)
        
if __name__ == "__main__":
    unittest.main()
        
        
        

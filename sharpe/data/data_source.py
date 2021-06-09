#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List, Union
import pandas as pd
import datetime

class DataSource(object):
    
    def __init__(self, feature_df:pd.DataFrame, price_s:pd.Series) -> None:
        self._feature_df = feature_df
        self._price_s = price_s        
        
        self.order_book_ids_index = feature_df.index.levels[0].unique()
        self.trading_dts_index = price_s.index.levels[1].unique()
        self.feature_list = feature_df.columns.to_list()
    
    
    def history_bars(self, order_book_ids:List[str], dt:datetime.datetime, bar_count:int) -> pd.DataFrame:
        """get the current state(feature) with look_backward_window"""
        
        end_position = self.trading_dts_index.searchsorted(dt, side="right")
        start_position = end_position - bar_count if end_position >= bar_count else 0
        trading_dates_slice = self.trading_dts_index[start_position: end_position]
        state = self._feature_df.loc[(self.order_book_ids_index, trading_dates_slice),:]
        return state
    
    def get_last_price(self, order_book_id, dt):
        return self._price_s.loc[(order_book_id, dt)]
    
    def get_previous_close(self, order_book_id, dt):
        idx = self.trading_dts_index.searchsorted(dt)
        prev_dt = self.trading_dts_index[idx-1]
        return self._price_s.loc[(order_book_id, prev_dt)]
    
    def get_available_trading_dts(self):
        return self.trading_dts_index
    
    def get_available_order_book_ids(self):
        return self.order_book_ids_index
    
    def instrument_type(self, order_book_id):
        return "CS" # common stock







if __name__ == "__main__":
    from sharpe.utils.mock_data import create_toy_feature
    
    feature_df, price_s = create_toy_feature(order_book_ids_number=2, feature_number=3)
    
    data_source = DataSource(feature_df=feature_df, price_s=price_s)
    
    #availabel_dts
    availabel_dts = data_source.get_available_trading_dts()
    
    #get_availabel_order_book_ids
    order_book_ids = data_source.get_available_order_book_ids()
    
    #get state
    state = data_source.history_bars(order_book_ids=order_book_ids, dt=availabel_dts[3], bar_count=2)
    
    #get last price
    last_price = data_source.get_last_price(order_book_id=order_book_ids[0], dt=availabel_dts[3])
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List, Union
import pandas as pd
import datetime

def count_nan(df):
    output = df.isnull().sum(axis = 0)
    return output 
#nan_groupby_status = index_daily.groupby(level=0).apply(count_nan)

class DataSource(object):
    
    def __init__(self, feature_df:pd.DataFrame, price_s:pd.Series) -> None:
        self._feature_df = feature_df.sort_index(level=[0,1], ascending=True)
        self._price_s = price_s        
        
        self.multi_index = self._feature_df.index
        if not isinstance(self.multi_index, pd.MultiIndex):
            raise ValueError("the input of dataframe should be with pandas.MultiIndex")
        
        
        #check whether balance data or not
        order_book_ids_stats = self.multi_index.get_level_values(0).value_counts()
        if len(order_book_ids_stats.unique()) == 1:
            print("the input dataframe is balance data")
        else:
            print("attention: the input dataframe is not a balance data")
            print(order_book_ids_stats)
        
        
        #check NaN
        nan_groupby_status =  self._feature_df.groupby(level=0).apply(count_nan)
        print("the NaN value statistic")
        print(nan_groupby_status)
        
        self.order_book_ids_index = self.index.get_level_values(0).unique()
        self.trading_dts_index = self.index.get_level_values(1).unique().sort_values()
        if not isinstance(self.trading_dts_index, pd.DatetimeIndex):
            print("the level 1 index should be pandas.DatetimeIndex")
        self.feature_list = feature_df.columns.to_list()
    
    
    def history_bars(self, dt:datetime.datetime, bar_count:int) -> pd.DataFrame:
        """get the current state(feature) with look_backward_window"""
        """remove order_book_ids parameter to allow unbalance data """
        
        end_position = self.trading_dts_index.searchsorted(dt, side="right")
        start_position = end_position - bar_count if end_position >= bar_count else 0
        trading_dates_slice = self.trading_dts_index[start_position: end_position]
        
        # order_book_ids
        idx = self.multi_index.get_loc_level(dt, level=1)
        position_bool = list(idx[0])
        order_book_ids = list(self.multi_index.get_level_values(0)[position_bool])
            
        state = self._feature_df.loc[(order_book_ids, trading_dates_slice),:]
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
    dt = availabel_dts[3]
    print("dt: {}".format(dt))
    state = data_source.history_bars(dt=dt, bar_count=2)
    print(state)
    
    #get last price
    last_price = data_source.get_last_price(order_book_id=order_book_ids[0], dt=availabel_dts[3])
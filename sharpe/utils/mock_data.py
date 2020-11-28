#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np


def create_toy_feature(order_book_ids_number, feature_number, start="2020-01-01", end="2020-01-11", frequency="D", random_seed=None):
    if random_seed is not None:
        np.random.seed(random_seed)
    
    order_book_ids = ["00000{}.XSHE".format(i) for i in range(1,order_book_ids_number+1)]
    
    trading_datetime = pd.date_range(start=start, end=end, freq=frequency)
    number = len(trading_datetime) * len(order_book_ids)
    
    multi_index = pd.MultiIndex.from_product([order_book_ids, trading_datetime],names=["order_book_id","datetime"])
    
    column_names = ["feature_{}".format(i) for i in range(1,feature_number+1)]
    
    feature_df = pd.DataFrame(np.random.randn(number, feature_number), index=multi_index, columns=column_names)
    
    
    # create mock price
    price_list= []
    for i in range(order_book_ids_number):
        start_price = np.random.randint(100)
        price = np.random.uniform(low = start_price, high = start_price+30, size = len(trading_datetime))
        price_list.append(price)
    
    price_all = np.hstack(price_list).round(decimals = 2)
    price_s = pd.Series(price_all, index=multi_index, name='price')
   
    return feature_df, price_s



if __name__ == "__main__":
    feature_df, price_s = create_toy_feature(order_book_ids_number=5, feature_number=3)
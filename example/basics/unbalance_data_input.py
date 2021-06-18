#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ================================= #
# understand pandas multiindex      #
# ================================= #
## create feature and label
import pandas as pd
import numpy as np
import datetime
start1 = "2020-12-26"
end1 = "2021-01-04"

start2 = "2020-12-24"
end2 = "2021-01-02"

middle_date ="2020-12-30"

frequency = "D"
feature_list = ["feature1","feature2","feature3"]
label_list = ["label1","label2"]


trading_datetime1 = pd.date_range(start=start1, end=end1, freq=frequency)
feature1 = pd.DataFrame(np.random.randn(len(trading_datetime1), len(feature_list)), columns=  feature_list, index=trading_datetime1)
feature1.index.name = "datetime"
feature1["order_book_id"] = "01"
label1 = pd.DataFrame(np.random.randn(len(trading_datetime1), len(label_list)), columns=label_list,index=trading_datetime1)
label1["order_book_id"] = "01"
label1.index.name = "datetime"


trading_datetime2 = pd.date_range(start=start1, end=middle_date, freq=frequency)
feature2 = pd.DataFrame(np.random.randn(len(trading_datetime2), len(feature_list)), columns=  feature_list, index=trading_datetime2)
feature2.index.name = "datetime"
feature2["order_book_id"] = "02"
label2 = pd.DataFrame(np.random.randn(len(trading_datetime2), len(label_list)), columns=label_list,index=trading_datetime2)
label2["order_book_id"] = "02"
label2.index.name = "datetime"


trading_datetime3 = pd.date_range(start=start2, end=end2, freq=frequency)
feature3 = pd.DataFrame(np.random.randn(len(trading_datetime3), len(feature_list)), columns=  feature_list, index=trading_datetime3)
feature3.index.name = "datetime"
label3 = pd.DataFrame(np.random.randn(len(trading_datetime3), len(label_list)), columns=label_list, index=trading_datetime3)
feature3["order_book_id"] = "03"

label3["order_book_id"] = "03"
label3.index.name = "datetime"


trading_datetime4 = pd.date_range(start=middle_date, end=end2, freq=frequency)
feature4 = pd.DataFrame(np.random.randn(len(trading_datetime4), len(feature_list)), columns=  feature_list, index=trading_datetime4)
feature4.index.name = "datetime"
label4 = pd.DataFrame(np.random.randn(len(trading_datetime4), len(label_list)), columns=label_list, index=trading_datetime4)
feature4["order_book_id"] = "04"

label4["order_book_id"] = "04"
label4.index.name = "datetime"



all_feature = pd.concat([feature1, feature2, feature3, feature4], axis=0)
all_label = pd.concat([label1, label2, label3, label4], axis=0)

#reset index
all_feature.reset_index(inplace=True)
all_feature.set_index(keys=["order_book_id","datetime"], inplace=True)

all_label.reset_index(inplace=True)
all_label.set_index(keys=["order_book_id","datetime"], inplace=True)

data_df_multiindex = pd.concat({"feature":all_feature, "label":all_label}, axis=1)


col_set = "feature"
features = data_df_multiindex[col_set]

all_price = pd.Series(100,index=all_feature.index)


from sharpe.data.data_source import DataSource
from sharpe.environment import TradingEnv
data_source = DataSource(feature_df=all_feature, price_s=all_price)

look_backward_window = 2    
starting_cash = {"STOCK":1000000, "FUTURE":10000}
env= TradingEnv(data_source=data_source, look_backward_window=2, starting_cash=starting_cash)
print('--------------------------------------------')


state = env.reset()


while True:
    print("the current trading_dt is: {}".format(env.trading_dt))
    
    print("current state: \n{}".format(state))

    next_state, reward, done, info = env.step(action=None)
    
    print("the reward of this action: {}".format(reward))
    #print("the next state is \n {}".format(next_state))
    if done:
        break
    else:
        state = next_state








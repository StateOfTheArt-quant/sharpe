#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from enum import Enum, EnumMeta


class CustomEnumMeta(EnumMeta):
    def __new__(metacls, cls, bases, classdict):
        enum_class = super(CustomEnumMeta, metacls).__new__(metacls, cls, bases, classdict)
        enum_class._member_reverse_map = {v.value: v for v in enum_class.__members__.values()}
        return enum_class

    def __contains__(cls, member):
        if super(CustomEnumMeta, cls).__contains__(member):
            return True
        if isinstance(member, str):
            return member in cls._member_reverse_map
        return False

    def __getitem__(self, item):
        try:
            return super(CustomEnumMeta, self).__getitem__(item)
        except KeyError:
            return self._member_reverse_map[item]


class CustomEnum(str, Enum, metaclass=CustomEnumMeta):
    def __repr__(self):
        return "%s.%s" % (
            self.__class__.__name__, self._name_)
    

class DEFAULT_ACCOUNT_TYPE(CustomEnum):
    STOCK = "STOCK"
    FUTURE = "FUTURE"
    BOND = "BOND"


class INSTRUMENT_TYPE(CustomEnum):
    CS = "CS"
    FUTURE = "Future"
    OPTION = "Option"
    ETF = "ETF"
    LOF = "LOF"
    INDX = "INDX"
    PUBLIC_FUND = 'PublicFund'
    BOND = "Bond"
    CONVERTIBLE = "Convertible"
    SPOT = "Spot"
    REPO = "Repo"



INST_TYPE_IN_STOCK_ACCOUNT = [
    INSTRUMENT_TYPE.CS,
    INSTRUMENT_TYPE.ETF,
    INSTRUMENT_TYPE.LOF,
    INSTRUMENT_TYPE.INDX,
    INSTRUMENT_TYPE.PUBLIC_FUND
]

class ORDER_TYPE(CustomEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class SIDE(CustomEnum):
    BUY = "BUY"                      
    SELL = "SELL"                    
    FINANCING = "FINANCING"          #     
    MARGIN = "MARGIN"                # inverse repurchse
    CONVERT_STOCK = "CONVERT_STOCK"  

class POSITION_EFFECT(CustomEnum):
    OPEN = "OPEN"
    CLOSE = "CLOSE"
    CLOSE_TODAY = "CLOSE_TODAY"
    EXERCISE = "EXERCISE"
    MATCH = "MATCH"

class POSITION_DIRECTION(CustomEnum):
    LONG = "LONG"
    SHORT = "SHORT"

    
class ORDER_STATUS(CustomEnum):
    PENDING_NEW = "PENDING_NEW"
    ACTIVE = "ACTIVE"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    PENDING_CANCEL = "PENDING_CANCEL"
    CANCELLED = "CANCELLED"

class MATCHING_TYPE(CustomEnum):
    CURRENT_BAR_CLOSE = "CURRENT_BAR_CLOSE"
    NEXT_BAR_OPEN = "NEXT_BAR_OPEN"
    NEXT_TICK_LAST = "NEXT_TICK_LAST"
    NEXT_TICK_BEST_OWN = "NEXT_TICK_BEST_OWN"
    NEXT_TICK_BEST_COUNTERPARTY = "NEXT_TICK_BEST_COUNTERPARTY"

class DAYS_CNT(object):
    DAYS_A_YEAR = 365
    TRADING_DAYS_A_YEAR = 252


class MARKET(CustomEnum):
    CN = "CN"
    HK = "HK"





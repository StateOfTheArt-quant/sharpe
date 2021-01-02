#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import abc
from six import with_metaclass

class AbstractBroker(with_metaclass(abc.ABCMeta)):
    """
    Broker Abstract Interface
    
    Magage the lifetime of the Orders
    """

    @abc.abstractmethod
    def submit_order(self, order):
        raise NotImplementedError

    @abc.abstractmethod
    def cancel_order(self, order):
        """
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_open_orders(self, order_book_id=None):
        """
        """
        raise NotImplementedError
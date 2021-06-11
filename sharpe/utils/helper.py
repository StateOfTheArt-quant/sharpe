#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import collections
import numpy as np

def round_ceil(a, precision=3):
    return np.true_divide(np.ceil(a * 10**precision), 10**precision)

def round_floor(a, precision=3):
    return np.true_divide(np.floor(a * 10**precision), 10**precision)

round_floor_vectorized  = np.vectorize(round_floor, otypes=[float])

def _clean_weights(weights, cutoff=1e-4, rounding=3):
    """
        Helper method to clean the raw weights, setting any weights whose absolute
        values are below the cutoff to zero, and rounding the rest.
        :param cutoff: the lower bound, defaults to 1e-4
        :type cutoff: float, optional
        :param rounding: number of decimal places to round the weights, defaults to 5.
                         Set to None if rounding is not desired.
        :type rounding: int, optional
        :return: asset weights
        :rtype: OrderedDict
    """
    if weights is None:
        raise AttributeError("Weights not yet computed")
    
    clean_weights = weights.copy()
    clean_weights[np.abs(clean_weights) < cutoff] = 0
    if rounding is not None:
        if not isinstance(rounding, int) or rounding < 1:
                raise ValueError("rounding must be a positive integer")
        clean_weights = round_floor_vectorized(clean_weights, rounding)
    return clean_weights


def clean_weights(weights, cutoff=1e-4, rounding=5):    
    if isinstance(weights, np.ndarray):
        clean_weights = _clean_weights(weights, cutoff, rounding)
        return clean_weights 
    
    elif isinstance(weights, dict):
        keys = weights.keys()
        values = list(weights.values())
        values_array = np.array(values)
        clean_weights = _clean_weights(values_array, cutoff, rounding)
        return collections.OrderedDict(zip(keys, clean_weights))
    else:
        raise ValueError("weight dtype is not supported")


if __name__ == "__main__":
    weights = np.array([0.9900001,0.01002])
    output_weights = clean_weights(weights, cutoff=1e-3,rounding=3)


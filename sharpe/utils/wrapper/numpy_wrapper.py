#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import gym


class Numpy(gym.Wrapper):
    """
    This wrapper converts
    * states from pandas to numpy
    """
    
    def _convert_state(self, state):
        if isinstance(state, pd.DataFrame):
            state = state.values.reshape(*self.observation_space.shape)
        return state
    
    def _convert_to_numpy(self, data):
        if isinstance(data, (pd.Series, pd.DataFrame)):
            data = data.values
        if isinstance(data, dict):
            data = {k: self._convert_to_numpy(data[k]) for k in data}
        return data
    
    def step(self, action):
        state, reward, done, info = self.env.step(action)
        state = self._convert_state(state)
        info = self._convert_to_numpy(info)
        return state, reward, done, info
    
    def reset(self, *args, **kwargs):
        state = self.env.reset(*args, **kwargs)
        state = self._convert_state(state)
        return state

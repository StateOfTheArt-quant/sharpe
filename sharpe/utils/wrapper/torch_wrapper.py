# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# ===================================================== #
# make sharpe more independent, do not depend on torch  #
# ===================================================== #

# import gym
# import torch
# import numpy as np
# from sharpe.utils.wrapper.numpy_wrapper import Numpy

# dtype_mapping = {np.dtype("int8"): torch.int8,
#                  np.dtype("int16"): torch.int16,
#                  np.dtype("int32"): torch.int32,
#                  np.dtype("float16"): torch.float16,
#                  np.dtype("float32"): torch.float32,
#                  np.dtype("float64"): torch.float64,
#                  np.dtype("bool"): torch.bool}


# class Torch(gym.Wrapper):
#     """
#     This wrapper converts
#     * states from pandas/numpy to torch.Tensor
#     * action from troch.Tensor to numpy
#     """
#     def __init__(self, env):
#         if not isinstance(env, Numpy):
#             env = Numpy(env)
#         super(Torch, self).__init__(env)
    
    
#     def _convert_atomic_action(self, action):
#         if isinstance(action, torch.Tensor):
#             action = action.view(-1).data.numpy()
#         if isinstance(action, (int, float)):
#             action = int(action)
#         return action
    
#     def step(self, action):
#         action = self._convert_atomic_action(action)
#         state, reward, done, info = self.env.step(action)
#         state = self._convert_state(state)
#         info = self._convert_to_tensor(info)
#         return state, reward, done, info
    
#     def _convert_state(self, state):
#         if isinstance(state, np.ndarray):
#             state_ts = torch.tensor(state, dtype=dtype_mapping[state.dtype])
#         return state_ts
    
#     def _convert_to_tensor(self, data):
#         if isinstance(data, np.ndarray):
#             data = self._convert_state(data)
#         if isinstance(data, dict):
#             data = {k: self._convert_to_tensor(data[k]) for k in data}
#         return data
    
#     def reset(self, *args, **kwargs):
#         state = self.env.reset(*args, **kwargs)
#         state = self._convert_state(state)
#         return state

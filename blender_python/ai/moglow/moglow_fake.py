import torch
from .builder import build
from .config import JsonConfig

import numpy as np
from ai_interface import AiInterface
from scipy.spatial.transform import Rotation


class MoGlow(AiInterface):
    def __init__(self):
        # super().__init__(init_pos)
        self.data = np.load("/home/suxy/Documents/BiYeSheJi/AI/StyleGestures-master/data/locomotion/all_locomotion_test_20fps.npz")
        self.data = self.data['clips'].reshape(-1, 66)
        self.count = 0
        self.rot = Rotation.from_euler("Z", 0)
        self.pos = np.array([0., 0., 0.])
        return

    def end(self) -> bool:
        del self.data
        self.count = 0
        self.data = None
        return True

    def get_next(self, control_arg: list):
        for_return = self.data[self.count][0:-3].copy()
        for_return = for_return.reshape(-1, 3)
        x = self.data[self.count][-3]
        z = self.data[self.count][-2]
        r = -self.data[self.count][-1]
        y = for_return[0, 1]
        for_return -= for_return[0]
        this_rot = Rotation.from_euler("y", r)
        this_pos = np.array([x, 0., z])
        this_pos = self.rot.apply(this_pos)
        for_return = self.rot.apply(for_return)
        for_return += self.pos
        for_return += np.array([0., y, 0.])
        self.rot *= this_rot
        self.pos += this_pos
        self.count += 1
        self.count = min(self.count, self.data.shape[0])
        print([z, x, self.rot.as_euler('YXZ')[0]])
        return {
            "data": for_return.reshape(-1),
            "control": [z, x, self.rot.as_euler('YXZ')[0]]
        }

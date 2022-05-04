import trans.constants as constant
import trans.inverse_kinematics as inv

import numpy as np
import math

import bpy
from mathutils import Euler, Matrix
from bpy_extras.io_utils import axis_conversion


class TransHandler:
    def __init__(self, inputs: dict):
        constant.set_initial_offset(inputs)
        self.inverse = inv.InverseKinematics()
        # initial rotation matrix
        structure = bpy.context.window_manager.suxy_bone_structure
        target = bpy.data.armatures[structure.target_name].bones
        self.matrix = dict()
        self.matrix_inv = dict()
        self.old_euler = dict()
        global_matrix = axis_conversion(from_forward=inputs["axis_forward"],
                                        from_up=inputs["axis_up"])
        global_matrix.invert()
        global_matrix = global_matrix.to_4x4()
        min_index = 1000
        for bone_tag in structure.tag:
            if bone_tag.is_position:
                continue
            index = bone_tag.index
            min_index = min(min_index, index)
        for bone_tag in structure.tag:
            if bone_tag.is_position:
                continue
            index = bone_tag.index
            name = bone_tag.name
            m_now = target[name].matrix_local
            m_now = global_matrix @ m_now.to_3x3().to_4x4()
            m_now = m_now.to_3x3()
            m_inv = Matrix(m_now)
            m_inv.invert()
            m_inv.resize_4x4()
            m_now.resize_4x4()
            self.matrix[index - min_index] = m_now
            self.matrix_inv[index - min_index] = m_inv
            self.old_euler[index - min_index] = Euler((0, 0, 0))
            # print(name)
            # print(index - min_index)
            # print(self.matrix[index - min_index])
            # print(self.matrix_inv[index - min_index])
            # print(" ")
        return

    def calculate_trans(self, position: np.ndarray):
        output = self.inverse.calculate_all_rotation(position)
        output = np.array(output)
        pos = output[0:1, :]
        rot = np.concatenate([output[1:, 1:2], output[1:, 2:3], output[1:, 0:1]], axis=1)
        # print(rot[17])
        rot = np.deg2rad(rot)
        for i in range(rot.shape[0]):
            # if i == 17:
            #     print(rot[i])
            tmp_e = Euler(rot[i], 'YXZ')
            tmp_m = tmp_e.to_matrix().to_4x4()
            tmp_m = (self.matrix_inv[i] @ tmp_m @ self.matrix[i])
            tmp_e = tmp_m.to_euler('ZXY', self.old_euler[i])
            self.old_euler[i] = tmp_e
            rot[i] = [tmp_e.x, tmp_e.y, tmp_e.z]
            # if i == 17:
            #     print(rot[i])
            #     print(" ")
        output = np.concatenate([pos, rot], axis=0)
        return output.reshape(-1)

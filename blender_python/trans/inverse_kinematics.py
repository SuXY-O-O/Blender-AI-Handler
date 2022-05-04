import numpy as np
from transformations import quaternion_matrix, rotation_matrix, quaternion_multiply, quaternion_from_matrix

from .forward_kinematics import ForwardKinematics
from .quaternion_frame import euler_to_quaternion, quaternion_to_euler
from .constants import INITIAL_OFFSET, ORIGIN, \
    INVERSE_ROTATION_ORDER, DEFAULT_ROTATION_ORDER, SPINE_INDEX, LEFT_HIP_INDEX, RIGHT_HIP_INDEX, \
    JOINT_NAME, PARENT_INDEX


class InverseKinematics(object):
    def __init__(self):
        self.joints = JOINT_NAME
        self.parents = PARENT_INDEX
        children_index = dict()
        for i in range(len(self.joints)):
            children = []
            for j in range(len(self.parents)):
                if i == self.parents[j]:
                    children.append(j)
            children_index[i] = children
        self.children_list = children_index
        self.positions = None
        self.changed_positions = None

    def calculate_all_rotation(self, positions: np.ndarray):
        self.positions = positions.reshape([1, -1, 3]).copy()
        self.changed_positions = self.positions.copy()
        # rotations = []
        # for frame in range(len(self.positions)):
        #     temp_rotation = self.calculate_rotation_for_frame(frame)
        #     rotations.append(temp_rotation)
        return self.calculate_rotation_for_frame(0)

    def calculate_rotation_for_frame(self, frame):
        rotations = [self.positions[frame][0]]
        for i in range(len(self.joints)):
            rotations.append(np.array([0, 0, 0]))
        for i, name in enumerate(self.joints):
            if i == 0:
                root_rotation = self.get_root_rotation(frame)
                rotations[i + 1] = root_rotation
            else:
                if len(self.children_list[i]) == 0:
                    continue
                child_index = self.children_list[i][0]
                child_name = self.joints[self.children_list[i][0]]
                node_init = INITIAL_OFFSET[child_name]
                # get goal
                vec = self.positions[frame][child_index] - self.positions[frame][i]
                temp_goal = []
                parent_list = []
                now = i
                while self.parents[now] != -1:
                    parent_list.insert(0, self.parents[now])
                    now = self.parents[now]
                for index in parent_list:
                    temp_goal = self.inverse_rotation(vec, rotations[index + 1])
                    vec = temp_goal
                    index += 1
                node_goal = temp_goal
                node_rotation = self.calculate_rotation_for_node(node_init, node_goal)
                rotations[i + 1] = node_rotation
                # ???
                self.update_children(rotations, frame)
        return rotations

    def inverse_rotation(self, init, rotation):
        inverse_rotation = [-rotation[2], -rotation[1], -rotation[0]]
        quaternion = euler_to_quaternion(inverse_rotation, rotation_order=INVERSE_ROTATION_ORDER)
        inverse_matrix = quaternion_matrix(quaternion)
        offset_matrix = np.eye(4, 4)
        offset_matrix[:3, 3] = init
        now_matrix = np.dot(inverse_matrix, offset_matrix)
        return np.dot(now_matrix, ORIGIN)[:3]

    def get_root_rotation(self, frame):
        spine_name = self.joints[SPINE_INDEX]
        root_name = self.joints[0]

        spine_init = INITIAL_OFFSET[spine_name] - INITIAL_OFFSET[root_name]
        spine_goal = self.positions[frame][SPINE_INDEX] - self.positions[frame][0]

        spine_euler = self.calculate_rotation_for_node(spine_init, spine_goal)
        quaternion1 = euler_to_quaternion(spine_euler, DEFAULT_ROTATION_ORDER)

        rotate_axis = spine_goal
        rotate_point = self.positions[frame][0]
        euler = self.refine_root_euler(frame, quaternion1, rotate_axis, rotate_point)
        return euler

    def refine_root_euler(self, frame, quaternion1, rotate_axis, rotate_point):
        def calculate_error(rot_angle):
            quaternion2 = quaternion_from_matrix(rotation_matrix(rot_angle, rotate_axis, rotate_point))
            quaternion = quaternion_multiply(quaternion2, quaternion1)
            _euler = quaternion_to_euler(quaternion, DEFAULT_ROTATION_ORDER)
            fk = ForwardKinematics(self.joints)
            fk.set_root_matrix(self.positions[frame][0], _euler, self.joints[0])
            left_hip = fk.get_node_position(LEFT_HIP_INDEX, [0, 0, 0])[:3]
            right_hip = fk.get_node_position(RIGHT_HIP_INDEX, [0, 0, 0])[:3]
            _error = np.sum(abs(self.positions[frame][LEFT_HIP_INDEX] - left_hip) + \
                            abs(self.positions[frame][RIGHT_HIP_INDEX] - right_hip), axis=-1)
            return _error, _euler

        optimal_error = 5999.0
        optimal_angle = 0.0
        optimal_euler = [0, 0, 0]
        for angle in range(0, 360, 10):
            error, euler = calculate_error(angle)
            # print("angle:", angle, error, euler)
            if error < optimal_error:
                optimal_angle = angle
                optimal_error = error
                optimal_euler = euler

        for angle in np.arange(optimal_angle - 7, optimal_angle + 7, 0.05):
            error, euler = calculate_error(angle)
            # print("angle:", angle, error, euler)
            if error < optimal_error:
                optimal_error = error
                optimal_euler = euler

        return optimal_euler

    @staticmethod
    def calculate_rotation_for_node(init, goal):
        n_init = init / np.linalg.norm(init, ord=2, axis=0)
        n_goal = goal / np.linalg.norm(goal, ord=2, axis=0)
        if np.linalg.norm(n_init + n_goal) == 0:
            q = [0, 1, 0, 0]
        else:
            half = (n_init + n_goal) / np.linalg.norm(n_init + n_goal, ord=2, axis=0)
            v = np.cross(n_init, half)
            q = [np.dot(n_init, half), v[0], v[1], v[2]]

        euler2 = quaternion_to_euler(q)

        return euler2

    @staticmethod
    def apply_ik(init, rotation):
        quaternion = euler_to_quaternion(rotation)
        rot_matrix = quaternion_matrix(quaternion)
        offset_matrix = np.eye(4, 4)
        offset_matrix[:3, 3] = init
        now_matrix = np.dot(rot_matrix, offset_matrix)
        return np.dot(now_matrix, ORIGIN)[:3]

    def update_children(self, rotation_data, frame):
        fk = ForwardKinematics(self.joints)
        fk.set_root_matrix(rotation_data[0], rotation_data[1], self.joints[0])
        for i, name in enumerate(self.joints):
            if i == 0:
                self.changed_positions[frame][i] = fk.get_node_position(i, rotation_data[i + 1])[:3]
            else:
                self.changed_positions[frame][i] = fk.get_node_position(i, rotation_data[i + 1], self.parents[i])[:3]

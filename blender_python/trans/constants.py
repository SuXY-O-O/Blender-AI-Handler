import numpy as np
from .utils import calculate_diatance_3d

# parameter
ORIGIN = point = np.array([0, 0, 0, 1])
DEBUG = 0
IK_DEBUG = 0
FK_DEBUG = 0
TOLERANCE = 1.0
MAX_ITERATION = 200
FILTER_WINDOW = 5

# data
FRAME_PER_SECOND = 20.0
DEFAULT_ROTATION_ORDER = ['Zrotation', 'Xrotation', 'Yrotation']
INVERSE_ROTATION_ORDER = [DEFAULT_ROTATION_ORDER[2], DEFAULT_ROTATION_ORDER[1], DEFAULT_ROTATION_ORDER[0]]

SPINE_INDEX = 11
LEFT_HIP_INDEX = 1
RIGHT_HIP_INDEX = 5

Z = np.array([0, 0, 0])
U = np.array([0, 1, 0])
D = np.array([0, -1, 0])
L = np.array([1, 0, 0])
R = np.array([-1, 0, 0])
F = np.array([0, 0, 1])
B = np.array([0, 0, -1])
INITIAL_DIRECTION = [
    np.array([0, 0, 0]),  # 'root',
    L, D, D, L,
    R, D, D, R,
    U, U, U, U,
    L, L, L, U,
    R, R, R, U
]
JOINT_NAME = [
    'Root',  # 0
    'Bone.000', 'Bone.001', 'Bone.002', 'Bone.003', 'Bone.004',
    'Bone.005', 'Bone.006', 'Bone.007', 'Bone.008', 'Bone.009',
    'Bone.010', 'Bone.011', 'Bone.012', 'Bone.013', 'Bone.014',
    'Bone.015', 'Bone.016', 'Bone.017', 'Bone.018', 'Bone.019'
]
PARENT_INDEX = [
    -1,
    0, 1, 2, 3,
    0, 5, 6, 7,
    0, 9, 10,
    11, 11, 13, 14, 15,
    11, 17, 18, 19
]
SKELETON_OFFSET = np.array([
    [-2.03029685e-02, 1.68440217e+01, -6.24466284e-02],
    [1.41187979e+00, 1.50809102e+01, 3.80191010e-01],
    [1.46695451e+00, 8.38195821e+00, 2.34405512e+00],
    [1.18385399e+00, 1.87078960e+00, -2.26383958e-01],
    [1.21741815e+00, 7.83476194e-01, 1.58826705e+00],
    [-1.41187979e+00, 1.50809102e+01, 3.80191010e-01],
    [-1.46695451e+00, 8.38195821e+00, 2.34405512e+00],
    [-1.18385399e+00, 1.87078960e+00, -2.26383958e-01],
    [-1.21741815e+00, 7.83476194e-01, 1.58826705e+00],
    [2.26656039e-03, 1.88166232e+01, 2.43522532e-01],
    [-3.10903284e-02, 2.07965797e+01, 6.23443995e-01],
    [7.40026337e-03, 2.25097286e+01, 8.29421933e-01],
    [1.32971585e-01, 2.41881257e+01, 1.24185347e+00],
    [3.04966425e+00, 2.23186851e+01, 7.00730962e-01],
    [3.91391720e+00, 1.75629219e+01, 1.28947735e-01],
    [4.02079454e+00, 1.49284439e+01, 1.65594046e+00],
    [4.15267230e+00, 1.44887233e+01, 1.90691817e+00],
    [-3.04966425e+00, 2.23186851e+01, 7.00730962e-01],
    [-3.91391720e+00, 1.75629219e+01, 1.28947735e-01],
    [-4.02079454e+00, 1.49284439e+01, 1.65594046e+00],
    [-4.15267230e+00, 1.44887233e+01, 1.90691817e+00]
])
INITIAL_OFFSET = dict()
for ind in range(len(JOINT_NAME)):
    INITIAL_OFFSET[JOINT_NAME[ind]] = SKELETON_OFFSET[ind]


# init bone length
def set_initial_offset(init_setting: dict):
    global JOINT_NAME, SPINE_INDEX, LEFT_HIP_INDEX, \
        RIGHT_HIP_INDEX, PARENT_INDEX, INITIAL_OFFSET, INITIAL_DIRECTION

    JOINT_NAME = init_setting['JOINT_NAME']
    SPINE_INDEX = init_setting['SPINE_INDEX']
    LEFT_HIP_INDEX = init_setting['LEFT_HIP_INDEX']
    RIGHT_HIP_INDEX = init_setting['RIGHT_HIP_INDEX']
    PARENT_INDEX = init_setting['PARENT_INDEX']

    INITIAL_DIRECTION.clear()
    for label in init_setting['INITIAL_DIRECTION']:
        if label == 'Z':
            INITIAL_DIRECTION.append(Z)
        elif label == 'U':
            INITIAL_DIRECTION.append(U)
        elif label == 'R':
            INITIAL_DIRECTION.append(R)
        elif label == 'D':
            INITIAL_DIRECTION.append(D)
        elif label == 'L':
            INITIAL_DIRECTION.append(L)
        elif label == 'F':
            INITIAL_DIRECTION.append(F)
        elif label == 'B':
            INITIAL_DIRECTION.append(B)

    position = init_setting['INIT_POS']
    for i, joint in enumerate(JOINT_NAME):
        if i == 0:
            INITIAL_OFFSET[joint] = np.array([0, 0, 0])
        else:
            direction = INITIAL_DIRECTION[i]
            parent = PARENT_INDEX[i]
            dis = calculate_diatance_3d(position[i], position[parent])
            direction_dis = np.linalg.norm(direction, ord=2, axis=0)
            INITIAL_OFFSET[joint] = direction / direction_dis * dis
    return

import bpy
import math
import numpy as np
from mathutils import Vector, Euler


def update_play_rate(self, context):
    context.scene.render.fps = context.window_manager.suxy_draw_option.play_rate


class DataDrawOptions(bpy.types.PropertyGroup):
    draw_rate: bpy.props.FloatProperty(name="draw delta time",
                                       default=0.05,
                                       description="Time interval of the keyframe",
                                       soft_min=0.0,
                                       soft_max=1.0)
    play_rate: bpy.props.IntProperty(name="playback fps",
                                     default=24,
                                     description="FPS when play the animation",
                                     soft_max=120,
                                     soft_min=1,
                                     update=update_play_rate)
    draw_line: bpy.props.BoolProperty(name="draw line",
                                      description="Draw a line from one joint",
                                      default=False)
    draw_line_target: bpy.props.StringProperty(name="line target",
                                               description="The target joint name of the line",
                                               default="root")
    draw_line_lock_z: bpy.props.BoolProperty(name="line lock z",
                                             description="lock z axis to 0",
                                             default=True)


def update_sub(context, bone_obj_name):
    location = None
    rotation = None
    bone_name = context.window_manager.suxy_sub_target_name
    bone_matrix = bpy.data.armatures[bone_obj_name].bones[bone_name].matrix
    if context.window_manager.suxy_sub_line_enable or context.window_manager.suxy_sub_box_enable:
        location = bpy.data.objects[bone_obj_name].pose.bones[bone_name].location
        location = bone_matrix @ location
    if context.window_manager.suxy_sub_box_enable:
        rotation = bpy.data.objects[bone_obj_name].pose.bones[bone_name].rotation_euler
        rotation = bone_matrix @ rotation.to_matrix()
        rotation = rotation.to_euler("XYZ")
    if context.window_manager.suxy_sub_line_enable:
        update_sub_line(context, location)
    if context.window_manager.suxy_sub_box_enable:
        update_sub_box(context, location, rotation)
    return


def update_sub_line(context, location):
    _location = [0., 0., 0.]
    for i in range(3):
        if context.window_manager.suxy_sub_line_axis[i]:
            _location[i] = location[i]
    name = context.window_manager.suxy_sub_line_name
    line_obj = bpy.data.objects[name]
    # select line object and enter edit mode
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    line_obj.select_set(True)
    bpy.context.view_layer.objects.active = line_obj
    bpy.ops.object.mode_set(mode='EDIT')
    # select the last vertex
    bpy.ops.curve.select_all(action='DESELECT')
    bpy.ops.curve.de_select_last()
    # add vertex
    bpy.ops.curve.vertex_add(location=_location)
    # return object mode
    bpy.ops.object.mode_set(mode='OBJECT')
    return


def str2vertex(identity):
    if identity == 'X':
        return np.array([1., 0, 0])
    elif identity == '-X':
        return np.array([-1., 0, 0])
    elif identity == 'Y':
        return np.array([0, 1., 0])
    elif identity == '-Y':
        return np.array([0, -1., 0])
    elif identity == 'Z':
        return np.array([0, 0, 1.])
    else:
        return np.array([0, 0, -1.])


def calculate_control_rotation(context):
    f = context.window_manager.suxy_user_real_input[0]
    s = context.window_manager.suxy_user_real_input[1]
    r = context.window_manager.suxy_user_real_input[2]
    length = math.sqrt(f * f + s * s)
    length += context.window_manager.suxy_sub_box_min
    if math.isclose(f, 0.0) and math.isclose(s, 0.0):
        rot = 0
    elif math.isclose(f, 0.0) and s > 0.0:
        rot = math.pi / 2.0
    elif math.isclose(f, 0.0) and s < 0.0:
        rot = -math.pi / 2.0
    elif math.isclose(s, 0.0) and f > 0.0:
        rot = 0
    elif math.isclose(s, 0.0) and f < 0.0:
        rot = -math.pi
    elif f > 0.0:
        rot = math.atan(s / f)
    else:
        rot = math.atan(s / f) + math.pi
    return rot + r, length


def update_sub_box(context, location, rotation):
    name = context.window_manager.suxy_sub_box_name
    box_obj = bpy.data.objects[name]
    # location
    box_obj.location = location
    # rotation
    con_rotation, con_scale = calculate_control_rotation(context)
    up_axis = str2vertex(context.window_manager.suxy_sub_box_up)
    # rotation = up_axis * rotation + con_rotation * up_axis
    rotation = con_rotation * up_axis
    box_obj.rotation_euler = rotation
    # scale
    scale = str2vertex(context.window_manager.suxy_sub_box_forward) * (con_scale - 0.75)
    scale += [0.75, 0.75, 0.75]
    box_obj.scale = scale
    # add key frame
    box_obj.keyframe_insert(data_path="location")
    box_obj.keyframe_insert(data_path="rotation_euler")
    box_obj.keyframe_insert(data_path="scale")
    return


def update_frame_index(self, context):
    context.scene.frame_current = context.window_manager.suxy_draw_value.frame_index
    value = context.window_manager.suxy_draw_value.my_values
    structure = context.window_manager.suxy_bone_structure
    target = bpy.data.objects[structure.target_name]
    for bone_tag in structure.tag:
        index = bone_tag.index * 3
        name = bone_tag.name
        if bone_tag.is_position:
            target.pose.bones[name].location[0] = value[index].float
            target.pose.bones[name].location[1] = value[index + 1].float
            target.pose.bones[name].location[2] = value[index + 2].float
            target.pose.bones[name].keyframe_insert(data_path="location")
        else:
            target.pose.bones[name].rotation_euler[0] = value[index].float
            target.pose.bones[name].rotation_euler[1] = value[index + 1].float
            target.pose.bones[name].rotation_euler[2] = value[index + 2].float
            target.pose.bones[name].keyframe_insert(data_path="rotation_euler")
    update_sub(context, structure.target_name)
    return


class DataDrawList(bpy.types.PropertyGroup):
    float: bpy.props.FloatProperty(default=0.0)


class DataDrawValues(bpy.types.PropertyGroup):
    frame_index: bpy.props.IntProperty(name="frame index",
                                       description="Index of the frame",
                                       default=0,
                                       update=update_frame_index)
    my_values: bpy.props.CollectionProperty(type=DataDrawList,
                                            description="The input data values")


def register_classes():
    bpy.utils.register_class(DataDrawList)
    bpy.utils.register_class(DataDrawOptions)
    bpy.utils.register_class(DataDrawValues)
    bpy.types.WindowManager.suxy_draw_option = bpy.props.PointerProperty(type=DataDrawOptions)
    bpy.types.WindowManager.suxy_draw_value = bpy.props.PointerProperty(type=DataDrawValues)
    bpy.context.window_manager.suxy_draw_value.my_values.clear()
    bpy.context.window_manager.suxy_draw_value.frame_index = 0


def unregister_classes():
    del bpy.types.WindowManager.suxy_draw_option
    del bpy.types.WindowManager.suxy_draw_value
    bpy.utils.unregister_class(DataDrawOptions)
    bpy.utils.unregister_class(DataDrawValues)
    bpy.utils.unregister_class(DataDrawList)

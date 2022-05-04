import math
import bpy
from mathutils import Vector, Euler


def check_curve_name(self, context):
    name = context.window_manager.suxy_sub_line_name
    if name not in bpy.data.objects.keys():
        print("Wrong Name, no such object!")
        # context.window_manager.suxy_sub_line_name = "WRONG!!!"
        return
    line_obj = bpy.data.objects[name]
    try:
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        line_obj.select_set(True)
        bpy.context.view_layer.objects.active = line_obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.select_all(action='SELECT')
        bpy.ops.curve.delete()
        bpy.ops.object.mode_set(mode='OBJECT')
    except:
        print("Wrong Name, object is not a curve!")
        # context.window_manager.suxy_sub_line_name = "WRONG!!!"
    return


def check_box_name(self, context):
    name = context.window_manager.suxy_sub_box_name
    if name not in bpy.data.objects.keys():
        print("Wrong Name, no such object!")
        # context.window_manager.suxy_sub_box_name = "WRONG!!!"
        return
    bpy.data.objects['cube'].animation_data_clear()
    return


def check_target_bone_name(self, context):
    flag = False
    name = context.window_manager.suxy_sub_target_name
    structure = context.window_manager.suxy_bone_structure
    for bone_tag in structure.tag:
        if bone_tag.name == name:
            flag = True
            break
    if not flag:
        print("Wrong Name, no such bone!")
        # context.window_manager.suxy_sub_target_name = "WRONG!!!"
    return


class SubLineClearOperator(bpy.types.Operator):
    bl_idname = "suxy.sub_line_clear"
    bl_label = "Sub Line Clear"

    def execute(self, context):
        name = context.window_manager.suxy_sub_line_name
        line_obj = bpy.data.objects[name]
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        line_obj.select_set(True)
        context.view_layer.objects.active = line_obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.select_all(action='SELECT')
        bpy.ops.curve.delete()
        bpy.ops.object.mode_set(mode='OBJECT')
        return {'FINISHED'}


class SubSettingPanel(bpy.types.Panel):
    bl_idname = "suxy.VIEW_PT_sub_settings_panel"
    bl_label = "SUB Settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = True
        box = layout.box()
        box.label(text="Target Bone")
        col = box.column()
        col.prop(context.window_manager, "suxy_sub_target_name", text="Target Bone Name")
        box = layout.box()
        box.label(text="Line Setting")
        col = box.column()
        col.prop(context.window_manager, "suxy_sub_line_name", text="Line Object Name")
        col.prop(context.window_manager, "suxy_sub_line_enable", text="Line Enable")
        row = col.row()
        row.label(text="Capture Axis")
        row.prop(context.window_manager, "suxy_sub_line_axis", index=0, text="X")
        row.prop(context.window_manager, "suxy_sub_line_axis", index=1, text="Y")
        row.prop(context.window_manager, "suxy_sub_line_axis", index=2, text="Z")
        col.operator(operator="suxy.sub_line_clear", text="Clear Vertex")
        box = layout.box()
        box.label(text="Box Setting")
        col = box.column()
        col.prop(context.window_manager, "suxy_sub_box_name", text="Box Object Name")
        col.prop(context.window_manager, "suxy_sub_box_enable", text="Box Enable")
        col.prop(context.window_manager, "suxy_sub_box_min", text="Min Length")
        row = col.row()
        row.prop(context.window_manager, "suxy_sub_box_up", text="Up Axis")
        row.prop(context.window_manager, "suxy_sub_box_forward", text="Forward Axis")


def register_classes():
    bpy.types.WindowManager.suxy_sub_target_name = bpy.props.StringProperty(name="target bone name",
                                                                            default="root",
                                                                            update=check_target_bone_name)
    bpy.types.WindowManager.suxy_sub_line_name = bpy.props.StringProperty(name="line name",
                                                                          default="curve",
                                                                          update=check_curve_name)
    bpy.types.WindowManager.suxy_sub_box_name = bpy.props.StringProperty(name="box name",
                                                                         default="cube",
                                                                         update=check_box_name)
    bpy.types.WindowManager.suxy_sub_line_enable = bpy.props.BoolProperty(name="line enable",
                                                                          default=True)
    bpy.types.WindowManager.suxy_sub_box_enable = bpy.props.BoolProperty(name="box enable",
                                                                         default=True)
    bpy.types.WindowManager.suxy_sub_line_axis = bpy.props.BoolVectorProperty(name="line axis enable",
                                                                              default=[True, True, True])
    bpy.types.WindowManager.suxy_sub_box_min = bpy.props.FloatProperty(name="box min length",
                                                                       default=1.0,
                                                                       min=0.0)
    bpy.types.WindowManager.suxy_sub_box_up = bpy.props.EnumProperty(name="box up axis",
                                                                     items=[("X", "X", ""),
                                                                            ("Y", "Y", ""),
                                                                            ("Z", "Z", ""),
                                                                            ("-X", "-X", ""),
                                                                            ("-Y", "-Y", ""),
                                                                            ("-Z", "-Z", "")
                                                                            ],
                                                                     default="Z")
    bpy.types.WindowManager.suxy_sub_box_forward = bpy.props.EnumProperty(name="box forward axis",
                                                                          items=[("X", "X", ""),
                                                                                 ("Y", "Y", ""),
                                                                                 ("Z", "Z", ""),
                                                                                 ("-X", "-X", ""),
                                                                                 ("-Y", "-Y", ""),
                                                                                 ("-Z", "-Z", "")
                                                                                 ],
                                                                          default="Y")
    bpy.utils.register_class(SubLineClearOperator)
    bpy.utils.register_class(SubSettingPanel)


def unregister_classes():
    del bpy.types.WindowManager.suxy_sub_target_name
    del bpy.types.WindowManager.suxy_sub_line_name
    del bpy.types.WindowManager.suxy_sub_box_name
    del bpy.types.WindowManager.suxy_sub_line_enable
    del bpy.types.WindowManager.suxy_sub_box_enable
    del bpy.types.WindowManager.suxy_sub_line_axis
    del bpy.types.WindowManager.suxy_sub_box_min
    del bpy.types.WindowManager.suxy_sub_box_up
    del bpy.types.WindowManager.suxy_sub_box_forward
    bpy.utils.unregister_class(SubSettingPanel)
    bpy.utils.unregister_class(SubLineClearOperator)

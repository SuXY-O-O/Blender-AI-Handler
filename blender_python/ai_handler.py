import importlib
import bpy
import json
import os
import sys
import time

import trans_handler as th
from ai_interface import AiInterface


class AiInitialSet(bpy.types.PropertyGroup):
    # joint_number: bpy.props.IntProperty(name="joint number",
    #                                     description="Joint numbers for the structure used in AI",
    #                                     default=21,
    #                                     min=0)
    ai_module: bpy.props.StringProperty(name="ai_module_path",
                                        description="The python path containing the AI module",
                                        subtype="DIR_PATH",
                                        default="/home/suxy/Documents/BiYeSheJi/blender_file/blender_python/ai/moglow/")
    ai_input: bpy.props.StringProperty(name="ai_input_file",
                                       description="A json file for AI initial data",
                                       subtype="FILE_PATH",
                                       default="/home/suxy/Documents/BiYeSheJi/blender_file/blender_python/data"
                                               "/ai_input.json")
    use_transition: bpy.props.BoolProperty(name="use_transition",
                                           description="Trans position to rotation",
                                           default=True)
    trans_input: bpy.props.StringProperty(name="transition_input",
                                          description="Initial data for trans position to rotation",
                                          subtype="FILE_PATH",
                                          default="/home/suxy/Documents/BiYeSheJi/blender_file/blender_python/data"
                                                  "/trans_input_new.json")


# class AiInputMonitor(bpy.types.Operator):
#     bl_idname = "suxy.ai_input_monitor"
#     bl_label = "AI Input Monitor"
#
#     def modal(self, context, event):
#         # print("inside")
#         if context.window_manager.suxy_ai_stop:
#             return {'FINISHED'}
#         _front = 0
#         _right = 0
#         if event.type == 'LEFT_ARROW':
#             _right += -1
#         if event.type == 'RIGHT_ARROW':
#             _right += 1
#         if event.type == 'UP_ARROW':
#             _front += 1
#         if event.type == 'DOWN_ARROW':
#             _front += -1
#         if _front == 0 and _right == 0:
#             return {'PASS_THROUGH'}
#         context.window_manager.suxy_user_input = [_front, 0, _right]
#         print("user input: " + str([_front, 0, _right]))
#         return {'PASS_THROUGH'}
#
#     def execute(self, context):
#         context.window_manager.modal_handler_add(self)
#         return {'RUNNING_MODAL'}


class AiRunningHandler(bpy.types.Operator):
    bl_idname = "suxy.ai_running_handler"
    bl_label = "AI Running Handler"

    _timer = None
    _module = None
    _is_running = False
    _need_trans = False
    frame_count = 0
    _file = None
    _trans = None
    _time_last = None

    def execute(self, context):
        # check input file path for AI
        if not os.path.exists(context.window_manager.suxy_ai_initial_set.ai_module) \
                or not os.path.exists(context.window_manager.suxy_ai_initial_set.ai_input):
            self.report({'ERROR'}, "Cannot find ai module file or input file")
            return {'CANCELLED'}
        # load AI settings
        ai_input = open(context.window_manager.suxy_ai_initial_set.ai_input, 'r')
        ai_input = json.load(ai_input)
        # load AI module
        sys.path.insert(0, context.window_manager.suxy_ai_initial_set.ai_module)
        ai_module = importlib.import_module(ai_input["module_name"])
        importlib.reload(ai_module)
        sys.path.pop(0)
        ai_class = getattr(ai_module, ai_input["class_name"])
        self._module = ai_class()
        if not isinstance(self._module, AiInterface):
            self.report({'ERROR'}, "Cannot find ai module file or input file")
            return {'CANCELLED'}
        # load position translation if needed
        self._need_trans = context.window_manager.suxy_ai_initial_set.use_transition
        if self._need_trans \
                and not os.path.exists(context.window_manager.suxy_ai_initial_set.trans_input):
            self.report({'ERROR'}, "Cannot find trans input file")
            return {'CANCELLED'}
        if self._need_trans:
            trans_input = open(context.window_manager.suxy_ai_initial_set.trans_input, 'r')
            trans_input = json.load(trans_input)
            # init_pos = np.array(trans_input["init_pos"])
            # init_pos = init_pos.reshape(-1, 3)
            # self._pos_2_rot = trans_handler.Pos2Rot(joint_num=trans_input["joint_num"],
            #                                         spine_index=trans_input["spine_index"],
            #                                         init_pos=init_pos,
            #                                         parent=trans_input["parent"])
            self._trans = th.TransHandler(trans_input)
        # add timer and modal handler
        self._timer = context.window_manager.event_timer_add(
            time_step=ai_input["running_rate"],
            window=context.window)
        context.window_manager.modal_handler_add(self)
        self.frame_count = 0
        self._time_last = time.time()
        # save file for debug
        # self._file = open('/home/suxy/Documents/tmp_bvh.txt', 'w')
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type != 'TIMER' or self._is_running:
            return {'PASS_THROUGH'}
        if context.window_manager.suxy_ai_stop:
            self.cancel(context)
            return {'FINISHED'}
        self._is_running = True
        print("Calculating " + str(self.frame_count) + "; Last frame time used: " + str(time.time() - self._time_last))
        self._time_last = time.time()
        arg = context.window_manager.suxy_user_input
        next_data = self._module.get_next([arg[0], arg[1], arg[2]])
        context.window_manager.suxy_user_real_input[0] = next_data["control"][0]
        context.window_manager.suxy_user_real_input[1] = next_data["control"][1]
        context.window_manager.suxy_user_real_input[2] = next_data["control"][2]
        if self._need_trans:
            # self._pos_2_rot.calculate_rotation(next_data.reshape(-1, 3))
            # next_data = next_data[0:3].tolist()
            # euler = self._pos_2_rot.get_euler()
            # next_data.extend(euler)
            next_data = self._trans.calculate_trans(next_data["data"])
        context.window_manager.suxy_draw_value.my_values.clear()
        for one_data in next_data:
            item = context.window_manager.suxy_draw_value.my_values.add()
            item.float = one_data
        context.window_manager.suxy_draw_value.frame_index = self.frame_count
        self.frame_count += 1
        self._is_running = False
        return {'PASS_THROUGH'}

    def cancel(self, context):
        if self._timer != None:
            context.window_manager.event_timer_remove(self._timer)
        self._timer = None
        self._module.end()
        del self._module
        self._module = None
        # del self._pos_2_rot
        # self._pos_2_rot = None
        self._is_running = False
        self.frame_count = 0
        # self._file.close()
        del self._trans
        self._trans = None


class AiStart(bpy.types.Operator):
    bl_idname = "suxy.ai_start"
    bl_label = "AI Start Button"

    def execute(self, context):
        context.window_manager.suxy_ai_stop = False
        # tmp = bpy.ops.suxy.ai_input_monitor('INVOKE_DEFAULT')
        # if 'RUNNING_MODAL' not in tmp:
        #     self.report({'ERROR'}, "Unable to get user input")
        #     context.window_manager.suxy_ai_stop = True
        #     return {'CANCELLED'}
        tmp = bpy.ops.suxy.ai_running_handler('INVOKE_DEFAULT')
        if 'RUNNING_MODAL' not in tmp:
            self.report({'ERROR'}, "Unable to invoke AI")
            context.window_manager.suxy_ai_stop = True
            return {'CANCELLED'}
        return {'FINISHED'}


class AiStop(bpy.types.Operator):
    bl_idname = "suxy.ai_stop"
    bl_label = "AI Stop Button"

    def execute(self, context):
        context.window_manager.suxy_ai_stop = True
        return {'FINISHED'}


class AiControlPanel(bpy.types.Panel):
    bl_idname = "suxy.VIEW_PT_ai_control_panel"
    bl_label = "Ai Controller"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Input fields")
        col = box.column()
        col.prop(context.window_manager.suxy_ai_initial_set, "ai_module", text="AI module path")
        col.prop(context.window_manager.suxy_ai_initial_set, "ai_input", text="AI input json file")
        col.prop(context.window_manager.suxy_ai_initial_set, "use_transition", text="Need translation")
        col.prop(context.window_manager.suxy_ai_initial_set, "trans_input", text="Translation init json file")
        box = layout.box()
        box.label(text="Control")
        col = box.column()
        col.prop(context.window_manager, "suxy_user_input", index=0, text="Side Speed")
        col.prop(context.window_manager, "suxy_user_input", index=1, text="Forward Speed")
        col.prop(context.window_manager, "suxy_user_input", index=2, text="Rotation Speed")
        box = layout.box()
        box.label(text="Switch")
        col = box.column()
        row = col.row()
        row.operator(operator="suxy.ai_start", text="Start")
        row.operator(operator="suxy.ai_stop", text="Stop")


def register_classes():
    bpy.utils.register_class(AiInitialSet)
    bpy.types.WindowManager.suxy_ai_initial_set = bpy.props.PointerProperty(type=AiInitialSet)
    bpy.types.WindowManager.suxy_user_input = bpy.props.FloatVectorProperty(name="user_input",
                                                                            description="User input monitor",
                                                                            default=(0.0, 0.0, 0.0),
                                                                            step=1)
    bpy.types.WindowManager.suxy_user_real_input = bpy.props.FloatVectorProperty(name="user_real_input",
                                                                                 description="User real input monitor",
                                                                                 default=(0.0, 0.0, 0.0))
    bpy.types.WindowManager.suxy_ai_stop = bpy.props.BoolProperty(name="ai_stop",
                                                                  description="Used to stop AI and user input",
                                                                  default=True)
    # bpy.utils.register_class(AiInputMonitor)
    bpy.utils.register_class(AiRunningHandler)
    bpy.utils.register_class(AiStart)
    bpy.utils.register_class(AiStop)
    bpy.utils.register_class(AiControlPanel)


def unregister_classes():
    del bpy.types.WindowManager.suxy_ai_initial_set
    del bpy.types.WindowManager.suxy_user_input
    del bpy.types.WindowManager.suxy_user_real_input
    del bpy.types.WindowManager.suxy_ai_stop
    # bpy.utils.unregister_class(AiInputMonitor)
    bpy.utils.unregister_class(AiInitialSet)
    bpy.utils.unregister_class(AiRunningHandler)
    bpy.utils.unregister_class(AiStart)
    bpy.utils.unregister_class(AiStop)
    bpy.utils.unregister_class(AiControlPanel)

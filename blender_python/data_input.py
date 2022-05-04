import bpy


class BvhInputOperator(bpy.types.Operator):
    bl_idname = "suxy.data_input_bvh"
    bl_label = "Bvh File Input"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    delta_time: bpy.props.FloatProperty(name="delta time",
                                        default=0.05,
                                        description="Time interval of the keyframe")

    data = None
    timer = None
    count = 0
    pause = False

    def invoke(self, context, event):
        cust_bone = context.window_manager.suxy_bone_structure
        t = bpy.data.objects[cust_bone.target_name]
        if t.animation_data is not None:
            print("WARNING: The existed animation data is cleared")
            t.animation_data_clear()
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        filepath_str = str(self.filepath)
        self.report({'INFO'}, "Imported " + filepath_str)
        if not filepath_str.endswith(".bvh"):
            self.report({'ERROR'}, "Wrong file type, expect bvh file")
            return {'CANCELLED'}
        if 'FINISHED' not in bpy.ops.import_anim.bvh(filepath=filepath_str):
            self.report({'ERROR'}, "Unable to open file: " + self.filepath)
            return {'CANCELLED'}
        self.data = context.object
        self.data.hide_viewport = True
        self.timer = context.window_manager.event_timer_add(time_step=context.window_manager.suxy_draw_option.draw_rate,
                                                            window=context.window)
        context.window_manager.modal_handler_add(self)
        self.count = self.data.animation_data.action.fcurves[0].range()[0]
        context.scene.frame_start = self.count
        self.pause = False
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type in {'ESC'}:
            self.cancel(context)
            self.report({'INFO'}, "canceled by " + event.type)
            return {'FINISHED'}
        elif event.type in {'RIGHTMOUSE'}:
            self.pause = not self.pause
            if self.pause:
                self.report({'INFO'}, "Pause")
            else:
                self.report({'INFO'}, "Continue")
            return {'PASS_THROUGH'}
        elif event.type == 'TIMER':
            if self.pause:
                return {'PASS_THROUGH'}
            data_curve = self.data.animation_data.action.fcurves
            if self.count >= data_curve[0].range()[1]:
                self.cancel(context)
                return {'FINISHED'}
            context.window_manager.suxy_draw_value.my_values.clear()
            lll = list()
            for fc in data_curve:
                item = context.window_manager.suxy_draw_value.my_values.add()
                item.float = fc.evaluate(self.count)
                lll.append(fc.evaluate(self.count))
            # TODO
            if self.count == 5:
                print(lll)
            context.window_manager.suxy_draw_value.frame_index = self.count
            self.count += 1
            return {'PASS_THROUGH'}
        else:
            return {'PASS_THROUGH'}

    def cancel(self, context):
        context.scene.frame_end = self.count
        self.count = 0
        wm = context.window_manager
        if self.timer is not None:
            wm.event_timer_remove(self.timer)
            self.timer = None
        if context.object.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        self.data.hide_viewport = False
        self.data.select_set(True)
        bpy.ops.object.delete()
        self.data = None


class DataInputPanel(bpy.types.Panel):
    bl_idname = "suxy.VIEW_PT_data_input_panel"
    bl_label = "BVH Data Input"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Playback FPS")
        col = box.column()
        col.prop(context.window_manager.suxy_draw_option, "play_rate", text="playback fps")
        box = layout.box()
        box.label(text="Input Bvh File")
        col = box.column()
        col.prop(context.window_manager.suxy_draw_option, "draw_rate", text="show rate")
        col.operator(operator="suxy.data_input_bvh", text="Select and Start")
        # box = layout.box()
        # box.label(text="Input Bvh File")


def register_classes():
    bpy.utils.register_class(BvhInputOperator)
    bpy.utils.register_class(DataInputPanel)


def unregister_classes():
    bpy.utils.unregister_class(DataInputPanel)
    bpy.utils.unregister_class(BvhInputOperator)

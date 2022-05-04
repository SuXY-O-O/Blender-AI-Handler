import bpy
import pickle
import os

bone_file_name = "suxy_bone.pkl"


class BoneStructureTag(bpy.types.PropertyGroup):
    index: bpy.props.IntProperty(name="index",
                                 description="Index in array",
                                 default=0)
    name: bpy.props.StringProperty(name="name",
                                   description="Name of the bone",
                                   default="root")
    is_position: bpy.props.BoolProperty(name="is position",
                                        description="The representation of the value",
                                        default=True)


def update_target_name(self, context):
    cust_bone = context.window_manager.suxy_bone_structure
    if cust_bone.target_name not in bpy.data.objects.keys():
        print("ERROR: Wrong target name: no such object")
        cust_bone.target_name = ""
        return
    t = bpy.data.objects[cust_bone.target_name]
    if "bones" not in dir(t.pose):
        print("ERROR: Wrong target name: not contain bones")
        return
    for item in cust_bone.tag:
        if item.name not in t.pose.bones.keys():
            print("ERROR: Wrong bone name: " + item.name)
            return
    if t.animation_data is not None:
        print("WARNING: The existed animation data will be cleared")
    print("INFO: Got target object name")


class BoneStructurePointer(bpy.types.PropertyGroup):
    index: bpy.props.IntProperty(name="index",
                                 description="Index in array",
                                 default=0)
    tag: bpy.props.CollectionProperty(type=BoneStructureTag)
    max_index: bpy.props.IntProperty(name="max_index",
                                     description="The max index",
                                     default=0)
    target_name: bpy.props.StringProperty(name="target_name",
                                          description="The name of the object in the scene",
                                          default="",
                                          update=update_target_name)


class BoneStructureExporter(bpy.types.Operator):
    bl_idname = "suxy.bone_structure_export"
    bl_label = "Bone Structure Exporter"

    filepath: bpy.props.StringProperty(subtype="DIR_PATH")

    def invoke(self, context, event):
        # context.window_manager.fileselect_add(self)
        # return {'RUNNING_MODAL'}
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        filename = os.path.join(self.filepath, bone_file_name)
        if not os.path.exists(self.filepath):
            self.report({'ERROR'}, "No such dir: " + self.filepath)
            return {'CANCELLED'}
        file = open(filename, 'wb')
        file.seek(0)
        file.truncate()
        file.seek(0)
        out_list = []
        for item in context.window_manager.suxy_bone_structure.tag:
            out_list.append((item.index, item.name, item.is_position))
        pickle.dump(out_list, file, -1)
        file.close()
        self.report({'INFO'}, "Exported " + filename)
        return {'FINISHED'}


class BoneStructureImporter(bpy.types.Operator):
    bl_idname = "suxy.bone_structure_import"
    bl_label = "Bone Structure Importer"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        _, filename = os.path.split(self.filepath)
        if filename != bone_file_name:
            self.report({'ERROR'}, "File name should be " + bone_file_name)
            return {'CANCELLED'}
        file = open(self.filepath, 'rb')
        in_list = pickle.load(file)
        context.window_manager.suxy_bone_structure.tag.clear()
        max_index = 0
        for item in in_list:
            tmp = context.window_manager.suxy_bone_structure.tag.add()
            tmp.index = item[0]
            tmp.name = item[1]
            tmp.is_position = item[2]
            if item[0] > max_index:
                max_index = item[0]
        context.window_manager.suxy_bone_structure.max_index = max_index
        file.close()
        self.report({'INFO'}, "Imported " + self.filepath)
        return {'FINISHED'}


class BoneStructureAdder(bpy.types.Operator):
    bl_idname = "suxy.bone_structure_add"
    bl_label = "Bone Structure Adder"

    index: bpy.props.IntProperty(description="Index of the value in list")
    name: bpy.props.StringProperty(description="Name of the bone")
    is_position: bpy.props.BoolProperty(description="The value represent position or rotation")

    def invoke(self, context, event):
        self.index = self.index + 1
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        for item in context.window_manager.suxy_bone_structure.tag:
            if item.index is self.index:
                self.report({'ERROR'}, "Duplicated index")
                return {'CANCELLED'}
        tmp = context.window_manager.suxy_bone_structure.tag.add()
        tmp.index = self.index
        tmp.name = self.name
        tmp.is_position = self.is_position
        if self.index > context.window_manager.suxy_bone_structure.max_index:
            context.window_manager.suxy_bone_structure.max_index = self.index
        return {'FINISHED'}


class BoneStructureDeleter(bpy.types.Operator):
    bl_idname = "suxy.bone_structure_delete"
    bl_label = "Bone Structure Deleter"

    index: bpy.props.IntProperty(description="Index of the value in list")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        i = -1
        for item in context.window_manager.suxy_bone_structure.tag:
            i = i + 1
            if item.index is self.index:
                context.window_manager.suxy_bone_structure.tag.remove(i)
                if context.window_manager.suxy_bone_structure.max_index is self.index:
                    max_index = 0
                    for one in context.window_manager.suxy_bone_structure.tag:
                        if one.index > max_index:
                            max_index = one.index
                    bpy.context.window_manager.suxy_bone_structure.max_index = max_index
                return {'FINISHED'}
        self.report({'ERROR'}, "Index not found")
        return {'CANCELLED'}


class BoneStructureUIList(bpy.types.UIList):
    bl_idname = "suxy.VIEW_UL_bone_structure_list"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "index", text="")
            layout.prop(item, "name", text="")
            layout.prop(item, "is_position", text="is_position")
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)


class BoneStructurePanel(bpy.types.Panel):
    bl_idname = "suxy.VIEW_PT_bone_structure_panel"
    bl_label = "Bone Structure"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.window_manager.suxy_bone_structure, "target_name", text="target object name")
        col.template_list("suxy.VIEW_UL_bone_structure_list",
                          "",
                          context.window_manager.suxy_bone_structure, "tag",
                          context.window_manager.suxy_bone_structure, "index")
        row = col.row()
        row.operator("suxy.bone_structure_add", text="Add Bone")
        row.operator("suxy.bone_structure_delete", text="Delete Bone")
        row = col.row()
        row.operator("suxy.bone_structure_export", text="Export")
        row.operator("suxy.bone_structure_import", text="Import")


def register_classes():
    bpy.utils.register_class(BoneStructureTag)
    bpy.utils.register_class(BoneStructurePointer)
    bpy.types.WindowManager.suxy_bone_structure = bpy.props.PointerProperty(type=BoneStructurePointer)
    bpy.context.window_manager.suxy_bone_structure.tag.clear()
    bpy.utils.register_class(BoneStructureExporter)
    bpy.utils.register_class(BoneStructureImporter)
    bpy.utils.register_class(BoneStructureAdder)
    bpy.utils.register_class(BoneStructureDeleter)
    bpy.utils.register_class(BoneStructureUIList)
    bpy.utils.register_class(BoneStructurePanel)


def unregister_classes():
    bpy.utils.unregister_class(BoneStructurePanel)
    bpy.utils.unregister_class(BoneStructureUIList)
    bpy.utils.unregister_class(BoneStructureExporter)
    bpy.utils.unregister_class(BoneStructureImporter)
    bpy.utils.unregister_class(BoneStructureAdder)
    bpy.utils.unregister_class(BoneStructureDeleter)
    bpy.utils.unregister_class(BoneStructurePointer)
    bpy.utils.unregister_class(BoneStructureTag)
    del bpy.types.WindowManager.suxy_bone_structure

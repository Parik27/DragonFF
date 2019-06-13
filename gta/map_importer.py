import logging
import mathutils
import bpy
from . import map as map_utilites, dff_importer

# def main(context):
#     for ob in context.scene.objects:
#         print(ob)

class Map_Import_Operator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "scene.dragonff_map_import"
    bl_label = "Import map section"

    _timer = None
    _updating = False
    _calcs_done = False
    inst_index = 0
    import_limit = 100000

    _context = None

    object_instances = []
    object_data = []
    model_buffer = {}

    def import_object(self):

        if self.inst_index >= len(self.object_instances) - 1 or self.inst_index >= self.import_limit:
            self._calcs_done = True
            return

        inst = self.object_instances[self.inst_index]
        self.inst_index += 1

        model = self.object_data[inst.id].modelName

        # implement model buffer
        if inst.id in self.model_buffer:
            objGroup = self.model_buffer[inst.id]
            newGroup = []
            for obj in objGroup:
                new_obj = bpy.data.objects.new("test", obj.data)
                new_obj.location = obj.location
                new_obj.rotation_quaternion = obj.rotation_quaternion
                new_obj.scale = obj.scale

                bpy.context.collection.objects.link(new_obj)
                newGroup.append(new_obj)
            # Parenting
            for obj in objGroup:
                if obj.parent in objGroup:
                    newGroup[objGroup.index(obj)].parent = newGroup[objGroup.index(obj.parent)]
            # Position root object
            if len(newGroup) > 0:
                Map_Import_Operator.applyTrasnformationToObject(newGroup[0], inst)
            print(str(inst.id) + 'loaded from buffer')
        else:
            importer = dff_importer.import_dff(
                {
                    'file_name'      : self.settings.dff_folder + '\\' + model + '.dff',
                    'image_ext'      : 'PNG',
                    'connect_bones'  : False,
                    'use_mat_split'  : False,
                    'remove_doubles' : True,
                    'group_materials': True,
                }
            )

            if len(importer.objects) > 0:
                Map_Import_Operator.applyTrasnformationToObject(importer.objects[0], inst)

            # Save into buffer
            self.model_buffer[inst.id] = importer.objects
            print(str(inst.id) + 'loaded new')
        
    def modal(self, context, event):

        if event.type in {'ESC'}:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER' and not self._updating:
            self._updating = True
            for x in range(10):
                self.import_object()

            num = (float(self.inst_index ) / float(len(self.object_instances)))
            bpy.context.window_manager.progress_update(num)

            dg = self._context.evaluated_depsgraph_get()
            dg.update() 

            self._updating = False
        if self._calcs_done:
            self.cancel(context)

        return {'PASS_THROUGH'}

    def execute(self, context):

        self.model_buffer = {}

        self._context = context
        self.settings = self._context.scene.dff

        map_data = map_utilites.MapDataUtility.getMapData(self.settings.engine_version, self.settings.game_root)
        self.object_instances = map_data['object_instances']
        self.object_data = map_data['object_data']

        bpy.context.window_manager.progress_begin(0, 100.0)

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.progress_end()
        wm.event_timer_remove(self._timer)

    @staticmethod
    def applyTrasnformationToObject(obj, inst):
        obj.location.x = float(inst.posX)
        obj.location.y = float(inst.posY)
        obj.location.z = float(inst.posZ)

        obj.rotation_mode       = 'QUATERNION'
        obj.rotation_quaternion.w = -float(inst.rotW)
        obj.rotation_quaternion.x = float(inst.rotX)
        obj.rotation_quaternion.y = float(inst.rotY)
        obj.rotation_quaternion.z = float(inst.rotZ)

        obj.scale.x = float(inst.scaleX)
        obj.scale.y = float(inst.scaleY)
        obj.scale.z = float(inst.scaleZ)

#     # @classmethod
#     # def poll(cls, context):
#         # return context.active_object is not None

#     def execute(self, context):
        
#         settings = context.scene.dff

#         map_data = map_utilites.MapDataUtility.getMapData(settings.engine_version, settings.game_root)
#         object_instances = map_data['object_instances']
#         object_data = map_data['object_data']

#         model_buffer = {}
#         import_limit = 150
#         import_counter = 0

#         # Progress bar
#         wm = bpy.context.window_manager
#         wm.progress_begin(0, 100.0)
#         self.timer = wm.event_timer_add(0.01)
            
#         for inst in object_instances:

#             model = object_data[inst.id].modelName

#             # implement model buffer
#             if inst.id in model_buffer:
#                 objGroup = model_buffer[inst.id]
#                 newGroup = []
#                 for obj in objGroup:
#                     new_obj = bpy.data.objects.new("gay", obj.data)
#                     bpy.context.collection.objects.link(new_obj)
#                     newGroup.append(new_obj)
#                 # Parenting
#                 for obj in objGroup:
#                     if obj.parent in objGroup:
#                         newGroup[objGroup.index(obj)].parent = newGroup[objGroup.index(obj.parent)]
#                     # if o.parent in obs:
#                     #     o.parent = group_objects[obs.index(o.parent)]
#                 # Position root object
#                 if len(newGroup) > 0:
#                     Map_Import_Operator.applyTrasnformationToObject(newGroup[0], inst)

#                 # group_objects = [o.copy() for o in bpy.data.groups['Group'].objects]
#                 # new_group = bpy.data.groups.new("NewGroup")
#                 # for o in group_objects:
#                 #     # parent
#                 #     if o.parent in obs:
#                 #         o.parent = group_objects[obs.index(o.parent)]
#                 #     # armature modifiers
#                 #     armature_mods = [m for m in o.modifiers if m.type == 'ARMATURE']
#                 #     for m in armature_mods:
#                 #         if m.object in obs:
#                 #             m.object = group_objects[obs.index(m.object)]
#                 #     new_group.objects.link(o)
#                 #     scene.objects.link(o)

#                 print('loaded from buffer')
#             else:
#                 # posX posY posZ scaleX scaleY scaleZ rotX rotY rotZ rotW
#                 # print(inst)
#                 importer = dff_importer.import_dff(
#                     {
#                         'file_name'      : settings.dff_folder + '\\' + model + '.dff',
#                         'image_ext'      : 'PNG',
#                         'connect_bones'  : False,
#                         'use_mat_split'  : False,
#                         'remove_doubles' : True,
#                         'group_materials': True,
#                         # 'position'       : mathutils.Vector((float(inst.posX), float(inst.posY), float(inst.posZ))),
#                         # 'rotation'       : mathutils.Quaternion((-float(inst.rotW), float(inst.rotX), float(inst.rotY), float(inst.rotZ))),
#                         # 'scale'          : mathutils.Vector((float(inst.scaleX), float(inst.scaleY), float(inst.scaleZ))),
#                         # 'meshes_only'    : True
#                     }
#                 )

#                 if len(importer.objects) > 0:
#                     Map_Import_Operator.applyTrasnformationToObject(importer.objects[0], inst)

#                 # Save into buffer
#                 model_buffer[inst.id] = importer.objects

#             import_counter += 1
#             num = (float(import_counter) / float(len(object_instances)))
#             print(num)
#             wm.progress_update(num)
#             if import_counter == import_limit: break

#         wm.event_timer_remove(self.timer)
#         wm.progress_end()
#         # bpy.context.scene.update()    # 2.7 ?
#         dg = context.evaluated_depsgraph_get()
#         dg.update() 
#         self.report({'INFO'}, 'ok')
        
#         return {'FINISHED'}

#     def applyTrasnformationToObject(object, inst):
#         object.location.x += float(inst.posX)
#         object.location.y += float(inst.posY)
#         object.location.z += float(inst.posZ)

#         object.rotation_quaternion.w = -float(inst.rotW)
#         object.rotation_quaternion.x = float(inst.rotX)
#         object.rotation_quaternion.y = float(inst.rotY)
#         object.rotation_quaternion.z = float(inst.rotZ)

#         object.scale.x = float(inst.scaleX)
#         object.scale.y = float(inst.scaleY)
#         object.scale.z = float(inst.scaleZ)

# # def register():
# #     bpy.utils.register_class(SimpleOperator)

# # def unregister():
# #     bpy.utils.unregister_class(SimpleOperator)

# # if __name__ == "__main__":
# #     register()

#     # test call
#     # bpy.ops.object.simple_operator()

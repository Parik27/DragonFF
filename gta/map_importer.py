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

    # @classmethod
    # def poll(cls, context):
        # return context.active_object is not None

    def execute(self, context):
        
        settings = context.scene.dff

        map_data = map_utilites.MapDataUtility.getMapData(settings.engine_version, settings.game_root)
        object_instances = map_data['object_instances']
        object_data = map_data['object_data']

        for inst in object_instances:
            
            model = object_data[inst.id].modelName

            # posX posY posZ scaleX scaleY scaleZ rotX rotY rotZ rotW

            # print(inst)

            version = dff_importer.import_dff(
                {
                    'file_name'      : settings.dff_folder + '\\' + model + '.dff',
                    'image_ext'      : 'PNG',
                    'connect_bones'  : False,
                    'use_mat_split'  : False,
                    'remove_doubles' : True,
                    'group_materials': True,
                    'position'       : mathutils.Vector((float(inst.posX), float(inst.posY), float(inst.posZ))),
                    'rotation'       : mathutils.Quaternion((float(inst.rotW), float(inst.rotX), float(inst.rotY), float(inst.rotZ))),
                    'scale'          : mathutils.Vector((float(inst.scaleX), float(inst.scaleY), float(inst.scaleZ))),
                    'meshes_only'    : True
                }
            )

        self.report({'INFO'}, 'ok')
        
        return {'FINISHED'}

# def register():
#     bpy.utils.register_class(SimpleOperator)

# def unregister():
#     bpy.utils.unregister_class(SimpleOperator)

# if __name__ == "__main__":
#     register()

    # test call
    # bpy.ops.object.simple_operator()

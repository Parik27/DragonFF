# GTA DragonFF - Blender scripts to edit basic GTA formats
# Copyright (C) 2019  Parik

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import bpy
import os
from ..gtaLib import map as map_utilites
from ..ops import dff_importer, col_importer, txd_importer
from .cull_importer import cull_importer
from .importer_common import hide_object

#######################################################
class map_importer:

    model_cache = {}
    object_data = []
    object_instances = []
    cull_instances = []
    col_files = []
    collision_collection = None
    object_instances_collection = None
    mesh_collection = None
    cull_collection = None
    map_section = ""
    settings = None

    #######################################################
    @staticmethod
    def import_object_instance(context, inst):
        self = map_importer

        # Skip LODs if user selects this
        if hasattr(inst, 'lod') and int(inst.lod) == -1 and self.settings.skip_lod:
            return

        # Deleted objects that Rockstar forgot to remove?
        if inst.id not in self.object_data:
            return

        model = self.object_data[inst.id].modelName
        txd = self.object_data[inst.id].txdName

        if inst.id in self.model_cache:

            # Get model from memory
            new_objects = {}
            model_cache = self.model_cache[inst.id]

            cached_objects = [obj for obj in model_cache if obj.dff.type == "OBJ"]
            for obj in cached_objects:
                new_obj = bpy.data.objects.new(model, obj.data)
                new_obj.location = obj.location
                new_obj.rotation_quaternion = obj.rotation_quaternion
                new_obj.scale = obj.scale

                if not self.settings.create_backfaces:
                    modifier = new_obj.modifiers.new("EdgeSplit", 'EDGE_SPLIT')
                    # When added to some objects (empties?), returned modifier is None
                    if modifier is not None:
                        modifier.use_edge_angle = False

                if '{}.dff'.format(model) in bpy.data.collections:
                    bpy.data.collections['{}.dff'.format(model)].objects.link(
                        new_obj
                    )
                else:
                    context.collection.objects.link(new_obj)
                new_objects[obj] = new_obj

            # Parenting
            for obj in cached_objects:
                if obj.parent in cached_objects:
                    new_objects[obj].parent = new_objects[obj.parent]

            # Position root object
            for obj in new_objects.values():
                if not obj.parent:
                    self.apply_transformation_to_object(
                        obj, inst
                    )

            cached_2dfx = [obj for obj in model_cache if obj.dff.type == "2DFX"]
            for obj in cached_2dfx:
                new_obj = bpy.data.objects.new(obj.name, obj.data)
                new_obj.location = obj.location
                new_obj.rotation_mode = obj.rotation_mode
                new_obj.lock_rotation = obj.lock_rotation
                new_obj.rotation_quaternion = obj.rotation_quaternion
                new_obj.rotation_euler = obj.rotation_euler
                new_obj.scale = obj.scale

                if obj.parent:
                    new_obj.parent = new_objects[obj.parent]

                for prop in obj.dff.keys():
                    new_obj.dff[prop] = obj.dff[prop]

                if '{}.dff'.format(model) in bpy.data.collections:
                    bpy.data.collections['{}.dff'.format(model)].objects.link(
                        new_obj
                    )
                else:
                    context.collection.objects.link(new_obj)
                new_objects[obj] = new_obj

            print(str(inst.id), 'loaded from cache')
        else:

            dff_filename = "%s.dff" % model
            txd_filename = "%s.txd" % txd

            dff_filepath = map_utilites.MapDataUtility.find_path_case_insensitive(self.settings.dff_folder, dff_filename)
            txd_filepath = map_utilites.MapDataUtility.find_path_case_insensitive(self.settings.dff_folder, txd_filename)

            # Import dff from a file if file exists
            if not dff_filepath:
                print("DFF not found:", os.path.join(self.settings.dff_folder, dff_filename))
                return

            txd_images = {}
            if self.settings.load_txd:
                if txd_filepath:
                    txd_images = txd_importer.import_txd(
                        {
                            'file_name'      : txd_filepath,
                            'skip_mipmaps'   : True,
                            'pack'           : self.settings.txd_pack,
                        }
                    ).images
                else:
                    print("TXD not found:", os.path.join(self.settings.dff_folder, txd_filename))

            importer = dff_importer.import_dff(
                {
                    'file_name'      : "%s/%s.dff" % (
                        self.settings.dff_folder, model
                    ),
                    'txd_images'       : txd_images,
                    'image_ext'        : 'PNG',
                    'connect_bones'    : False,
                    'use_mat_split'    : self.settings.read_mat_split,
                    'remove_doubles'   : not self.settings.create_backfaces,
                    'create_backfaces' : self.settings.create_backfaces,
                    'group_materials'  : True,
                    'import_normals'   : True,
                    'materials_naming' : "DEF",
                    'import_breakable' : self.settings.import_breakable,
                }
            )

            collection_objects = list(importer.current_collection.objects)
            root_objects = [obj for obj in collection_objects if obj.dff.type == "OBJ" and not obj.parent]

            for obj in root_objects:
                map_importer.apply_transformation_to_object(
                    obj, inst
                )

            # Set root object as 2DFX parent
            if root_objects:
                for obj in collection_objects:
                    # Skip Road Signs
                    if obj.dff.type == "2DFX" and obj.dff.ext_2dfx.effect != '7':
                        obj.parent = root_objects[0]

            # Move dff collection to a top collection named for the file it came from
            if not self.object_instances_collection:
                self.create_object_instances_collection(context)

            context.scene.collection.children.unlink(importer.current_collection)
            self.object_instances_collection.children.link(importer.current_collection)

            # Save into buffer
            self.model_cache[inst.id] = collection_objects
            print(str(inst.id), 'loaded new')

        # Look for collision mesh
        name = self.model_cache[inst.id][0].name
        for obj in bpy.data.objects:
            if obj.dff.type == 'COL' and obj.name.endswith("%s.ColMesh" % name):
                new_obj = bpy.data.objects.new(obj.name, obj.data)
                new_obj.dff.type = 'COL'
                new_obj.location = obj.location
                new_obj.rotation_quaternion = obj.rotation_quaternion
                new_obj.scale = obj.scale
                map_importer.apply_transformation_to_object(
                    new_obj, inst
                )
                if '{}.dff'.format(name) in bpy.data.collections:
                    bpy.data.collections['{}.dff'.format(name)].objects.link(
                        new_obj
                    )
                hide_object(new_obj)

    #######################################################
    @staticmethod
    def import_collision(context, filename):
        self = map_importer

        if not self.collision_collection:
            self.create_collisions_collection(context)

        collection = bpy.data.collections.new(filename)
        self.collision_collection.children.link(collection)
        col_list = col_importer.import_col_file(os.path.join(self.settings.dff_folder, filename), filename)

        # Move all collisions to a top collection named for the file they came from
        for c in col_list:
            context.scene.collection.children.unlink(c)
            collection.children.link(c)

    #######################################################
    @staticmethod
    def import_cull(context, cull):
        self = map_importer

        if not self.cull_collection:
            self.create_cull_collection(context)

        obj = cull_importer.import_cull(cull)

        self.cull_collection.objects.link(obj)

    #######################################################
    @staticmethod
    def create_object_instances_collection(context):
        self = map_importer

        coll_name = '%s Meshes' % self.settings.game_version_dropdown
        self.mesh_collection = bpy.data.collections.get(coll_name)

        if not self.mesh_collection:
            self.mesh_collection = bpy.data.collections.new(coll_name)
            context.scene.collection.children.link(self.mesh_collection)

        # Create a new collection in Mesh to hold all the subsequent dffs loaded from this map section
        coll_name = self.map_section
        if os.path.isabs(coll_name):
            coll_name = os.path.basename(coll_name)
        self.object_instances_collection = bpy.data.collections.new(coll_name)
        self.mesh_collection.children.link(self.object_instances_collection)

    #######################################################
    @staticmethod
    def create_collisions_collection(context):
        self = map_importer

        coll_name = '%s Collisions' % self.settings.game_version_dropdown
        self.collision_collection = bpy.data.collections.get(coll_name)

        if not self.collision_collection:
            self.collision_collection = bpy.data.collections.new(coll_name)
            context.scene.collection.children.link(self.collision_collection)

            # Hide collection
            context.view_layer.active_layer_collection = context.view_layer.layer_collection.children[coll_name]
            context.view_layer.active_layer_collection.hide_viewport = True

    #######################################################
    @staticmethod
    def create_cull_collection(context):
        self = map_importer

        coll_name = '%s CULL' % self.settings.game_version_dropdown
        self.cull_collection = bpy.data.collections.get(coll_name)

        if not self.cull_collection:
            self.cull_collection = bpy.data.collections.new(coll_name)
            context.scene.collection.children.link(self.cull_collection)

            # Hide collection
            context.view_layer.active_layer_collection = context.view_layer.layer_collection.children[coll_name]
            context.view_layer.active_layer_collection.hide_viewport = True

    #######################################################
    @staticmethod
    def load_map(settings):
        self = map_importer

        self.model_cache = {}
        self.col_files = []
        self.object_instances_collection = None
        self.mesh_collection = None
        self.collision_collection = None
        self.cull_collection = None
        self.settings = settings

        if self.settings.use_custom_map_section:
            self.map_section = self.settings.custom_ipl_path
        else:
            self.map_section = self.settings.map_sections

        # Get all the necessary IDE and IPL data
        map_data = map_utilites.MapDataUtility.load_map_data(
            self.settings.game_version_dropdown,
            self.settings.game_root,
            self.map_section,
            self.settings.use_custom_map_section)

        self.object_instances = map_data.object_instances
        self.object_data = map_data.object_data

        if self.settings.load_cull:
            self.cull_instances = map_data.cull_instances
        else:
            self.cull_instances = []

        if self.settings.load_collisions:

            # Get a list of the .col files available
            col_files_all = set()
            for filename in os.listdir(self.settings.dff_folder):
                if filename.lower().endswith(".col"):
                    col_files_all.add(filename)

            # Run through all instances and determine which .col files to load
            for i in range(len(self.object_instances)):
                id = self.object_instances[i].id
                # Deleted objects that Rockstar forgot to remove?
                if id not in self.object_data:
                    continue

                objdata = self.object_data[id]
                if not hasattr(objdata, 'filename'):
                    continue

                prefix = objdata.filename.split('/')[-1][:-4].lower()
                for filename in col_files_all:
                    if filename.startswith(prefix):
                        if not bpy.data.collections.get(filename) and filename not in self.col_files:
                            self.col_files.append(filename)

    #######################################################
    @staticmethod
    def apply_transformation_to_object(obj, inst):
        obj.location.x = float(inst.posX)
        obj.location.y = float(inst.posY)
        obj.location.z = float(inst.posZ)

        obj.rotation_mode = 'QUATERNION'
        obj.rotation_quaternion.w = -float(inst.rotW)
        obj.rotation_quaternion.x = float(inst.rotX)
        obj.rotation_quaternion.y = float(inst.rotY)
        obj.rotation_quaternion.z = float(inst.rotZ)

        if hasattr(inst, 'scaleX'):
            obj.scale.x = float(inst.scaleX)
        if hasattr(inst, 'scaleY'):
            obj.scale.y = float(inst.scaleY)
        if hasattr(inst, 'scaleZ'):
            obj.scale.z = float(inst.scaleZ)

#######################################################
def load_map(settings):
    map_importer.load_map(settings)

    return map_importer

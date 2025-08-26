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

import os 
import bpy

from ..gtaLib import map as map_utilites
from ..ops import dff_importer, col_importer, txd_importer
from .ipl.cull_importer import cull_importer
from .ipl.grge_importer import grge_importer
from .importer_common import hide_object

#######################################################
class map_importer:

    model_cache = {}
    object_data = []
    object_instances = []
    cull_instances = []
    grge_instances = []
    col_files = []
    enex_instances = []
    collision_collection = None
    object_instances_collection = None
    mesh_collection = None
    cull_collection = None
    grge_collection = None
    enex_collection = None
    enex_collection_name = None
    map_section = ""
    settings = None

    #######################################################
    @staticmethod
    def fix_id(idblock):
        if idblock is None:
            return False
        try:
            _ = idblock.name
            return True
        except ReferenceError:
            return False

    #######################################################
    def assign_map_properties(obj, ipl_data):
        obj.dff_map.object_id = ipl_data.get("object_id", 0)
        obj.dff_map.model_name = ipl_data.get("model_name", "")
        obj.dff_map.interior = ipl_data.get("interior", 0)
        obj.dff_map.lod = ipl_data.get("lod", 0)
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

                try:
                    self.assign_map_properties(new_obj, {
                        "object_id": int(inst.id),
                        "model_name": str(model),
                        "interior": int(getattr(inst, "interior", 0)),
                        "lod": int(getattr(inst, "lod", -1)),
                    })
                except Exception:
                    pass

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

                    # Store IPL
                    obj.ide.obj_id = inst.id
                    obj.ide.model_name = self.object_data[inst.id].modelName
                    if hasattr(inst, 'interior'):
                        obj.ipl.interior = inst.interior
                    if hasattr(inst, 'lod'):
                        obj.ipl.lod = inst.lod

                    # Store IDE data
                    ide_data = self.object_data[inst.id]
                    obj.ide.txd_name = ide_data.txdName
                    if hasattr(ide_data, 'drawDistance'):
                        obj.ide.draw_distance = ide_data.drawDistance
                    if hasattr(ide_data, 'drawDistance1'):
                        obj.ide.draw_distance1 = ide_data.drawDistance1
                    if hasattr(ide_data, 'drawDistance2'):
                        obj.ide.draw_distance2 = ide_data.drawDistance2
                    if hasattr(ide_data, 'drawDistance3'):
                        obj.ide.draw_distance3 = ide_data.drawDistance3
                    obj.ide.flags = ide_data.flags
                    obj.ide.obj_type = 'objs'  # Mark as regular object
                    if hasattr(ide_data, 'timeOn'):
                        obj.ide.obj_type = 'tobj'  # Mark as time object
                        obj.ide.time_on = ide_data.timeOn
                        obj.ide.time_off = ide_data.timeOff

            cached_2dfx = [obj for obj in model_cache if obj.dff.type == "2DFX"]
            for obj in cached_2dfx:
                new_obj = bpy.data.objects.new(obj.name, obj.data)
                new_obj.location = obj.location
                new_obj.rotation_mode = obj.rotation_mode
                new_obj.lock_rotation = obj.lock_rotation
                new_obj.rotation_quaternion = obj.rotation_quaternion
                new_obj.rotation_euler = obj.rotation_euler
                new_obj.scale = obj.scale

                self.assign_map_properties(new_obj, inst)

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
                }
            )

            collection_objects = list(importer.current_collection.objects)
            root_objects = [obj for obj in collection_objects if obj.dff.type == "OBJ" and not obj.parent]

            for obj in root_objects:
                map_importer.apply_transformation_to_object(
                    obj, inst
                )

                # Store IPL data
                obj.ide.obj_id = inst.id
                obj.ide.model_name = self.object_data[inst.id].modelName
                if hasattr(inst, 'interior'):
                    obj.ipl.interior = inst.interior
                if hasattr(inst, 'lod'):
                    obj.ipl.lod = inst.lod

                # Store IDE data
                ide_data = self.object_data[inst.id]
                obj.ide.txd_name = ide_data.txdName
                if hasattr(ide_data, 'drawDistance'):
                    obj.ide.draw_distance = ide_data.drawDistance
                if hasattr(ide_data, 'drawDistance1'):
                    obj.ide.draw_distance1 = ide_data.drawDistance1
                if hasattr(ide_data, 'drawDistance2'):
                    obj.ide.draw_distance2 = ide_data.drawDistance2
                if hasattr(ide_data, 'drawDistance3'):
                    obj.ide.draw_distance3 = ide_data.drawDistance3
                obj.ide.flags = ide_data.flags
                obj.ide.obj_type = 'objs'  # Mark as regular object
                if hasattr(ide_data, 'timeOn'):
                    obj.ide.obj_type = 'tobj'  # Mark as time object
                    obj.ide.time_on = ide_data.timeOn
                    obj.ide.time_off = ide_data.timeOff

            # Set root object as 2DFX parent
            if root_objects:
                for obj in collection_objects:
                    # Skip Road Signs
                    if obj.dff.type == "2DFX" and obj.dff.ext_2dfx.effect != '7':
                        obj.parent = root_objects[0]

            # Move dff collection to a top collection named for the file it came from
            if not self.object_instances_collection:
                self.object_instances_collection = self.create_object_instances_collection(context)

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
            self.collision_collection = self.create_entries_collection(context, "Collisions")

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
            self.cull_collection = self.create_entries_collection(context, "CULL")

        obj = cull_importer.import_cull(cull)
        self.cull_collection.objects.link(obj)

    #######################################################
    @staticmethod
    def import_grge(context, grge):
        self = map_importer

        if not self.grge_collection:
            self.grge_collection = self.create_entries_collection(context, "GRGE")

        obj = grge_importer.import_grge(grge)
        self.grge_collection.objects.link(obj)

    #######################################################
    @staticmethod
    def create_enex_cylinder():
        name = "_ENEX_"
        me = bpy.data.meshes.get(name)
        if me:
            return me

        import bmesh
        me = bpy.data.meshes.new(name)
        bm = bmesh.new()
        bmesh.ops.create_cone(
            bm,
            segments    = 24,
            radius1     = 0.45,
            radius2     = 0.45,
            depth       = 1.0,
            cap_ends    = True,
            cap_tris    = False
        )
        bm.to_mesh(me)
        bm.free()
        return me
    #######################################################
    @staticmethod
    def import_enex(context, e):
        self = map_importer

        if isinstance(e, (list, tuple)):
            row = list(e)
            if len(row) < 18:
                row += [None] * (18 - len(row))

            X1, Y1, Z1 = row[0], row[1], row[2]
            EnterAngle  = row[3]
            SizeX, SizeY, SizeZ = row[4], row[5], row[6]
            X2, Y2, Z2  = row[7], row[8], row[9]
            ExitAngle   = row[10]
            TargetInterior = row[11]
            Flags = row[12]
            raw_name = row[13]
            name = None
            if isinstance(raw_name, str):
                s = raw_name.strip()
                if len(s) >= 2 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'")):
                    s = s[1:-1]
                name = s
            Sky = row[14]
            NumPedsToSpawn = row[15]
            TimeOn = row[16]
            TimeOff = row[17]

            coll = self.create_enex_collection(context)
            me = self.create_enex_cylinder()

            label = f"ENEX_{name}" if name else "ENEX"
            obj = bpy.data.objects.new(label, me)

            try:
                obj.location = (float(X1 or 0.0), float(Y1 or 0.0), float(Z1 or 0.0))
            except Exception:
                obj.location = (0.0, 0.0, 0.0)

            obj.rotation_mode = 'ZXY'
            try:
                obj.rotation_euler = (0.0, 0.0, float(EnterAngle or 0.0))
            except Exception:
                obj.rotation_euler = (0.0, 0.0, 0.0)

            obj.hide_render = True
            try:
                obj.display_type = 'WIRE'
            except Exception:
                pass

            mat = bpy.data.materials.get("_ENEX") or bpy.data.materials.new("_ENEX")
            mat.diffuse_color = (1.0, 0.85, 0.10, 1.0)
            if not obj.data.materials:
                obj.data.materials.append(mat)
            else:
                obj.data.materials[0] = mat

            # tag section
            if hasattr(obj, "dff"):
                obj.dff.type = "ENEX"
            if hasattr(obj, "dff_map"):
                obj.dff_map.ipl_section = "enex"
            else:
                obj["ipl_section"] = "enex"

            # store all fields so you can round-trip/export later
            def _setf(k, v):
                try:
                    if v is not None: obj[f"enex_{k}"] = float(v)
                except Exception:
                    pass
            def _seti(k, v):
                try:
                    if v is not None: obj[f"enex_{k}"] = int(v)
                except Exception:
                    pass
            def _sets(k, v):
                if v is not None: obj[f"enex_{k}"] = str(v)

            _setf("X1", X1); _setf("Y1", Y1); _setf("Z1", Z1)
            _setf("EnterAngle", EnterAngle)
            _setf("SizeX", SizeX); _setf("SizeY", SizeY); _setf("SizeZ", SizeZ)
            _setf("X2", X2); _setf("Y2", Y2); _setf("Z2", Z2)
            _setf("ExitAngle", ExitAngle)
            _seti("TargetInterior", TargetInterior)
            _seti("Flags", Flags)
            _sets("Name", name)
            _seti("Sky", Sky)
            _seti("NumPedsToSpawn", NumPedsToSpawn)
            _seti("TimeOn", TimeOn)
            _seti("TimeOff", TimeOff)

            coll.objects.link(obj)
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
        coll =  bpy.data.collections.new(coll_name)
        self.mesh_collection.children.link(coll)

        return coll

    #######################################################
    @staticmethod
    def create_entries_collection(context, postfix):
        self = map_importer

        coll_name = '%s %s' % (self.settings.game_version_dropdown, postfix)
        coll = bpy.data.collections.get(coll_name)

        if not coll:
            coll = bpy.data.collections.new(coll_name)
            context.scene.collection.children.link(coll)

            # Hide collection
            context.view_layer.active_layer_collection = context.view_layer.layer_collection.children[coll_name]
            context.view_layer.active_layer_collection.hide_viewport = True

        return coll

    #######################################################
    @staticmethod
    def create_enex_collection(context):
        self = map_importer
        if self.settings is None:
            self.settings = context.scene.dff

        coll_name = f"{self.settings.game_version_dropdown} ENEX"

        coll = self.enex_collection if map_importer.fix_id(self.enex_collection) else None
        if coll is None and self.enex_collection_name:
            coll = bpy.data.collections.get(self.enex_collection_name)

        if coll is None:
            coll = bpy.data.collections.get(coll_name)
            if coll is None:
                coll = bpy.data.collections.new(coll_name)

        if coll.name not in {c.name for c in context.scene.collection.children}:
            context.scene.collection.children.link(coll)

        # Optional (nice): start hidden
        try:
            context.view_layer.active_layer_collection = context.view_layer.layer_collection.children[coll_name]
            context.view_layer.active_layer_collection.hide_viewport = True
        except Exception:
            pass

        self.enex_collection = coll
        self.enex_collection_name = coll.name
        return coll

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
        self.grge_collection = None
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

        if self.settings.load_grge:
            self.grge_instances = map_data.grge_instances
        else:
            self.grge_instances = []

        if self.settings.load_enex:
            self.enex_instances = map_data.enex_instances
        else:
            self.enex_instances = []

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

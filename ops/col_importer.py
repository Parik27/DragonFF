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
import bmesh
import mathutils

from ..gtaLib import col
from ..gtaLib.data import col_materials as mats
from .importer_common import (
    link_object, create_collection, material_helper
)

#######################################################        
class col_importer:
    
    #######################################################
    def __init__(self, col):
        self.col = col

    #######################################################
    def from_file(filename):

        collision = col.coll()
        collision.load_file(filename)

        return col_importer(collision)

    #######################################################
    def from_mem(memory):

        collision = col.coll()
        collision.load_memory(memory)

        return col_importer(collision)
    
    #######################################################
    def __add_spheres(self, collection, array):

        for index, entity in enumerate(array):
            name = collection.name + ".ColSphere.%d" % index
        
            # Check if this is a vehicle sphere
            if entity.surface.material in (6, 7, 45, 63, 64, 65):

                presets = mats.COL_PRESET_SA if col.Sections.version == 3 else mats.COL_PRESET_VC

                for preset in presets:
                    if (preset[0] == 13 and
                        preset[1] == entity.surface.material and
                        preset[2] == entity.surface.flags):
                        name = collection.name + "." + preset[3].replace(" ", "_")
                        break

            obj = bpy.data.objects.new(name, None)

            obj.location = entity.center
            obj.scale = [entity.radius] * 3

            obj.empty_display_type = 'SPHERE'

            obj.dff.type = 'COL'
            obj.dff.col_material = entity.surface.material
            obj.dff.col_flags = entity.surface.flags
            obj.dff.col_brightness = entity.surface.brightness
            obj.dff.col_day_light = entity.surface.light & 0xf
            obj.dff.col_night_light = (entity.surface.light >> 4) & 0xf

            link_object(obj, collection)

    #######################################################
    def __add_boxes(self, collection, array):

        for index, entity in enumerate(array):
            name = collection.name + ".ColBox.%d" % index

            obj = bpy.data.objects.new(name, None)

            mn = mathutils.Vector(entity.min)
            mx = mathutils.Vector(entity.max)
            half = 0.5 * (mx - mn)
            obj.location = mn + half
            obj.scale = half

            obj.empty_display_type = 'CUBE'

            obj.dff.type = 'COL'
            obj.dff.col_material = entity.surface.material
            obj.dff.col_flags = entity.surface.flags
            obj.dff.col_brightness = entity.surface.brightness
            obj.dff.col_day_light = entity.surface.light & 0xf
            obj.dff.col_night_light = (entity.surface.light >> 4) & 0xf

            link_object(obj, collection)

    #######################################################
    def __add_mesh_mats(self, object, materials):

        for surface in materials:
            
            colour = mats.groups[mats.default['group']][1]
            name = mats.groups[mats.default['group']][0]
            
            try:
                # SA
                if col.Sections.version == 3 or surface.material >= 34:
                    mat = mats.sa_mats[surface.material]
                    
                # VC/III
                else:
                    mat = mats.vc_mats[surface.material]
                
                # Generate names
                colour = mats.groups[mat[0]][1]
                name = "%s - %s" % (mats.groups[mat[0]][0], mat[1])

            except KeyError:
                pass

            # Convert hex to a value Blender understands
            colour = [colour[0:2], colour[2: 4], colour[4: 6], "FF"]
            colour = [int(x, 16) for x in colour]

            mat = bpy.data.materials.new(name)
            mat.dff.col_mat_index   = surface.material
            mat.dff.col_flags       = surface.flags
            mat.dff.col_brightness  = surface.brightness
            mat.dff.col_day_light   = surface.light & 0xf
            mat.dff.col_night_light = (surface.light >> 4) & 0xf

            helper = material_helper(mat)
            helper.set_base_color(colour)
            
            object.data.materials.append(helper.material)
            
    #######################################################
    def __add_mesh(self, collection, name, verts, faces, face_groups, shadow=False):

        mesh      = bpy.data.meshes.new(name)
        materials = {}
        
        bm = bmesh.new()

        for v in verts:
            bm.verts.new(v)

        bm.verts.ensure_lookup_table()
            
        for f in faces:
            try:
                face = bm.faces.new(
                    [
                        bm.verts[f.a],
                        bm.verts[f.c],
                        bm.verts[f.b]
                    ]
                )
                if hasattr(f, "surface"):
                    surface = f.surface
                else:
                    surface = col.TSurface(f.material, 0, 1, f.light)

                if surface not in materials:
                    materials[surface] = len(materials)
                
                face.material_index = materials[surface]

            except Exception as e:
                print(e)
                
        bm.to_mesh(mesh)
        bm.free()

        # Face groups get stored in a face attribute on the mesh, each face storing the index of its group
        if face_groups:
            if (2, 93, 0) > bpy.app.version:
                attribute = mesh.attributes.new(name="face group", type="INT", domain="POLYGON")
                attribute = mesh.attributes[attribute.name]
            else:
                attribute = mesh.attributes.new(name="face group", type="INT", domain="FACE")

            for fg_idx, fg in enumerate(face_groups):
                for face_idx in range(fg.start, fg.end+1):
                    if face_idx >= len(mesh.polygons):
                        break
                    attribute.data[face_idx].value = fg_idx

        obj = bpy.data.objects.new(name, mesh)
        obj.dff.type = 'SHA' if shadow else 'COL'
        
        link_object(obj, collection)

        self.__add_mesh_mats(obj, materials)
            
    #######################################################
    def add_to_scene(self, collection_prefix, link=True):

        collection_list = []
        
        for model in self.col.models:

            collection = create_collection("%s.%s" % (collection_prefix,
                                                           model.model_name),
                                           link
            )            

            # Store the import bounds as a custom property of the collection
            collection.dff.bounds_min = model.bounds.min
            collection.dff.bounds_max = model.bounds.max

            self.__add_spheres(collection, model.spheres)
            self.__add_boxes(collection, model.boxes)

            if len(model.mesh_verts) > 0:
                self.__add_mesh(collection,
                                collection.name + ".ColMesh",
                                model.mesh_verts,
                                model.mesh_faces,
                                model.face_groups if model.flags & 8 else None)

            if len(model.shadow_verts) > 0:
                self.__add_mesh(collection,
                                collection.name + ".ShadowMesh",
                                model.shadow_verts,
                                model.shadow_faces,
                                None,
                                True)

            collection.dff.auto_bounds = len(collection.objects) > 0

            collection_list.append(collection)

        return collection_list
    
#######################################################
def import_col_file(filename, collection_prefix, link=True):

    col = col_importer.from_file(filename)
    return col.add_to_scene(collection_prefix, link)

#######################################################
def import_col_mem(mem, collection_prefix, link=True):

    col = col_importer.from_mem(mem)
    return col.add_to_scene(collection_prefix, link)

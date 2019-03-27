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

from . import col
from .importer_common import (
    link_object, create_collection, hide_object, material_helper
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
            name = collection.name + ".Sphere.%d" % (index)
        
            obj  = bpy.data.objects.new(name, None)
            
            obj.location = entity.center
            obj.scale = [entity.radius] * 3
            if (2, 80, 0) > bpy.app.version:
                obj.empty_draw_type = 'SPHERE'
            else:
                obj.empty_display_type = 'SPHERE'

            obj["col_surface"] = entity.surface
            
            link_object(obj, collection)

    #######################################################
    def __add_mesh_mats(self, object, materials):

        # TODO: materials.ini integration needed
        for surface in materials:
            mat = bpy.data.materials.new("")

            mat.dff.is_col_material = True
            mat.dff.col_mat_index   = surface.material
            mat.dff.col_brightness  = surface.brightness
            mat.dff.col_light       = surface.light

            object.data.materials.append(mat)
            
    #######################################################
    def __add_mesh(self, collection, name, verts, faces):

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
                        bm.verts[f.b],
                        bm.verts[f.c]
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
        
        obj = bpy.data.objects.new(name, mesh)
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
            self.__add_spheres(collection, model.spheres)

            if len(model.mesh_verts) > 0:
                self.__add_mesh(collection,
                                collection.name + ".ColMesh",
                                model.mesh_verts,
                                model.mesh_faces)

            if len(model.shadow_verts) > 0:
                self.__add_mesh(collection,
                                collection.name + ".ShadowMesh",
                                model.shadow_verts,
                                model.shadow_faces)
                        
            collection_list.append(collection)

            # Hide objects
            if (2, 80, 0) > bpy.app.version:
                for obj in collection.objects:
                    hide_object(obj)
            else:
               collection.hide_viewport = True     

        return collection_list
    
#######################################################
def import_col_file(filename, collection_prefix, link=True):

    col = col_importer.from_file(filename)
    return col.add_to_scene(collection_prefix, link)

#######################################################
def import_col_mem(mem, collection_prefix, link=True):
    
    col = col_importer.from_mem(mem)
    return col.add_to_scene(collection_prefix, link)

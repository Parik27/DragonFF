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

#######################################################
def link_object(obj, collection):
        collection.objects.link(obj)
        if (2, 80, 0) > bpy.app.version:
            bpy.context.scene.objects.link(obj)

#######################################################        
def create_collection(name, link=True):
        if (2, 80, 0) > bpy.app.version:
            return bpy.data.groups.new(name)
        else:
            collection = bpy.data.collections.new(name)
            if link:
                bpy.context.scene.collection.children.link(collection)
                
            return collection        

#######################################################        
class col_importer:

    #######################################################
    def create_collection(name):
        if (2, 80, 0) > bpy.app.version:
            return bpy.data.groups.new(name)
        else:
            collection = bpy.data.collections.new(name)
            bpy.context.scene.collection.children.link(collection)

            return collection
    
    #######################################################
    def __init__(self, col):
        self.col = col

    #######################################################
    def from_file(filename: str):

        collision = col.coll()
        collision.load_file(filename)

        return col_importer(collision)

    #######################################################
    def from_mem(memory: str):

        collision = col.coll()
        collision.load_memory(memory)

        return col_importer(collision)
    
    #######################################################
    def __add_spheres(self, collection, array):

        name = collection.name + ".Sphere"
        
        mesh = bpy.data.metaballs.new(name)
        obj  = bpy.data.objects.new(name, mesh)

        mesh.threshold = 0.00001
        mesh.resolution = 0.05
        
        link_object(obj, collection)
        
        for entity in array:
            element = mesh.elements.new(type='BALL')
            element.co = entity.center
            element.radius = entity.radius

    #######################################################
    def __add_mesh(self, collection, name, verts, faces):

        mesh = bpy.data.meshes.new(name)
        bm = bmesh.new()

        for v in verts:
            bm.verts.new(v)

        bm.verts.ensure_lookup_table()
            
        for f in faces:
            bm.faces.new(
                [
                    bm.verts[f.a],
                    bm.verts[f.b],
                    bm.verts[f.c]
                ]
            )

        bm.to_mesh(mesh)
        bm.free()
        
        obj = bpy.data.objects.new(name, mesh)
        link_object(obj, collection)
            
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
                                "ColMesh",
                                model.mesh_verts,
                                model.mesh_faces)

            if len(model.shadow_verts) > 0:
                self.__add_mesh(collection,
                                "ShadowMesh",
                                model.shadow_verts,
                                model.shadow_faces)
                        
            collection_list.append(collection)
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

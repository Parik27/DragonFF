# GTA Blender Tools - Tools to edit basic GTA formats
# Copyright (C) 2019  Parik

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
import bmesh
import mathutils

from . import dff

#######################################################
class dff_exporter:

    selected = False
    mass_export = False
    file_name = ""
    dff = None
    frames = {}

    #######################################################
    def clear_extension(string):
        
        k = string.rfind('.')
        return string if k < 0 else string[:k]
    
    #######################################################
    def create_frame(obj):
        self = dff_exporter
        
        frame = dff.Frame()
        
        # Get rid of everything before the last period
        frame.name = self.clear_extension(obj.name)

        matrix = obj.matrix_world

        frame.creation_flags  = 0
        frame.position        = matrix.to_translation()
        frame.rotation_matrix = dff.Matrix._make(
            matrix.to_3x3()
        )

        frame.parent = -1
        if obj.parent is not None:
            frame.parent = self.frames[obj.name]

        self.frames[obj.name] = len(self.dff.frame_list)
        self.dff.frame_list.append(frame)

        return frame

    #######################################################
    def generate_material_list(obj):
        self = dff_exporter

        materials = []

        for b_material in obj.data.materials:

            # Blender 2.7x compatibility
            if (2, 80, 0) > bpy.app.version:
                pass

            else:
                from bpy_extras.node_shader_utils import PrincipledBSDFWrapper
            
                material = dff.Material()

                principled = PrincipledBSDFWrapper(b_material,
                                                   is_readonly=True)

                material.colour = dff.RGBA._make(
                    # Blender uses float for RGB Values, and has no Alpha
                    list(int(255 * x) for x in principled.base_color)
                    + [255])

                # Texture
                if principled.base_color_texture.image is not None:
                    #TODO: Texture Filters
                    #TODO: Texture Extensions
                    
                    texture = dff.Texture()
                    texture.name = self.clear_extension(
                        principled.base_color_texture.image.name
                    )
                    texture.filters = 0 # <-- find a way to store this in Blender

                    material.textures.append(texture)

                # Surface Properties
                # TODO: Ambient property from custom properties
                specular = principled.specular
                diffuse  = principled.roughness
                ambient  = principled.roughness
                material.surface_properties = dff.GeomSurfPro(
                    ambient, specular, diffuse
                )
                
                materials.append(material)
                
        return materials
    
    #######################################################
    def populate_atomic(obj):
        self = dff_exporter

        # Create geometry
        geometry = dff.Geometry()
        
        bm       = bmesh.new()
        bm.from_mesh(obj.data)

        bmesh.ops.triangulate(bm, faces=bm.faces[:])

        bm.verts.ensure_lookup_table()
        bm.verts.index_update()
        
        # Vertices and Normals
        # TODO: Check if the normals are same as the custom ones set while importing
        for vertex in bm.verts:
            geometry.vertices.append(dff.Vector._make(vertex.co))
            geometry.normals.append(dff.Vector._make(vertex.normal))

        # Allocate uv layers array
        uv_layers_count = len(bm.loops.layers.uv)
        geometry.uv_layers = [[None] * len(bm.verts)] * uv_layers_count
        
        # Faces
        for face in bm.faces:
            geometry.triangles.append(                
                dff.Triangle._make((
                    face.verts[1].index, #b
                    face.verts[0].index, #a
                    face.material_index, #material
                    face.verts[2].index #c
                ))
            )

            # Set UV Coordinates for this face
            for loop in face.loops:
                for index, layer in enumerate(bm.loops.layers.uv.values()):
                    uv = loop[layer].uv
                    geometry.uv_layers[index][loop.vert.index] = dff.TexCoords._make(
                        (uv.x, 1 - uv.y) #UV Coordinates are flipped in the Y Axis
                    )

        self.create_frame(obj)

        # Bounding sphere
        sphere_center = 0.125 * sum(
            (mathutils.Vector(b) for b in obj.bound_box),
            mathutils.Vector()
        )
        sphere_center = obj.matrix_world @ sphere_center
        sphere_radius = 1.414 * max(*obj.dimensions) # sqrt(2) * side = diagonal

        geometry.bounding_sphere = dff.Sphere._make(
            list(sphere_center) + [sphere_radius]
        )

        geometry.surface_properties = (0,0,0)
        geometry.materials = self.generate_material_list(obj)
        
        # Add Geometry to list
        self.dff.geometry_list.append(geometry)
        
        # Create Atomic from geometry and frame
        geometry_index = len(self.dff.geometry_list) - 1
        frame_index    = len(self.dff.frame_list) - 1
        atomic         = dff.Atomic._make((frame_index,
                                           geometry_index,
                                           0x4,
                                           0
        ))
        self.dff.atomic_list.append(atomic)
        bm.free()
        
    #######################################################
    def export_objects(objects, name=None):
        self = dff_exporter

        if len(objects) < 1:
            return
        
        for obj in objects:

            # create atomic in this case
            if obj.type == "MESH":
                self.populate_atomic(obj)
            pass

        if name is None:
            self.dff.write_file(self.file_name, 0x33002 )
        else:
            self.dff.write_file("%s/%s", (self.path, name))
    
    #######################################################
    def export_dff(filename):
        self = dff_exporter

        self.file_name = filename
        
        self.dff = dff.dff()
        objects = []

        # Export collections
        for collection in bpy.data.collections:
            if self.mass_export:
                
                if not self.selected:
                    self.export_objects(collection.objects,
                                        collection.name)
                else:
                    # Only add selected objects to the array
                    for obj in collection.objects:
                        if obj.select_get():
                            objects.append(obj)

                    self.export_objects(objects,
                                        collection.name)
                    objects = []
            else:
                if not self.selected:
                    objects += collection.objects
                    
                else:
                    # Only add selected objects to the array
                    for obj in collection.objects:
                        if obj.select_get():
                            objects.append(obj)

                self.export_objects(objects)
                
#######################################################
def export_dff(options):

    # Shadow Function
    dff_exporter.selected    = options['selected']
    dff_exporter.mass_export = options['mass_export']
    dff_exporter.path        = options['directory']
    
    dff_exporter.export_dff(options['file_name'])

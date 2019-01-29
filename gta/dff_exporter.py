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

from . import dff

#######################################################
class dff_exporter:

    selected = False
    mass_export = False
    file_name = ""
    dff = None
    version = None
    frames = {}
    bones = {}

    #######################################################
    def multiply_matrix(a, b):
        # For compatibility with 2.79
        if bpy.app.version < (2, 80, 0):
            return a * b
        return a @ b
    
    #######################################################
    def clear_extension(string):
        
        k = string.rfind('.')
        return string if k < 0 else string[:k]
    
    #######################################################
    def create_frame(obj, append=True):
        self = dff_exporter
        
        frame = dff.Frame()
        
        # Get rid of everything before the last period
        frame.name = self.clear_extension(obj.name)

        # Is obj a bone?
        is_bone = type(obj) is bpy.types.Bone
        
        matrix                = obj.matrix_local
        frame.creation_flags  =  0
        frame.parent          = -1
        frame.position        = matrix.to_translation()
        frame.rotation_matrix = dff.Matrix._make(
            matrix.to_3x3().transposed()
        )

        id_array = self.bones if is_bone else self.frames
        
        if obj.parent is not None:
            frame.parent = id_array[obj.parent.name]

        id_array[obj.name] = len(self.dff.frame_list)

        if append:
            self.dff.frame_list.append(frame)

        return frame

    #######################################################
    def generate_material_list(obj):
        self = dff_exporter

        materials = []

        for b_material in obj.data.materials:

            # Blender 2.7x compatibility
            if (2, 80, 0) > bpy.app.version:
                material = dff.Material()
                material.colour = dff.RGBA(
                    list(int(255 * x) for x in b_material.diffuse_color) + [255]
                )

                # Texture
                try:
                    texture = dff.Texture()
                    texture.filters = 0
                    texture.name = self.clear_extension(
                        b_material.texture_slots[0].texture.image.name
                    )
                    material.textures.append(texture)
                except:
                    pass

                # Surface properties
                specular = b_material.specular_intensity
                diffuse  = b_material.diffuse_intensity
                ambient  = b_material.ambient
                
                material.surface_properties = dff.GeomSurfPro(
                    ambient, specular, diffuse
                )
                
                materials.append(material)
            else:
                from bpy_extras.node_shader_utils import PrincipledBSDFWrapper
            
                material = dff.Material()

                principled = PrincipledBSDFWrapper(b_material,
                                                   is_readonly=True)

                material.colour = dff.RGBA._make(
                    # Blender uses float for RGB Values, and has no Alpha
                    list(int(255 * x) for x in principled.base_color) + [255])
                
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
    def init_skin_plg(obj):

        # Returns a SkinPLG object if the object has an armature modifier
        armature = None
        for modifier in obj.modifiers:
            if modifier.type == 'ARMATURE':
                armature = modifier.object
                break
            
        if armature is None:
            return None
        
        skin = dff.SkinPLG()
        
        bones = armature.data.bones
        skin.num_bones = len(bones)
        
        for bone in bones:
            matrix = bone.matrix_local.inverted().transposed()
            skin.bone_matrices.append(
                matrix
            )

        # Set vertex group weights
        for vertex in obj.data.vertices:
            skin.vertex_bone_indices.append([0,0,0,0])
            skin.vertex_bone_weights.append([0,0,0,0])
            for index, group in enumerate(vertex.groups):

                # Only upto 4 vertices per group are supported
                if index > 4:
                    break
                skin.vertex_bone_indices[-1][index] = group.group
                skin.vertex_bone_weights[-1][index] = group.weight

        return skin
    
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

        # Set SkinPLG
        skin = self.init_skin_plg(obj)


        # These are used to set the vertex indices for new vertices
        # created in the next loop to get rid of shared vertices.
        override_faces = {}
        
        # Vertices and Normals
        # TODO: Check if the normals are same as the custom ones set while importing
        i = 0        
        while i < len(bm.verts):
            vertex = bm.verts[i]
            
            geometry.vertices.append(dff.Vector._make(vertex.co))
            geometry.normals.append(dff.Vector._make(vertex.normal))

            # Look for shared vertices with different
            # UV Coordinates (Done) / Vertex Color (TODO)
            uv_layers = bm.loops.layers.uv.values()
            vertex_coord = [None] * len(uv_layers)
            
            for loop in vertex.link_loops:
                for index, layer in enumerate(uv_layers):

                    if vertex_coord[index] is None:
                        vertex_coord[index] = loop[layer].uv
                        continue

                    # create a fork
                    if vertex_coord[index] != loop[layer].uv:
                        face = loop.face
                        face.loops.index_update()
                        
                        if face.index not in override_faces:
                            override_faces[face.index] = [
                                vert.index for vert in face.verts
                            ]

                        print(face.index, loop.index)
                        override_faces[face.index][loop.index] = len(bm.verts)

                        # Update the SkinPLG to include the duplicated vertex
                        if skin is not None:
                            bone_indices = skin.vertex_bone_indices
                            bone_weights = skin.vertex_bone_weights

                            bone_indices.append(bone_indices[vertex.index])
                            bone_weights.append(bone_weights[vertex.index])
                        
                        bm.verts.new(vertex.co, vertex)
                        bm.verts.ensure_lookup_table()
            
            i += 1

        # Allocate uv layers array
        uv_layers_count = len(bm.loops.layers.uv)
        geometry.uv_layers = [[dff.TexCoords(0,0)] * len(bm.verts)] * uv_layers_count
        
        # Faces
        for face in bm.faces:

            verts = [vert.index for vert in face.verts]
            if face.index in override_faces:
                verts = override_faces[face.index]
                
            geometry.triangles.append(                
                dff.Triangle._make((
                    verts[1], #b
                    verts[0], #a
                    face.material_index, #material
                    verts[2] #c
                ))
            )

            # Set UV Coordinates for this face
            face.loops.index_update()
            for loop in face.loops:
                for index, layer in enumerate(bm.loops.layers.uv.values()):
                    uv = loop[layer].uv
                    geometry.uv_layers[index][verts[loop.index]] = dff.TexCoords._make(
                        (uv.x, 1 - uv.y) #UV Coordinates are flipped in the Y Axis
                    )

        self.create_frame(obj)

        # Bounding sphere
        sphere_center = 0.125 * sum(
            (mathutils.Vector(b) for b in obj.bound_box),
            mathutils.Vector()
        )
        sphere_center = self.multiply_matrix(obj.matrix_world, sphere_center)
        sphere_radius = 1.414 * max(*obj.dimensions) # sqrt(2) * side = diagonal

        geometry.bounding_sphere = dff.Sphere._make(
            list(sphere_center) + [sphere_radius]
        )

        geometry.surface_properties = (0,0,0)
        geometry.materials = self.generate_material_list(obj)

        if skin is not None:
            geometry.extensions['skin'] = skin
        
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
    def export_armature(obj):
        self = dff_exporter
        
        for index, bone in enumerate(obj.data.bones):

            # Create a special bone (contains information for all subsequent bones)
            if index == 0:
                frame = self.create_frame(bone, False)

                # set the first bone's parent to armature's parent
                if obj.parent is not None:
                    frame.parent = self.frames[obj.parent.name]

                bone_data = dff.HAnimPLG()
                bone_data.header = dff.HAnimHeader(
                    0x100,
                    bone["bone_id"],
                    len(obj.data.bones)
                )
                # Make bone array in the root bone
                for _index, _bone in enumerate(obj.data.bones):
                    bone_data.bones.append(
                        dff.Bone(
                                _bone["bone_id"],
                                _index,
                                _bone["type"])
                    )

                frame.bone_data = bone_data
                self.dff.frame_list.append(frame)
                continue

            # Create a regular Bone
            frame = self.create_frame(bone, False)

            # Set bone data
            bone_data = dff.HAnimPLG()
            bone_data.header = dff.HAnimHeader(
                0x100,
                bone["bone_id"],
                0
            )
            frame.bone_data = bone_data
            self.dff.frame_list.append(frame)
        
        
    #######################################################
    def export_objects(objects, name=None):
        self = dff_exporter
        
        self.dff = dff.dff()

        # Skip empty collections
        if len(objects) < 1:
            return
        
        for obj in objects:

            # create atomic in this case
            if obj.type == "MESH":
                self.populate_atomic(obj)

            # create an empty frame
            elif obj.type == "EMPTY":
                self.create_frame(obj)

            elif obj.type == "ARMATURE":
                self.export_armature(obj)
                
        if name is None:
            self.dff.write_file(self.file_name, self.version )
        else:
            self.dff.write_file("%s/%s" % (self.path, name), self.version)
    
    #######################################################
    def export_dff(filename):
        self = dff_exporter

        self.file_name = filename
        
        objects = []

        # Export collections
        if self.mass_export:
            for collection in bpy.data.collections:
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
            for obj in bpy.data.objects:
                
                if not self.selected or obj.select_get():
                    objects.append(obj)

            self.export_objects(objects)
                
#######################################################
def export_dff(options):

    # Shadow Function
    dff_exporter.selected    = options['selected']
    dff_exporter.mass_export = options['mass_export']
    dff_exporter.path        = options['directory']
    dff_exporter.version     = options['version']
    
    dff_exporter.export_dff(options['file_name'])

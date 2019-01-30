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
    parent_queue = {}

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
        
        frame       = dff.Frame()
        frame_index = len(self.dff.frame_list)
        
        # Get rid of everything before the last period
        frame.name = self.clear_extension(obj.name)

        # Is obj a bone?
        is_bone = type(obj) is bpy.types.Bone

        # Scan parent queue
        for name in self.parent_queue:
            if name == obj.name:
                index = self.parent_queue[name]
                self.dff.frame_list[index].parent = frame_index
        
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

        id_array[obj.name] = frame_index

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
                except BaseException:
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

                    # Use node label if it is a substring of image name, else
                    # use image name
                    node_label = principled.base_color_texture.node_image.label
                    image_name = principled.base_color_texture.image.name

                    texture.name = self.clear_extension(
                        node_label
                        if node_label in image_name and node_label is not ""
                        else image_name
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
    def get_vertex_shared_loops(vertex, layers_list):
        temp = [[None] * len(layers) for layers in layers_list]
        shared_loops = []
        
        for loop in vertex.link_loops:

            shared = False
            for i, layers in enumerate(layers_list):
                for j, layer in enumerate(layers):

                    if temp[i][j] is None:
                        temp[i][j] = loop[layer]

                    if temp[i][j] != loop[layer]:
                        shared = True
                        break

                if shared:
                    shared_loops.append(loop)
                    break
                
        return shared_loops
    
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

        has_prelit_colours = len(obj.data.vertex_colors) > 0

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

            shared_loops = self.get_vertex_shared_loops(
                vertex,
                [
                    bm.loops.layers.uv.values(),
                    bm.loops.layers.color.values()
                ]
            )
            
            # create a fork
            for loop in shared_loops:
                face = loop.face
                face.loops.index_update()
                
                if face.index not in override_faces:
                    override_faces[face.index] = [
                        vert.index for vert in face.verts
                    ]
                else:
                    continue
                        
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

        # Allocate uv layers/vertex colours array
        uv_layers_count = len(bm.loops.layers.uv)
        geometry.uv_layers = [[dff.TexCoords(0,0)] * len(bm.verts)
                              for i in range(uv_layers_count)]
        if has_prelit_colours:
            geometry.prelit_colours = [dff.RGBA(255,255,255,255)] * len(bm.verts)
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

            face.loops.index_update()
            for loop in face.loops:
                
                # Set UV Coordinates for this face
                for index, layer in enumerate(bm.loops.layers.uv.values()):
                    uv = loop[layer].uv
                    geometry.uv_layers[index][verts[loop.index]] = dff.TexCoords(
                        uv.x, 1 - uv.y #UV Coordinates are flipped in the Y Axis
                    )

                # Set prelit faces for this face
                if has_prelit_colours:
                    for index, layer in enumerate(bm.loops.layers.color.values()):
                        color = loop[layer]
                        geometry.prelit_colours[verts[loop.index]] = dff.RGBA._make(
                            int(c * 255) for c in color
                        )
                        break #only once
                
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
    def calculate_parent_depth(obj):
        parent = obj.parent
        depth = 0
        
        while parent is not None:
            parent = parent.parent
            depth += 1

        return depth        
        
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
        
        objects = {}

        # Export collections
        if self.mass_export:
            for collection in bpy.data.collections:
                for obj in collection.objects:
                    
                    if not self.selected or obj.select_get():
                        objects[obj] = self.calculate_parent_depth(obj)

                objects = sorted(objects, key=objects.get)
                self.export_objects(objects,
                                    collection.name)
                objects = {}
                self.frames = {}
                self.bones = {}
        else:
            for obj in bpy.data.objects:
                
                if not self.selected or obj.select_get():
                    objects[obj] = self.calculate_parent_depth(obj)

            objects = sorted(objects, key=objects.get)
            self.export_objects(objects)
                
#######################################################
def export_dff(options):

    # Shadow Function
    dff_exporter.selected    = options['selected']
    dff_exporter.mass_export = options['mass_export']
    dff_exporter.path        = options['directory']
    dff_exporter.version     = options['version']

    dff_exporter.export_dff(options['file_name'])

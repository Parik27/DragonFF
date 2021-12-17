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
import bmesh
import math
import mathutils

from ..gtaLib import dff
from .importer_common import (
    link_object, create_collection,
    material_helper, set_object_mode,
    hide_object)
from .col_importer import import_col_mem

#######################################################
class ext_2dfx_importer:

    """ Helper class for 2dfx importing """
    # Basically I didn't want to have such functions in
    # the main dfff_importer, as the functions wouldn't
    # make any sense being there.
    
    #######################################################
    def __init__(self, effects):
        self.effects = effects

    #######################################################
    def import_light(self, entry):
        pass
    
    #######################################################
    def get_objects(self):

        """ Import and return the list of imported objects """

        functions = {
            0: self.import_light
        }

        objects = []
        
        for entry in self.effects.entries:
            if entry.effect_id in functions:
                objects.append(functions[entry.effect_id](entry))

        return objects
    
#######################################################
class dff_importer:

    image_ext          = "png"
    use_bone_connect   = False
    current_collection = None
    use_mat_split      = False
    remove_doubles     = False
    group_materials    = False
    version            = ""
    warning            = ""

    __slots__ = [
        'dff',
        'meshes',
        'objects',
        'file_name',
        'skin_data',
        'bones'
    ]

    #######################################################
    def multiply_matrix(a, b):
        # For compatibility with 2.79
        if bpy.app.version < (2, 80, 0):
            return a * b
        return a @ b
    
    #######################################################
    def _init():
        self = dff_importer

        # Variables
        self.dff = None
        self.meshes = {}
        self.objects = []
        self.file_name = ""
        self.skin_data = {}
        self.bones = {}
        self.materials = {}
        self.warning = ""

    #######################################################
    # TODO: Cyclomatic Complexity too high
    def import_atomics():
        self = dff_importer

        # Import atomics (meshes)
        for atomic in self.dff.atomic_list:

            frame = self.dff.frame_list[atomic.frame]
            geom = self.dff.geometry_list[atomic.geometry]
            
            mesh = bpy.data.meshes.new(frame.name)
            bm   = bmesh.new()

            # Temporary Custom Properties that'll be used to set Object properties
            # later.
            mesh['dragon_normals'] = False
            mesh['dragon_pipeline'] = 'NONE'
            mesh['dragon_cust_pipeline'] = None
            mesh['dragon_light'] = (geom.flags & dff.rpGEOMETRYLIGHT) != 0
            mesh['dragon_modulate_color'] = \
                (geom.flags & dff.rpGEOMETRYMODULATEMATERIALCOLOR) != 0

            uv_layers = []
            
            # Vertices
            for v in geom.vertices:
                bm.verts.new(v)

            bm.verts.ensure_lookup_table()
            bm.verts.index_update()

            # Will use this later when creating frames to construct an armature
            if 'skin' in geom.extensions:

                if atomic.frame in self.skin_data:
                    skin = geom.extensions['skin']
                    self.skin_data[atomic.frame].vertex_bone_indices += \
                        skin.vertex_bone_indices
                    self.skin_data[atomic.frame].vertex_bone_weights += \
                        skin.vertex_bone_weights
                    
                else:
                    self.skin_data[atomic.frame] = geom.extensions['skin']
                    
            if 'user_data' in geom.extensions:
                mesh['dff_user_data'] = geom.extensions['user_data'].to_mem()[12:]
            
            # Add UV Layers
            for layer in geom.uv_layers:
                uv_layers.append(bm.loops.layers.uv.new())
                
            # Add Vertex Colors
            if geom.flags & dff.rpGEOMETRYPRELIT:
                vertex_color = bm.loops.layers.color.new()

            extra_vertex_color = None
            if 'extra_vert_color' in geom.extensions:
                extra_vertex_color = bm.loops.layers.color.new()

            if dff_importer.use_mat_split and 'mat_split' in geom.extensions:
                faces = geom.extensions['mat_split']
            else:
                faces = geom.triangles
                 
            
            for f in faces:
                try:
                    face = bm.faces.new(
                        [
                            bm.verts[f.a],
                            bm.verts[f.b],
                            bm.verts[f.c]
                        ])

                    face.material_index = f.material
                    
                    # Setting UV coordinates
                    for loop in face.loops:
                        for i, layer in enumerate(geom.uv_layers):

                            bl_layer = uv_layers[i]
                            
                            uv_coords = layer[loop.vert.index]

                            loop[bl_layer].uv = (
                                uv_coords.u,
                                1 - uv_coords.v # Y coords are flipped in Blender
                            )
                        # Vertex colors
                        if geom.flags & dff.rpGEOMETRYPRELIT:
                            loop[vertex_color] = [
                                c / 255.0 for c in
                                geom.prelit_colors[loop.vert.index]
                            ]
                        # Night/Extra Vertex Colors
                        if extra_vertex_color:
                            extension = geom.extensions['extra_vert_color']
                            loop[extra_vertex_color] = [
                                c / 255.0 for c in
                                extension.colors[loop.vert.index]
                            ]
                            
                    face.smooth = True
                except BaseException as e:
                    print(e)
                    
            bm.to_mesh(mesh)

            # Set loop normals
            if geom.has_normals:
                normals = []
                for loop in mesh.loops:
                    normals.append(geom.normals[loop.vertex_index])

                mesh.normals_split_custom_set(normals)
                mesh.use_auto_smooth = True
                mesh['dragon_normals'] = True

            # Set pipeline
            if geom.pipeline is not None:
                
                pipeline = "0x%X" % (geom.pipeline)

                if pipeline in ["0x53F20098", "0x53F2009A"]:
                    mesh['dragon_pipeline'] = pipeline
                else:
                    mesh['dragon_pipeline'] = "CUSTOM"
                    mesh['dragon_cust_pipeline'] = pipeline
                
            mesh.update()

            # Import materials and add the mesh to the meshes list
            self.import_materials(geom, frame, mesh)
            if atomic.frame in self.meshes:
                self.merge_meshes(self.meshes[atomic.frame], mesh)

                self.warning = \
                "Multiple Meshes with same Atomic index. Export will be invalid."
                
                pass
            else:
                self.meshes[atomic.frame] = mesh


    #######################################################
    def merge_meshes(mesha, meshb):
        bm = bmesh.new()

        bm.from_mesh(mesha)
        bm.from_mesh(meshb)

        bm.to_mesh(mesha)
                
    #######################################################
    def set_empty_draw_properties(empty):
        if (2, 80, 0) > bpy.app.version:
            empty.empty_draw_type = 'CUBE'
            empty.empty_draw_size = 0.05
        else:
            empty.empty_display_type = 'CUBE'
            empty.empty_display_size = 0.05
        pass

    ##################################################################
    def import_2dfx(self, effects):
        
        for effect in effects.entries:
            pass

    ##################################################################
    def generate_material_name(material, fallback):

        name = None
        
        patterns = {
            "vehiclegeneric": "generic",
            "interior": "interior",
            "vehiclesteering": "steering"
        }

        if material.is_textured:
            texture = material.textures[0].name

            for pattern in patterns:
                if pattern in texture:
                    name = patterns[pattern]

        mat_color = material.color
        if mat_color.a < 200:
            name = "glass"

        colors = {
            "[255, 60, 0, 255]": "right rear light",
            "[185, 255, 0, 255]": "left rear light",
            "[0, 255, 200, 255]": "right front light",
            "[255, 175, 0, 255]": "left front light",
            "[255, 0, 175, 255]": "secondary",
            "[60, 255, 0, 255]": "primary",
            "[184, 255, 0, 255]": "breaklight l",
            "[255, 59, 0, 255]": "breaklight r",
            "[255, 173, 0, 255]": "revlight L",
            "[0, 255, 198, 255]": "revlight r",
            "[255, 174, 0, 255]": "foglight l",
            "[0, 255, 199, 255]": "foglight r",
            "[183, 255, 0, 255]": "indicator lf",
            "[255, 58, 0, 255]": "indicator rf",
            "[182, 255, 0, 255]": "indicator lm",
            "[255, 57, 0, 255]": "indicator rm",
            "[181, 255, 0, 255]": "indicator lr",
            "[255, 56, 0, 255]": "indicator rr",
            "[0, 16, 255, 255]": "light night",
            "[0, 17, 255, 255]": "light all-day",
            "[0, 18, 255, 255]": "default day"
        }

        for color in colors:
            if eval(color) == list(mat_color):
                name = colors[color]
                
        return name if name else fallback
        
    ##################################################################
    # TODO: MatFX: Dual Textures
    def import_materials(geometry, frame, mesh):

        self = dff_importer        
        from bpy_extras.image_utils import load_image

        # Refactored
        for index, material in enumerate(geometry.materials):

            # Check for equal materials
            if self.group_materials and hash(material) in self.materials:
                mesh.materials.append(self.materials[hash(material)])
                continue
            
            # Generate a nice name with index and frame
            name = "%s.%d" % (frame.name, index)
            name = self.generate_material_name(material, name)
            
            mat = bpy.data.materials.new(name)
            mat.blend_method = 'CLIP'
            helper = material_helper(mat)
            
            helper.set_base_color(material.color)

            # Loading Texture
            if material.is_textured == 1 and self.image_ext:
                texture = material.textures[0]
                path    = os.path.dirname(self.file_name)
                image_name = "%s.%s" % (texture.name, self.image_ext)

                # name.None shouldn't exist, lol / Share loaded images among imported materials
                if (image_name in bpy.data.images and
                        path == bpy.path.abspath(bpy.data.images[image_name].filepath)):
                    image = bpy.data.images[image_name]
                else:
                    image = load_image(image_name,
                                       path,
                                       recursive=False,
                                       place_holder=True,
                                       check_existing=True
                                       )
                helper.set_texture(image, texture.name)
                
            # Normal Map
            if 'bump_map' in material.plugins:
                mat.dff.export_bump_map = True
                
                for bump_fx in material.plugins['bump_map']:

                    texture = None
                    if bump_fx.height_map is not None:
                        texture = bump_fx.height_map
                        if bump_fx.bump_map is not None:
                            mat.dff.bump_map_tex = bump_fx.bump_map.name

                    elif bump_fx.bump_map is not None:
                        texture = bump_fx.bump_map

                    if texture:
                        path = os.path.dirname(self.file_name)
                        image_name = "%s.%s" % (texture.name, self.image_ext)

                        # see name.None note above / Share loaded images among imported materials
                        if (image_name in bpy.data.images and
                                path == bpy.path.abspath(bpy.data.images[image_name].filepath)):
                            image = bpy.data.images[image_name]
                        else:
                            image = load_image(image_name,
                                               path,
                                               recursive=False,
                                               place_holder=True,
                                               check_existing=True
                                               )

                        helper.set_normal_map(image,
                                              texture.name,
                                              bump_fx.intensity
                        )

            # Surface Properties
            if material.surface_properties is not None:
                props = material.surface_properties

            elif geometry.surface_properties is not None:
                props = geometry.surface_properties

            if props is not None:
                helper.set_surface_properties(props)

            # Environment Map
            if 'env_map' in material.plugins:
                plugin = material.plugins['env_map'][0]
                helper.set_environment_map(plugin)

            # Specular Material
            if 'spec' in material.plugins:
                plugin = material.plugins['spec'][0]
                helper.set_specular_material(plugin)

            # Reflection Material
            if 'refl' in material.plugins:
                plugin = material.plugins['refl'][0]
                helper.set_reflection_material(plugin)

            if 'udata' in material.plugins:
                plugin = material.plugins['udata'][0]
                helper.set_user_data(plugin)
                
            # UV Animation
            # TODO: Figure out ways to add multiple uv animations
            if 'uv_anim' in material.plugins:
                plugin = material.plugins['uv_anim'][0]

                for uv_anim in self.dff.uvanim_dict:
                    if uv_anim.name == plugin:
                        helper.set_uv_animation(uv_anim)
                        break
                
            # Add imported material to the object
            mesh.materials.append(helper.material)

            # Add imported material to lookup table for similar materials
            if self.group_materials:
                self.materials[hash(material)] = helper.material

    #######################################################
    def construct_bone_dict():
        self = dff_importer
        
        for index, frame in enumerate(self.dff.frame_list):
            if frame.bone_data:
                bone_id = frame.bone_data.header.id
                if bone_id != -1:
                    self.bones[bone_id] = {'frame': frame,
                                              'index': index}
                        
    #######################################################
    def align_roll( vec, vecz, tarz ):

        sine_roll = vec.normalized().dot(vecz.normalized().cross(tarz.normalized()))

        if 1 < abs(sine_roll):
            sine_roll /= abs(sine_roll)
            
        if 0 < vecz.dot( tarz ):
            return math.asin( sine_roll )
        
        elif 0 < sine_roll:
            return -math.asin( sine_roll ) + math.pi
        
        else:
            return -math.asin( sine_roll ) - math.pi

    #######################################################
    def get_skinned_obj_index(frame, frame_index):
        self = dff_importer

        possible_frames = [
            frame.parent, # The parent frame 
            frame_index - 1, # The previous frame
            0 # The first frame
        ]
        
        for possible_frame in possible_frames:
            
            if possible_frame in self.skin_data:
                return possible_frame

        # Find an arbritary frame
        for _, index in enumerate(self.skin_data):
            return index

        raise Exception("Cannot construct an armature without skinned mesh")
        
    #######################################################
    def construct_armature(frame, frame_index):

        self = dff_importer
        
        armature = bpy.data.armatures.new(frame.name)
        obj = bpy.data.objects.new(frame.name, armature)
        link_object(obj, dff_importer.current_collection)

        try:
            skinned_obj_index = self.get_skinned_obj_index(frame, frame_index)
        except Exception as e:
            raise e
        
        skinned_obj_data = self.skin_data[skinned_obj_index]
        skinned_obj = self.objects[skinned_obj_index]
        
        # armature edit bones are only available in edit mode :/
        set_object_mode(obj, "EDIT")
        edit_bones = obj.data.edit_bones
        
        bone_list = {}
                        
        for index, bone in enumerate(frame.bone_data.bones):
            
            bone_frame = self.bones[bone.id]['frame']

            # Set vertex group name of the skinned object
            skinned_obj.vertex_groups[index].name = bone_frame.name
            
            e_bone = edit_bones.new(bone_frame.name)
            e_bone.tail = (0,0.05,0) # Stop bone from getting delete

            e_bone['bone_id'] = bone.id
            e_bone['type'] = bone.type

            if bone_frame.user_data is not None:
                e_bone['dff_user_data'] = bone_frame.user_data.to_mem()[12:]
            
            matrix = skinned_obj_data.bone_matrices[bone.index]
            matrix = mathutils.Matrix(matrix).transposed()
            matrix = matrix.inverted()

            e_bone.transform(matrix, scale=True, roll=False)
            e_bone.roll = self.align_roll(e_bone.vector,
                                          e_bone.z_axis,
                                          self.multiply_matrix(
                                              matrix.to_3x3(),
                                              mathutils.Vector((0,0,1))
                                          )
            )
            
            # Setting parent. See "set parent" note below
            if bone_frame.parent != -1:
                try:
                    e_bone.parent = bone_list[bone_frame.parent][0]
                    if self.use_bone_connect:

                        if not bone_list[bone_frame.parent][1]:

                            mat = [e_bone.parent.head, e_bone.parent.tail, e_bone.head]
                            mat = mathutils.Matrix(mat)
                            if abs(mat.determinant()) < 0.0000001:
                                
                                length = (e_bone.parent.head - e_bone.head).length
                                e_bone.length      = length
                                e_bone.use_connect = self.use_bone_connect
                            
                                bone_list[bone_frame.parent][1] = True
                        
                except BaseException:
                    print("DragonFF: Bone parent not found")
            
            bone_list[self.bones[bone.id]['index']] = [e_bone, False]
            
                    
        set_object_mode(obj, "OBJECT")

        # Add Armature modifier to skinned object
        modifier        = skinned_obj.modifiers.new("Armature", 'ARMATURE')
        modifier.object = obj
        
        return (armature, obj)

    #######################################################
    def set_vertex_groups(obj, skin_data):

        # Allocate vertex groups
        for i in range(skin_data.num_bones):
            obj.vertex_groups.new()

        # vertex_bone_indices stores what 4 bones influence this vertex
        for i in range(len(skin_data.vertex_bone_indices)):

            for j in range(len(skin_data.vertex_bone_indices[i])):

                bone = skin_data.vertex_bone_indices[i][j]
                weight = skin_data.vertex_bone_weights[i][j]
                
                obj.vertex_groups[bone].add([i], weight, 'ADD')

    #######################################################
    def remove_object_doubles():
        self = dff_importer

        for frame in self.meshes:
            bm = bmesh.new()
            bm.from_mesh(self.meshes[frame])

            # Mark edges with 1 linked face, sharp
            for edge in bm.edges:
                if len(edge.link_loops) == 1:
                    edge.smooth = False
            
            bmesh.ops.remove_doubles(bm, verts = bm.verts, dist = 0.00001)

            # Add an edge split modifier
            object   = self.objects[frame]
            modifier = object.modifiers.new("EdgeSplit", 'EDGE_SPLIT')
            modifier.use_edge_angle = False
            
            bm.to_mesh(self.meshes[frame])
                
    #######################################################
    def import_frames():
        self = dff_importer

        # Initialise bone indices for use in armature construction
        self.construct_bone_dict()
        #self.import_2dfx(self.dff.ext_2dfx)
        
        for index, frame in enumerate(self.dff.frame_list):

            # Check if the mesh for the frame has been loaded
            mesh = None
            if index in self.meshes:
                mesh = self.meshes[index]

            obj = None

            # Load rotation matrix
            matrix = mathutils.Matrix(
                (
                    frame.rotation_matrix.right,
                    frame.rotation_matrix.up,
                    frame.rotation_matrix.at
                )
            )
            
            matrix.transpose()

            if frame.bone_data is not None:
                
                # Construct an armature
                if frame.bone_data.header.bone_count > 0:
                    try:
                        mesh, obj = self.construct_armature(frame, index)
                    except Exception as e:
                        print(e)
                        continue
                    
                # Skip bones
                elif frame.bone_data.header.id in self.bones and mesh is None:
                    continue
                    
            # Create and link the object to the scene
            if obj is None:
                obj = bpy.data.objects.new(frame.name, mesh)
                link_object(obj, dff_importer.current_collection)

                obj.rotation_mode       = 'QUATERNION'
                obj.rotation_quaternion = matrix.to_quaternion()
                obj.location            = frame.position
                obj.scale               = matrix.to_scale()


                # Set empty display properties to something decent
                if mesh is None:
                    self.set_empty_draw_properties(obj)                        

                else:
                    # Set object properties from mesh properties
                    obj.dff.pipeline       = mesh['dragon_pipeline']
                    obj.dff.export_normals = mesh['dragon_normals']
                    obj.dff.light          = mesh['dragon_light']
                    obj.dff.modulate_color = mesh['dragon_modulate_color']

                    if obj.dff.pipeline == 'CUSTOM':
                        obj.dff.custom_pipeline = mesh['dragon_cust_pipeline']
                    
                    # Delete temporary properties used earlier
                    del mesh['dragon_pipeline'      ]
                    del mesh['dragon_normals'       ]
                    del mesh['dragon_cust_pipeline' ]
                    del mesh['dragon_light'         ]
                    del mesh['dragon_modulate_color']
                    
                # Set vertex groups
                if index in self.skin_data:
                    self.set_vertex_groups(obj, self.skin_data[index])
            
            # set parent
            # Note: I have not considered if frames could have parents
            # that have not yet been defined. If I come across such
            # a model, the code will be modified to support that

            if  frame.parent != -1:
                obj.parent = self.objects[frame.parent]
                
            self.objects.append(obj)

            # Set a collision model used for export
            obj["gta_coll"] = self.dff.collisions
            if frame.user_data is not None:
                obj["dff_user_data"] = frame.user_data.to_mem()[12:]

        if self.remove_doubles:
            self.remove_object_doubles()

    #######################################################
    def preprocess_atomics():
        self = dff_importer

        atomic_frames = []
        to_be_preprocessed = [] #these will be assigned a new frame
        
        for index, atomic in enumerate(self.dff.atomic_list):

            frame = self.dff.frame_list[atomic.frame]

            # For GTA SA bones, which have the frame of the pedestrian
            # (incorrectly?) set in the atomic to a bone
            if frame.bone_data is not None and frame.bone_data.header.id != -1:
                to_be_preprocessed.append(index)

            atomic_frames.append(atomic.frame)

        # Assign every atomic in the list a new (possibly valid) frame
        for atomic in to_be_preprocessed:
            
            for index, frame in enumerate(self.dff.frame_list):

                # Find an empty frame
                if (frame.bone_data is None or frame.bone_data.header.id == -1) \
                   and index not in atomic_frames:
                    _atomic = list(self.dff.atomic_list[atomic])
                    _atomic[0] = index # _atomic.frame = index
                    self.dff.atomic_list[atomic] = dff.Atomic(*_atomic)
                    break
                    
            
    #######################################################
    def import_dff(file_name):
        self = dff_importer
        self._init()

        # Load the DFF
        self.dff = dff.dff()
        self.dff.load_file(file_name)
        self.file_name = file_name

        self.preprocess_atomics()
        
        # Create a new group/collection
        self.current_collection = create_collection(
            os.path.basename(file_name)
        )
        
        self.import_atomics()
        self.import_frames()

        # Set imported version
        self.version = "0x%05x" % self.dff.rw_version
        
        # Add collisions
        for collision in self.dff.collisions:
            col = import_col_mem(collision, os.path.basename(file_name), False)
            
            if (2, 80, 0) <= bpy.app.version:
                for collection in col:
                    self.current_collection.children.link(collection)

                    # Hide objects
                    for object in collection.objects:
                        hide_object(object)

#######################################################
def import_dff(options):

    # Shadow function
    dff_importer.image_ext        = options['image_ext']
    dff_importer.use_bone_connect = options['connect_bones']
    dff_importer.use_mat_split    = options['use_mat_split']
    dff_importer.remove_doubles   = options['remove_doubles']
    dff_importer.group_materials  = options['group_materials']

    dff_importer.import_dff(options['file_name'])

    return dff_importer
    return dff_importer

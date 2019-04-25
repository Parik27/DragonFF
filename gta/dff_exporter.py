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
from .importer_common import set_object_mode

#######################################################
def clear_extension(string):
    
    k = string.rfind('.')
    return string if k < 0 else string[:k]
    
#######################################################
class material_helper:

    """ Material Helper for Blender 2.7x and 2.8 compatibility"""

    #######################################################
    def get_base_color(self):

        if self.principled:
            node = self.principled.node_principled_bsdf.inputs["Base Color"]
            return dff.RGBA._make(
                list(int(255 * x) for x in node.default_value)
            )
        alpha = int(self.material.alpha * 255)
        return dff.RGBA._make(
                    list(int(255*x) for x in self.material.diffuse_color) + [alpha]
                )

    #######################################################
    def get_texture(self):

        texture = dff.Texture()
        texture.filters = 0 # <-- find a way to store this in Blender
        
        # 2.8         
        if self.principled:
            if self.principled.base_color_texture.image is not None:

                node_label = self.principled.base_color_texture.node_image.label
                image_name = self.principled.base_color_texture.image.name

                # Use node label if it is a substring of image name, else
                # use image name
                
                texture.name = clear_extension(
                    node_label
                    if node_label in image_name and node_label is not ""
                    else image_name
                )
                return texture
            return None

        # Blender Internal
        try:
            texture.name = clear_extension(
                self.material.texture_slots[0].texture.image.name
            )
            return texture

        except BaseException:
            return None

    #######################################################
    def get_surface_properties(self):

        if self.principled:
            specular = self.principled.specular
            diffuse = self.principled.roughness
            ambient = self.material.dff.ambient
            
        else:

            specular = self.material.specular_intensity
            diffuse  = self.material.diffuse_intensity
            ambient  = self.material.ambient
            
        return dff.GeomSurfPro(ambient, specular, diffuse)

    #######################################################
    def get_normal_map(self):

        bump_texture = None
        diffuse_texture = dff.Texture()
        
        diffuse_texture.filters = 0

        if not self.material.dff.export_bump_map:
            return None
        
        # 2.8
        if self.principled:
            
            if self.principled.normalmap_texture.image is not None:

                bump_texture = dff.Texture()
                
                node_label = self.principled.node_normalmap.label
                image_name = self.principled.normalmap_texture.image.name

                bump_texture.name = clear_extension(
                    node_label
                    if node_label in image_name and node_label is not ""
                    else image_name
                )
                intensity = self.principled.normalmap_strength

        # 2.79
        for slot in self.material.texture_slots:

            bump_texture = dff.Texture()
            
            if slot.texture.use_normal_map:
                bump_texture.name = clear_extension(slot.texture.image.name)
                intensity = slot.normal_factor
                return (bump_texture, slot.normal_factor)

        diffuse_texture.name = self.material["bump_map_tex"]
        if diffuse_texture.name == "":
            diffuse_texture = None

        if bump_texture is not None:
            return dff.BumpMapFX(intensity, diffuse_texture, bump_texture)

        return None

    #######################################################
    def get_environment_map(self):

        if not self.material.dff.export_env_map:
            return None

        texture_name = self.material.dff.env_map_tex
        coef         = self.material.dff.env_map_coef
        use_fb_alpha  = self.material.dff.env_map_fb_alpha

        texture = dff.Texture()
        texture.name = texture_name
        texture.filters = 0
        
        return dff.EnvMapFX(coef, use_fb_alpha, texture)

    #######################################################
    def get_specular_material(self):

        props = self.material.dff
        
        if not props.export_specular:
            return None

        return dff.SpecularMat(props.specular_level,
                               props.specular_texture.encode('ascii'))

    #######################################################
    def get_reflection_material(self):

        props = self.material.dff

        if not props.export_reflection:
            return None

        return dff.ReflMat(
            props.reflection_scale_x, props.reflection_scale_y,
            props.reflection_offset_x, props.reflection_offset_y,
            props.reflection_intensity
        )

    
    #######################################################
    def get_uv_animation(self):

        #TODO: Add Blender Internal Support

        anim = dff.UVAnim()

        # See if export_animation checkbox is checked
        if not self.material.dff.export_animation:
            return None

        anim.name = self.material.dff.animation_name
        
        if self.principled:
            if self.principled.base_color_texture.has_mapping_node():
                anim_data = self.material.node_tree.animation_data
                
                fps = bpy.context.scene.render.fps
                
                if anim_data:
                    for curve in anim_data.action.fcurves:

                        # Rw doesn't support Z texture coordinate.
                        if curve.array_index > 1:
                            continue

                        # Offset in the UV array
                        uv_offset = {
                            'nodes["Mapping"].translation': 4,
                            'nodes["Mapping"].scale': 1,
                        }
                        off = uv_offset[curve.data_path]
                        
                        for i, frame in enumerate(curve.keyframe_points):
                            
                            if len(anim.frames) <= i:
                                anim.frames.append(dff.UVFrame(0,[0]*6, i-1))

                            _frame = list(anim.frames[i])
                                
                            uv = _frame[1]
                            uv[off + curve.array_index] = frame.co[1]

                            _frame[0] = frame.co[0] / fps

                            anim.frames[i] = dff.UVFrame._make(_frame)
                            anim.duration = max(anim.frames[i].time,anim.duration)
                            
                    return anim
    
    #######################################################
    def __init__(self, material):
        self.material = material
        self.principled = None

        if bpy.app.version >= (2, 80, 0):
            from bpy_extras.node_shader_utils import PrincipledBSDFWrapper
            
            self.principled = PrincipledBSDFWrapper(self.material,
                                                    is_readonly=False)
        
        

#######################################################
def edit_bone_matrix(edit_bone):

    """ A helper function to return correct matrix from any
        bone setup there might. 
        
        Basically resets the Tail to +0.05 in Y Axis to make a correct
        prediction
    """

    return edit_bone.matrix
    
    # What I wrote above is rubbish, by the way. This is a hack-ish solution
    original_tail = list(edit_bone.tail)
    edit_bone.tail = edit_bone.head + mathutils.Vector([0, 0.05, 0])
    matrix = edit_bone.matrix

    edit_bone.tail = original_tail
    return matrix
            
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
    def create_frame(obj, append=True, set_parent=True):
        self = dff_exporter
        
        frame       = dff.Frame()
        frame_index = len(self.dff.frame_list)
        
        # Get rid of everything before the last period
        frame.name = clear_extension(obj.name)

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
        
        if set_parent and obj.parent is not None:
            frame.parent = id_array[obj.parent.name]            
            

        id_array[obj.name] = frame_index

        if append:
            self.dff.frame_list.append(frame)

        return frame

    #######################################################
    def generate_material_list(obj):
        materials = []
        self = dff_exporter

        for b_material in obj.data.materials:
            material = dff.Material()
            helper = material_helper(b_material)

            material.color             = helper.get_base_color()
            material.surface_properties = helper.get_surface_properties()
            
            texture = helper.get_texture()
            if texture:
                material.textures.append(texture)

            # Materials
            material.add_plugin('bump_map', helper.get_normal_map())
            material.add_plugin('env_map', helper.get_environment_map())
            material.add_plugin('spec', helper.get_specular_material())
            material.add_plugin('refl', helper.get_reflection_material())

            anim = helper.get_uv_animation()
            if anim:
                material.add_plugin('uv_anim', anim.name)
                self.dff.uvanim_dict.append(anim)
                
            materials.append(material)
                
        return materials

    #######################################################
    def init_skin_plg(obj, mesh):

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

        bone_groups = {} # This variable will store the bone groups
                         # to export keyed by their indices
                         
        for index, bone in enumerate(bones):
            matrix = bone.matrix_local.inverted().transposed()
            skin.bone_matrices.append(
                matrix
            )
            try:
                bone_groups[obj.vertex_groups[bone.name].index] = index

            except KeyError:
                pass
            
        # Set vertex group weights
        for vertex in mesh.vertices:
            skin.vertex_bone_indices.append([0,0,0,0])
            skin.vertex_bone_weights.append([0,0,0,0])
            for index, group in enumerate(vertex.groups):

                # Only upto 4 vertices per group are supported
                if index >= 4:
                    break
                
                if group.group in bone_groups:
                    skin.vertex_bone_indices[-1][index] = bone_groups[group.group]
                    skin.vertex_bone_weights[-1][index] = group.weight
                    
        return skin

    #######################################################
    def get_vertex_shared_loops(vertex, layers_list, funcs):
        #temp = [[None] * len(layers) for layers in layers_list]
        shared_loops = {}

        for loop in vertex.link_loops:
            start_loop = vertex.link_loops[0]
            
            shared = False
            for i, layers in enumerate(layers_list):
               
                for layer in layers:

                    if funcs[i](start_loop[layer], loop[layer]):
                        shared = True
                        break

                if shared:
                    shared_loops[loop] = True
                    break
                
        return shared_loops.keys()

    #######################################################
    def convert_to_mesh(obj):

        """ 
        A Blender 2.8 <=> 2.7 compatibility function for bpy.types.Object.to_mesh
        """
        
        # Temporarily disable armature
        disabled_modifiers = []
        for modifier in obj.modifiers:
            if modifier.type == 'ARMATURE':
                modifier.show_viewport = False
                disabled_modifiers.append(modifier)

        if bpy.app.version < (2, 80, 0):
            mesh = obj.to_mesh(bpy.context.scene, True, 'PREVIEW')
        else:
            mesh = obj.to_mesh(bpy.context.depsgraph, True)

        # Re enable disabled modifiers
        for modifier in disabled_modifiers:
            modifier.show_viewport = True

        return mesh
    
    #######################################################
    def populate_atomic(obj):
        self = dff_exporter

        # Create geometry
        geometry = dff.Geometry()

        mesh = self.convert_to_mesh(obj)
        bm   = bmesh.new()
        
        bm.from_mesh(mesh)

        bmesh.ops.triangulate(bm, faces=bm.faces[:])

        bm.verts.ensure_lookup_table()
        bm.verts.index_update()

        # Set SkinPLG
        skin = self.init_skin_plg(obj, mesh)

        has_prelit_colors = len(mesh.vertex_colors) > 0
        has_night_colors  = len(mesh.vertex_colors) > 1

        # These are used to set the vertex indices for new vertices
        # created in the next loop to get rid of shared vertices.
        override_faces = {}
        
        # Vertices and Normals
        i = 0
        length = len(bm.verts)
        while i < len(bm.verts):
            vertex = bm.verts[i]
            
            geometry.vertices.append(dff.Vector._make(vertex.co))
            geometry.normals.append(dff.Vector._make(vertex.normal))

            # These are already filtered vertices, no need to check them again
            if i >= length:
                i += 1
                continue
            
            shared_loops = self.get_vertex_shared_loops(
                vertex,
                [
                    bm.loops.layers.uv.values(),
                    bm.loops.layers.color.values()
                ],
                [
                    lambda a, b: a.uv != b.uv,
                    lambda a, b: a != b
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

        # Allocate uv layers/vertex colors array
        uv_layers_count = len(bm.loops.layers.uv)
        geometry.uv_layers = [[dff.TexCoords(0,0)] * len(bm.verts)
                              for i in range(uv_layers_count)]
        extra_vert = None
        if has_prelit_colors:
            geometry.prelit_colors = [dff.RGBA(255,255,255,255)] * len(bm.verts)

            if has_night_colors:
                extra_vert = dff.ExtraVertColorExtension(
                    [dff.RGBA(255,255,255,255)] * len(bm.verts)
                )
            
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
                if has_prelit_colors:
                    for index, layer in enumerate(bm.loops.layers.color.values()):
                        color = list(loop[layer])
                        if len(color) < 4:
                            color.append(1)
                        
                        prelit_color = dff.RGBA._make(
                            int(c * 255) for c in color
                        )
                        if index == 0:
                            geometry.prelit_colors[verts[loop.index]] = prelit_color
                            
                        elif index == 1:
                            extra_vert.colors[verts[loop.index]] = prelit_color
                            break # upto 2 vertex colors
                
        self.create_frame(obj)

        # Custom Split Normals
        mesh.calc_normals_split()

        for loop in mesh.loops:
            geometry.normals[loop.vertex_index] = loop.normal
        
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
        if extra_vert:
            geometry.extensions['extra_vert_color'] = extra_vert
            
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
    def check_armature_parent(obj):

        # This function iterates through all modifiers of the parent's modifier,
        # and check if its parent has an armature modifier set to obj.
        
        for modifier in obj.parent.modifiers:
            if modifier.type == 'ARMATURE':
                if modifier.object == obj:
                    return True

        return False
    
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

            # Set collision
            if 'gta_coll' in obj:
                if len(obj['gta_coll']) > 0:
                    self.dff.collisions = obj['gta_coll']
                
        if name is None:
            self.dff.write_file(self.file_name, self.version )
        else:
            self.dff.write_file("%s/%s" % (self.path, name), self.version)

    #######################################################
    def is_selected(obj):
        if bpy.app.version < (2, 80, 0):
            return obj.select
        return obj.select_get()
            
    #######################################################
    def export_dff(filename):
        self = dff_exporter

        self.file_name = filename
        
        objects = {}

        # TODO: 2.79 -> Support Mass Export
        
        # Export collections
        if bpy.app.version < (2, 80, 0):
            collections = [bpy.data]

        else:
            root_collection = bpy.context.scene.collection
            collections = root_collection.children.values() + [root_collection]
            
        for collection in collections:
            for obj in collection.objects:
                    
                if not self.selected or obj.select_get():
                    objects[obj] = self.calculate_parent_depth(obj)

            if self.mass_export:
                objects = sorted(objects, key=objects.get)
                self.export_objects(objects,
                                    collection.name)
                objects     = {}
                self.frames = {}
                self.bones  = {}

        if not self.mass_export:
                
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

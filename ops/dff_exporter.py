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

from bpy_extras import anim_utils

from .exporter_common import (
    clear_extension, extract_texture_info_from_name)
from .col_exporter import export_col

from ..gtaLib import dff
from ..ops.ext_2dfx_exporter import ext_2dfx_exporter
from ..ops.state import State

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
        texture.filters = int(self.material.dff.tex_filters)
        texture.uv_addressing = int(self.material.dff.tex_u_addr) << 4 | int(self.material.dff.tex_v_addr)

        # 2.8
        if self.principled:
            if self.principled.base_color_texture.image is not None:

                node_label = self.principled.base_color_texture.node_image.label
                image_name = self.principled.base_color_texture.image.name

                # Use node label if it is a substring of image name, else
                # use image name
                if node_label in image_name and node_label != "":
                    image_name = node_label

                texture_name, _ = extract_texture_info_from_name(image_name)
                texture.name = clear_extension(texture_name)
                return texture
            return None

        # Blender Internal
        try:
            image_name = self.material.texture_slots[0].texture.image.name
            texture_name, _ = extract_texture_info_from_name(image_name)
            texture.name = clear_extension(texture_name)
            return texture

        except BaseException:
            return None

    #######################################################
    def get_surface_properties(self):

        ambient  = self.material.dff.ambient
        specular = self.material.dff.specular
        diffuse  = self.material.dff.diffuse

        return dff.GeomSurfPro(ambient, specular, diffuse)

    #######################################################
    def get_bump_map(self):

        bump_texture = None
        height_texture = None

        if not self.material.dff.export_bump_map:
            return None

        bump_texture_name = self.material.dff.bump_map_tex
        intensity = self.material.dff.bump_map_intensity
        bump_dif_alpha = self.material.dff.bump_dif_alpha

        base_color_texture = None
        if bump_dif_alpha:
            base_color_texture = self.get_texture()

        # Create bump texture (may have empty name when use diffuse alpha is set)
        bump_texture = dff.Texture()
        bump_texture.name = bump_texture_name
        
        # If diffuse alpha is checked use material texture as heightmap
        if bump_dif_alpha and base_color_texture:
            height_texture = dff.Texture()
            height_texture.name = base_color_texture.name
        
        return dff.BumpMapFX(intensity, height_texture, bump_texture)

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
    def get_dual_texture(self):

        if not self.material.dff.export_dual_tex:
            return None

        texture_name = self.material.dff.dual_tex
        src_blend    = int(self.material.dff.dual_src_blend)
        dst_blend    = int(self.material.dff.dual_dst_blend)

        texture = dff.Texture()
        texture.name = texture_name
        texture.filters = 0
        
        return dff.DualFX(src_blend, dst_blend, texture)

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
    def get_user_data(self):

        if 'dff_user_data' not in self.material:
            return None
        
        return dff.UserData.from_mem(
                self.material['dff_user_data'])
    
    #######################################################
    def get_uv_animation(self):

        # See if export_animation checkbox is checked
        if not self.material.dff.export_animation:
            return None

        # Check if mapping nodes exist
        if not self.principled or not self.principled.base_color_texture.has_mapping_node():
            return None

        # Check if animation data exists
        anim_data = self.material.node_tree.animation_data
        if not anim_data:
            return None

        # Check if action exists
        action = anim_data.action
        if not action:
            return None

        if bpy.app.version < (4, 4, 0):
            action_fcurves = action.fcurves

        else:
            # Check if action slot exists
            action_slot = anim_data.action_slot
            if not action_slot:
                return None

            channelbag = anim_utils.action_get_channelbag_for_slot(action, action_slot)
            action_fcurves = channelbag.fcurves

        fps = bpy.context.scene.render.fps

        mapping = self.principled.base_color_texture.node_mapping_get()
        data_path_offset = {
            f'nodes["{mapping.name}"].inputs[2].default_value': 0,  # rot z
            f'nodes["{mapping.name}"].inputs[3].default_value': 1,  # scale x/y
            f'nodes["{mapping.name}"].inputs[1].default_value': 4,  # pos x/y
        }

        all_times = set()
        keyframe_data = {}

        for curve in action_fcurves:
            if curve.data_path not in data_path_offset:
                continue

            offset = data_path_offset[curve.data_path]
            if offset == 0 and curve.array_index != 2:
                continue

            if curve.array_index > 1:
                continue

            for keyframe in curve.keyframe_points:
                time = keyframe.co[0] / fps
                all_times.add(time)
                interp = keyframe.interpolation

                if time not in keyframe_data or interp == 'CONSTANT':
                    keyframe_data[time] = interp

        if not all_times:
            return None

        sorted_times = sorted(all_times)
        time_offset = sorted_times[0]
        shifted_times = [t - time_offset for t in sorted_times]

        def get_uv_at(time):
            frame = time * fps
            uv = [0.0, 1.0, 1.0, 0.0, 0.0, 0.0]
            for curve in action_fcurves:
                if curve.data_path not in data_path_offset:
                    continue

                offset = data_path_offset[curve.data_path]

                if offset == 0 and curve.array_index != 2:
                    continue

                if curve.array_index > 1:
                    continue

                idx = offset + curve.array_index if offset != 0 else 0
                uv[idx] = curve.evaluate(frame)
            return uv

        time_values = {}

        for i, shifted_t in enumerate(shifted_times):
            original_t = sorted_times[i]
            time_values[shifted_t] = get_uv_at(original_t)

        interp_data = {}

        for i, shifted_t in enumerate(shifted_times):
            original_t = sorted_times[i]
            interp = keyframe_data.get(original_t, 'LINEAR')
            interp_data[shifted_t] = 'CONSTANT' if interp == 'CONSTANT' else 'LINEAR'

        anim = dff.UVAnim()
        anim.name = self.material.dff.animation_name
        uv_0 = time_values[0]
        flipped_0 = [uv_0[0], uv_0[1], uv_0[2], 0.0, uv_0[4], 1 - (uv_0[5] + uv_0[2])]
        anim.frames.append(dff.UVFrame(0.0, flipped_0, -1))
        prev_idx = 0

        for i in range(len(shifted_times) - 1):
            next_t = shifted_times[i + 1]
            interp = interp_data[shifted_times[i]]
            prev_uv = anim.frames[-1].uv
            current_uv = time_values[next_t]
            flipped_current = [current_uv[0], current_uv[1], current_uv[2], 0.0, current_uv[4], 1 - (current_uv[5] + current_uv[2])]

            if interp == 'CONSTANT':
                anim.frames.append(dff.UVFrame(next_t, list(prev_uv), prev_idx))
                prev_idx = len(anim.frames) - 1
                anim.frames.append(dff.UVFrame(next_t, flipped_current, prev_idx))
                prev_idx = len(anim.frames) - 1
            else:
                anim.frames.append(dff.UVFrame(next_t, flipped_current, prev_idx))
                prev_idx = len(anim.frames) - 1

        if anim.frames:
            anim.duration = shifted_times[-1]

        is_fully_constant = len(shifted_times) >= 2 and all(v == 'CONSTANT' for v in interp_data.values())

        if is_fully_constant:
            num_intervals = len(shifted_times) - 1
            mean_delta = shifted_times[-1] / num_intervals
            extra_t = shifted_times[-1] + mean_delta
            last_uv = anim.frames[-1].uv
            anim.frames.append(dff.UVFrame(extra_t, list(last_uv), prev_idx))
            anim.duration = extra_t

        return anim

    #######################################################
    def __init__(self, material):
        self.material = material
        self.principled = None

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

class DffExportException(Exception):
    pass

#######################################################
class dff_exporter:

    selected = False
    mass_export = False
    preserve_positions = True
    preserve_rotations = True
    file_name = ""
    dff = None
    version = None
    frame_objects = {}
    collection = None
    export_coll = False
    coll_ext_type = 0
    apply_coll_trans = True
    exclude_geo_faces = False
    from_outliner = False

    #######################################################
    @staticmethod
    def multiply_matrix(a, b):
        return a @ b

    #######################################################
    @staticmethod
    def get_object_parent(obj):
        if type(obj) is bpy.types.Object and obj.parent_bone:
            parent = obj.parent.data.bones.get(obj.parent_bone)
            if parent:
                return parent

        return obj.parent

    #######################################################
    @staticmethod
    def create_frame(obj, append=True, set_parent=True, matrix_local=None):
        self = dff_exporter

        frame       = dff.Frame()
        frame_index = len(self.dff.frame_list)

        # Is obj a bone?
        is_bone = type(obj) is bpy.types.Bone

        # Get rid of everything before the last period
        if self.export_frame_names:
            if is_bone or obj.dff.export_frame_name:
                frame.name = clear_extension(obj.name)

        matrix = matrix_local or obj.matrix_local
        if is_bone and obj.parent is not None:
            matrix = self.multiply_matrix(obj.parent.matrix_local.inverted(), matrix)

        parent = self.get_object_parent(obj)

        if is_bone or parent:
            position = matrix.to_translation()
            rotation_matrix = matrix.to_3x3().transposed()
        else:
            if self.preserve_positions:
                position = matrix.to_translation()
            else:
                position = (0, 0, 0)

            if self.preserve_rotations:
                rotation_matrix = matrix.to_3x3().transposed()
            else:
                rotation_matrix = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))

        frame.creation_flags  =  0
        frame.parent          = -1
        frame.position        = position
        frame.rotation_matrix = dff.Matrix._make(rotation_matrix)

        if "dff_user_data" in obj:
            frame.user_data = dff.UserData.from_mem(obj["dff_user_data"])

        if set_parent and parent is not None:

            if parent not in self.frame_objects:
                raise DffExportException(f"Failed to set parent for {obj.name} "
                                         f"to {parent.name}.")

            parent_frame_idx = self.frame_objects[parent]
            frame.parent = parent_frame_idx

        if append:
            self.dff.frame_list.append(frame)

        self.frame_objects[obj] = frame_index
        return frame

    #######################################################
    @staticmethod
    def get_last_frame_index():
        return len(dff_exporter.dff.frame_list) - 1

    #######################################################
    @staticmethod
    def generate_material_list(obj):
        materials = []
        self = dff_exporter

        for b_material in obj.data.materials:

            if b_material is None:
                continue
            
            material = dff.Material()
            helper = material_helper(b_material)

            material.color             = helper.get_base_color()
            material.surface_properties = helper.get_surface_properties()
            
            texture = helper.get_texture()
            if texture:
                material.textures.append(texture)

            # Materials
            material.add_plugin('bump_map', helper.get_bump_map())
            material.add_plugin('env_map', helper.get_environment_map())
            material.add_plugin('dual', helper.get_dual_texture())
            material.add_plugin('spec', helper.get_specular_material())
            material.add_plugin('refl', helper.get_reflection_material())
            material.add_plugin('udata', helper.get_user_data())

            anim = helper.get_uv_animation()
            if anim:
                material.add_plugin('uv_anim', anim.name)
                self.dff.uvanim_dict.append(anim)

            # Create a dummy uv anim to apply to the second uv channel to force dual pass blending
            if b_material.dff.force_dual_pass and b_material.dff.export_dual_tex and b_material.dff.dual_tex:
                dummy_anim = dff.UVAnim()
                dummy_anim.name = "DragonFF"
                dummy_anim.node_to_uv[0] = 1
                dummy_anim.duration = 1.0
                dummy_anim.frames = [
                    dff.UVFrame(0.0, [0.0, 1.0, 1.0, 0.0, 0.0, 0.0], -1),
                    dff.UVFrame(1.0, [0.0, 1.0, 1.0, 0.0, 0.0, 0.0],  0)
                ]

                material.add_plugin('uv_anim', dummy_anim.name)
                self.dff.uvanim_dict.append(dummy_anim)

            materials.append(material)
                
        return materials

    #######################################################
    @staticmethod
    def get_skin_plg_and_bone_groups(obj, mesh):

        # Returns a SkinPLG object if the object has an armature modifier
        armature = None
        for modifier in obj.modifiers:
            if modifier.type == 'ARMATURE':
                armature = modifier.object
                break
            
        if armature is None:
            return (None, {})
        
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
            
        return (skin, bone_groups)

    #######################################################
    @staticmethod
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
    @staticmethod
    def get_delta_morph_entries(obj, shape_keys):
        dm_entries = []
        self = dff_exporter

        if shape_keys and len(shape_keys.key_blocks) > 1:
            for kb in shape_keys.key_blocks[1:]:
                min_corner = mathutils.Vector(min(v.co[i] for v in kb.data) for i in range(3))
                max_corner = mathutils.Vector(max(v.co[i] for v in kb.data) for i in range(3))
                dimensions = mathutils.Vector(max_corner[i] - min_corner[i] for i in range(3))

                sphere_center = 0.5 * (min_corner + max_corner)
                sphere_center = self.multiply_matrix(obj.matrix_world, sphere_center)
                sphere_radius = 1.732 * max(*dimensions) / 2

                entrie = dff.DeltaMorph()
                entrie.name = kb.name
                entrie.bounding_sphere = dff.Sphere._make(
                    list(sphere_center) + [sphere_radius]
                )

                dm_entries.append(entrie)

        return dm_entries

    #######################################################
    @staticmethod
    def triangulate_mesh(mesh, preserve_loop_normals):
        loop_normals = [loop.normal.copy() for loop in mesh.loops] if preserve_loop_normals else []

        # Check that the mesh is already triangulated
        if all(len(polygon.vertices) == 3 for polygon in mesh.polygons):
            return loop_normals

        bm = bmesh.new()
        bm.from_mesh(mesh)

        if preserve_loop_normals:
            face_verts_to_loop_idx_map = {}
            loop_idx = 0
            for face in bm.faces:
                vert_to_loop_idx = {}
                for vert in face.verts:
                    vert_to_loop_idx[vert] = loop_idx
                    loop_idx += 1
                face_verts_to_loop_idx_map[face] = vert_to_loop_idx

        face_map = bmesh.ops.triangulate(bm, faces=bm.faces)['face_map']

        if preserve_loop_normals:
            normals = []
            for face in bm.faces:
                face_orig = face_map.get(face, face)
                vert_to_loop_idx = face_verts_to_loop_idx_map[face_orig]
                for vert in face.verts:
                    normals.append(loop_normals[vert_to_loop_idx[vert]])
            loop_normals = normals

        bm.to_mesh(mesh)
        bm.free()

        return loop_normals

    #######################################################
    @staticmethod
    def find_vert_idx_by_tmp_idx(verts, idx):
        for i, vert in enumerate(verts):
            if vert['tmp_idx'] == idx:
                return i

    #######################################################
    @staticmethod
    def populate_geometry_from_vertices_data(vertices_list, skin_plg, dm_entries,
                                             obj, geometry, num_vcols):

        has_prelit_colors = num_vcols > 0 and obj.dff.day_cols
        has_night_colors  = num_vcols > 1 and obj.dff.night_cols

        # This number denotes what the maximum number of uv maps exported will be.
        # If obj.dff.uv_map2 is set (i.e second UV map WILL be exported), the
        # maximum will be 2. If obj.dff.uv_map1 is NOT set, the maximum cannot
        # be greater than 0.
        max_uv_layers = (obj.dff.uv_map2 + 1) * obj.dff.uv_map1

        extra_vert = None
        if has_night_colors:
            extra_vert = dff.ExtraVertColorExtension([])

        delta_morph_plg = None
        if dm_entries:
            delta_morph_plg = dff.DeltaMorphPLG()
            for entrie in dm_entries:
                delta_morph_plg.append_entry(entrie)
           
        for idx, vertex in enumerate(vertices_list):
            geometry.vertices.append(dff.Vector._make(vertex['co']))
            geometry.normals.append(dff.Vector._make(vertex['normal']))

            # vcols
            #######################################################
            if has_prelit_colors:
                geometry.prelit_colors.append(dff.RGBA._make(
                    int(col * 255) for col in vertex['vert_cols'][0]))
            if has_night_colors:
                extra_vert.colors.append(dff.RGBA._make(
                    int(col * 255) for col in vertex['vert_cols'][1]))

            # uv layers
            #######################################################
            for index, uv in enumerate(vertex['uvs']):
                if index >= max_uv_layers:
                    break

                while index >= len(geometry.uv_layers):
                    geometry.uv_layers.append([])

                geometry.uv_layers[index].append(dff.TexCoords(uv.x, 1-uv.y))

            # bones
            #######################################################
            if skin_plg is not None:
                skin_plg.vertex_bone_indices.append([0,0,0,0])
                skin_plg.vertex_bone_weights.append([0,0,0,0])

                for index, bone in enumerate(vertex['bones']):
                    skin_plg.vertex_bone_indices[-1][index] = bone[0]
                    skin_plg.vertex_bone_weights[-1][index] = bone[1]

            # delta_morph
            #######################################################
            if delta_morph_plg is not None:
                sk_cos = vertex['sk_cos']
                for index, co in enumerate(sk_cos[1:]):
                    pos = mathutils.Vector(co) - mathutils.Vector(sk_cos[0])
                    if pos.length == 0.0:
                        continue

                    entrie = dm_entries[index]
                    entrie.indices.append(idx)
                    entrie.positions.append(pos)

        if skin_plg is not None:
            geometry.extensions['skin'] = skin_plg
        if extra_vert:
            geometry.extensions['extra_vert_color'] = extra_vert
        if delta_morph_plg is not None:
            geometry.extensions['delta_morph'] = delta_morph_plg

    #######################################################
    @staticmethod
    def populate_geometry_from_faces_data(faces_list, geometry):
        triangles = [
            dff.Triangle._make((
                verts[1], #b
                verts[0], #a
                face['mat_idx'], #material
                verts[2] #c
            ))
            for face in faces_list
            for verts in [face['verts']]
        ]
        geometry.triangles.extend(triangles)
        geometry.triangles.sort(key=lambda triangle: triangle.material)

    #######################################################
    @staticmethod
    def convert_slinear_to_srgb (col):
        color = mathutils.Color (col[:3])
        color_srgb = color.from_scene_linear_to_srgb()
        return tuple(max(0, min(1, channel)) for channel in color_srgb) + (col[3],)  # Including alpha unchanged

    #######################################################
    @staticmethod
    def get_vertex_colors(mesh : bpy.types.Mesh):
        self = dff_exporter

        v_cols = []

        if bpy.app.version < (3, 2, 0):
            for layer in mesh.vertex_colors:
                v_cols.append([list(i.color) for i in layer.data])
            return v_cols

        for attrib in mesh.color_attributes[:2]:
            # Already per loop
            if attrib.domain == 'CORNER':
                v_cols.append(
                    [
                        list(self.convert_slinear_to_srgb(i.color))
                        for i in attrib.data
                    ]
                )

            # Per-vertex, need to convert to per-loop
            else:
                colors = {}
                for polygon in mesh.polygons:
                    for v_ix, l_ix in zip(polygon.vertices, polygon.loop_indices):
                        colors[l_ix] = self.convert_slinear_to_srgb(
                            list(attrib.data[v_ix].color))
                v_cols.append(colors)

        return v_cols

    #######################################################
    @staticmethod
    def populate_geometry_with_mesh_data(obj, geometry):
        self = dff_exporter

        mesh, shape_keys = self.convert_to_mesh(obj)

        use_loop_normals = obj.dff.export_split_normals
        if use_loop_normals:
            normals = self.triangulate_mesh(mesh, True)
        else:
            normals = [vert.normal.copy() for vert in mesh.vertices]
            self.triangulate_mesh(mesh, False)

        # NOTE: Mesh.calc_normals is no longer needed and has been removed
        if bpy.app.version < (4, 0, 0):
            mesh.calc_normals()

        # NOTE: Mesh.calc_normals_split is no longer needed and has been removed
        if bpy.app.version < (4, 1, 0):
            mesh.calc_normals_split()

        vcols = self.get_vertex_colors (mesh)
        verts_indices = {}
        vertices_list = []
        faces_list = []

        skin_plg, bone_groups = self.get_skin_plg_and_bone_groups(obj, mesh)
        dm_entries = self.get_delta_morph_entries(obj, shape_keys)

        # Check for vertices once before exporting to report instanstly
        if not self.exclude_geo_faces and len(mesh.vertices) > 0xFFFF:
            raise DffExportException(f"Too many vertices in mesh ({obj.name}): {len(mesh.vertices)}/65535")

        for polygon in mesh.polygons:
            face = {"verts": [], "mat_idx": polygon.material_index}

            for loop_index in polygon.loop_indices:
                loop = mesh.loops[loop_index]
                vert_index = loop.vertex_index
                vertex = mesh.vertices[vert_index]
                uvs = []
                vert_cols = []
                bones = []
                sk_cos = []

                for uv_layer in mesh.uv_layers:
                    uvs.append(uv_layer.data[loop_index].uv)

                for vert_col in vcols:
                    vert_cols.append(vert_col[loop_index])

                for group in vertex.groups:
                    # Only upto 4 vertices per group are supported
                    if len(bones) >= 4:
                        break

                    if group.group in bone_groups and group.weight > 0:
                        bones.append((bone_groups[group.group], group.weight))

                if shape_keys:
                    for kb in shape_keys.key_blocks:
                        sk_cos.append(kb.data[vert_index].co)

                normal = normals[loop_index if use_loop_normals else vert_index]

                key = (vert_index,
                       tuple(normal),
                       tuple(tuple(uv) for uv in uvs))

                if key not in verts_indices:
                    face['verts'].append (len(vertices_list))
                    verts_indices[key] = len(vertices_list)
                    vertices_list.append({"idx": vert_index,
                                          "co": vertex.co,
                                          "normal": normal,
                                          "uvs": uvs,
                                          "vert_cols": vert_cols,
                                          "bones": bones,
                                          "sk_cos": sk_cos})
                else:
                    face['verts'].append(verts_indices[key])

            faces_list.append(face)

        # Check vertices count again since duplicate vertices may have increased
        # vertices count above the limit
        if not self.exclude_geo_faces and len(vertices_list) > 0xFFFF:
            raise DffExportException(f"Too many vertices in mesh ({obj.name}): {len(vertices_list)}/65535")

        self.populate_geometry_from_vertices_data(
            vertices_list, skin_plg, dm_entries, obj, geometry, len(vcols))

        self.populate_geometry_from_faces_data(faces_list, geometry)

    #######################################################
    @staticmethod
    def populate_geometry_with_breakable_object(obj, geometry):
        self = dff_exporter

        breakable_model = dff.ExtensionBreakable()
        geometry.extensions["breakable_model"] = breakable_model

        if not obj or obj.type != 'MESH':
            breakable_model.magic = 0
            return

        breakable_model.magic = 0x64646464
        breakable_model.pos_rule = int(obj.dff.breakable_pos_rule)

        mesh, _ = self.convert_to_mesh(obj)
        self.triangulate_mesh(mesh, False)

        vcols = self.get_vertex_colors(mesh)
        verts_indices = {}
        vertices_list = []
        faces_list = []

        # Check for vertices once before exporting to report instanstly
        if len(mesh.vertices) > 0xFFFF:
            raise DffExportException(f"Too many vertices in mesh ({obj.name}): {len(mesh.vertices)}/65535")

        for polygon in mesh.polygons:
            face = {"verts": [], "mat_idx": polygon.material_index}

            for loop_index in polygon.loop_indices:
                loop = mesh.loops[loop_index]
                vert_index = loop.vertex_index
                vertex = mesh.vertices[vert_index]

                if mesh.uv_layers:
                    uv = mesh.uv_layers[0].data[loop_index].uv
                    uv = (uv.x, uv.y)
                else:
                    uv = (0.0, 1.0)

                if vcols:
                    vert_col = vcols[0][loop_index]
                else:
                    vert_col = (1.0, 1.0, 1.0)

                key = (vert_index, uv)

                if key not in verts_indices:
                    face['verts'].append(len(vertices_list))
                    verts_indices[key] = len(vertices_list)
                    vertices_list.append({"idx": vert_index,
                                          "co": vertex.co,
                                          "uv": uv,
                                          "vert_col": vert_col})
                else:
                    face['verts'].append(verts_indices[key])

            faces_list.append(face)

        # Check vertices count again since duplicate vertices may have increased
        # vertices count above the limit
        if not self.exclude_geo_faces and len(vertices_list) > 0xFFFF:
            raise DffExportException(f"Too many vertices in mesh ({obj.name}): {len(vertices_list)}/65535")

        for vertex in vertices_list:
            breakable_model.positions.append(dff.Vector._make(vertex['co']))

            uv = vertex['uv']
            breakable_model.uvs.append(dff.TexCoords(uv[0], 1-uv[1]))

            vert_col = vertex['vert_col']
            breakable_model.prelits.append(dff.RGBA._make(
                int(col * 255) for col in vert_col))

        triangles = [
            dff.Triangle._make((
                verts[1], #b
                verts[0], #a
                face['mat_idx'], #material
                verts[2] #c
            ))
            for face in faces_list
            for verts in [face['verts']]
        ]
        breakable_model.triangles.extend(triangles)
        breakable_model.triangles.sort(key=lambda triangle: triangle.material)

        for mat_slot in obj.material_slots:
            texture_name = ""
            mask_name = ""
            ambient_color = (1, 1, 1)

            if mat_slot.material:
                helper = material_helper(mat_slot.material)

                # Set texture name
                texture = helper.get_texture()
                if texture:
                    texture_name = texture.name

                # Set ambient color
                if helper.principled:
                    ambient_color = helper.principled.base_color[:3]

            breakable_model.texture_names.append(texture_name)
            breakable_model.texture_masks.append(mask_name)
            breakable_model.ambient_colors.append(dff.Vector._make(ambient_color))

    #######################################################
    @staticmethod
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

        # Temporarily reset key shape values
        key_shape_values = {}
        if obj.data.shape_keys:
            for kb in obj.data.shape_keys.key_blocks:
                key_shape_values[kb] = kb.value
                kb.value = 0.0

        depsgraph   = bpy.context.evaluated_depsgraph_get()
        object_eval = obj.evaluated_get(depsgraph)
        mesh        = object_eval.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
            

        # Re enable disabled modifiers
        for modifier in disabled_modifiers:
            modifier.show_viewport = True

        # Restore key shape values
        for kb, v in key_shape_values.items():
            kb.value = v

        # Modifiers cannot be applied with shape keys
        if object_eval.data.shape_keys:
            vertices_num = len(mesh.vertices)
            for kb in object_eval.data.shape_keys.key_blocks:
                if vertices_num != len(kb.data):
                    raise DffExportException(f"Modifier cannot be applied to a mesh with shape keys ({obj.name})")

        return mesh, object_eval.data.shape_keys

    #######################################################
    def populate_atomic(obj, frame_index=None):
        self = dff_exporter

        # Get frame index from parent
        if frame_index is None:
            parent = self.get_object_parent(obj)
            if parent:
                frame_index = self.frame_objects.get(parent)

        # Get frame index from armature modifier
        if frame_index is None:
            for modifier in obj.modifiers:
                if modifier.type == 'ARMATURE':
                    frame_index = self.frame_objects.get(modifier.object)
                    if frame_index is not None:
                        break

        # Create new frame if there is no parent
        if frame_index is None:
            self.create_frame(obj, set_parent=False)
            frame_index = self.get_last_frame_index()

        # Create geometry
        geometry = dff.Geometry()
        self.populate_geometry_with_mesh_data (obj, geometry)

        # Bounding sphere
        sphere_center = 0.125 * sum(
            (mathutils.Vector(b) for b in obj.bound_box),
            mathutils.Vector()
        )
        sphere_center = self.multiply_matrix(obj.matrix_world, sphere_center)
        sphere_radius = 1.732 * max(*obj.dimensions) / 2

        geometry.bounding_sphere = dff.Sphere._make(
            list(sphere_center) + [sphere_radius]
        )

        geometry.surface_properties = (0,0,0)
        geometry.materials = self.generate_material_list(obj)

        # Add Breakable Extension
        if obj.dff.export_breakable:
            self.populate_geometry_with_breakable_object(obj.dff.breakable_object, geometry)

        geometry.export_flags['export_normals'] = obj.dff.export_normals
        geometry.export_flags['write_mesh_plg'] = obj.dff.export_binsplit
        geometry.export_flags['light'] = obj.dff.light
        geometry.export_flags['modulate_color'] = obj.dff.modulate_color
        geometry.export_flags['triangle_strip'] = obj.dff.triangle_strip
        geometry.export_flags['exclude_geo_faces'] = self.exclude_geo_faces
        
        if "dff_user_data" in obj.data:
            geometry.extensions['user_data'] = dff.UserData.from_mem(
                obj.data['dff_user_data'])

        # Add Geometry to list
        self.dff.geometry_list.append(geometry)

        # Create Atomic from geometry and frame
        atomic          = dff.Atomic()
        atomic.frame    = frame_index
        atomic.geometry = len(self.dff.geometry_list) - 1
        atomic.flags    = 0x4

        try:
            if obj.dff.pipeline != 'NONE':
                if obj.dff.pipeline == 'CUSTOM':
                    atomic.extensions['pipeline'] = int(obj.dff.custom_pipeline, 0)
                else:
                    atomic.extensions['pipeline'] = int(obj.dff.pipeline, 0)

        except ValueError:
            print("Invalid (Custom) Pipeline")

        if "skin" in geometry.extensions:
            right_to_render = dff.RightToRender._make((0x0116,
                obj.dff.right_to_render
            ))
            atomic.extensions['right_to_render'] = right_to_render

        if obj.dff.sky_gfx:
            atomic.extensions['sky_gfx'] = 1

        self.dff.atomic_list.append(atomic)

    #######################################################
    @staticmethod
    def check_armature_parent(obj):

        # This function iterates through all modifiers of the parent's modifier,
        # and check if its parent has an armature modifier set to obj.
        
        for modifier in obj.parent.modifiers:
            if modifier.type == 'ARMATURE':
                if modifier.object == obj:
                    return True

        return False

    #######################################################
    @staticmethod
    def validate_bone_for_export (obj, bone):
        if "bone_id" not in bone or "type" not in bone:
            raise DffExportException(f"Bone ID/Type not found in bone ({bone.name}) "
                                     f"in armature ({obj.name}). Please ensure "
                                     "you're using an armature imported from an "
                                     "existing DFF file")

    #######################################################
    @staticmethod
    def export_armature(obj):
        self = dff_exporter
        
        for index, bone in enumerate(obj.data.bones):

            self.validate_bone_for_export (obj, bone)

            # Create a special bone (contains information for all subsequent bones)
            if index == 0:

                # set the first bone's parent to armature's parent
                if obj.parent and obj.parent in self.frame_objects:
                    frame_parent = self.frame_objects[obj.parent]
                else:
                    self.create_frame(obj)
                    frame_parent = self.get_last_frame_index()

                frame = self.create_frame(bone, False)
                frame.parent = frame_parent

                bone_data = dff.HAnimPLG()
                bone_data.header = dff.HAnimHeader(
                    0x100,
                    bone["bone_id"],
                    len(obj.data.bones)
                )
                
                # Make bone array in the root bone
                for _index, _bone in enumerate(obj.data.bones):
                    self.validate_bone_for_export (obj, _bone)

                    bone_data.bones.append(
                        dff.Bone(
                                _bone["bone_id"],
                                _index,
                                _bone["type"])
                    )

                frame.bone_data = bone_data
                self.dff.frame_list.append(frame)
                self.frame_objects[obj] = self.get_last_frame_index()
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
            self.frame_objects[bone] = self.get_last_frame_index()

    #######################################################
    @staticmethod
    def export_empty(obj):
        self = dff_exporter

        parent = self.get_object_parent(obj)
        set_parent = False
        matrix_local = None

        if parent in self.frame_objects:
            set_parent = True
            if obj.parent_type == "BONE":
                matrix_local = obj.matrix_basis

        # Create new frame
        self.create_frame(obj, set_parent=set_parent, matrix_local=matrix_local)

    #######################################################
    @staticmethod
    def export_objects(objects, name=None):
        self = dff_exporter

        self.dff = dff.dff()

        # Skip empty collections
        if len(objects) < 1:
            return

        atomics_data = []

        for obj in objects:

            # We can just ignore collision meshes here as the DFF exporter will still look for
            # them in their own nested collection later if export_coll is true.
            if obj.dff.type != 'OBJ':
                continue

            # create atomic in this case
            if obj.type == "MESH":
                frame_index = None
                # create an empty frame
                if obj.dff.is_frame:
                    self.export_empty(obj)
                    frame_index = self.get_last_frame_index()
                atomics_data.append((obj, frame_index))

            # create an empty frame
            elif obj.type == "EMPTY":
                self.export_empty(obj)

            elif obj.type == "ARMATURE":
                self.export_armature(obj)

        atomics_data = sorted(atomics_data, key=lambda a: a[0].dff.atomic_index)

        for mesh, frame_index in atomics_data:
            self.populate_atomic(mesh, frame_index)

        # 2DFX
        ext_2dfx_exporter(self.dff.ext_2dfx).export_objects(objects, not self.preserve_positions)

        # Collision
        if self.export_coll:
            mem = export_col({
                'file_name'             : None,
                'version'               : 3,
                'collection'            : self.collection,
                'apply_transformations' : self.apply_coll_trans,
                'only_selected'         : self.selected
            })

            if len(mem) != 0:
                col = dff.ExtensionColl(self.coll_ext_type, mem)
                self.dff.collisions = [col]

        if name is None:
            self.dff.write_file(self.file_name, self.version )
        else:
            filename = "%s/%s" % (self.path, name)
            if not filename.endswith('.dff'):
                filename += '.dff'
            self.dff.write_file(filename, self.version)

    #######################################################
    @staticmethod
    def is_selected(obj):
        return obj.select_get()
            
    #######################################################
    @staticmethod
    def export_dff(filename):
        self = dff_exporter

        self.file_name = filename
        self.frame_objects = {}

        State.update_scene()
        objects = {}

        # Export collections
        if self.from_outliner:
            collections = [bpy.context.view_layer.objects.active.users_collection[0]]
        else:
            collections = [c for c in bpy.data.collections if c.dff.type != 'NON'] + [bpy.context.scene.collection]

        for collection in collections:
            for obj in collection.objects:
                    
                if not self.selected or obj.select_get():
                    objects[obj] = obj.dff.frame_index

            if self.mass_export:
                objects = sorted(objects, key=objects.get)
                self.export_objects(objects,
                                    collection.name)
                objects            = {}
                self.frame_objects = {}
                self.collection = collection

        if not self.mass_export:
            if self.from_outliner:
                self.collection = collections[0]

            objects = sorted(objects, key=objects.get)
            self.export_objects(objects)
                
#######################################################
def export_dff(options):

    # Shadow Function
    dff_exporter.selected           = options['selected']
    dff_exporter.export_frame_names = options['export_frame_names']
    dff_exporter.exclude_geo_faces  = options['exclude_geo_faces']
    dff_exporter.mass_export        = options['mass_export']
    dff_exporter.preserve_positions = options['preserve_positions']
    dff_exporter.preserve_rotations = options['preserve_rotations']
    dff_exporter.path               = options['directory']
    dff_exporter.version            = options['version']
    dff_exporter.export_coll        = options['export_coll']
    dff_exporter.coll_ext_type      = options['coll_ext_type']
    dff_exporter.apply_coll_trans   = options['apply_coll_trans']
    dff_exporter.from_outliner      = options['from_outliner']

    dff_exporter.export_dff(options['file_name'])

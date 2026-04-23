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

from ..gtaLib.dff import strlen
from ..gtaLib.data import presets

#######################################################
def set_object_mode(obj, mode):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode=mode, toggle=False)

#######################################################
def link_object(obj, collection):
    collection.objects.link(obj)

#######################################################
def create_collection(name, link=True):
    collection = bpy.data.collections.new(name)
    if link:
        bpy.context.scene.collection.children.link(collection)

    return collection

#######################################################
def hide_object(object, hide=True):
    object.hide_set(hide)

#######################################################
def create_bmesh_for_mesh(mesh, obj_mode):
    if obj_mode == "EDIT":
        bm = bmesh.from_edit_mesh(mesh)
    else:
        bm = bmesh.new()
        bm.from_mesh(mesh)
    return bm

#######################################################
def invert_matrix_safe(matrix):
    if abs(matrix.determinant()) > 1e-8:
        matrix.invert()
    else:
        matrix.identity()

#######################################################
def redraw_viewport():
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()

#######################################################
class material_helper:

    """ Material Helper for Blender 2.7x and Blender 2.8 compatibility"""

    #######################################################
    def set_base_color(self, color):

        if self.principled:
            self.principled.base_color = [i / 255 for i in color[:3]]

            # Set Alpha
            node = self.principled.node_principled_bsdf.inputs["Base Color"]
            node.default_value[3] = color[3] / 255

            self.material.diffuse_color = [i / 255 for i in color]

        else:
            self.material.diffuse_color = [i / 255 for i in color[:3]]
            self.material.alpha = color[3] / 255

        # Set preset material colours
        color_key = tuple(color)
        if color_key in presets.material_colours:
            colours = list(presets.material_colours)
            self.material.dff["preset_mat_cols"] = colours.index(color_key)

    #######################################################
    def set_texture(self, image, label="", filters=0, uv_addressing=0):

        if self.principled:
            self.principled.base_color_texture.node_image.label = label
            self.principled.base_color_texture.image  = image


            # Connect Alpha output to Principled BSDF
            image_node      = self.principled.base_color_texture.node_image
            principled_node = self.principled.node_principled_bsdf
            node_tree       = self.principled.material.node_tree

            node_tree.links.new(image_node.outputs["Alpha"],
                                principled_node.inputs["Alpha"])

        else:
            slot               = self.material.texture_slots.add()
            slot.texture       = bpy.data.textures.new(
                name           = label,
                type           = "IMAGE"
            )
            slot.texture.image = image

        self.material.dff.tex_filters = str(filters)
        self.material.dff.tex_u_addr  = str((uv_addressing >> 4) & 0xF)
        self.material.dff.tex_v_addr  = str(uv_addressing & 0xF)

        if image:
            self.material.dff.tex_name = image.name

    #######################################################
    def set_surface_properties(self, props):

        self.material.dff.diffuse  = props.diffuse
        self.material.dff.specular = props.specular
        self.material.dff.ambient  = props.ambient

    #######################################################
    def set_environment_map(self, plugin):

        if plugin.env_map:
            self.material.dff.env_map_tex      = plugin.env_map.name

        self.material.dff.export_env_map       = True
        self.material.dff.env_map_coef         = plugin.coefficient
        self.material.dff.env_map_fb_alpha     = plugin.use_fb_alpha        

    #######################################################
    def set_dual_texture(self, plugin):

        if plugin.texture:
            self.material.dff.dual_tex         = plugin.texture.name

        self.material.dff.export_dual_tex      = True
        self.material.dff.dual_src_blend       = str(plugin.src_blend)
        self.material.dff.dual_dst_blend       = str(plugin.dst_blend)

    #######################################################
    def set_specular_material(self, plugin):

        self.material.dff.export_specular = True
        self.material.dff.specular_level = plugin.level
        self.material.dff.specular_texture = plugin.texture[:strlen(plugin.texture)].decode('ascii')

        # Set preset specular level
        level_key = round(plugin.level, 2)
        if level_key in presets.material_specular_levels:
            levels = list(presets.material_specular_levels)
            self.material.dff["preset_specular_levels"] = levels.index(level_key)

    #######################################################
    def set_reflection_material(self, plugin):

        self.material.dff.export_reflection = True

        self.material.dff.reflection_scale_x = plugin.s_x
        self.material.dff.reflection_scale_y = plugin.s_y

        self.material.dff.reflection_offset_y = plugin.o_y
        self.material.dff.reflection_offset_x = plugin.o_x

        self.material.dff.reflection_intensity = plugin.intensity

        # Set preset reflection intensities
        intensity_key = round(plugin.intensity, 2)
        if intensity_key in presets.material_reflection_intensities:
            intensities = list(presets.material_reflection_intensities)
            self.material.dff["preset_reflection_intensities"] = intensities.index(intensity_key)

        # Set preset reflection scales
        scale_key = round(plugin.s_x, 2)
        if scale_key in presets.material_reflection_scales:
            scales = list(presets.material_reflection_scales)
            self.material.dff["preset_reflection_scales"] = scales.index(scale_key)

    #######################################################
    def set_uv_animation(self, uv_anim):
        anim_data = self.material.node_tree.animation_data_create()
       
        if self.principled:
            mapping = self.principled.base_color_texture.node_mapping_get()
            mapping.vector_type = 'POINT'
            fps = bpy.context.scene.render.fps
            action = bpy.data.actions.new(uv_anim.name)
            anim_data.action = action
           
            if bpy.app.version < (4, 4, 0):
                action_fcurves = action.fcurves
            else:
                slot = action.slots.new(id_type='NODETREE', name='UV')
                anim_data.action_slot = slot
                layer = action.layers.new('UV')
                strip = layer.strips.new(type='KEYFRAME')
                channelbag = strip.channelbag(slot, ensure=True)
                action_fcurves = channelbag.fcurves
           
            fcurves = [
                action_fcurves.new(data_path=f'nodes["{mapping.name}"].inputs[2].default_value', index=2),
                action_fcurves.new(data_path=f'nodes["{mapping.name}"].inputs[3].default_value', index=0),
                action_fcurves.new(data_path=f'nodes["{mapping.name}"].inputs[3].default_value', index=1),
                None,
                action_fcurves.new(data_path=f'nodes["{mapping.name}"].inputs[1].default_value', index=0),
                action_fcurves.new(data_path=f'nodes["{mapping.name}"].inputs[1].default_value', index=1),
            ]
           
            frames_to_import = uv_anim.frames
            if len(frames_to_import) > 1:
                last = frames_to_import[-1]
                prev = frames_to_import[-2]
                if last.time > prev.time and last.uv == prev.uv:
                    frames_to_import = uv_anim.frames[:-1]
           
            for frame_idx, frame in enumerate(frames_to_import):
                for fc_idx, fc in enumerate(fcurves):
                    if not fc:
                        continue
                   
                    should_add_kp = True
                   
                    if frame_idx > 0 and frame.time == frames_to_import[frame_idx-1].time:
                        if len(fc.keyframe_points) < 2:
                            should_add_kp = False
                        else:
                            prev_kp, kp = fc.keyframe_points[-2:]
                            if prev_kp.interpolation == 'CONSTANT':
                                should_add_kp = False
                            elif prev_kp.co[1] == kp.co[1]:
                                should_add_kp = False
                                prev_kp.interpolation = 'CONSTANT'
                   
                    if should_add_kp:
                        fc.keyframe_points.add(1)
                   
                    kp = fc.keyframe_points[-1]
                    val = frame.uv[fc_idx]
                   
                    if fc_idx == 5:
                        scale_y = frame.uv[2]
                        val = 1 - (val + scale_y)
                   
                    kp.co = frame.time * fps + 1, val
                    kp.interpolation = 'LINEAR'
       
        self.material.dff.animation_name = uv_anim.name
        self.material.dff.export_animation = True

    #######################################################
    def set_user_data(self, user_data):
        self.material['dff_user_data'] = user_data.to_mem()[12:]
        
    #######################################################
    def __init__(self, material):
        self.material   = material
        self.principled = None

        # Init Principled Wrapper for Blender 2.8
        from bpy_extras.node_shader_utils import PrincipledBSDFWrapper

        self.principled = PrincipledBSDFWrapper(self.material,
                                                is_readonly=False)

        self.principled.specular    = 0
        self.principled.roughness   = 1

#######################################################
class object_helper:

    #######################################################
    def __init__(self, name):

        """
        An object helper for importing different types of objects
        """
        
        self.name = name
        self.mesh = None
        self.object = None

    #######################################################
    def get_object(self):
        pass
    
    pass

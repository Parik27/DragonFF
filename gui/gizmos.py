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
from bpy.types import Gizmo, GizmoGroup
from mathutils import Matrix, Vector

#######################################################
class Bounds3DGizmo(Gizmo):

    bl_idname = "VIEW3D_GT_bounds3d"
    bl_target_properties = (
        {"id": "bounds_min", "type": 'FLOAT', "array_length": 3},
        {"id": "bounds_max", "type": 'FLOAT', "array_length": 3},
    )

    __slots__ = (
        "custom_shape",
    )

    #######################################################
    def draw(self, context):
        bounds_min = self.target_get_value("bounds_min")
        bounds_max = self.target_get_value("bounds_max")

        x = bounds_min[0]
        y = bounds_min[1]
        z = bounds_min[2]

        sx = bounds_max[0] - x
        sy = bounds_max[1] - y
        sz = bounds_max[2] - z

        matrix = Matrix((
            (sx, 0, 0, x),
            (0, sy, 0, y),
            (0, 0, sz, z),
            (0, 0, 0, 1),
        ))
        self.draw_custom_shape(self.custom_shape, matrix=matrix)

    #######################################################
    def setup(self):
        shape_verts = (
            (0, 0, 0),
            (1, 0, 0),
            (1, 1, 0),
            (0, 1, 0),
            (0, 0, 0),
            (0, 0, 1),
            (1, 0, 1),
            (1, 1, 1),
            (0, 1, 1),
            (0, 0, 1),
            (1, 0, 1),
            (1, 0, 0),
            (1, 1, 0),
            (1, 1, 1),
            (0, 1, 1),
            (0, 1, 0),
        )
        if not hasattr(self, "custom_shape"):
            self.custom_shape = self.new_custom_shape('LINE_STRIP', shape_verts)

#######################################################
class Bound2DWidthGizmo(Gizmo):

    bl_idname = "VIEW3D_GT_bound2d_width_widget"
    bl_target_properties = (
        {"id": "size", "type": 'FLOAT', "array_length": 2},
    )

    __slots__ = (
        "custom_shape",
        "init_mouse_x",
        "init_size",
    )

    #######################################################
    def _update_offset_matrix(self):
        size = self.target_get_value("size")
        self.matrix_offset.col[0][0] = size[0] * 0.5
        self.matrix_offset.col[1][1] = size[1] * 0.5

    #######################################################
    def draw(self, context):
        self._update_offset_matrix()
        self.draw_custom_shape(self.custom_shape)

    #######################################################
    def draw_select(self, context, select_id):
        self._update_offset_matrix()
        self.draw_custom_shape(self.custom_shape, select_id=select_id)

    #######################################################
    def setup(self):
        shape_verts = (
            (1, 1, 0), (1, -1, 0),
            (-1, -1, 0), (-1, 1, 0),
        )
        if not hasattr(self, "custom_shape"):
            self.custom_shape = self.new_custom_shape('LINES', shape_verts)

    #######################################################
    def invoke(self, context, event):
        self.init_mouse_x = event.mouse_x
        self.init_size = self.target_get_value("size")
        return {'RUNNING_MODAL'}

    #######################################################
    def exit(self, context, cancel):
        context.area.header_text_set(None)
        if cancel:
            self.target_set_value("size", self.init_size)
        else:
            bpy.ops.ed.undo_push(message="Size Width")

    #######################################################
    def modal(self, context, event, tweak):
        delta = (event.mouse_x - self.init_mouse_x) / 50.0
        if 'SNAP' in tweak:
            delta = round(delta)
        if 'PRECISE' in tweak:
            delta /= 10.0

        size_x = self.init_size[0] + delta
        size_y = self.target_get_value("size")[1]

        if size_x < 0:
            size_x = 0

        self.target_set_value("size", (size_x, size_y))
        context.area.header_text_set("Size X: %.4f" % size_x)
        return {'RUNNING_MODAL'}

#######################################################
class Bound2DHeightGizmo(Gizmo):

    bl_idname = "VIEW3D_GT_bound2d_height_widget"
    bl_target_properties = (
        {"id": "size", "type": 'FLOAT', "array_length": 2},
    )

    __slots__ = (
        "custom_shape",
        "init_mouse_y",
        "init_size",
    )

    #######################################################
    def _update_offset_matrix(self):
        size = self.target_get_value("size")
        self.matrix_offset.col[0][0] = size[0] * 0.5
        self.matrix_offset.col[1][1] = size[1] * 0.5

    #######################################################
    def draw(self, context):
        self._update_offset_matrix()
        self.draw_custom_shape(self.custom_shape)

    #######################################################
    def draw_select(self, context, select_id):
        self._update_offset_matrix()
        self.draw_custom_shape(self.custom_shape, select_id=select_id)

    #######################################################
    def setup(self):
        shape_verts = (
            (-1, 1, 0), (1, 1, 0),
            (1, -1, 0), (-1, -1, 0),
        )
        if not hasattr(self, "custom_shape"):
            self.custom_shape = self.new_custom_shape('LINES', shape_verts)

    #######################################################
    def invoke(self, context, event):
        self.init_mouse_y = event.mouse_y
        self.init_size = self.target_get_value("size")
        return {'RUNNING_MODAL'}

    #######################################################
    def exit(self, context, cancel):
        context.area.header_text_set(None)
        if cancel:
            self.target_set_value("size", self.init_size)
        else:
            bpy.ops.ed.undo_push(message="Size Height")

    #######################################################
    def modal(self, context, event, tweak):
        delta = (event.mouse_y - self.init_mouse_y) / 50.0
        if 'SNAP' in tweak:
            delta = round(delta)
        if 'PRECISE' in tweak:
            delta /= 10.0

        size_x = self.target_get_value("size")[0]
        size_y = self.init_size[1] + delta

        if size_y < 0:
            size_y = 0

        self.target_set_value("size", (size_x, size_y))
        context.area.header_text_set("Size Y: %.4f" % size_y)
        return {'RUNNING_MODAL'}

#######################################################
class VectorPlaneGizmo(Gizmo):

    bl_idname = "VIEW3D_GT_vector_plane"
    bl_target_properties = (
        {"id": "vector", "type": 'FLOAT', "array_length": 3},
    )

    __slots__ = (
        "custom_shape",
    )

    #######################################################
    def draw(self, context):
        vector = Vector(self.target_get_value("vector"))

        matrix_basis = self.matrix_basis

        matrix_scale = Matrix.Identity(4)
        matrix_scale[0][0], matrix_scale[1][1], matrix_scale[2][2] = 1, 1, vector.length

        matrix = vector.normalized().to_track_quat("Z", "Y").to_matrix().to_4x4() @ matrix_scale
        matrix[0][3] = matrix_basis[0][3]
        matrix[1][3] = matrix_basis[1][3]
        matrix[2][3] = matrix_basis[2][3]

        self.draw_custom_shape(self.custom_shape, matrix=matrix)

    #######################################################
    def setup(self):
        shape_verts = (
            (-1, 0, 0),
            (-1, 0, 1),
            (1, 0, 0),
            (1, 0, 1),
        )
        if not hasattr(self, "custom_shape"):
            self.custom_shape = self.new_custom_shape('TRI_STRIP', shape_verts)

#######################################################
class CollisionCollectionGizmoGroup(GizmoGroup):

    bl_idname = "OBJECT_GGT_collision_collection"
    bl_label = "Collision Collection Widget"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT', 'SHOW_MODAL_ALL'}

    #######################################################
    @classmethod
    def poll(cls, context):
        if not context.scene.dff.draw_bounds:
            return False

        col = context.collection
        return (col and not col.dff.auto_bounds)

    #######################################################
    def setup(self, context):

        def get_bounds_min():
            return context.collection.dff.bounds_min

        def get_bounds_max():
            return context.collection.dff.bounds_max

        def set_bounds_min(value):
            context.collection.dff.bounds_min = value

        def set_bounds_max(value):
            context.collection.dff.bounds_max = value

        gz = self.gizmos.new(Bounds3DGizmo.bl_idname)

        gz.target_set_handler("bounds_min", get=get_bounds_min, set=set_bounds_min)
        gz.target_set_handler("bounds_max", get=get_bounds_max, set=set_bounds_max)

        gz.color = 0.84, 0.84, 0.54
        gz.alpha = 0.5

        gz.use_draw_modal = False
        gz.use_draw_scale = False

#######################################################
class PedAttractor2DFXGizmoGroup(GizmoGroup):

    bl_idname = "OBJECT_GGT_2dfx_ped_attractor"
    bl_label = "2DFX Ped Attractor Widget"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT'}

    #######################################################
    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj and obj.type == 'EMPTY' and obj.dff.type == '2DFX' and obj.dff.ext_2dfx.effect == '3')

    #######################################################
    def setup(self, context):

        gz = self.gizmos.new("GIZMO_GT_arrow_3d")
        gz.color = gz.color_highlight = 1, 0, 0
        self.queue_dir_gizmo = gz

        gz = self.gizmos.new("GIZMO_GT_arrow_3d")
        gz.color = gz.color_highlight = 0, 1, 0
        self.use_dir_gizmo = gz

        gz = self.gizmos.new("GIZMO_GT_arrow_3d")
        gz.color = gz.color_highlight = 0, 0, 1
        self.forward_dir_gizmo = gz

        for gz in (self.queue_dir_gizmo, self.use_dir_gizmo, self.forward_dir_gizmo):
            gz.alpha = gz.alpha_highlight = 0.5
            gz.length = 1
            gz.target_set_handler("offset", get=lambda: 0, set=lambda v: None)
            gz.use_draw_scale = False

    #######################################################
    def refresh(self, context):
        obj = context.object
        location = obj.matrix_world.to_translation()
        matrix = Matrix.Translation(location)

        queue_dir = obj.dff.ext_2dfx.val_euler_1
        use_dir = obj.matrix_world.to_euler()
        forward_dir = obj.dff.ext_2dfx.val_euler_2

        self.queue_dir_gizmo.matrix_basis = matrix @ queue_dir.to_matrix().to_4x4()
        self.use_dir_gizmo.matrix_basis = matrix @ use_dir.to_matrix().to_4x4()
        self.forward_dir_gizmo.matrix_basis = matrix @ forward_dir.to_matrix().to_4x4()

#######################################################
class RoadSign2DFXGizmoGroup(GizmoGroup):

    bl_idname = "OBJECT_GGT_2dfx_road_sign"
    bl_label = "2DFX Road Sign Widget"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT'}

    #######################################################
    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj and obj.type == 'FONT' and obj.dff.type == '2DFX' and obj.dff.ext_2dfx.effect == '7')

    #######################################################
    def setup(self, context):
        self.width_gizmo = self.gizmos.new(Bound2DWidthGizmo.bl_idname)
        self.height_gizmo = self.gizmos.new(Bound2DHeightGizmo.bl_idname)

        obj = context.object

        for gz in (self.width_gizmo, self.height_gizmo):
            gz.target_set_prop("size", obj.data.ext_2dfx, "size")
            gz.color = 1, 1, 0
            gz.alpha = 0.5

            gz.color_highlight = 1, 1, 1
            gz.alpha_highlight = 0.5

            gz.use_draw_modal = True
            gz.use_draw_scale = False

    #######################################################
    def refresh(self, context):
        obj = context.object
        matrix = obj.matrix_world.normalized()

        self.width_gizmo.matrix_basis = matrix
        self.height_gizmo.matrix_basis = matrix

        # After manually changing obj.data properties and doing undo, gizmo's properties reset for some reason
        if self.width_gizmo.target_get_value("size") != tuple(obj.data.ext_2dfx.size):
            self.width_gizmo.target_set_prop("size", obj.data.ext_2dfx, "size")
            self.height_gizmo.target_set_prop("size", obj.data.ext_2dfx, "size")

#######################################################
class Escalator2DFXGizmoGroup(GizmoGroup):

    bl_idname = "OBJECT_GGT_2dfx_escalator"
    bl_label = "2DFX Escalator Widget"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT'}

    #######################################################
    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj and obj.type == 'EMPTY' and obj.dff.type == '2DFX' and obj.dff.ext_2dfx.effect == '10')

    #######################################################
    def setup(self, context):

        def get_bottom_vector():
            v1 = context.object.matrix_world.to_translation()
            v2 = self.bottom_gizmo.matrix_world.to_translation()
            return v2 - v1

        def get_top_vector():
            v1 = self.bottom_gizmo.matrix_world.to_translation()
            v2 = self.top_gizmo.matrix_world.to_translation()
            return v2 - v1

        def get_end_vector():
            v1 = self.top_gizmo.matrix_world.to_translation()
            v2 = self.end_gizmo.matrix_world.to_translation()
            return v2 - v1

        def get_bottom_z():
            return context.object.dff.ext_2dfx.val_vector_1[2]

        def get_top_z():
            return context.object.dff.ext_2dfx.val_vector_2[2]

        def get_end_z():
            return context.object.dff.ext_2dfx.val_vector_3[2]

        def set_bottom_z(value):
            context.object.dff.ext_2dfx.val_vector_1[2] = value

        def set_top_z(value):
            context.object.dff.ext_2dfx.val_vector_2[2] = value

        def set_end_z(value):
            context.object.dff.ext_2dfx.val_vector_3[2] = value

        gz = self.gizmos.new("GIZMO_GT_arrow_3d")
        gz.target_set_handler("offset", get=get_bottom_z, set=set_bottom_z)
        self.bottom_gizmo = gz

        gz = self.gizmos.new("GIZMO_GT_arrow_3d")
        gz.target_set_handler("offset", get=get_top_z, set=set_top_z)
        gz.color = 1.0, 0.5, 0.0
        self.top_gizmo = gz

        gz = self.gizmos.new("GIZMO_GT_arrow_3d")
        gz.target_set_handler("offset", get=get_end_z, set=set_end_z)
        self.end_gizmo = gz

        for gz in (self.bottom_gizmo, self.top_gizmo, self.end_gizmo):
            gz.draw_style = 'BOX'
            gz.length = 0
            gz.color_highlight = 1.0, 0.5, 1.0
            gz.alpha_highlight = 0.5
            gz.use_draw_scale = False

        gz = self.gizmos.new(VectorPlaneGizmo.bl_idname)
        gz.target_set_handler("vector", get=get_bottom_vector, set=lambda v: None)
        self.bottom_plane_gizmo = gz

        gz = self.gizmos.new(VectorPlaneGizmo.bl_idname)
        gz.target_set_handler("vector", get=get_top_vector, set=lambda v: None)
        gz.color = 1.0, 0.5, 0.0
        self.top_plane_gizmo = gz

        gz = self.gizmos.new(VectorPlaneGizmo.bl_idname)
        gz.target_set_handler("vector", get=get_end_vector, set=lambda v: None)
        self.end_plane_gizmo = gz

        for gz in self.gizmos:
            gz.alpha = 0.5

    #######################################################
    def refresh(self, context):
        obj = context.object
        matrix = obj.matrix_world.normalized()

        bottom = obj.dff.ext_2dfx.val_vector_1
        top = obj.dff.ext_2dfx.val_vector_2
        end = obj.dff.ext_2dfx.val_vector_3

        self.bottom_gizmo.matrix_basis = matrix @ Matrix.Translation((bottom[0], bottom[1], 0))
        self.top_gizmo.matrix_basis = matrix @ Matrix.Translation((top[0], top[1], 0))
        self.end_gizmo.matrix_basis = matrix @ Matrix.Translation((end[0], end[1], 0))

        self.bottom_plane_gizmo.matrix_basis = matrix
        self.top_plane_gizmo.matrix_basis = matrix @ Matrix.Translation(bottom)
        self.end_plane_gizmo.matrix_basis = matrix @ Matrix.Translation(top)

        if obj.dff.ext_2dfx.escalator_direction == '0':
            self.bottom_gizmo.color = self.bottom_plane_gizmo.color = 1, 0, 0
            self.end_gizmo.color = self.end_plane_gizmo.color = 0, 1, 0
        else:
            self.bottom_gizmo.color = self.bottom_plane_gizmo.color = 0, 1, 0
            self.end_gizmo.color = self.end_plane_gizmo.color = 1, 0, 0

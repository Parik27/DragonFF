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
from mathutils import Matrix

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
class CollisionCollectionGizmoGroup(GizmoGroup):

    bl_idname = "OBJECT_GGT_collision_collection"
    bl_label = "Collision Collection Widget"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT'}

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

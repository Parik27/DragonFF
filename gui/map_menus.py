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

from .col_ot import FaceGroupsDrawer
from .map_ot import SCENE_OT_ipl_select, OBJECT_OT_dff_add_cull
from ..gtaLib.data import map_data

#######################################################
class IDEObjectProps(bpy.types.PropertyGroup):
    """IDE properties for objects"""

    obj_id: bpy.props.StringProperty(
        name="Object ID",
        description="Unique object ID in IDE files",
        default=""
    )

    model_name: bpy.props.StringProperty(
        name="Model Name",
        description="Model name (should match DFF filename)",
        default=""
    )

    txd_name: bpy.props.StringProperty(
        name="TXD Name",
        description="Texture dictionary name",
        default=""
    )

    flags: bpy.props.StringProperty(
        name="Flags",
        description="Object flags",
        default="0"
    )

    draw_distance: bpy.props.StringProperty(
        name="Draw Distance",
        description="Single draw distance",
        default="100"
    )

    draw_distance1: bpy.props.StringProperty(
        name="Draw Distance 1",
        description="First draw distance (for multi-LOD objects)",
        default=""
    )

    draw_distance2: bpy.props.StringProperty(
        name="Draw Distance 2",
        description="Second draw distance (for multi-LOD objects)",
        default=""
    )

    draw_distance3: bpy.props.StringProperty(
        name="Draw Distance 3",
        description="Third draw distance (for multi-LOD objects)",
        default=""
    )

    obj_type: bpy.props.EnumProperty(
        name="Object Type",
        description="IDE object type",
        items=[
            ('objs', 'Regular Object', 'Standard object'),
            ('tobj', 'Time Object', 'Time-based object')
        ],
        default='objs'
    )

    time_on: bpy.props.StringProperty(
        name="Time On",
        description="Hour when object appears (0-23)",
        default="0"
    )

    time_off: bpy.props.StringProperty(
        name="Time Off",
        description="Hour when object disappears (0-23)",
        default="24"
    )

#######################################################
class IPLObjectProps(bpy.types.PropertyGroup):
    """IPL properties for objects"""

    interior: bpy.props.StringProperty(
        name="Interior",
        description="Interior ID (0 for exterior)",
        default="0"
    )

    lod: bpy.props.StringProperty(
        name="LOD",
        description="LOD object ID (-1 for no LOD)",
        default="-1"
    )

#######################################################
class DFFFrameProps(bpy.types.PropertyGroup):
    obj  : bpy.props.PointerProperty(type=bpy.types.Object)
    icon : bpy.props.StringProperty()

#######################################################
class DFFAtomicProps(bpy.types.PropertyGroup):
    obj       : bpy.props.PointerProperty(type=bpy.types.Object)
    frame_obj : bpy.props.PointerProperty(type=bpy.types.Object)

#######################################################
class DFFSceneProps(bpy.types.PropertyGroup):

    #######################################################
    def update_map_sections(self, context):
        return map_data.data[self.game_version_dropdown]['IPL_paths']

    #######################################################
    def frames_active_changed(self, context):
        scene_dff = context.scene.dff

        frames_num = len(scene_dff.frames)
        if not frames_num:
            return

        if scene_dff.frames_active >= frames_num:
            scene_dff.frames_active = frames_num - 1
            return

        frame_object = scene_dff.frames[scene_dff.frames_active].obj

        for a in scene_dff.frames: a.obj.select_set(False)
        frame_object.select_set(True)
        context.view_layer.objects.active = frame_object

    #######################################################
    def atomics_active_changed(self, context):
        scene_dff = context.scene.dff

        atomics_num = len(scene_dff.atomics)
        if not atomics_num:
            return

        if scene_dff.atomics_active >= atomics_num:
            scene_dff.atomics_active = atomics_num - 1
            return

        atomic_object = scene_dff.atomics[scene_dff.atomics_active].obj

        for a in scene_dff.atomics: a.obj.select_set(False)
        atomic_object.select_set(True)
        context.view_layer.objects.active = atomic_object

    game_version_dropdown : bpy.props.EnumProperty(
        name = 'Game',
        items = (
            (map_data.game_version.III, 'GTA III', 'GTA III map segments'),
            (map_data.game_version.VC, 'GTA VC', 'GTA VC map segments'),
            (map_data.game_version.SA, 'GTA SA', 'GTA SA map segments'),
            (map_data.game_version.LCS, 'GTA LCS', 'GTA LCS map segments'),
            (map_data.game_version.VCS, 'GTA VCS', 'GTA VCS map segments'),
        )
    )

    map_sections : bpy.props.EnumProperty(
        name = 'Map segment',
        items = update_map_sections
    )

    custom_ipl_path : bpy.props.StringProperty(
        name        = "IPL path",
        default     = '',
        description = "Custom IPL path (supports both relative paths from game root and absolute paths)"
    )

    use_custom_map_section : bpy.props.BoolProperty(
        name        = "Use Custom Map Section",
        default     = False
    )

    skip_lod: bpy.props.BoolProperty(
        name        = "Skip LOD Objects",
        default     = False
    )

    load_txd: bpy.props.BoolProperty(
        name        = "Load TXD files",
        default     = False
    )

    txd_pack : bpy.props.BoolProperty(
        name        = "Pack Images",
        description = "Pack images as embedded data into the .blend file",
        default     = False
    )

    read_mat_split  :  bpy.props.BoolProperty(
        name        = "Read Material Split",
        description = "Whether to read material split for loading triangles",
        default     = False
    )

    create_backfaces:  bpy.props.BoolProperty(
        name        = "Create Backfaces",
        description = "Create backfaces by duplicating existing faces. Incompatible with Use Edge Split",
        default     = False
    )

    load_collisions: bpy.props.BoolProperty(
        name        = "Load Map Collisions",
        default     = False
    )

    load_cull: bpy.props.BoolProperty(
        name        = "Load Map CULL",
        default     = False
    )

    game_root : bpy.props.StringProperty(
        name = 'Game root',
        default = 'C:/Program Files (x86)/Steam/steamapps/common/',
        description = "Folder with the game's executable",
        subtype = 'DIR_PATH'
    )

    dff_folder : bpy.props.StringProperty(
        name = 'Dff folder',
        default = 'C:/Users/blaha/Documents/GitHub/DragonFF/tests/dff',
        description = "Define a folder where all of the dff models are stored.",
        subtype = 'DIR_PATH'
    )

    draw_facegroups : bpy.props.BoolProperty(
        name="Draw Face Groups",
        description="Display the Face Groups of the active object (if they exist) in the viewport",
        default=False,
        get=FaceGroupsDrawer.get_draw_enabled,
        set=FaceGroupsDrawer.set_draw_enabled
    )

    draw_bounds: bpy.props.BoolProperty(
        name="Draw Bounds",
        description = "Display the bounds of the active collection in the viewport",
        default = False
    )

    face_group_min : bpy.props.IntProperty(
        name = 'Face Group Minimum Size',
        description="Don't generate groups below this size",
        default = 20,
        min = 5,
        max = 200
    )

    face_group_max : bpy.props.IntProperty(
        name = 'Face Group Maximum Size',
        description="Don't generate groups above this size (minimum size overrides this if larger)",
        default = 50,
        min = 5,
        max = 200
    )

    face_group_avoid_smalls : bpy.props.BoolProperty(
        name = "Avoid overly small groups",
        description="Combine really small groups with their neighbor to avoid pointless isolated groups",
        default = True
    )

    frames : bpy.props.CollectionProperty(
        type    = DFFFrameProps,
        options = {'SKIP_SAVE','HIDDEN'}
    )

    frames_active : bpy.props.IntProperty(
        name    = "Active frame",
        default = 0,
        min     = 0,
        update  = frames_active_changed
    )

    atomics : bpy.props.CollectionProperty(
        type    = DFFAtomicProps,
        options = {'SKIP_SAVE','HIDDEN'}
    )

    atomics_active : bpy.props.IntProperty(
        name    = "Active atomic",
        default = 0,
        min     = 0,
        update  = atomics_active_changed
    )

    real_time_update : bpy.props.BoolProperty(
        name        = "Real Time Update",
        description = "Update the list of objects in real time",
        default     = True
    )

    filter_collection : bpy.props.BoolProperty(
        name        = "Filter Collection",
        description = "Filter frames and atomics by active collection",
        default     = True
    )

#######################################################
class MapImportPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "DragonFF - Map I/O"
    bl_idname = "SCENE_PT_layout"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    #######################################################
    def draw(self, context):
        layout = self.layout
        settings = context.scene.dff

        flow = layout.grid_flow(row_major=True,
                                columns=0,
                                even_columns=True,
                                even_rows=False,
                                align=True)

        col = flow.column()
        col.prop(settings, "game_version_dropdown")
        if settings.use_custom_map_section:
            row = col.row(align=True)
            row.prop(settings, "custom_ipl_path")
            row.operator(SCENE_OT_ipl_select.bl_idname, text="", icon='FILEBROWSER')
        else:
            col.prop(settings, "map_sections")
        col.prop(settings, "use_custom_map_section")
        col.separator()

        box = col.box()
        box.prop(settings, "load_txd")
        if settings.load_txd:
            box.prop(settings, "txd_pack")

        col.prop(settings, "skip_lod")
        col.prop(settings, "read_mat_split")
        col.prop(settings, "create_backfaces")
        col.prop(settings, "load_collisions")
        col.prop(settings, "load_cull")

        layout.separator()

        layout.prop(settings, 'game_root')
        layout.prop(settings, 'dff_folder')

        row = layout.row()
        row.operator("scene.dragonff_map_import")

        layout.separator()

        row = layout.row()
        row.operator("export_scene.dff_ipl", text="Export IPL")

        row = layout.row()
        row.operator("export_scene.dff_ide", text="Export IDE")

#######################################################
class MapObjectPanel(bpy.types.Panel):
    """Panel for IPL/IDE object properties"""
    bl_label = "DragonFF - Map Properties"
    bl_idname = "OBJECT_PT_map_props"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    #######################################################
    @classmethod
    def poll(cls, context):
        return context.object is not None

    #######################################################
    def draw(self, context):
        layout = self.layout
        obj = context.object

        # IPL Data
        box = layout.box()
        box.label(text="IPL Data (Instance Placement):", icon='OUTLINER_OB_EMPTY')

        col = box.column()

        row = col.row()
        row.label(text="Object ID:")
        row.label(text=obj.ide.obj_id if obj.ide.obj_id else "Not Set")

        row = col.row()
        row.label(text="Model Name:")
        row.label(text=obj.ide.model_name if obj.ide.model_name else "Not Set")

        row = col.row()
        row.prop(obj.ipl, "interior")

        if context.scene.dff.game_version_dropdown == map_data.game_version.SA:
            row = col.row()
            row.prop(obj.ipl, "lod")

        # Show current transform
        col.separator()
        col.label(text="Transform:")
        col.label(text=f"Position: {obj.location.x:.3f}, {obj.location.y:.3f}, {obj.location.z:.3f}")
        rot = obj.rotation_quaternion
        col.label(text=f"Rotation: {rot.x:.3f}, {rot.y:.3f}, {rot.z:.3f}, {rot.w:.3f}")

        # IDE Data
        box = layout.box()
        box.label(text="IDE Data (Object Definition):", icon='OUTLINER_DATA_MESH')

        col = box.column()

        # Object ID
        row = col.row(align=True)
        row.prop(obj.ide, "obj_id")

        # Model Name
        row = col.row()
        row.prop(obj.ide, "model_name")

        # Object Type
        row = col.row()
        row.prop(obj.ide, "obj_type")

        # TXD Name
        row = col.row()
        row.prop(obj.ide, "txd_name")

        # Flags
        row = col.row()
        row.prop(obj.ide, "flags")

        # Draw Distances
        col.separator()
        col.label(text="Draw Distances:")

        # Check which draw distance format to use
        if obj.ide.draw_distance1 or obj.ide.draw_distance2 or obj.ide.draw_distance3:
            # Multiple draw distances
            row = col.row()
            row.prop(obj.ide, "draw_distance1")
            row = col.row()
            row.prop(obj.ide, "draw_distance2")
            row = col.row()
            row.prop(obj.ide, "draw_distance3")
        else:
            # Single draw distance
            row = col.row()
            row.prop(obj.ide, "draw_distance")

        # Time Object Properties
        if obj.ide.obj_type == 'tobj':
            col.separator()
            col.label(text="Time Object Properties:")

            row = col.row()
            row.prop(obj.ide, "time_on")
            row.prop(obj.ide, "time_off")

#######################################################
class DFF_MT_AddMapObject(bpy.types.Menu):
    bl_label = "Map"

    def draw(self, context):
        self.layout.operator(OBJECT_OT_dff_add_cull.bl_idname, text="CULL", icon="CUBE")

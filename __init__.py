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
from .gui import gui
from .ops import map_importer

from bpy.utils import register_class, unregister_class

bl_info = {
    "name": "GTA DragonFF",
    "author": "Parik",
    "version": (0, 0, 2),
    "blender": (2, 80, 0),
    "category": "Import-Export",
    "location": "File > Import/Export",
    "description": "Importer and Exporter for GTA Formats"
}


# Class list to register
_classes = [
    gui.IMPORT_OT_dff,
    gui.IMPORT_OT_txd,
    gui.EXPORT_OT_dff,
    gui.EXPORT_OT_col,
    gui.SCENE_OT_dff_frame_move,
    gui.SCENE_OT_dff_atomic_move,
    gui.SCENE_OT_dff_update,
    gui.SCENE_OT_ipl_select,
    gui.OBJECT_OT_dff_generate_bone_props,
    gui.OBJECT_OT_dff_set_parent_bone,
    gui.OBJECT_OT_dff_clear_parent_bone,
    gui.OBJECT_OT_facegoups_col,
    gui.MATERIAL_PT_dffMaterials,
    gui.OBJECT_PT_dffObjects,
    gui.OBJECT_PT_dffCollections,
    gui.COLLECTION_OT_dff_generate_bounds,
    gui.EXT2DFXObjectProps,
    gui.Light2DFXObjectProps,
    gui.RoadSign2DFXObjectProps,
    gui.IMPORT_OT_ParticleTXDNames,
    gui.DFFMaterialProps,
    gui.DFFObjectProps,
    gui.DFFCollectionProps,
    gui.MapImportPanel,
    gui.TXDImportPanel,
    gui.DFFFrameProps,
    gui.DFFAtomicProps,
    gui.DFFSceneProps,
    gui.DFF_MT_ExportChoice,
    gui.DFF_MT_EditArmature,
    gui.DFF_MT_Pose,
    gui.DFF_UL_FrameItems,
    gui.DFF_UL_AtomicItems,
    gui.SCENE_PT_dffFrames,
    gui.SCENE_PT_dffAtomics,
    gui.Bounds3DGizmo,
    gui.Bound2DWidthGizmo,
    gui.Bound2DHeightGizmo,
    gui.VectorPlaneGizmo,
    gui.CollisionCollectionGizmoGroup,
    gui.RoadSign2DFXGizmoGroup,
    gui.Escalator2DFXGizmoGroup,
    map_importer.Map_Import_Operator,
    gui.EXPORT_OT_ipl,
    gui.EXPORT_OT_ide,
    gui.IDEObjectProps,
    gui.IPLObjectProps,
    gui.MapObjectPanel
]

_draw_3d_handler = None

#######################################################
def draw_3d_callback():
    gui.DFFSceneProps.draw_fg()

#######################################################
def register():

    # Register all the classes
    for cls in _classes:
        register_class(cls)

    bpy.types.Scene.dff = bpy.props.PointerProperty(type=gui.DFFSceneProps)
    bpy.types.Light.ext_2dfx = bpy.props.PointerProperty(type=gui.Light2DFXObjectProps)
    bpy.types.TextCurve.ext_2dfx = bpy.props.PointerProperty(type=gui.RoadSign2DFXObjectProps)
    bpy.types.Material.dff = bpy.props.PointerProperty(type=gui.DFFMaterialProps)
    bpy.types.Object.dff = bpy.props.PointerProperty(type=gui.DFFObjectProps)
    bpy.types.Collection.dff = bpy.props.PointerProperty(type=gui.DFFCollectionProps)
    bpy.types.Object.ide = bpy.props.PointerProperty(type=gui.IDEObjectProps)
    bpy.types.Object.ipl = bpy.props.PointerProperty(type=gui.IPLObjectProps)

    bpy.types.TOPBAR_MT_file_import.append(gui.import_dff_func)
    bpy.types.TOPBAR_MT_file_export.append(gui.export_dff_func)
    bpy.types.OUTLINER_MT_collection.append(gui.export_col_outliner)
    bpy.types.OUTLINER_MT_object.append(gui.export_dff_outliner)
    bpy.types.VIEW3D_MT_edit_armature.append(gui.edit_armature_dff_func)
    bpy.types.VIEW3D_MT_pose.append(gui.pose_dff_func)

    global _draw_3d_handler
    _draw_3d_handler = bpy.types.SpaceView3D.draw_handler_add(draw_3d_callback, (), 'WINDOW', 'POST_VIEW')

    gui.State.hook_events()

#######################################################
def unregister():

    del bpy.types.Scene.dff
    del bpy.types.Light.ext_2dfx
    del bpy.types.TextCurve.ext_2dfx
    del bpy.types.Material.dff
    del bpy.types.Object.dff
    del bpy.types.Collection.dff
    del bpy.types.Object.ide
    del bpy.types.Object.ipl

    bpy.types.TOPBAR_MT_file_import.remove(gui.import_dff_func)
    bpy.types.TOPBAR_MT_file_export.remove(gui.export_dff_func)
    bpy.types.OUTLINER_MT_collection.remove(gui.export_col_outliner)
    bpy.types.OUTLINER_MT_object.remove(gui.export_dff_outliner)
    bpy.types.VIEW3D_MT_edit_armature.remove(gui.edit_armature_dff_func)
    bpy.types.VIEW3D_MT_pose.remove(gui.pose_dff_func)

    bpy.types.SpaceView3D.draw_handler_remove(_draw_3d_handler, 'WINDOW')

    gui.State.unhook_events()

    # Unregister all the classes
    for cls in _classes:
        unregister_class(cls)

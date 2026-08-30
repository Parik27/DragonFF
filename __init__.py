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
    gui.EXPORT_OT_dff,
    gui.EXPORT_OT_txd,
    gui.EXPORT_OT_col,
    gui.EXPORT_OT_ipl_cull,
    gui.SCENE_OT_dff_frame_move,
    gui.SCENE_OT_dff_atomic_move,
    gui.SCENE_OT_dff_update,
    gui.SCENE_OT_dff_import_map,
    gui.SCENE_OT_ipl_select,
    gui.OBJECT_OT_dff_generate_bone_props,
    gui.OBJECT_OT_dff_set_parent_bone,
    gui.OBJECT_OT_dff_clear_parent_bone,
    gui.OBJECT_OT_facegoups_col,
    gui.OBJECT_OT_dff_add_collision_box,
    gui.OBJECT_OT_dff_add_collision_sphere,
    gui.OBJECT_OT_dff_add_2dfx_light,
    gui.OBJECT_OT_dff_add_2dfx_particle,
    gui.OBJECT_OT_dff_add_2dfx_ped_attractor,
    gui.OBJECT_OT_dff_add_2dfx_sun_glare,
    gui.OBJECT_OT_dff_add_2dfx_road_sign,
    gui.OBJECT_OT_dff_add_2dfx_trigger_point,
    gui.OBJECT_OT_dff_add_2dfx_cover_point,
    gui.OBJECT_OT_dff_add_2dfx_escalator,
    gui.OBJECT_OT_dff_add_cull,
    gui.MATERIAL_PT_dffMaterials,
    gui.OBJECT_PT_dffObjects,
    gui.OBJECT_PT_dffCollections,
    gui.COLLECTION_OT_dff_generate_bounds,
    gui.EXT2DFXObjectProps,
    gui.Light2DFXObjectProps,
    gui.RoadSign2DFXObjectProps,
    gui.CULLObjectProps,
    gui.IMPORT_OT_ParticleTXDNames,
    gui.DFFMaterialProps,
    gui.COLMaterialEnumProps,
    gui.DFFObjectProps,
    gui.DFFCollectionProps,
    gui.MapImportPanel,
    gui.DFFFrameProps,
    gui.DFFAtomicProps,
    gui.DFFSceneProps,
    gui.DFF_MT_ExportChoice,
    gui.DFF_MT_EditArmature,
    gui.DFF_MT_Pose,
    gui.DFF_MT_AddCollisionObject,
    gui.DFF_MT_Add2DFXObject,
    gui.DFF_MT_AddMapObject,
    gui.DFF_MT_AddObject,
    gui.DFF_UL_FrameItems,
    gui.DFF_UL_AtomicItems,
    gui.SCENE_PT_dffFrames,
    gui.SCENE_PT_dffAtomics,
    gui.Bounds3DGizmo,
    gui.Bound2DWidthGizmo,
    gui.Bound2DHeightGizmo,
    gui.VectorPlaneGizmo,
    gui.CollisionCollectionGizmoGroup,
    gui.PedAttractor2DFXGizmoGroup,
    gui.RoadSign2DFXGizmoGroup,
    gui.Escalator2DFXGizmoGroup,
    gui.UVAnimatorProperties,
    gui.UV_OT_AnimateSpriteSheet,
    gui.NODE_PT_UVAnimator,
    gui.COLSceneProps
]

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
    bpy.types.Scene.dff_uv_animator_props = bpy.props.PointerProperty(type=gui.UVAnimatorProperties)
    bpy.types.Scene.dff_col = bpy.props.PointerProperty(type=gui.COLSceneProps)

    bpy.types.TOPBAR_MT_file_import.append(gui.import_dff_func)
    bpy.types.TOPBAR_MT_file_export.append(gui.export_dff_func)
    bpy.types.OUTLINER_MT_collection.append(gui.export_col_outliner)
    bpy.types.OUTLINER_MT_object.append(gui.export_dff_outliner)
    bpy.types.VIEW3D_MT_edit_armature.append(gui.edit_armature_dff_func)
    bpy.types.VIEW3D_MT_pose.append(gui.pose_dff_func)
    bpy.types.VIEW3D_MT_add.append(gui.add_object_dff_func)

    gui.State.hook_events()

#######################################################
def unregister():

    del bpy.types.Scene.dff
    del bpy.types.Light.ext_2dfx
    del bpy.types.TextCurve.ext_2dfx
    del bpy.types.Material.dff
    del bpy.types.Object.dff
    del bpy.types.Collection.dff
    del bpy.types.Scene.dff_uv_animator_props
    del bpy.types.Scene.dff_col

    bpy.types.TOPBAR_MT_file_import.remove(gui.import_dff_func)
    bpy.types.TOPBAR_MT_file_export.remove(gui.export_dff_func)
    bpy.types.OUTLINER_MT_collection.remove(gui.export_col_outliner)
    bpy.types.OUTLINER_MT_object.remove(gui.export_dff_outliner)
    bpy.types.VIEW3D_MT_edit_armature.remove(gui.edit_armature_dff_func)
    bpy.types.VIEW3D_MT_pose.remove(gui.pose_dff_func)
    bpy.types.VIEW3D_MT_add.remove(gui.add_object_dff_func)

    gui.FaceGroupsDrawer.disable_draw()

    gui.State.unhook_events()

    # Unregister all the classes
    for cls in _classes:
        unregister_class(cls)

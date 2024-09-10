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
    gui.EXPORT_OT_dff,
    gui.EXPORT_OT_col,
    gui.SCENE_OT_dff_frame_move,
    gui.SCENE_OT_dff_atomic_move,
    gui.SCENE_OT_dff_update,
    gui.OBJECT_OT_dff_set_parent_bone,
    gui.OBJECT_OT_facegoups_col,
    gui.MATERIAL_PT_dffMaterials,
    gui.OBJECT_PT_dffObjects,
    gui.DFFMaterialProps,
    gui.DFFObjectProps,
    gui.MapImportPanel,
    gui.DFFFrameProps,
    gui.DFFAtomicProps,
    gui.DFFSceneProps,
    gui.DFF_MT_ExportChoice,
    gui.DFF_UL_FrameItems,
    gui.DFF_UL_AtomicItems,
    gui.SCENE_PT_dffFrames,
    gui.SCENE_PT_dffAtomics,
    map_importer.Map_Import_Operator
]
#######################################################
def register():

    # Register all the classes
    for cls in _classes:
        register_class(cls)

    if (2, 80, 0) > bpy.app.version:        
        bpy.types.INFO_MT_file_import.append(gui.import_dff_func)
        bpy.types.INFO_MT_file_export.append(gui.export_dff_func)
        
    else:
        bpy.types.TOPBAR_MT_file_import.append(gui.import_dff_func)
        bpy.types.TOPBAR_MT_file_export.append(gui.export_dff_func)
        bpy.types.OUTLINER_MT_collection.append(gui.export_col_outliner)
        bpy.types.OUTLINER_MT_object.append(gui.export_dff_outliner)
        bpy.types.VIEW3D_MT_pose.append(gui.set_parent_bone_func)
        bpy.types.SpaceView3D.draw_handler_add(gui.DFFSceneProps.draw_fg, (), 'WINDOW', 'POST_VIEW')

    gui.State.hook_events()

#######################################################
def unregister():

    if (2, 80, 0) > bpy.app.version:
        bpy.types.INFO_MT_file_import.remove(gui.import_dff_func)
        bpy.types.INFO_MT_file_export.remove(gui.export_dff_func)

    else:
        bpy.types.TOPBAR_MT_file_import.remove(gui.import_dff_func)
        bpy.types.TOPBAR_MT_file_export.remove(gui.export_dff_func)
        bpy.types.OUTLINER_MT_collection.remove(gui.export_col_outliner)
        bpy.types.OUTLINER_MT_object.remove(gui.export_dff_outliner)
        bpy.types.VIEW3D_MT_pose.remove(gui.set_parent_bone_func)

    gui.State.unhook_events()

    # Unregister all the classes
    for cls in _classes:
        unregister_class(cls)      

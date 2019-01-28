# GTA Blender Tools - Tools to edit basic GTA formats
# Copyright (C) 2019  Parik

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
import os
from . import dff_importer, dff_exporter

from bpy_extras.io_utils import ImportHelper, ExportHelper

#######################################################
class EXPORT_OT_dff(bpy.types.Operator, ExportHelper):
    
    bl_idname      = "export_dff.scene"
    bl_description = "Export a Renderware DFF or COL File"
    bl_label       = "GTA Renderware (.dff, .col)"
    filename_ext   = ".dff"

    filepath       = bpy.props.StringProperty(name="File path",
                                              maxlen=1024,
                                              default="",
                                              subtype='FILE_PATH')
    
    filter_glob    = bpy.props.StringProperty(default="*.dff;*.col",
                                              options={'HIDDEN'})
    
    directory      = bpy.props.StringProperty(maxlen=1024,
                                              default="",
                                              subtype='FILE_PATH')

    mass_export     =  bpy.props.BoolProperty(
        name        = "Mass Export",
        default     = False
    )
    
    only_selected   =  bpy.props.BoolProperty(
        name        = "Only Selected",
        default     = False
    )



    #######################################################
    def execute(self, context):
        
        dff_exporter.export_dff(
            {
                "file_name"   : self.filepath,
                "directory"   : self.directory,
                "selected"    :  self.only_selected,
                "mass_export" : self.mass_export,
            }
        )
            
        return {'FINISHED'}

    #######################################################
    def invoke(self, context, event):
        
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    #filter_folder = bpy.props.BoolProperty(default=True, options={'HIDDEN'})

#######################################################
class IMPORT_OT_dff(bpy.types.Operator, ImportHelper):
    
    bl_idname      = "import_scene.dff"
    bl_description = 'Import a Renderware DFF or COL File'
    bl_label       = "GTA Renderware (.dff, .col)"

    filter_glob   : bpy.props.StringProperty(default="*.dff;*.col",
                                              options={'HIDDEN'})
    
    directory     : bpy.props.StringProperty(maxlen=1024,
                                              default="",
                                              subtype='FILE_PATH',
                                              options={'HIDDEN'})
    
    # Stores all the file names to read (not just the firsst)
    files : bpy.props.CollectionProperty(
        type    = bpy.types.OperatorFileListElement,
        options = {'HIDDEN'}
    )

    # Stores a single file path
    filepath : bpy.props.StringProperty(
         name        = "File Path",
         description = "Filepath used for importing the DFF/COL file",
         maxlen      = 1024,
         default     = "",
         options     = {'HIDDEN'}
     )

    
    load_txd :  bpy.props.BoolProperty(
        name        = "Load TXD file",
        default     = True
    )

    connect_bones :  bpy.props.BoolProperty(
        name        = "Connect Bones",
        description = "Whether to connect bones (not recommended for anim editing)",
        default     = False
    )
    
    image_ext : bpy.props.EnumProperty(
        items =
        (
            ("PNG", ".PNG", "Load a PNG image"),
            ("JPG", ".JPG", "Load a JPG image"),
            ("JPEG", ".JPEG", "Load a JPEG image"),
            ("TGA", ".TGA", "Load a TGA image"),
            ("BMP", ".BMP", "Load a BMP image"),
            ("TIF", ".TIF", "Load a TIF image"),
            ("TIFF", ".TIFF", "Load a TIFF image"),
            ("NONE", "None", "Don't import textures from images" )
        ),
        name        = "Image extension",
        description = "Image extension to search textures in"
    )

    #######################################################
    def draw(self, context):
        layout = self.layout

        layout.prop(self, "load_txd")
        layout.prop(self, "connect_bones")
        layout.prop(self, "image_ext")
        
    #######################################################
    def execute(self, context):
        
        for file in [os.path.join(self.directory,file.name) for file in self.files]:
            dff_importer.import_dff(
                {
                    'file_name'    : file,
                    'image_ext'    : self.image_ext,
                    'connect_bones': self.connect_bones
                }
            )
        return {'FINISHED'}

    #######################################################
    def invoke(self, context, event):
        
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

#######################################################
def import_dff_func(self, context):
    
    self.layout.operator(IMPORT_OT_dff.bl_idname, text="GTA Renderware (.dff, .col)")

#######################################################
def export_dff_func(self, context):

    self.layout.operator(EXPORT_OT_dff.bl_idname, text="GTA Renderware (.dff, .col)")

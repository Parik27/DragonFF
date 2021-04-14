import bpy
import os
from bpy_extras.io_utils import ImportHelper, ExportHelper

from ..ops import dff_exporter, dff_importer, col_importer

#######################################################
class EXPORT_OT_dff(bpy.types.Operator, ExportHelper):
    
    bl_idname      = "export_dff.scene"
    bl_description = "Export a Renderware DFF or COL File"
    bl_label       = "DragonFF DFF (.dff)"
    filename_ext   = ".dff"

    filepath       : bpy.props.StringProperty(name="File path",
                                              maxlen=1024,
                                              default="",
                                              subtype='FILE_PATH')
    
    filter_glob    : bpy.props.StringProperty(default="*.dff;*.col",
                                              options={'HIDDEN'})
    
    directory      : bpy.props.StringProperty(maxlen=1024,
                                              default="",
                                              subtype='FILE_PATH')

    mass_export     :  bpy.props.BoolProperty(
        name        = "Mass Export",
        default     = False
    )

    export_coll     : bpy.props.BoolProperty(
        name        = "Export Collision",
        default     = True
    )
    
    only_selected   :  bpy.props.BoolProperty(
        name        = "Only Selected",
        default     = False
    )
    reset_positions :  bpy.props.BoolProperty(
        name        = "Preserve Positions",
        description = "Don't set object positions to (0,0,0)",
        default     = False
    )
    export_version  : bpy.props.EnumProperty(
        items =
        (
            ('0x33002', "GTA 3 (v3.3.0.2)", "Grand Theft Auto 3 PC (v3.3.0.2)"),
            ('0x34003', "GTA VC (v3.4.0.3)", "Grand Theft Auto VC PC (v3.4.0.3)"),
            ('0x36003', "GTA SA (v3.6.0.3)", "Grand Theft Auto SA PC (v3.6.0.3)"),
            ('custom', "Custom", "Custom RW Version")
        ),
        name = "Version Export"
    )
    custom_version      : bpy.props.StringProperty(
        maxlen=7,
        default="",
        name = "Custom Version")

    #######################################################
    def verify_rw_version(self):
        if len(self.custom_version) != 7:
            return False

        for i, char in enumerate(self.custom_version):
            if i % 2 == 0 and not char.isdigit():
                return False
            if i % 2 == 1 and not char == '.':
                return False

        return True
    
    #######################################################
    def draw(self, context):
        layout = self.layout

        layout.prop(self, "mass_export")

        if self.mass_export:
            box = layout.box()
            row = box.row()
            row.label(text="Mass Export:")

            row = box.row()
            row.prop(self, "reset_positions")

        layout.prop(self, "only_selected")
        layout.prop(self, "export_coll")
        layout.prop(self, "export_version")

        if self.export_version == 'custom':
            col = layout.column()
            col.alert = not self.verify_rw_version()
            icon = "ERROR" if col.alert else "NONE"
            
            col.prop(self, "custom_version", icon=icon)
        return None

    #######################################################
    def get_selected_rw_version(self):

        if self.export_version != "custom":
            return int(self.export_version, 0)
        
        else:
            return int(
                "0x%c%c%c0%c" % (self.custom_version[0],
                                 self.custom_version[2],
                                 self.custom_version[4],
                                 self.custom_version[6]),
                0)
    
    #######################################################
    def execute(self, context):

        if self.export_version == "custom":
            if not self.verify_rw_version():
                self.report({"ERROR_INVALID_INPUT"}, "Invalid RW Version")
                return {'FINISHED'}
        
        dff_exporter.export_dff(
            {
                "file_name"      : self.filepath,
                "directory"      : self.directory,
                "selected"       : self.only_selected,
                "mass_export"    : self.mass_export,
                "version"        : self.get_selected_rw_version(),
                "export_coll"    : self.export_coll
            }
        )

        # Save settings of the export in scene custom properties for later
        context.scene['dragonff_imported_version'] = self.export_version
        context.scene['dragonff_custom_version']   = self.custom_version
            
        return {'FINISHED'}

    #######################################################
    def invoke(self, context, event):
        if 'dragonff_imported_version' in context.scene:
            self.export_version = context.scene['dragonff_imported_version']
        if 'dragonff_custom_version' in context.scene:
            self.custom_version = context.scene['dragonff_custom_version']
        
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

#######################################################
class IMPORT_OT_dff(bpy.types.Operator, ImportHelper):
    
    bl_idname      = "import_scene.dff"
    bl_description = 'Import a Renderware DFF or COL File'
    bl_label       = "DragonFF DFF (.dff)"

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

    read_mat_split  :  bpy.props.BoolProperty(
        name        = "Read Material Split",
        description = "Whether to read material split for loading triangles",
        default     = False
    )

    load_images : bpy.props.BoolProperty(
        name    = "Scan for Images",
        default = True
    )

    remove_doubles  :  bpy.props.BoolProperty(
        name        = "Use Edge Split",
        default     = True
    )
    group_materials :  bpy.props.BoolProperty(
        name        = "Group Similar Materials",
        default     = True
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
            ("TIFF", ".TIFF", "Load a TIFF image")
        ),
        name        = "Extension",
        description = "Image extension to search textures in"
    )

    #######################################################
    def draw(self, context):
        layout = self.layout

        layout.prop(self, "load_txd")
        layout.prop(self, "connect_bones")
        
        box = layout.box()
        box.prop(self, "load_images")
        if self.load_images:
            box.prop(self, "image_ext")
        
        layout.prop(self, "read_mat_split")
        layout.prop(self, "remove_doubles")
        layout.prop(self, "group_materials")
        
    #######################################################
    def execute(self, context):
        
        for file in [os.path.join(self.directory,file.name) for file in self.files] if self.files else [self.filepath]:
            if file.endswith(".col"):
                col_importer.import_col_file(file, os.path.basename(file))
                            
            else:
                # Set image_ext to none if scan images is disabled
                image_ext = self.image_ext
                if not self.load_images:
                    image_ext = None
                    
                importer = dff_importer.import_dff(
                    {
                        'file_name'      : file,
                        'image_ext'      : image_ext,
                        'connect_bones'  : self.connect_bones,
                        'use_mat_split'  : self.read_mat_split,
                        'remove_doubles' : self.remove_doubles,
                        'group_materials': self.group_materials
                    }
                )

                if importer.warning != "":
                    self.report({'WARNING'}, importer.warning)

                version = importer.version

                # Set imported version to scene settings for use later in export.
                if version in ['0x33002', '0x34003', '0x36003']:
                    context.scene['dragonff_imported_version'] = version
                else:
                    context.scene['dragonff_imported_version'] = "custom"
                    context.scene['dragonff_custom_version'] = "{}.{}.{}.{}".format(
                        *(version[i] for i in [2,3,4,6])
                    ) #convert hex to x.x.x.x format
                
        return {'FINISHED'}

    #######################################################
    def invoke(self, context, event):
        
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

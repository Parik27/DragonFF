import bpy
import os
from bpy_extras.io_utils import ImportHelper, ExportHelper
import time

from ..ops import dff_exporter, dff_importer, col_importer
from ..ops.state import State

#######################################################
class EXPORT_OT_dff(bpy.types.Operator, ExportHelper):
    
    bl_idname           = "export_dff.scene"
    bl_description      = "Export a Renderware DFF or COL File"
    bl_label            = "DragonFF DFF (.dff)"
    filename_ext        = ".dff"

    filepath            : bpy.props.StringProperty(name="File path",
                                              maxlen=1024,
                                              default="",
                                              subtype='FILE_PATH')
    
    filter_glob         : bpy.props.StringProperty(default="*.dff;*.col",
                                              options={'HIDDEN'})
    
    directory           : bpy.props.StringProperty(maxlen=1024,
                                              default="",
                                              subtype='FILE_PATH')

    mass_export         : bpy.props.BoolProperty(
        name            = "Mass Export",
        default         = False
    )

    export_coll         : bpy.props.BoolProperty(
        name            = "Export Collision",
        default         = True
    )
    
    export_frame_names  : bpy.props.BoolProperty(
        name            = "Export Frame Names",
        default         = True
    )
    
    exclude_geo_faces   : bpy.props.BoolProperty(
        name            = "Exclude Geometry Faces",
        description     = "Exclude faces from the Geometry section and force export Bin Mesh PLG",
        default         = False
    )
    
    only_selected       : bpy.props.BoolProperty(
        name            = "Only Selected",
        default         = False
    )
    
    preserve_positions     : bpy.props.BoolProperty(
        name            = "Preserve Positions",
        description     = "Don't set object positions to (0,0,0)",
        default         = True
    )
    
    export_version      : bpy.props.EnumProperty(
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

    from_outliner       : bpy.props.BoolProperty(
        name="Was invoked from the Outliner context menu",
        default=False
    )

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

        # Exporting from the Outliner context menu indicates just the active object, so hide these options for clarity
        if not self.from_outliner:
            layout.prop(self, "mass_export")

            if self.mass_export:
                box = layout.box()
                row = box.row()
                row.label(text="Mass Export:")

                row = box.row()
                row.prop(self, "preserve_positions")

            layout.prop(self, "only_selected")
        else:
            layout.prop(self, "preserve_positions")

        layout.prop(self, "export_coll")
        layout.prop(self, "export_frame_names")
        layout.prop(self, "exclude_geo_faces")
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

        start = time.time ()
        try:
            dff_exporter.export_dff(
                {
                    "file_name"          : self.filepath,
                    "directory"          : self.directory,
                    "selected"           : False if self.from_outliner else self.only_selected,
                    "mass_export"        : False if self.from_outliner else self.mass_export,
                    "preserve_positions" : self.preserve_positions,
                    "version"            : self.get_selected_rw_version(),
                    "export_coll"        : self.export_coll,
                    "export_frame_names" : self.export_frame_names,
                    "exclude_geo_faces"  : self.exclude_geo_faces,
                    "from_outliner"      : self.from_outliner
                }
            )
            self.report({"INFO"}, f"Finished export in {time.time() - start:.2f}s")

        except dff_exporter.DffExportException as e:
            self.report({"ERROR"}, str(e))

        # Save settings of the export in scene custom properties for later
        context.scene['dragonff_imported_version'] = self.export_version
        context.scene['dragonff_custom_version']   = self.custom_version
            
        return {'FINISHED'}

    #######################################################
    def invoke(self, context, event):
        # Set good defaults for when invoked from Outliner context menu (probably used with a map edit in mind)
        if self.from_outliner:
            self.filepath = bpy.context.view_layer.objects.active.name
            self.export_coll = False
            self.preserve_positions = False

        if 'dragonff_imported_version' in context.scene:
            self.export_version = context.scene['dragonff_imported_version']
        if 'dragonff_custom_version' in context.scene:
            self.custom_version = context.scene['dragonff_custom_version']

        if not self.filepath:
            if context.blend_data.filepath:
                self.filepath = context.blend_data.filepath
            else:
                self.filepath = "untitled"

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

#######################################################
class IMPORT_OT_dff(bpy.types.Operator, ImportHelper):
    
    bl_idname      = "import_scene.dff"
    bl_description = 'Import a Renderware DFF or COL File'
    bl_label       = "DragonFF DFF (.dff, .col)"

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
        default     = False
    )

    txd_filename :  bpy.props.StringProperty(
        name        = "Custom TXD File Name",
        description = "File name used for importing the TXD file. Leave blank if TXD name is same as DFF name",
        maxlen      = 256,
        default     = "",
    )

    skip_mipmaps :  bpy.props.BoolProperty(
        name        = "Skip mipmaps",
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

    import_normals  :  bpy.props.BoolProperty(
        name        = "Import Custom Normals",
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
            ("TIFF", ".TIFF", "Load a TIFF image")
        ),
        name        = "Extension",
        description = "Image extension to search textures in"
    )

    #######################################################
    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.prop(self, "load_txd")
        if self.load_txd:
            box.prop(self, "skip_mipmaps")
            box.prop(self, "txd_filename", text="File name")

        layout.prop(self, "connect_bones")
        
        box = layout.box()
        box.prop(self, "load_images")
        if self.load_images:
            box.prop(self, "image_ext")
        
        layout.prop(self, "read_mat_split")
        layout.prop(self, "remove_doubles")
        layout.prop(self, "import_normals")
        layout.prop(self, "group_materials")
        
    #######################################################
    def execute(self, context):
        
        for file in [os.path.join(self.directory,file.name) for file in self.files] if self.files else [self.filepath]:
            if file.endswith(".col"):
                col_list = col_importer.import_col_file(file, os.path.basename(file))
                # Move all collisions to a top collection named for the file they came from
                collection = bpy.data.collections.new(os.path.basename(file))
                context.scene.collection.children.link(collection)
                for c in col_list:
                    context.scene.collection.children.unlink(c)
                    collection.children.link(c)

            else:
                # Set image_ext to none if scan images is disabled
                image_ext = self.image_ext
                if not self.load_images:
                    image_ext = None
                    
                importer = dff_importer.import_dff(
                    {
                        'file_name'      : file,
                        'load_txd'       : self.load_txd,
                        'txd_filename'   : self.txd_filename,
                        'skip_mipmaps'   : self.skip_mipmaps,
                        'image_ext'      : image_ext,
                        'connect_bones'  : self.connect_bones,
                        'use_mat_split'  : self.read_mat_split,
                        'remove_doubles' : self.remove_doubles,
                        'group_materials': self.group_materials,
                        'import_normals' : self.import_normals
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

#######################################################
class SCENE_OT_dff_frame_move(bpy.types.Operator):

    bl_idname           = "scene.dff_frame_move"
    bl_description      = "Move the active frame up/down in the list"
    bl_label            = "Move Frame"

    direction           : bpy.props.EnumProperty(
        items =
        (
            ("UP", "", ""),
            ("DOWN", "", "")
        )
    )

    #######################################################
    def execute(self, context):

        def append_children_recursive(ob):
            for ch in ob.children:
                children.append(ch)
                append_children_recursive(ch)

        State.update_scene(context.scene)

        scene_dff = context.scene.dff
        active_index = scene_dff.frames_active
        frames_num = len(scene_dff.frames)

        if frames_num < 2:
            return {'CANCELLED'}

        if self.direction == "UP":
            obj1 = scene_dff.frames[active_index].obj

            new_index = active_index - 1
            if new_index < 0:
                return {'CANCELLED'}

            obj2 = scene_dff.frames[new_index].obj
            if obj2 == obj1.parent:
                return {'CANCELLED'}

            obj1.dff.frame_index = new_index
            obj2.dff.frame_index = active_index
            scene_dff.frames.move(new_index, active_index)
            scene_dff.frames_active = new_index

        else:
            obj1 = scene_dff.frames[active_index].obj
            if (3, 1, 0) > bpy.app.version:
                children = []
                append_children_recursive(obj1)
            else:
                children = obj1.children_recursive

            new_index = active_index + 1
            for frame in scene_dff.frames[new_index:]:
                if frame.obj in children:
                    new_index += 1
                else:
                    break

            if new_index >= frames_num:
                return {'CANCELLED'}

            for frame in scene_dff.frames[active_index:new_index]:
                frame.obj.dff.frame_index += 1
            scene_dff.frames[new_index].obj.dff.frame_index = active_index
            scene_dff.frames.move(new_index, active_index)
            scene_dff.frames_active = active_index + 1

        return {'FINISHED'}

#######################################################
class SCENE_OT_dff_atomic_move(bpy.types.Operator):

    bl_idname           = "scene.dff_atomic_move"
    bl_description      = "Move the active atomic up/down in the list"
    bl_label            = "Move Atomic"

    direction           : bpy.props.EnumProperty(
        items =
        (
            ("UP", "", ""),
            ("DOWN", "", "")
        )
    )

    #######################################################
    def execute(self, context):
        State.update_scene(context.scene)

        scene_dff = context.scene.dff
        active_index = scene_dff.atomics_active
        atomics_num = len(scene_dff.atomics)

        if atomics_num < 2:
            return {'CANCELLED'}

        step = -1 if self.direction == "UP" else 1
        new_index = active_index + step

        if new_index < 0 or new_index >= atomics_num:
            return {'CANCELLED'}

        obj1 = scene_dff.atomics[active_index].obj
        obj2 = scene_dff.atomics[new_index].obj

        obj1.dff.atomic_index = new_index
        obj2.dff.atomic_index = active_index
        scene_dff.atomics.move(new_index, active_index)
        scene_dff.atomics_active = new_index

        return {'FINISHED'}

#######################################################
class SCENE_OT_dff_update(bpy.types.Operator):

    bl_idname           = "scene.dff_update"
    bl_description      = "Update the list of objects"
    bl_label            = "Update Scene"


    #######################################################
    def execute(self, context):
        State.update_scene(context.scene)
        return {'FINISHED'}

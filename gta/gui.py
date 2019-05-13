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
import os
from . import dff_importer, dff_exporter, col_importer

from bpy_extras.io_utils import ImportHelper, ExportHelper

#######################################################
class EXPORT_OT_dff(bpy.types.Operator, ExportHelper):
    
    bl_idname      = "export_dff.scene"
    bl_description = "Export a Renderware DFF or COL File"
    bl_label       = "DragonFF DFF (.dff)"
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
    reset_positions =  bpy.props.BoolProperty(
        name        = "Preserve Positions",
        description = "Don't set object positions to (0,0,0)",
        default     = False
    )
    export_version  = bpy.props.EnumProperty(
        items =
        (
            ('0x33002', "GTA 3 (v3.3.0.2)", "Grand Theft Auto 3 PC (v3.3.0.2)"),
            ('0x34003', "GTA VC (v3.4.0.3)", "Grand Theft Auto VC PC (v3.4.0.3)"),
            ('0x36003', "GTA SA (v3.6.0.3)", "Grand Theft Auto SA PC (v3.6.0.3)"),
            ('custom', "Custom", "Custom RW Version")
        ),
        name = "Version Export"
    )
    custom_version      = bpy.props.StringProperty(
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
                "version"        : self.get_selected_rw_version()
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
    
    #filter_folder = bpy.props.BoolProperty(default=True, options={'HIDDEN'})

#######################################################
class IMPORT_OT_dff(bpy.types.Operator, ImportHelper):
    
    bl_idname      = "import_scene.dff"
    bl_description = 'Import a Renderware DFF or COL File'
    bl_label       = "DragonFF DFF (.dff)"

    filter_glob   = bpy.props.StringProperty(default="*.dff;*.col",
                                              options={'HIDDEN'})
    
    directory     = bpy.props.StringProperty(maxlen=1024,
                                              default="",
                                              subtype='FILE_PATH',
                                              options={'HIDDEN'})
    
    # Stores all the file names to read (not just the firsst)
    files = bpy.props.CollectionProperty(
        type    = bpy.types.OperatorFileListElement,
        options = {'HIDDEN'}
    )

    # Stores a single file path
    filepath = bpy.props.StringProperty(
         name        = "File Path",
         description = "Filepath used for importing the DFF/COL file",
         maxlen      = 1024,
         default     = "",
         options     = {'HIDDEN'}
     )

    
    load_txd =  bpy.props.BoolProperty(
        name        = "Load TXD file",
        default     = True
    )

    connect_bones =  bpy.props.BoolProperty(
        name        = "Connect Bones",
        description = "Whether to connect bones (not recommended for anim editing)",
        default     = False
    )

    read_mat_split  =  bpy.props.BoolProperty(
        name        = "Read Material Split",
        description = "Whether to read material split for loading triangles",
        default     = False
    )

    load_images = bpy.props.BoolProperty(
        name    = "Scan for Images",
        default = True
    )

    remove_doubles  =  bpy.props.BoolProperty(
        name        = "Use Edge Split",
        default     = True
    )

    group_materials =  bpy.props.BoolProperty(
        name        = "Group Similar Materials",
        default     = True
    )
    
    image_ext = bpy.props.EnumProperty(
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
        
        for file in [os.path.join(self.directory,file.name) for file in self.files]:
            if file.endswith(".col"):
                col_importer.import_col_file(file, os.path.basename(file))
                            
            else:
                # Set image_ext to none if scan images is disabled
                image_ext = self.image_ext
                if not self.load_images:
                    image_ext = None
                    
                version = dff_importer.import_dff(
                    {
                        'file_name'      : file,
                        'image_ext'      : image_ext,
                        'connect_bones'  : self.connect_bones,
                        'use_mat_split'  : self.read_mat_split,
                        'remove_doubles' : self.remove_doubles,
                        'group_materials': self.group_materials
                    }
                )

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
class MATERIAL_PT_dffMaterials(bpy.types.Panel):

    bl_idname      = "MATERIAL_PT_dffMaterials"
    bl_label       = "DragonFF - Export Material"
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context     = "material"

    ambient     =  bpy.props.BoolProperty(
        name        = "Export Material",
        default     = False
    )

    #######################################################
    def draw_col_menu(self, context):

        layout = self.layout
        settings = context.material.dff

        props = [["col_mat_index", "Material"],
                 ["col_brightness", "Brightness"],
                 ["col_light", "Light"]]
        
        for prop in props:
            self.draw_labelled_prop(layout.row(), settings, [prop[0]], prop[1])

    #######################################################
    def draw_labelled_prop(self, row, settings, props, label, text=""):

        row.label(text=label)
        for prop in props:
            row.prop(settings, prop, text=text)
        
    #######################################################
    def draw_env_map_box(self, context, box):

        settings = context.material.dff

        box.row().prop(context.material.dff, "export_env_map")
        if settings.export_env_map:
            box.row().prop(settings, "env_map_tex", text="Texture")

            self.draw_labelled_prop(
                box.row(), settings, ["env_map_coef"], "Coefficient")
            self.draw_labelled_prop(
                box.row(), settings, ["env_map_fb_alpha"], "Use FB Alpha")

    #######################################################
    def draw_bump_map_box(self, context, box):

        settings = context.material.dff
        box.row().prop(settings, "export_bump_map")
        
        if settings.export_bump_map:
            box.row().prop(settings, "bump_map_tex", text="Diffuse Texture")

    #######################################################
    def draw_uv_anim_box(self, context, box):

        settings = context.material.dff

        box.row().prop(settings, "export_animation")
        if settings.export_animation:
            box.row().prop(settings, "animation_name", text="Name")
            
            
    #######################################################
    def draw_refl_box(self, context, box):

        settings = context.material.dff
        box.row().prop(settings, "export_reflection")

        if settings.export_reflection:
            self.draw_labelled_prop(
                box.row(), settings, ["reflection_scale_x", "reflection_scale_y"],
                "Scale"
            )
            self.draw_labelled_prop(
                box.row(), settings, ["reflection_offset_x", "reflection_offset_y"],
                "Offset"
            )
            self.draw_labelled_prop(
                box.row(), settings, ["reflection_intensity"], "Intensity"
            )

    #######################################################
    def draw_specl_box(self, context, box):

        settings = context.material.dff
        box.row().prop(settings, "export_specular")

        if settings.export_specular:
            self.draw_labelled_prop(
                box.row(), settings, ["specular_level"], "Level"
            )
            box.row().prop(settings, "specular_texture", text="Texture")
        
    #######################################################
    def draw_mesh_menu(self, context):

        layout = self.layout
        settings = context.material.dff

        layout.prop(settings, "ambient")

        # This is for conveniently setting the base colour from the settings
        # without removing the texture node
        
        try:

            if bpy.app.version >= (2, 80, 0):
                prop = context.material.node_tree.nodes["Principled BSDF"].inputs[0]
                prop_val = "default_value"
            else:
                prop = context.material
                prop_val = "diffuse_color"
                
            row = layout.row()
            row.prop(
                prop,
                prop_val,
                text="Color")
            
            row.prop(settings,
                     "preset_mat_cols",
                     text="",
                     icon="MATERIAL",
                     icon_only=True
            )
            
        except Exception as e:
            print(e)
                
        
        self.draw_env_map_box  (context, layout.box())
        self.draw_bump_map_box (context, layout.box())
        self.draw_refl_box     (context, layout.box())
        self.draw_specl_box    (context, layout.box())
        self.draw_uv_anim_box  (context, layout.box())

    #######################################################
    # Callback function from preset_mat_cols enum
    def set_preset_color(self, context):
        try:
            color = eval(context.material.dff.preset_mat_cols)
            color = [i / 255 for i in color]
                
            if bpy.app.version >= (2, 80, 0):                
                node = context.material.node_tree.nodes["Principled BSDF"]
                node.inputs[0].default_value = color

            # Viewport color in Blender 2.8 and Material color in 2.79.
            context.material.diffuse_color = color[:-1]

        except Exception as e:
            print(e)
        
    #######################################################
    def draw(self, context):

        if not context.material.dff:
            return
        
        if context.material.dff.is_col_material:
            self.draw_col_menu(context)
            return

        self.draw_mesh_menu(context)
    
#######################################################
def import_dff_func(self, context):
    
    self.layout.operator(IMPORT_OT_dff.bl_idname, text="DragonFF DFF (.dff)")

#######################################################
def export_dff_func(self, context):

    self.layout.operator(EXPORT_OT_dff.bl_idname, text="DragonFF DFF (.dff)")

#######################################################
class OBJECT_PT_dffObjects(bpy.types.Panel):

    bl_idname      = "OBJECT_PT_dffObjects"
    bl_label       = "DragonFF - Export Object"
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context     = "object"

    #######################################################
    def draw_labelled_prop(self, row, settings, props, label, text=""):
        
        row.label(text=label)
        for prop in props:
            row.prop(settings, prop, text=text)


    #######################################################
    def validate_pipeline(self, pipeline):

        try:
            int(pipeline, 0)
        except ValueError:
            return False

        return True
            
    #######################################################
    def draw_mesh_menu(self, context):

        layout = self.layout
        settings = context.object.dff

        box = layout.box()
        box.prop(settings, "pipeline", text="Pipeline")
        if settings.pipeline == 'CUSTOM':
            col = box.column()
            
            col.alert = not self.validate_pipeline(settings.custom_pipeline)
            icon = "ERROR" if col.alert else "NONE"

            col.prop(settings, "custom_pipeline", icon=icon, text="Custom Pipeline")
        
        properties = [         
            ["export_normals", "Export Normals"],
            ["uv_map1", "UV Map 1"],
            ["uv_map2", "UV Map 2"],
            ["day_cols", "Day Vertex Colours"],
            ["night_cols", "Night Vertex Colours"],
        ]

        for property in properties:
            layout.prop(settings, property[0], text=property[1])
    
    #######################################################
    def draw_obj_menu(self, context):

        layout = self.layout
        settings = context.object.dff

        layout.prop(settings, "type", text="Type")

        if settings.type == 'OBJ':
            if context.object.type == 'MESH':
                self.draw_mesh_menu(context)
    
    #######################################################
    def draw(self, context):

        if not context.object.dff:
            return
        
        self.draw_obj_menu(context)
    
# Custom properties
#######################################################
class DFFMaterialProps(bpy.types.PropertyGroup):

    ambient           = bpy.props.FloatProperty  (name="Ambient Shading")
    
    # Environment Map
    export_env_map    = bpy.props.BoolProperty   (name="Environment Map")
    env_map_tex       = bpy.props.StringProperty ()
    env_map_coef      = bpy.props.FloatProperty  ()
    env_map_fb_alpha  = bpy.props.BoolProperty   ()

    # Bump Map
    export_bump_map   = bpy.props.BoolProperty   (name="Bump Map")
    bump_map_tex      = bpy.props.StringProperty ()

    # Reflection
    export_reflection    = bpy.props.BoolProperty  (name="Reflection Material")
    reflection_scale_x   = bpy.props.FloatProperty ()
    reflection_scale_y   = bpy.props.FloatProperty ()
    reflection_offset_x  = bpy.props.FloatProperty ()
    reflection_offset_y  = bpy.props.FloatProperty ()
    reflection_intensity = bpy.props.FloatProperty ()
    
    # Specularity
    export_specular  = bpy.props.BoolProperty(name="Specular Material")
    specular_level   = bpy.props.FloatProperty  ()
    specular_texture = bpy.props.StringProperty ()

    # Collision Data
    is_col_material = bpy.props.BoolProperty()
    col_brightness  = bpy.props.IntProperty()
    col_light       = bpy.props.IntProperty()
    col_mat_index   = bpy.props.IntProperty()

    # UV Animation
    export_animation = bpy.props.BoolProperty   (name="UV Animation")
    animation_name   = bpy.props.StringProperty ()

    # Pre-set Material Colours
    preset_mat_cols = bpy.props.EnumProperty(
        items =
        (
            ("[255, 60, 0, 255]", "Right Tail Light", ""),
            ("[185, 255, 0, 255]", "Left Tail Light", ""),
            ("[0, 255, 200, 255]", "Right Headlight", ""),
            ("[255, 175, 0, 255]", "Left Headlight", ""),
            ("[0, 255, 255, 255]", "4 Colors Paintjob", ""),
            ("[255, 0, 175, 255]", "Secondary Color", ""),
            ("[60, 255, 0, 255]", "Primary Color", ""),
            ("[184, 255, 0, 255]", "ImVehFT - Breaklight L", ""),
            ("[255, 59, 0, 255]", "ImVehFT - Breaklight R", ""),
            ("[255, 173, 0, 255]", "ImVehFT - Revlight L", ""),
            ("[0, 255, 198, 255]", "ImVehFT - Revlight R", ""),
            ("[255, 174, 0, 255]", "ImVehFT - Foglight L", ""),
            ("[0, 255, 199, 255]", "ImVehFT - Foglight R", ""),
            ("[183, 255, 0, 255]", "ImVehFT - Indicator LF", ""),
            ("[255, 58, 0, 255]", "ImVehFT - Indicator RF", ""),
            ("[182, 255, 0, 255]", "ImVehFT - Indicator LM", ""),
            ("[255, 57, 0, 255]", "ImVehFT - Indicator RM", ""),
            ("[181, 255, 0, 255]", "ImVehFT - Indicator LR", ""),
            ("[255, 56, 0, 255]", "ImVehFT - Indicator RR", ""),
            ("[0, 16, 255, 255]", "ImVehFT - Light Night", ""),
            ("[0, 17, 255, 255]", "ImVehFT - Light All-day", ""),
            ("[0, 18, 255, 255]", "ImVehFT - Default Day", "")
        ),
        update = MATERIAL_PT_dffMaterials.set_preset_color
    )
    
    def register():
        bpy.types.Material.dff = bpy.props.PointerProperty(type=DFFMaterialProps)

#######################################################
class DFFObjectProps(bpy.types.PropertyGroup):

    # Atomic Properties
    type = bpy.props.EnumProperty(
        items = (
            ('OBJ', 'Object', 'Object will be exported as a mesh or a dummy'),
            ('COL', 'Collision Object', 'Object is a collision object'),
            ('NON', "Don't export", 'Object will NOT be exported.')
        )
    )

    # Mesh properties
    pipeline = bpy.props.EnumProperty(
        items = (
            ('NONE', 'None', 'Export without setting a pipeline'),
            ('0x53F20098', 'Buildings', 'Refl. Building Pipleine (0x53F20098)'),
            (
                '0x53F2009A',
                'Night Vertex Colors',
                'Night Vertex Colors (0x53F2009C)'
            ),
            ('CUSTOM', 'Custom Pipeline', 'Set a different pipeline')
        )
    )
    custom_pipeline = bpy.props.StringProperty()
    export_normals = bpy.props.BoolProperty()
    uv_map1 = bpy.props.BoolProperty()
    uv_map2 = bpy.props.BoolProperty()
    day_cols = bpy.props.BoolProperty()
    night_cols = bpy.props.BoolProperty()
    
    
    #######################################################    
    def register():
        bpy.types.Object.dff = bpy.props.PointerProperty(type=DFFObjectProps)

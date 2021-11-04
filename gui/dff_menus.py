import bpy
from .dff_ot import EXPORT_OT_dff, IMPORT_OT_dff
from .col_ot import EXPORT_OT_col

#######################################################
class MATERIAL_PT_dffMaterials(bpy.types.Panel):

    bl_idname      = "MATERIAL_PT_dffMaterials"
    bl_label       = "DragonFF - Export Material"
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context     = "material"

    ambient     :  bpy.props.BoolProperty(
        name        = "Export Material",
        default     = False
    )

    #######################################################
    def draw_col_menu(self, context):

        layout = self.layout
        settings = context.material.dff

        props = [["col_mat_index", "Material"],
                 ["col_flags", "Flags"],
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
            box.row().prop(settings, "bump_map_tex", text="Height Map Texture")

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
            
        except Exception:
            pass
                
        
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

        if not context.material or not context.material.dff:
            return
        
        if context.object.dff.type == 'COL':
            self.draw_col_menu(context)
            return

        self.draw_mesh_menu(context)

#######################################################@
class DFF_MT_ExportChoice(bpy.types.Menu):
    bl_label = "DragonFF"

    def draw(self, context):
        self.layout.operator(EXPORT_OT_dff.bl_idname,
                             text="DragonFF DFF (.dff)")
        self.layout.operator(EXPORT_OT_col.bl_idname,
                             text="DragonFF Collision (.col)")
            
        
#######################################################
def import_dff_func(self, context):
    self.layout.operator(IMPORT_OT_dff.bl_idname, text="DragonFF DFF (.dff)")

#######################################################
def export_dff_func(self, context):
    self.layout.menu("DFF_MT_ExportChoice", text="DragonFF")

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
        
        box.prop(settings, "export_normals", text="Export Normals")
        box.prop(settings, "export_binsplit", text="Export Bin Mesh PLG")
        box.prop(settings, "light", text="Enable Lighting")
        box.prop(settings, "modulate_color", text="Enable Modulate Material Color")
            
        properties = [         
            ["day_cols", "Day Vertex Colours"],
            ["night_cols", "Night Vertex Colours"],
        ]

        box = layout.box()
        box.label(text="Export Vertex Colours")
        
        for property in properties:
            box.prop(settings, property[0], text=property[1])

        box = layout.box()
        box.label(text="Export UV Maps")

        box.prop(settings, "uv_map1", text="UV Map 1")

        # Second UV Map can only be disabled if the first UV map is enabled.
        if settings.uv_map1:
            box.prop(settings, "uv_map2", text="UV Map 2")

    #######################################################
    def draw_col_menu(self, context):
        layout = self.layout
        settings = context.object.dff

        box = layout.box()
        box.label(text="Material Surface")
        
        box.prop(settings, "col_material", text="Material")
        box.prop(settings, "col_flags", text="Flags")
        box.prop(settings, "col_brightness", text="Brightness")
        box.prop(settings, "col_light", text="Light")

        pass
            
    #######################################################
    def draw_obj_menu(self, context):

        layout = self.layout
        settings = context.object.dff

        layout.prop(settings, "type", text="Type")

        if settings.type == 'OBJ':
            if context.object.type == 'MESH':
                self.draw_mesh_menu(context)

        elif settings.type == 'COL':
            if context.object.type == 'EMPTY':
                self.draw_col_menu(context)
    
    #######################################################
    def draw(self, context):

        if not context.object.dff:
            return
        
        self.draw_obj_menu(context)
    
# Custom properties
#######################################################
class DFFMaterialProps(bpy.types.PropertyGroup):

    ambient           : bpy.props.FloatProperty  (name="Ambient Shading", default=1)
    
    # Environment Map
    export_env_map    : bpy.props.BoolProperty   (name="Environment Map")
    env_map_tex       : bpy.props.StringProperty ()
    env_map_coef      : bpy.props.FloatProperty  ()
    env_map_fb_alpha  : bpy.props.BoolProperty   ()

    # Bump Map
    export_bump_map   : bpy.props.BoolProperty   (name="Bump Map")
    bump_map_tex      : bpy.props.StringProperty ()

    # Reflection
    export_reflection    : bpy.props.BoolProperty  (name="Reflection Material")
    reflection_scale_x   : bpy.props.FloatProperty ()
    reflection_scale_y   : bpy.props.FloatProperty ()
    reflection_offset_x  : bpy.props.FloatProperty ()
    reflection_offset_y  : bpy.props.FloatProperty ()
    reflection_intensity : bpy.props.FloatProperty ()
    
    # Specularity
    export_specular  : bpy.props.BoolProperty(name="Specular Material")
    specular_level   : bpy.props.FloatProperty  ()
    specular_texture : bpy.props.StringProperty ()

    # Collision Data
    col_flags       : bpy.props.IntProperty()
    col_brightness  : bpy.props.IntProperty()
    col_light       : bpy.props.IntProperty()
    col_mat_index   : bpy.props.IntProperty()

    # UV Animation
    export_animation : bpy.props.BoolProperty   (name="UV Animation")
    animation_name   : bpy.props.StringProperty ()

    # Pre-set Material Colours
    preset_mat_cols : bpy.props.EnumProperty(
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
    type : bpy.props.EnumProperty(
        items = (
            ('OBJ', 'Object', 'Object will be exported as a mesh or a dummy'),
            ('COL', 'Collision Object', 'Object is a collision object'),
            ('SHA', 'Shadow Object', 'Object is a shadow object'),
            ('NON', "Don't export", 'Object will NOT be exported.')
        )
    )

    # Mesh properties
    pipeline : bpy.props.EnumProperty(
        items = (
            ('NONE', 'None', 'Export without setting a pipeline'),
            ('0x53F20098', 'Buildings', 'Refl. Building Pipleine (0x53F20098)'),
            (
                '0x53F2009A',
                'Night Vertex Colors',
                'Night Vertex Colors (0x53F2009C)'
            ),
            ('CUSTOM', 'Custom Pipeline', 'Set a different pipeline')
        ),
        name="Pipeline",
        description="Select the Engine rendering pipeline"
    )
    custom_pipeline : bpy.props.StringProperty(name="Custom Pipeline")
    
    export_normals : bpy.props.BoolProperty(
        default=True,
        description="Whether Normals will be exported. (Disable for Map objects)"
    )

    light : bpy.props.BoolProperty(
        default=True,
        description="Enable rpGEOMETRYLIGHT flag"
    )

    modulate_color : bpy.props.BoolProperty(
        default=True,
        description="Enable rpGEOMETRYMODULATEMATERIALCOLOR flag"
    )
    
    uv_map1 : bpy.props.BoolProperty(
        default=True,
        description="First UV Map will be exported")
    
    uv_map2 : bpy.props.BoolProperty(
        default=True,
        description="Second UV Map will be exported"
    )
    
    day_cols : bpy.props.BoolProperty(
        default=True,
        description="Whether Day Vertex Prelighting Colours will be exported"
    )
    
    night_cols : bpy.props.BoolProperty(
        default=True,
        description="Extra prelighting colours. (Tip: Disable export normals)"
    )
    
    export_binsplit : bpy.props.BoolProperty(
        default=True,
        description="Enabling will increase file size, but will increase\
compatibiility with DFF Viewers"
    )

    col_material : bpy.props.IntProperty(
        default = 12,
        description = "Material used for the Sphere/Cone"
    )

    col_flags : bpy.props.IntProperty(
        default = 0,
        description = "Flags for the Sphere/Cone"
    )

    col_brightness : bpy.props.IntProperty(
        default = 0,
        description = "Brightness used for the Sphere/Cone"
    )
    
    col_light : bpy.props.IntProperty(
        default = 0,
        description = "Light used for the Sphere/Cone"
    )
    
    #######################################################    
    def register():
        bpy.types.Object.dff = bpy.props.PointerProperty(type=DFFObjectProps)

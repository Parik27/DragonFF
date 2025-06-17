import bpy
from .dff_ot import EXPORT_OT_dff, IMPORT_OT_dff, \
    IMPORT_OT_txd, \
    OBJECT_OT_dff_generate_bone_props, \
    OBJECT_OT_dff_set_parent_bone, OBJECT_OT_dff_clear_parent_bone
from .dff_ot import SCENE_OT_dff_frame_move, SCENE_OT_dff_atomic_move, SCENE_OT_dff_update
from .col_ot import EXPORT_OT_col, OBJECT_OT_facegoups_col, COLLECTION_OT_dff_generate_bounds
from .ext_2dfx_menus import EXT2DFXObjectProps, EXT2DFXMenus
from .ide_ot import EXPORT_OT_ide
from .ipl_ot import EXPORT_OT_ipl

texture_filters_items = (
    ("0", "Disabled", ""),
    ("1", "Nearest", "Point sampled"),
    ("2", "Linear", "Bilinear"),
    ("3", "Mip Nearest", "Point sampled per pixel MipMap"),
    ("4", "Mip Linear", "Bilinear per pixel MipMap"),
    ("5", "Linear Mip Nearest", "MipMap interp point sampled"),
    ("6", "Linear Mip Linear", "Trilinear")
)

texture_uv_addressing_items = (
    ("0", "Disabled", ""),
    ("1", "Wrap", ""),
    ("2", "Mirror", ""),
    ("3", "Clamp", ""),
    ("4", "Border", "")
)

box_indices = (
    (0, 1), (1, 3), (3, 2), (2, 0),
    (2, 3), (3, 7), (7, 6), (6, 2),
    (6, 7), (7, 5), (5, 4), (4, 6),
    (4, 5), (5, 1), (1, 0), (0, 4),
    (2, 6), (6, 4), (4, 0), (0, 2),
    (7, 3), (3, 1), (1, 5), (5, 7),
)

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
                 ["col_day_light", "Day Light"],
                 ["col_night_light", "Night Light"]]
        
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
    def draw_texture_prop_box(self, context, box):

        settings = context.material.dff

        box.label(text="Texture properties")

        box.prop(settings, "tex_filters", text="Filters")
        self.draw_labelled_prop(
            box.row(), settings, ["tex_u_addr", "tex_v_addr"], "UV addressing")

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

            node = next((node for node in context.material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED'), None)
            prop = node.inputs[0]
            prop_val = "default_value"
                
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


        self.draw_texture_prop_box (context, layout.box())
        self.draw_env_map_box      (context, layout.box())
        self.draw_bump_map_box     (context, layout.box())
        self.draw_refl_box         (context, layout.box())
        self.draw_specl_box        (context, layout.box())
        self.draw_uv_anim_box      (context, layout.box())

    #######################################################
    # Callback function from preset_mat_cols enum
    def set_preset_color(self, context):
        try:
            color = (int(x) for x in context.material.dff.preset_mat_cols[1:-1].split(","))
            color = [i / 255 for i in color]
                
            node = next((node for node in context.material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED'), None)
            node.inputs[0].default_value = color

            # Viewport color in Blender 2.8 and Material color in 2.79.
            context.material.diffuse_color = color

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
        op = self.layout.operator(EXPORT_OT_dff.bl_idname,
                             text="DragonFF DFF (.dff)")
        op.from_outliner = False
        op = self.layout.operator(EXPORT_OT_col.bl_idname,
                             text="DragonFF Collision (.col)")
        op.use_active_collection = False
        self.layout.operator(EXPORT_OT_ide.bl_idname,
                             text="DragonFF IDE (.ide)")
        self.layout.operator(EXPORT_OT_ipl.bl_idname,
                             text="DragonFF IPL (.ipl)")


    #######################################################
def import_dff_func(self, context):
    self.layout.operator(IMPORT_OT_dff.bl_idname, text="DragonFF DFF (.dff, col)")

#######################################################
def export_dff_func(self, context):
    self.layout.menu("DFF_MT_ExportChoice", text="DragonFF")

#######################################################
def export_dff_outliner(self, context):
    self.layout.separator()
    self.layout.operator_context = 'INVOKE_DEFAULT'
    op = self.layout.operator(EXPORT_OT_dff.bl_idname, text="Export collection objects as DFF (.dff)")
    op.from_outliner = True

#######################################################
def export_col_outliner(self, context):
    self.layout.separator()
    self.layout.operator_context = 'INVOKE_DEFAULT'
    op = self.layout.operator(EXPORT_OT_col.bl_idname, text="Export collection as collision container (.col)")
    op.use_active_collection = True
    op.filepath = context.collection.name

#######################################################@
class DFF_MT_EditArmature(bpy.types.Menu):
    bl_label = "DragonFF"

    def draw(self, context):
        self.layout.operator(OBJECT_OT_dff_generate_bone_props.bl_idname, text="Generate Bone Properties")

#######################################################
def edit_armature_dff_func(self, context):
    self.layout.separator()
    self.layout.menu("DFF_MT_EditArmature", text="DragonFF")

#######################################################@
class DFF_MT_Pose(bpy.types.Menu):
    bl_label = "DragonFF"

    def draw(self, context):
        self.layout.operator(OBJECT_OT_dff_set_parent_bone.bl_idname, text="Set Object Parent To Bone")
        self.layout.operator(OBJECT_OT_dff_clear_parent_bone.bl_idname, text="Clear Object Parent")

#######################################################
def pose_dff_func(self, context):
    self.layout.separator()
    self.layout.menu("DFF_MT_Pose", text="DragonFF")

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
        box.prop(settings, "export_normals", text="Export Normals")
        box.prop(settings, "export_split_normals", text="Export Custom Split Normals")
        box.prop(settings, "export_binsplit", text="Export Bin Mesh PLG")
        box.prop(settings, "triangle_strip", text="Use Triangle Strip")
        box.prop(settings, "light", text="Enable Lighting")
        box.prop(settings, "modulate_color", text="Enable Modulate Material Color")

        row = box.row()
        if settings.is_frame_locked:
            row.enabled = False
        row.prop(settings, "is_frame", text="Export As Frame")

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

        box = layout.box()
        box.label(text="Atomic")
        box.prop(settings, "pipeline", text="Pipeline")
        if settings.pipeline == 'CUSTOM':
            col = box.column()

            col.alert = not self.validate_pipeline(settings.custom_pipeline)
            icon = "ERROR" if col.alert else "NONE"

            col.prop(settings, "custom_pipeline", icon=icon, text="Custom Pipeline")

        box.prop(settings, "right_to_render", text="Right To Render")

    #######################################################
    def draw_col_menu(self, context):
        layout = self.layout
        settings = context.object.dff

        box = layout.box()
        box.label(text="Material Surface")
        
        box.prop(settings, "col_material", text="Material")
        box.prop(settings, "col_flags", text="Flags")
        box.prop(settings, "col_brightness", text="Brightness")
        box.prop(settings, "col_day_light", text="Day Light")
        box.prop(settings, "col_night_light", text="Night Light")

    #######################################################
    def draw_2dfx_menu(self, context):
        layout = self.layout
        settings = context.object.dff.ext_2dfx

        layout.prop(settings, "effect", text="Effect")
        EXT2DFXMenus.draw_menu(int(settings.effect), layout, context)

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
            if context.object.type == 'MESH':
                settings = context.scene.dff
                box = layout.box()
                box.prop(settings, "draw_facegroups", text="Display Face Groups")
                box.label(text="Face Group Generation:")
                box.prop(settings, 'face_group_min', slider=True)
                box.prop(settings, 'face_group_max', slider=True)
                box.prop(settings, 'face_group_avoid_smalls')
                box.operator(OBJECT_OT_facegoups_col.bl_idname, text=OBJECT_OT_facegoups_col.bl_label)

        elif settings.type == '2DFX':
            self.draw_2dfx_menu(context)

    #######################################################
    def draw(self, context):

        if not context.object.dff:
            return
        
        self.draw_obj_menu(context)

#######################################################
class OBJECT_PT_dffCollections(bpy.types.Panel):

    bl_idname = "OBJECT_PT_dffCollections"
    bl_label  = "DragonFF - Export Collection"

    # Collections Properties panel was introduced in Blender 3.0
    if (3, 0, 0) > bpy.app.version:
        bl_space_type  = "VIEW_3D"
        bl_region_type = "UI"
        bl_category    = "DragonFF"
    else:
        bl_space_type  = "PROPERTIES"
        bl_region_type = "WINDOW"
        bl_context     = "collection"

    #######################################################
    def draw_labelled_prop(self, row, settings, props, label, text=""):

        row.label(text=label)
        for prop in props:
            row.prop(settings, prop, text=text)

    #######################################################
    def draw_collection_menu(self, context):

        layout = self.layout
        settings = context.collection.dff

        layout.prop(settings, "type", text="Type")

        box = layout.box()
        box.label(text="Bounds")

        box.prop(settings, "auto_bounds", text="Auto Bounds")
        if not settings.auto_bounds:
            box.prop(context.scene.dff, "draw_bounds", text="Display Bounds")
            box.prop(settings, "bounds_min", text="Min")
            box.prop(settings, "bounds_max", text="Max")
            box.operator(COLLECTION_OT_dff_generate_bounds.bl_idname, text="Generate")

    #######################################################
    def draw(self, context):

        if not context.collection.dff:
            return

        self.draw_collection_menu(context)

# Custom properties
#######################################################
class DFFMaterialProps(bpy.types.PropertyGroup):

    ambient           : bpy.props.FloatProperty  (name="Ambient Shading", default=1)
    tex_filters       : bpy.props.EnumProperty  (items=texture_filters_items, default="0")
    tex_u_addr        : bpy.props.EnumProperty  (name="", items=texture_uv_addressing_items, default="0")
    tex_v_addr        : bpy.props.EnumProperty  (name="", items=texture_uv_addressing_items, default="0")

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
    col_flags       : bpy.props.IntProperty(min=0, max=255)
    col_brightness  : bpy.props.IntProperty(min=0, max=255)
    col_day_light   : bpy.props.IntProperty(min=0, max=15)
    col_night_light : bpy.props.IntProperty(min=0, max=15)
    col_mat_index   : bpy.props.IntProperty(min=0, max=255)

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
            ("[255, 0, 255, 255]", "Fourth Color", ""),
            ("[0, 255, 255, 255]", "Third Color", ""),
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
        
#######################################################
class DFFObjectProps(bpy.types.PropertyGroup):

    # Atomic Properties
    type : bpy.props.EnumProperty(
        items = (
            ('OBJ', 'Object', 'Object will be exported as a mesh or a dummy'),
            ('COL', 'Collision Object', 'Object is a collision object'),
            ('SHA', 'Shadow Object', 'Object is a shadow object'),
            ('2DFX', '2DFX', 'Object is a 2D effect'),
            ('NON', "Don't export", 'Object will NOT be exported.')
        )
    )

    is_frame : bpy.props.BoolProperty(
        default     = False,
        description = "Object will be exported as a frame"
    )

    # Mesh properties
    export_normals : bpy.props.BoolProperty(
        default=True,
        description="Whether Normals will be exported. (Disable for Map objects)"
    )

    export_split_normals : bpy.props.BoolProperty(
        default=False,
        description="Whether Custom Split Normals will be exported (Flat Shading)."
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

    triangle_strip : bpy.props.BoolProperty(
        default=False,
        description="Use Triangle Strip instead of Triangle List for Bin Mesh PLG"
    )

    col_material : bpy.props.IntProperty(
        default = 12,
        min = 0,
        max = 255,
        description = "Material used for the Sphere/Cone"
    )

    col_flags : bpy.props.IntProperty(
        default = 0,
        min = 0,
        max = 255,
        description = "Flags for the Sphere/Cone"
    )

    col_brightness : bpy.props.IntProperty(
        default = 0,
        min = 0,
        max = 255,
        description = "Brightness used for the Sphere/Cone"
    )

    col_day_light : bpy.props.IntProperty(
        default = 0,
        min = 0,
        max = 15,
        description = "Day Light used for the Sphere/Cone"
    )

    col_night_light : bpy.props.IntProperty(
        default = 0,
        min = 0,
        max = 15,
        description = "Night Light used for the Sphere/Cone"
    )

    # Atomic properties
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

    right_to_render : bpy.props.IntProperty(
        default = 1,
        min = 0,
        description = "Right To Render value (only for skinned object)"
    )

    frame_index : bpy.props.IntProperty(
        default = 2**31-1,
        min = 0,
        max = 2**31-1,
        options = {'SKIP_SAVE', 'HIDDEN'}
    )

    atomic_index : bpy.props.IntProperty(
        default = 2**31-1,
        min = 0,
        max = 2**31-1,
        options = {'SKIP_SAVE', 'HIDDEN'}
    )

    # 2DFX properties
    ext_2dfx : bpy.props.PointerProperty(type=EXT2DFXObjectProps)

    # Miscellaneous properties
    is_frame_locked : bpy.props.BoolProperty()

#######################################################
class DFFCollectionProps(bpy.types.PropertyGroup):

    type : bpy.props.EnumProperty(
        items = (
            ('CMN',   'Common', 'Common collection'),
            ('NON',   "Don't export", 'Objects in this collection will NOT be exported')
        )
    )

    auto_bounds: bpy.props.BoolProperty(
        default = True,
        description = "Calculate bounds automatically"
    )

    bounds_min: bpy.props.FloatVectorProperty()
    bounds_max: bpy.props.FloatVectorProperty()

#######################################################
class TXDImportPanel(bpy.types.Panel):

    bl_label       = "DragonFF - TXD Import"
    bl_idname      = "SCENE_PT_txdImport"
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = "scene"
    bl_options     = {'DEFAULT_CLOSED'}

    #######################################################
    def draw(self, context):
        layout = self.layout
        layout.operator(IMPORT_OT_txd.bl_idname)

#######################################################
class DFF_UL_FrameItems(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if item and item.obj:
            layout.label(text=item.obj.name, icon=item.icon)

    def draw_filter(self, context, layout):
        layout.prop(context.scene.dff, "filter_collection", toggle=True)

    def filter_items(self, context, data, propname):
        frames = context.scene.dff.frames
        frames_num = len(frames)

        flt_flags = [self.bitflag_filter_item | (1 << 0)] * frames_num

        active_object = context.view_layer.objects.active
        active_collections = {active_object.users_collection} if active_object else None

        if active_collections and context.scene.dff.filter_collection:
            for i, frame in enumerate(frames):
                if not active_collections.issubset({frame.obj.users_collection}):
                    flt_flags[i] &= ~self.bitflag_filter_item

        return flt_flags, list(range(frames_num))

#######################################################
class DFF_UL_AtomicItems(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if item and item.obj:
            text = item.obj.name
            if item.frame_obj and not item.obj.dff.is_frame:
                text += " [%s]" % item.frame_obj.name
            layout.label(text=text, icon='MESH_DATA')

    def draw_filter(self, context, layout):
        layout.prop(context.scene.dff, "filter_collection", toggle=True)

    def filter_items(self, context, data, propname):
        atomics = context.scene.dff.atomics
        atomics_num = len(atomics)

        flt_flags = [self.bitflag_filter_item | (1 << 0)] * atomics_num

        active_object = context.view_layer.objects.active
        active_collections = {active_object.users_collection} if active_object else None

        if active_collections and context.scene.dff.filter_collection:
            for i, atomic in enumerate(atomics):
                if not active_collections.issubset({atomic.obj.users_collection}):
                    flt_flags[i] &= ~self.bitflag_filter_item

        return flt_flags, list(range(atomics_num))

#######################################################
class SCENE_PT_dffFrames(bpy.types.Panel):

    bl_idname      = "SCENE_PT_dffFrames"
    bl_label       = "DragonFF - Frames"
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context     = "scene"
    bl_options     = {'DEFAULT_CLOSED'}

    def draw(self, context):
        scene_dff = context.scene.dff

        layout = self.layout
        row = layout.row()

        col = row.column()
        col.template_list(
            "DFF_UL_FrameItems",
            "",
            scene_dff,
            "frames",
            scene_dff,
            "frames_active",
            rows=3,
            maxrows=8,
            sort_lock=True
        )

        if len(scene_dff.frames) > 1:
            col = row.column(align=True)
            col.operator(SCENE_OT_dff_frame_move.bl_idname, icon='TRIA_UP', text="").direction = 'UP'
            col.operator(SCENE_OT_dff_frame_move.bl_idname, icon='TRIA_DOWN', text="").direction = 'DOWN'

        row = layout.row()
        col = row.column()
        col.prop(scene_dff, "real_time_update", toggle=True)
        if not scene_dff.real_time_update:
            col = row.column()
            col.operator(SCENE_OT_dff_update.bl_idname, icon='FILE_REFRESH', text="")

#######################################################
class SCENE_PT_dffAtomics(bpy.types.Panel):

    bl_idname      = "SCENE_PT_dffAtomics"
    bl_label       = "DragonFF - Atomics"
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context     = "scene"
    bl_options     = {'DEFAULT_CLOSED'}

    def draw(self, context):
        scene_dff = context.scene.dff

        layout = self.layout
        row = layout.row()

        col = row.column()
        col.template_list(
            "DFF_UL_AtomicItems",
            "",
            scene_dff,
            "atomics",
            scene_dff,
            "atomics_active",
            rows=3,
            maxrows=8,
            sort_lock=True
        )

        if len(scene_dff.atomics) > 1:
            col = row.column(align=True)
            col.operator(SCENE_OT_dff_atomic_move.bl_idname, icon='TRIA_UP', text="").direction = 'UP'
            col.operator(SCENE_OT_dff_atomic_move.bl_idname, icon='TRIA_DOWN', text="").direction = 'DOWN'

        row = layout.row()
        col = row.column()
        col.prop(scene_dff, "real_time_update", toggle=True)
        if not scene_dff.real_time_update:
            col = row.column()
            col.operator(SCENE_OT_dff_update.bl_idname, icon='FILE_REFRESH', text="")

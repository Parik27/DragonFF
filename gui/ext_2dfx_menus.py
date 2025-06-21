import bpy

from bpy_extras.io_utils import ImportHelper

from .ext_2dfx_ot import *
from ..gtaLib import txd

particle_txd_names = [
    'wincrack_32', 'white', 'waterwake', 'waterclear256', 'txgrassbig1',
    'txgrassbig0', 'target256', 'shad_rcbaron', 'shad_ped', 'shad_heli',
    'shad_exp', 'shad_car', 'shad_bike', 'seabd32', 'roadsignfont',
    'particleskid', 'lunar', 'lockonFire', 'lockon', 'lamp_shad_64',
    'headlight1', 'headlight', 'handman', 'finishFlag', 'coronastar',
    'coronaringb', 'coronareflect', 'coronamoon', 'coronaheadlightline', 'cloudmasked',
    'cloudhigh', 'cloud1', 'carfx1', 'bloodpool_64'
]

#######################################################
def particle_txd_search_func(props, context, edit_text):
    return particle_txd_names

#######################################################
class IMPORT_OT_ParticleTXDNames(bpy.types.Operator, ImportHelper):

    bl_idname = "import.particle_txd_names"
    bl_label = "Import texture names from particle.txd"
    bl_description = 'Import texture names from particle.txd'

    filename : bpy.props.StringProperty(subtype='FILE_PATH')

    filter_glob : bpy.props.StringProperty(default="*.txd",
                                              options={'HIDDEN'})

    def execute(self, context):
        global particle_txd_names
        txd_file = txd.txd()
        txd_file.load_file(self.filepath)
        particle_txd_names = [tex.name for tex in txd_file.native_textures]
        return {'FINISHED'}

#######################################################
class EXT2DFXObjectProps(bpy.types.PropertyGroup):

    effect : bpy.props.EnumProperty(
        items = (
            ('0', 'Light', 'Light'),
            ('1', 'Particle', 'Particle'),
            ('3', 'Ped Attractor', 'Ped Attractor'),
            ('4', 'Sun Glare', 'Sun Glare'),
            ('6', 'Enter Exit', 'Enter Exit'),
            ('7', 'Road Sign', 'Road Sign'),
            ('8', 'Trigger Point', 'Trigger Point'),
            ('9', 'Cover Point', 'Cover Point'),
            ('10', 'Escalator', 'Escalator'),
        )
    )

    ped_attractor_type : bpy.props.EnumProperty(
        items = (
            ('0', 'ATM', 'Ped uses ATM (at day time only)'),
            ('1', 'Seat', 'Ped sits (at day time only)'),
            ('2', 'Stop', 'Ped stands (at day time only)'),
            ('3', 'Pizza', 'Ped stands for few seconds'),
            ('4', 'Shelter', 'Ped goes away after spawning, but stands if weather is rainy'),
            ('5', 'Trigger Script', 'Launches an external script'),
            ('6', 'Look At', 'Ped looks at object, then goes away'),
            ('7', 'Scripted', ''),
            ('8', 'Park', 'Ped lays (at day time only, ped goes away after 6 PM)'),
            ('9', 'Step', 'Ped sits on steps'),
        )
    )

    val_byte_1 : bpy.props.IntProperty(min = 0, max = 255)
    val_byte_2 : bpy.props.IntProperty(min = 0, max = 255)
    val_byte_3 : bpy.props.IntProperty(min = 0, max = 255)
    val_byte_4 : bpy.props.IntProperty(min = 0, max = 255)

    val_short_1 : bpy.props.IntProperty(min = 0, max = 65535)

    val_int_1 : bpy.props.IntProperty()

    val_float_1 : bpy.props.FloatProperty()
    val_float_2 : bpy.props.FloatProperty()

    val_str8_1 : bpy.props.StringProperty(maxlen = 7)

    val_str24_1 : bpy.props.StringProperty(maxlen = 23)

    val_vector_1 : bpy.props.FloatVectorProperty(default = [0, 0, 0])
    val_vector_2 : bpy.props.FloatVectorProperty(default = [0, 0, 0])
    val_vector_3 : bpy.props.FloatVectorProperty(default = [0, 0, 0])

    val_euler_1 : bpy.props.FloatVectorProperty(
        default = [0, 0, 0],
        subtype='EULER',
        min=-math.pi * 2,
        max=math.pi * 2,
        step=100
    )

    val_euler_2 : bpy.props.FloatVectorProperty(
        default = [0, 0, 0],
        subtype='EULER',
        min=-math.pi * 2,
        max=math.pi * 2,
        step=100
    )

    val_degree_1 : bpy.props.FloatProperty(
        min = -180,
        max = 180
    )

    val_degree_2 : bpy.props.FloatProperty(
        min = -180,
        max = 180
    )

    val_hour_1 : bpy.props.IntProperty(min = 0, max = 24)
    val_hour_2 : bpy.props.IntProperty(min = 0, max = 24)

    val_chance_1 : bpy.props.IntProperty(min = 0, max = 100)

    escalator_direction : bpy.props.EnumProperty(
        items = (
            ('0', 'Down', 'Down Direction'),
            ('1', 'Up', 'Up Direction'),
        )
    )

#######################################################
class Light2DFXObjectProps(bpy.types.PropertyGroup):

    alpha : bpy.props.FloatProperty(
        min = 0,
        max = 1,
        default = 200 / 255
    )

    corona_far_clip : bpy.props.FloatProperty(
        description = "Corona visibility distance"
    )

    point_light_range : bpy.props.FloatProperty(
        description = "Point light source radius"
    )

    export_view_vector : bpy.props.BoolProperty()

    view_vector : bpy.props.IntVectorProperty(
        min = -128,
        max = 127,
        default = [0, 0, 100]
    )

    corona_size : bpy.props.FloatProperty()

    shadow_size : bpy.props.FloatProperty()

    corona_show_mode : bpy.props.EnumProperty(
        items = (
            ('0', 'DEFAULT', ''),
            ('1', 'RANDOM_FLASHING', ''),
            ('2', 'RANDOM_FLASHIN_ALWAYS_AT_WET_WEATHER', ''),
            ('3', 'LIGHTS_ANIM_SPEED_4X', ''),
            ('4', 'LIGHTS_ANIM_SPEED_2X', ''),
            ('5', 'LIGHTS_ANIM_SPEED_1X', ''),
            ('6', 'WARNLIGHT', ''),
            ('7', 'TRAFFICLIGHT', ''),
            ('8', 'TRAINCROSSLIGHT', ''),
            ('9', 'DISABLED', ''),
            ('10', 'AT_RAIN_ONLY', 'Enables only in rainy weather'),
            ('11', '5S_ON_5S_OFF', '5s - on, 5s - off'),
            ('12', '6S_ON_4S_OFF', '6s - on, 4s - off'),
            ('13', '6S_ON_4S_OFF_2', '6s - on, 4s - off'),
        )
    )

    corona_flare_type : bpy.props.IntProperty(
        min = 0,
        max = 2,
        description = "Type of highlights for the corona"
    )

    shadow_color_multiplier : bpy.props.IntProperty(
        min = 0,
        max = 255,
        description = "Shadow intensity"
    )

    corona_enable_reflection : bpy.props.BoolProperty(
        description = "Enable corona reflection on wet asphalt"
    )

    # NOTE: bpy.props.StringProperty supports a search argument since version 3.3
    if bpy.app.version < (3, 3, 0):
        corona_tex_name : bpy.props.StringProperty(
            maxlen = 23,
            description = "Corona texture name in particle.txd"
        )

        shadow_tex_name : bpy.props.StringProperty(
            maxlen = 23,
            description = "Shadow texture name in particle.txd"
        )

    else:
        corona_tex_name : bpy.props.StringProperty(
            maxlen = 23,
            description = "Corona texture name in particle.txd",
            search = particle_txd_search_func
        )

        shadow_tex_name : bpy.props.StringProperty(
            maxlen = 23,
            description = "Shadow texture name in particle.txd",
            search = particle_txd_search_func
        )

    shadow_z_distance : bpy.props.IntProperty(
        min = 0,
        max = 255,
        description = "Maximum distance for drawing shadow"
    )

    flag1_corona_check_obstacles : bpy.props.BoolProperty(
        description = "If there are any objects between the corona and the camera, the corona will not be rendered"
    )

    flag1_fog_type : bpy.props.IntProperty(
        min = 0,
        max = 3,
        description = "Fog type for point light source"
    )

    flag1_without_corona : bpy.props.BoolProperty()

    flag1_corona_only_at_long_distance : bpy.props.BoolProperty()

    flag1_at_day : bpy.props.BoolProperty()

    flag1_at_night : bpy.props.BoolProperty()

    flag1_blinking1 : bpy.props.BoolProperty(
        description = "Blinks (almost imperceptibly)"
    )

    flag2_corona_only_from_below : bpy.props.BoolProperty(
        description = "The corona is visible only from below (when the height of the camera position is less than the height of the light source)"
    )

    flag2_blinking2 : bpy.props.BoolProperty(
        description = "Blinks (very fast)"
    )

    flag2_update_height_above_ground : bpy.props.BoolProperty()

    flag2_check_view_vector : bpy.props.BoolProperty(
        description = "Works only if the camera is in a certain position (View Vector)"
    )

    flag2_blinking3 : bpy.props.BoolProperty(
        description = "Blinks (randomly)"
    )

#######################################################
class RoadSign2DFXObjectProps(bpy.types.PropertyGroup):

    size : bpy.props.FloatVectorProperty(
        size = 2,
        min = 0,
        description = "Scale"
    )

    color : bpy.props.EnumProperty(
        items = (
            ('0', 'White', ''),
            ('1', 'Black', ''),
            ('2', 'Grey', ''),
            ('3', 'Red', ''),
        ),
        description = "Text color"
    )

#######################################################
class EXT2DFXMenus:

    #######################################################
    def draw_light_menu(layout, context):
        obj = context.object
        box = layout.box()

        if obj.type != 'LIGHT':
            box.label(text="This effect is only available for light objects", icon="ERROR")
            return

        settings = obj.data.ext_2dfx

        box.prop(obj.data, "color", text="Color")
        box.prop(settings, "alpha", text="Alpha")
        box.prop(settings, "point_light_range", text="Point Light Range")
        box.prop(settings, "export_view_vector", text="Export View Vector")
        if settings.export_view_vector:
            box.prop(settings, "view_vector", text="View Vector")

        box = layout.box()
        box.label(text="Corona")
        box.prop(settings, "corona_show_mode", text="Show Mode")
        box.prop(settings, "corona_far_clip", text="Far Clip")
        box.prop(settings, "corona_size", text="Size")
        box.prop(settings, "corona_enable_reflection", text="Enable Reflection")
        box.prop(settings, "corona_flare_type", text="Flare Type")
        box.prop(settings, "corona_tex_name", text="Texture")

        box = layout.box()
        box.label(text="Shadow")
        box.prop(settings, "shadow_size", text="Size")
        box.prop(settings, "shadow_color_multiplier", text="Color Multiplier")
        box.prop(settings, "shadow_z_distance", text="Z Distance")
        box.prop(settings, "shadow_tex_name", text="Texture")

        box = layout.box()
        box.label(text="Flags")
        box.prop(settings, "flag1_corona_check_obstacles", text="Corona Check Obstacles")
        box.prop(settings, "flag1_fog_type", text="Fog Type")
        box.prop(settings, "flag1_without_corona", text="Without Corona")
        box.prop(settings, "flag1_corona_only_at_long_distance", text="Corona Only At Long Distance")
        box.prop(settings, "flag2_corona_only_from_below", text="Corona Only From Below")
        box.prop(settings, "flag1_at_day", text="At Day")
        box.prop(settings, "flag1_at_night", text="At Night")
        box.prop(settings, "flag2_update_height_above_ground", text="Update Height Above Ground")
        box.prop(settings, "flag2_check_view_vector", text="Check View Vector")
        box.prop(settings, "flag1_blinking1", text="Blinking 1")
        box.prop(settings, "flag2_blinking2", text="Blinking 2")
        box.prop(settings, "flag2_blinking3", text="Blinking 3")

        if bpy.app.version >= (3, 3, 0):
            box = layout.box()
            box.operator(IMPORT_OT_ParticleTXDNames.bl_idname)

    #######################################################
    def draw_particle_menu(layout, context):
        obj = context.object
        settings = obj.dff.ext_2dfx

        box = layout.box()
        box.prop(settings, "val_str24_1", text="Effect Name")

    #######################################################
    def draw_ped_attractor(layout, context):
        obj = context.object
        settings = obj.dff.ext_2dfx

        box = layout.box()
        box.prop(settings, "ped_attractor_type", text="Type")
        box.prop(settings, "val_euler_1", text="Queue Direction")
        box.prop(obj, "rotation_euler", text="Use Direction")
        box.prop(settings, "val_euler_2", text="Forward Direction")
        box.prop(settings, "val_str8_1", text="External Script")
        box.prop(settings, "val_chance_1", text="Ped Existing Probability")
        box.prop(settings, "val_int_1", text="Unknown")

    #######################################################
    def draw_sun_glare_menu(layout, context):
        pass

    #######################################################
    def draw_enter_exit_menu(layout, context):
        obj = context.object
        settings = obj.dff.ext_2dfx

        box = layout.box()
        box.prop(settings, "val_degree_1", text="Enter Angle")
        box.prop(settings, "val_float_1", text="Approximation Radius X")
        box.prop(settings, "val_float_2", text="Approximation Radius Y")
        box.prop(settings, "val_vector_1", text="Exit Location")
        box.prop(settings, "val_degree_2", text="Exit Angle")
        box.prop(settings, "val_short_1", text="Interior")
        box.prop(settings, "val_byte_1", text="Flags")
        box.prop(settings, "val_byte_2", text="Sky Color")
        box.prop(settings, "val_str8_1", text="Interior Name")
        box.prop(settings, "val_hour_1", text="Time On")
        box.prop(settings, "val_hour_2", text="Time Off")
        box.prop(settings, "val_byte_3", text="Flags 2")
        box.prop(settings, "val_byte_4", text="Unknown")

    #######################################################
    def draw_road_sign_menu(layout, context):
        obj = context.object
        box = layout.box()

        if obj.type != 'FONT':
            box.label(text="This effect is only available for text objects", icon="ERROR")
            return

        settings = obj.data.ext_2dfx

        box.prop(settings, "size", text="Size")
        box.prop(settings, "color", text="Color")

    #######################################################
    def draw_trigger_point_menu(layout, context):
        obj = context.object
        settings = obj.dff.ext_2dfx

        box = layout.box()
        box.prop(settings, "val_int_1", text="Point ID")

    #######################################################
    def draw_cover_point_menu(layout, context):
        obj = context.object
        settings = obj.dff.ext_2dfx

        box = layout.box()
        box.prop(settings, "val_int_1", text="Cover Type")

    #######################################################
    def draw_escalator_menu(layout, context):
        obj = context.object
        box = layout.box()

        if obj.type != 'EMPTY':
            box.label(text="This effect is only available for empty objects", icon="ERROR")
            return

        settings = obj.dff.ext_2dfx

        box.prop(settings, "val_vector_1", text="Bottom")
        box.prop(settings, "val_vector_2", text="Top")
        box.prop(settings, "val_vector_3", text="End")
        box.prop(settings, "escalator_direction", text="Direction")

    #######################################################
    def draw_menu(effect, layout, context):
        self = EXT2DFXMenus

        functions = {
            0: self.draw_light_menu,
            1: self.draw_particle_menu,
            3: self.draw_ped_attractor,
            4: self.draw_sun_glare_menu,
            6: self.draw_enter_exit_menu,
            7: self.draw_road_sign_menu,
            8: self.draw_trigger_point_menu,
            9: self.draw_cover_point_menu,
            10: self.draw_escalator_menu,
        }

        functions[effect](layout, context)

#######################################################@
class DFF_MT_Add2DFXObject(bpy.types.Menu):
    bl_label = "2DFX"

    def draw(self, context):
        self.layout.operator(OBJECT_OT_dff_add_2dfx_light.bl_idname, text="Light", icon="LIGHT")
        self.layout.operator(OBJECT_OT_dff_add_2dfx_particle.bl_idname, text="Particle", icon="PARTICLES")
        self.layout.operator(OBJECT_OT_dff_add_2dfx_sun_glare.bl_idname, text="Sun Glare", icon="LIGHT_SUN")
        self.layout.operator(OBJECT_OT_dff_add_2dfx_ped_attractor.bl_idname, text="Ped Attractor", icon="ARMATURE_DATA")
        self.layout.operator(OBJECT_OT_dff_add_2dfx_road_sign.bl_idname, text="Road Sign", icon="TEXT")
        self.layout.operator(OBJECT_OT_dff_add_2dfx_trigger_point.bl_idname, text="Trigger Point", icon="KEYFRAME")
        self.layout.operator(OBJECT_OT_dff_add_2dfx_cover_point.bl_idname, text="Cover Point", icon="MOD_PHYSICS")
        self.layout.operator(OBJECT_OT_dff_add_2dfx_escalator.bl_idname, text="Escalator", icon="MOD_ARRAY")

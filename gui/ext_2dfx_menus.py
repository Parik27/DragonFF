import bpy

#######################################################
class EXT2DFXObjectProps(bpy.types.PropertyGroup):

    effect : bpy.props.EnumProperty(
        items = (
            ('0', 'Light', 'Light'),
            ('1', 'Particle', 'Particle'),
            ('4', 'Sun Glare', 'Sun Glare'),
        )
    )

    val_str24_1 : bpy.props.StringProperty(maxlen = 23)

#######################################################
class Light2DFXObjectProps(bpy.types.PropertyGroup):

    alpha : bpy.props.FloatProperty(
        min=0,
        max=1
    )

    corona_far_clip : bpy.props.FloatProperty(
        description = "Corona visibility distance"
    )

    point_light_range : bpy.props.FloatProperty(
        description = "Point light source radius"
    )

    export_view_vector : bpy.props.BoolProperty()

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
        min=0,
        max=2,
        description = "Type of highlights for the corona"
    )

    shadow_color_multiplier : bpy.props.IntProperty(
        min=0,
        max=255,
        description = "Shadow intensity"
    )

    corona_enable_reflection : bpy.props.BoolProperty(
        description = "Enable corona reflection on wet asphalt"
    )

    corona_tex_name : bpy.props.StringProperty(
        maxlen = 23,
        description = "Corona texture name in particle.txd"
    )

    shadow_tex_name : bpy.props.StringProperty(
        maxlen = 23,
        description = "Shadow texture name in particle.txd"
    )

    shadow_z_distance : bpy.props.IntProperty(
        min=0,
        max=255,
        description = "Maximum distance for drawing shadow"
    )

    flag1_corona_check_obstacles : bpy.props.BoolProperty(
        description = "If there are any objects between the corona and the camera, the corona will not be rendered"
    )

    flag1_fog_type : bpy.props.IntProperty(
        min=0,
        max=3,
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

    flag2_udpdate_height_above_ground : bpy.props.BoolProperty()

    flag2_check_view_vector : bpy.props.BoolProperty(
        description = "Works only if the camera is in a certain position (View Vector)"
    )

    flag2_blinking3 : bpy.props.BoolProperty(
        description = "Blinks (randomly)"
    )

    #######################################################
    def register():
        bpy.types.Light.ext_2dfx = bpy.props.PointerProperty(type=Light2DFXObjectProps)

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
        box.prop(settings, "flag2_udpdate_height_above_ground", text="Udpdate Height Above Ground")
        box.prop(settings, "flag2_check_view_vector", text="Check View Vector")
        box.prop(settings, "flag1_blinking1", text="Blinking 1")
        box.prop(settings, "flag2_blinking2", text="Blinking 2")
        box.prop(settings, "flag2_blinking3", text="Blinking 3")

    #######################################################
    def draw_particle_menu(layout, context):
        obj = context.object
        settings = obj.dff.ext_2dfx

        box = layout.box()
        box.prop(settings, "val_str24_1", text="Effect Name")

    #######################################################
    def draw_sun_glare_menu(layout, context):
        pass

    #######################################################
    def draw_menu(effect, layout, context):
        self = EXT2DFXMenus

        functions = {
            0: self.draw_light_menu,
            1: self.draw_particle_menu,
            4: self.draw_sun_glare_menu,
        }

        functions[effect](layout, context)

import bpy
import math
from ..ops.ext_2dfx_importer import ext_2dfx_importer
from ..ops.importer_common import link_object

#######################################################
class Add2DFXHelper:
    bl_options = {'REGISTER', 'UNDO'}

    location: bpy.props.FloatVectorProperty(
        name="Location",
        description="Location for the newly added object",
        subtype='XYZ',
        default=(0, 0, 0)
    )

    #######################################################
    def apply_2dfx_object(self, context, obj, effect):
        obj.location = self.location
        obj.dff.type = '2DFX'
        obj.dff.ext_2dfx.effect = effect
        link_object(obj, context.collection)

        context.view_layer.objects.active = obj
        for o in context.selected_objects:
            o.select_set(False)
        obj.select_set(True)

    #######################################################
    def invoke(self, context, event):
        self.location = context.scene.cursor.location
        return self.execute(context)

#######################################################
class OBJECT_OT_dff_add_2dfx_light(bpy.types.Operator, Add2DFXHelper):

    bl_idname = "object.dff_add_2dfx_light"
    bl_label = "Add 2DFX Light"
    bl_description = "Add 2DFX Light effect object to the scene"

    color: bpy.props.FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        description = "Light color",
        min=0,
        max=1,
        default=(1, 1, 1)
    )

    #######################################################
    def execute(self, context):
        obj = ext_2dfx_importer.create_light_object(self.color)
        self.apply_2dfx_object(context, obj, '0')

        settings = obj.data.ext_2dfx
        settings.alpha = 0.784314
        settings.corona_far_clip = 200.0
        settings.point_light_range = 1.0
        settings.corona_size = 0.2
        settings.shadow_size = 0.0
        settings.corona_show_mode = '0'
        settings.corona_enable_reflection = False
        settings.corona_flare_type = 0
        settings.shadow_color_multiplier = 40
        settings.corona_tex_name = "coronastar"
        settings.shadow_tex_name = "shad_exp"
        settings.shadow_z_distance = 0

        settings.flag1_at_day = True
        settings.flag1_at_night = True

        settings.view_vector = (-110, 0, 0)
        settings.export_view_vector = True

        return {'FINISHED'}

#######################################################
class OBJECT_OT_dff_add_2dfx_particle(bpy.types.Operator, Add2DFXHelper):

    bl_idname = "object.dff_add_2dfx_particle"
    bl_label = "Add 2DFX Particle"
    bl_description = "Add 2DFX Particle effect object to the scene"

    effect: bpy.props.StringProperty(
        name="Effect Name",
        description="Effect name from effects.fxp",
        maxlen = 23,
        default="explosion_large"
    )

    #######################################################
    def execute(self, context):
        obj = ext_2dfx_importer.create_particle_object(self.effect)
        self.apply_2dfx_object(context, obj, '1')

        return {'FINISHED'}

#######################################################
class OBJECT_OT_dff_add_2dfx_ped_attractor(bpy.types.Operator, Add2DFXHelper):

    bl_idname = "object.dff_add_2dfx_ped_attractor"
    bl_label = "Add 2DFX Ped Attractor"
    bl_description = "Add 2DFX Ped Attractor effect object to the scene"

    ped_attractor_type : bpy.props.EnumProperty(
        name="Type",
        items=(
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
        ),
        default='6'
    )

    ped_existing_probability : bpy.props.IntProperty(
        name="Ped Existing Probability",
        min=0,
        max=100,
        default=75
    )

    #######################################################
    def execute(self, context):
        obj = ext_2dfx_importer.create_ped_attractor_object(
            attractor_type=self.ped_attractor_type,
            queue_euler=(math.pi / 2, 0, math.pi),
            use_euler=(math.pi / 2, 0, math.pi),
            forward_euler=(math.pi / 2, 0, 0),
            external_script='none',
            ped_existing_probability=self.ped_existing_probability,
            unk=0
        )
        self.apply_2dfx_object(context, obj, '3')

        return {'FINISHED'}

#######################################################
class OBJECT_OT_dff_add_2dfx_sun_glare(bpy.types.Operator, Add2DFXHelper):

    bl_idname = "object.dff_add_2dfx_sun_glare"
    bl_label = "Add 2DFX Sun Glare"
    bl_description = "Add 2DFX Sun Glare effect object to the scene"

    #######################################################
    def execute(self, context):
        obj = ext_2dfx_importer.create_sun_glare_object()
        self.apply_2dfx_object(context, obj, '4')

        return {'FINISHED'}

#######################################################
class OBJECT_OT_dff_add_2dfx_road_sign(bpy.types.Operator, Add2DFXHelper):

    bl_idname = "object.dff_add_2dfx_road_sign"
    bl_label = "Add 2DFX Road Sign"
    bl_description = "Add 2DFX Road Sign effect object to the scene"

    color: bpy.props.EnumProperty(
        name="Color",
        items = (
            ('0', 'White', ''),
            ('1', 'Black', ''),
            ('2', 'Grey', ''),
            ('3', 'Red', ''),
        ),
        description = "Text color"
    )

    rotation_euler: bpy.props.FloatVectorProperty(
        name="Rotation",
        description="Rotation for the newly added object",
        subtype='EULER',
        min=-math.pi * 2,
        max=math.pi * 2,
        step=100,
        default=(math.pi / 2, -math.pi / 2, -math.pi / 2)
    )

    #######################################################
    def execute(self, context):
        obj = ext_2dfx_importer.create_road_sign_object(
            body="> Text\n^ Text\n# Text",
            size=(3.9, 2.3),
            color=self.color,
            rotation_euler=self.rotation_euler
        )
        self.apply_2dfx_object(context, obj, '7')

        return {'FINISHED'}

#######################################################
class OBJECT_OT_dff_add_2dfx_trigger_point(bpy.types.Operator, Add2DFXHelper):

    bl_idname = "object.dff_add_2dfx_trigger_point"
    bl_label = "Add 2DFX Trigger Point"
    bl_description = "Add 2DFX Trigger Point effect object to the scene"

    point_id: bpy.props.IntProperty(
        name="Point ID",
        description="Point ID",
        default=0
    )

    #######################################################
    def execute(self, context):
        obj = ext_2dfx_importer.create_trigger_point_object(self.point_id)
        self.apply_2dfx_object(context, obj, '8')

        return {'FINISHED'}

#######################################################
class OBJECT_OT_dff_add_2dfx_cover_point(bpy.types.Operator, Add2DFXHelper):

    bl_idname = "object.dff_add_2dfx_cover_point"
    bl_label = "Add 2DFX Cover Point"
    bl_description = "Add 2DFX Cover Point effect object to the scene"

    angle: bpy.props.FloatProperty(
        name="Angle",
        description="Angle along the Z axis",
        subtype='ANGLE',
        min=-math.pi * 2,
        max=math.pi * 2,
        step=100,
        default=0
    )

    cover_type: bpy.props.IntProperty(
        name="Cover Type",
        description="Cover Type",
        default=1
    )

    #######################################################
    def execute(self, context):
        obj = ext_2dfx_importer.create_cover_point_object(
            cover_type=self.cover_type,
            rotation_euler=(0, 0, self.angle)
        )
        self.apply_2dfx_object(context, obj, '9')

        return {'FINISHED'}

#######################################################
class OBJECT_OT_dff_add_2dfx_escalator(bpy.types.Operator, Add2DFXHelper):

    bl_idname = "object.dff_add_2dfx_escalator"
    bl_label = "Add 2DFX Escalator"
    bl_description = "Add 2DFX Escalator effect object to the scene"

    escalator_direction : bpy.props.EnumProperty(
        name="Direction",
        description="Escalator direction",
        items = (
            ('0', 'Down', 'Down Direction'),
            ('1', 'Up', 'Up Direction'),
        )
    )

    angle: bpy.props.FloatProperty(
        name="Angle",
        description="Angle along the Z axis",
        subtype='ANGLE',
        min=-math.pi * 2,
        max=math.pi * 2,
        step=100,
        default=0
    )

    #######################################################
    def execute(self, context):
        obj = ext_2dfx_importer.create_escalator_object(
            bottom=(0.0, -2.0, 0.0),
            top=(0.0, -11.0, 6.62),
            end=(0.0, -13.0, 6.62),
            direction=self.escalator_direction,
            angle=self.angle
        )
        self.apply_2dfx_object(context, obj, '10')

        return {'FINISHED'}

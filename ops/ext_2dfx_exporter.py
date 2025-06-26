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

import math

from mathutils import Matrix, Vector

from ..gtaLib import dff

#######################################################
class ext_2dfx_exporter:

    """ Helper class for 2dfx exporting """

    #######################################################
    def __init__(self, effects):
        self.effects = effects

    #######################################################
    def export_light(self, obj, use_local_position):
        if obj.type != 'LIGHT':
            return

        FL1, FL2 = dff.Light2dfx.Flags1, dff.Light2dfx.Flags2
        settings = obj.data.ext_2dfx
        loc = obj.location if use_local_position else obj.matrix_world.translation

        entry = dff.Light2dfx(loc)
        if settings.export_view_vector:
            entry.lookDirection = settings.view_vector
        entry.color = dff.RGBA._make(
                list(int(255 * x) for x in list(obj.data.color) + [settings.alpha])
            )
        entry.coronaFarClip = settings.corona_far_clip
        entry.pointlightRange = settings.point_light_range
        entry.coronaSize = settings.corona_size
        entry.shadowSize = settings.shadow_size
        entry.coronaShowMode = int(settings.corona_show_mode)
        entry.coronaEnableReflection = int(settings.corona_enable_reflection)
        entry.coronaFlareType = settings.corona_flare_type
        entry.shadowColorMultiplier = settings.shadow_color_multiplier
        entry.coronaTexName = settings.corona_tex_name
        entry.shadowTexName = settings.shadow_tex_name
        entry.shadowZDistance = settings.shadow_z_distance

        if settings.flag1_corona_check_obstacles:
            entry.set_flag(FL1.CORONA_CHECK_OBSTACLES.value)

        entry.set_flag(settings.flag1_fog_type << 1)

        if settings.flag1_without_corona:
            entry.set_flag(FL1.WITHOUT_CORONA.value)

        if settings.flag1_corona_only_at_long_distance:
            entry.set_flag(FL1.CORONA_ONLY_AT_LONG_DISTANCE.value)

        if settings.flag1_at_day:
            entry.set_flag(FL1.AT_DAY.value)

        if settings.flag1_at_night:
            entry.set_flag(FL1.AT_NIGHT.value)

        if settings.flag1_blinking1:
            entry.set_flag(FL1.BLINKING1.value)

        if settings.flag2_corona_only_from_below:
            entry.set_flag2(FL2.CORONA_ONLY_FROM_BELOW.value)

        if settings.flag2_blinking2:
            entry.set_flag2(FL2.BLINKING2.value)

        if settings.flag2_update_height_above_ground:
            entry.set_flag2(FL2.UPDATE_HEIGHT_ABOVE_GROUND.value)

        if settings.flag2_check_view_vector:
            entry.set_flag2(FL2.CHECK_DIRECTION.value)

        if settings.flag2_blinking3:
            entry.set_flag2(FL2.BLINKING3.value)

        return entry

    #######################################################
    def export_particle(self, obj, use_local_position):
        settings = obj.dff.ext_2dfx
        loc = obj.location if use_local_position else obj.matrix_world.translation

        entry = dff.Particle2dfx(loc)
        entry.effect = settings.val_str24_1

        return entry

    #######################################################
    def export_ped_attractor(self, obj, use_local_position):
        settings = obj.dff.ext_2dfx
        loc = obj.location if use_local_position else obj.matrix_world.translation

        entry = dff.PedAttractor2dfx(loc)
        entry.type = int(settings.ped_attractor_type)
        entry.queue_direction = settings.val_euler_1.to_matrix() @ Vector((0.0, 0.0, 1.0))
        entry.use_direction = obj.matrix_world.to_quaternion() @ Vector((0.0, 0.0, 1.0))
        entry.forward_direction = settings.val_euler_2.to_matrix() @ Vector((0.0, 0.0, 1.0))
        entry.external_script = settings.val_str8_1
        entry.ped_existing_probability = settings.val_chance_1
        entry.unk = settings.val_int_1

        return entry

    #######################################################
    def export_sun_glare(self, obj, use_local_position):
        loc = obj.location if use_local_position else obj.matrix_world.translation

        entry = dff.SunGlare2dfx(loc)

        return entry

    #######################################################
    def export_enter_exit(self, obj, use_local_position):
        settings = obj.dff.ext_2dfx
        loc = obj.location if use_local_position else obj.matrix_world.translation

        entry = dff.EnterExit2dfx(loc)
        entry.enter_angle = math.radians(settings.val_degree_1)
        entry.approximation_radius_x = settings.val_float_1
        entry.approximation_radius_y = settings.val_float_2
        entry.exit_location = settings.val_vector_1
        entry.exit_angle = settings.val_degree_2
        entry.interior = settings.val_short_1
        entry._flags1 = settings.val_byte_1
        entry.sky_color = settings.val_byte_2
        entry.interior_name = settings.val_str8_1
        entry.time_on = settings.val_hour_1
        entry.time_off = settings.val_hour_2
        entry._flags2 = settings.val_byte_3
        entry.unk = settings.val_byte_4

        return entry

    #######################################################
    def export_road_sign(self, obj, use_local_position):
        if obj.type != 'FONT':
            return

        lines = obj.data.body.split("\n")[:4]
        if not lines:
            return

        lines_num = len(lines)
        while len(lines) < 4:
            lines.append("_" * 16)

        max_chars_num = 2
        for i, line in enumerate(lines):
            if len(line) < 16:
                line += (16 - len(line)) * "_"
            line = line.replace(" ", "_")[:16]
            lines[i] = line

            line_chars_num = len(line.rstrip("_"))
            if max_chars_num < line_chars_num:
                max_chars_num = line_chars_num

        max_chars_num = next((i for i in (2, 4, 8, 16) if max_chars_num <= i), max_chars_num)

        settings = obj.data.ext_2dfx

        flags = {1:1, 2:2, 3:3, 4:0}[lines_num]
        flags |= {2:1, 4:2, 8:3, 16:0}[max_chars_num] << 2
        flags |= int(settings.color) << 4

        rotation = obj.matrix_world.to_euler('ZXY')

        entry = dff.RoadSign2dfx(obj.matrix_world.translation)

        entry.rotation = Vector((
            rotation.x * (180 / math.pi),
            rotation.y * (180 / math.pi),
            rotation.z * (180 / math.pi)
        ))

        entry.text1, entry.text2, \
        entry.text3, entry.text4 = lines

        entry.size = settings.size
        entry.flags = flags

        return entry

    #######################################################
    def export_trigger_point(self, obj, use_local_position):
        settings = obj.dff.ext_2dfx
        loc = obj.location if use_local_position else obj.matrix_world.translation

        entry = dff.TriggerPoint2dfx(loc)
        entry.point_id = settings.val_int_1

        return entry

    #######################################################
    def export_cover_point(self, obj, use_local_position):
        settings = obj.dff.ext_2dfx
        loc = obj.location if use_local_position else obj.matrix_world.translation

        entry = dff.CoverPoint2dfx(loc)
        entry.cover_type = settings.val_int_1

        direction = obj.matrix_world.to_quaternion() @ Vector((0.0, 1.0, 0.0))
        direction.z = 0
        direction.normalize()

        entry.direction_x = direction.x
        entry.direction_y = direction.y

        return entry

    #######################################################
    def export_escalator(self, obj, use_local_position):
        settings = obj.dff.ext_2dfx
        loc = obj.location if use_local_position else obj.matrix_world.translation

        matrix = obj.matrix_world.to_quaternion().to_matrix().to_4x4()
        for axis in range(3):
            matrix[axis][3] = loc[axis]

        bottom = (matrix @ Matrix.Translation(settings.val_vector_1)).to_translation()
        top = (matrix @ Matrix.Translation(settings.val_vector_2)).to_translation()
        end = (matrix @ Matrix.Translation(settings.val_vector_3)).to_translation()

        entry = dff.Escalator2dfx(loc)
        entry.bottom = tuple(bottom)
        entry.top = tuple(top)
        entry.end = tuple(end)
        entry.direction = int(settings.escalator_direction)

        return entry

    #######################################################
    def export_objects(self, objects, use_local_position=False):

        """ Export objects and fill 2dfx entries """

        functions = {
            0: self.export_light,
            1: self.export_particle,
            3: self.export_ped_attractor,
            4: self.export_sun_glare,
            6: self.export_enter_exit,
            7: self.export_road_sign,
            8: self.export_trigger_point,
            9: self.export_cover_point,
            10: self.export_escalator,
        }

        ext_2dfx_objects = [obj for obj in objects if obj.dff.type == '2DFX']
        ext_2dfx_objects.sort(key=lambda obj: obj.name)

        for obj in ext_2dfx_objects:
            entry = functions[int(obj.dff.ext_2dfx.effect)](obj, use_local_position)
            if entry:
                self.effects.append_entry(entry)

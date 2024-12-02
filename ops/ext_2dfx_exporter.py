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

from ..gtaLib import dff

#######################################################
class ext_2dfx_exporter:

    """ Helper class for 2dfx exporting """

    #######################################################
    def __init__(self, effects):
        self.effects = effects

    #######################################################
    def export_light(self, obj):
        if obj.type != 'LIGHT':
            return

        FL1, FL2 = dff.Light2dfx.Flags1, dff.Light2dfx.Flags2
        settings = obj.data.ext_2dfx

        entry = dff.Light2dfx(obj.location)
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

        if settings.flag2_udpdate_height_above_ground:
            entry.set_flag2(FL2.UDPDATE_HEIGHT_ABOVE_GROUND.value)

        if settings.flag2_check_view_vector:
            entry.set_flag2(FL2.CHECK_DIRECTION.value)

        if settings.flag2_blinking3:
            entry.set_flag2(FL2.BLINKING3.value)

        return entry

    #######################################################
    def export_particle(self, obj):
        settings = obj.dff.ext_2dfx

        entry = dff.Particle2dfx(obj.location)
        entry.effect = settings.val_str24_1

        return entry

    #######################################################
    def export_sun_glare(self, obj):
        entry = dff.SunGlare2dfx(obj.location)

        return entry

    #######################################################
    def export_trigger_point(self, obj):
        settings = obj.dff.ext_2dfx

        entry = dff.TriggerPoint2dfx(obj.location)
        entry.point_id = settings.val_int_1

        return entry

    #######################################################
    def export_objects(self, objects):

        """ Export objects and fill 2dfx entries """

        functions = {
            0: self.export_light,
            1: self.export_particle,
            4: self.export_sun_glare,
            8: self.export_trigger_point,
        }

        for obj in objects:
            if obj.dff.type != '2DFX':
                continue

            entry = functions[int(obj.dff.ext_2dfx.effect)](obj)
            if entry:
                self.effects.append_entry(entry)

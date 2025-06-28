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

from math import atan2
from mathutils import Vector

#######################################################
class cull_importer:

    """ Helper class for CULL importing """

    #######################################################
    @staticmethod
    def create_cull_object(location, scale, flags, angle=0):
        obj = bpy.data.objects.new("cull", None)
        obj.empty_display_type = 'CUBE'
        obj.location = location
        obj.rotation_euler = (0, 0, angle)
        obj.scale = scale
        obj.dff.type = 'CULL'

        obj.lock_rotation[0] = True
        obj.lock_rotation[1] = True
        obj.lock_rotation_w = True

        settings = obj.dff.cull

        settings.flag_cam_close_in_for_player   = bool(flags & (1<<0))
        settings.flag_cam_stairs_for_player     = bool(flags & (1<<1))
        settings.flag_cam_1st_person_for_player = bool(flags & (1<<2))
        settings.flag_no_rain                   = bool(flags & (1<<3))
        settings.flag_no_police                 = bool(flags & (1<<4))
        settings.flag_5                         = bool(flags & (1<<5))
        settings.flag_do_need_to_load_collision = bool(flags & (1<<6))
        settings.flag_7                         = bool(flags & (1<<7))
        settings.flag_police_abandon_cars       = bool(flags & (1<<8))
        settings.flag_in_room_for_audio         = bool(flags & (1<<9))
        settings.flag_water_fudge               = bool(flags & (1<<10))
        settings.flag_military_zone             = bool(flags & (1<<12))
        settings.flag_extra_air_resistance      = bool(flags & (1<<14))
        settings.flag_fewer_cars                = bool(flags & (1<<15))

        return obj

    #######################################################
    @staticmethod
    def import_cull(cull):
        self = cull_importer

        location = Vector((float(cull.centerX), float(cull.centerY), float(cull.centerZ)))
        angle = 0
        scale = Vector()
        flags = int(cull.flags)

        wanted_level_drop = 0

        if hasattr(cull, 'widthX'):
            scale.x = float(cull.widthX)
            scale.y = float(cull.widthY)

            top_z = float(cull.topZ)
            bottom_z = float(cull.bottomZ)

            location.z = (top_z + bottom_z) * 0.5
            scale.z = (top_z - bottom_z) * 0.5

            angle = -atan2(2 * float(cull.skewX), 2 * scale.y)

            if hasattr(cull, 'Vx'):
                # TODO: mirror
                pass

        elif hasattr(cull, "lowerLeftX"):
            lower_left = Vector((float(cull.lowerLeftX), float(cull.lowerLeftY), float(cull.lowerLeftZ)))
            upper_right = Vector((float(cull.upperRightX), float(cull.upperRightY), float(cull.upperRightZ)))

            for axis in range(3):
                location[axis] = (upper_right[axis] + lower_left[axis]) * 0.5
                scale[axis] = (upper_right[axis] - lower_left[axis]) * 0.5

            wanted_level_drop = int(cull.wantedLevelDrop)

        obj = self.create_cull_object(location, scale, flags, angle)
        obj.dff.cull.wanted_level_drop = wanted_level_drop

        return obj

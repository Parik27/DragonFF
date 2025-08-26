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
        settings.flags = {str(1 << i) for i in range(16) if flags & (1 << i)}

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
        mirror_enabled = False
        mirror_axis = 'AXIS_X'
        mirror_coordinate = 0.0

        if hasattr(cull, 'widthX'):
            scale.x = float(cull.widthX)
            scale.y = float(cull.widthY)

            top_z = float(cull.topZ)
            bottom_z = float(cull.bottomZ)

            location.z = (top_z + bottom_z) * 0.5
            scale.z = (top_z - bottom_z) * 0.5

            angle = -atan2(2 * float(cull.skewX), 2 * scale.y)

            if hasattr(cull, 'Vx'):
                mirror_enabled = True
                vx, vy, vz = float(cull.Vx), float(cull.Vy), float(cull.Vz)
                if vx > 0.5:
                    mirror_axis = 'AXIS_X'
                elif vx < -0.5:
                    mirror_axis = 'AXIS_NEGATIVE_X'
                elif vy > 0.5:
                    mirror_axis = 'AXIS_Y'
                elif vy < -0.5:
                    mirror_axis = 'AXIS_NEGATIVE_Y'
                elif vz > 0.5:
                    mirror_axis = 'AXIS_Z'
                elif vz < -0.5:
                    mirror_axis = 'AXIS_NEGATIVE_Z'
                mirror_coordinate = float(cull.cm)

        elif hasattr(cull, "lowerLeftX"):
            lower_left = Vector((float(cull.lowerLeftX), float(cull.lowerLeftY), float(cull.lowerLeftZ)))
            upper_right = Vector((float(cull.upperRightX), float(cull.upperRightY), float(cull.upperRightZ)))

            for axis in range(3):
                location[axis] = (upper_right[axis] + lower_left[axis]) * 0.5
                scale[axis] = (upper_right[axis] - lower_left[axis]) * 0.5

            wanted_level_drop = int(cull.wantedLevelDrop)

        obj = self.create_cull_object(location, scale, flags, angle)
        settings = obj.dff.cull
        settings.wanted_level_drop = wanted_level_drop
        settings.mirror_enabled = mirror_enabled
        settings.mirror_axis = mirror_axis
        settings.mirror_coordinate = mirror_coordinate

        return obj

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

from math import radians
from mathutils import Vector

#######################################################
class enex_importer:

    """ Helper class for ENEX importing """

    #######################################################
    @staticmethod
    def create_enex_object(location, flags, angle=0):
        obj = bpy.data.objects.new("enex", None)
        obj.empty_display_type = 'SPHERE'
        obj.location = location
        obj.rotation_euler = (0, 0, angle)
        obj.dff.type = 'ENEX'

        obj.lock_rotation[0] = True
        obj.lock_rotation[1] = True
        obj.lock_rotation_w = True
        obj.lock_scale[2] = True

        settings = obj.dff.enex
        settings.flags = {str(1 << i) for i in range(16) if flags & (1 << i)}

        return obj

    #######################################################
    @staticmethod
    def import_enex(enex):
        self = enex_importer

        location = Vector((float(enex.x1), float(enex.y1), float(enex.z1)))
        angle = float(enex.enterAngle)
        scale = Vector((float(enex.sizeX), float(enex.sizeY), 1))
        flags = int(enex.flags)

        exit_offset = Vector((float(enex.x2), float(enex.y2), float(enex.z2))) - location
        exit_angle = radians(float(enex.exitAngle))

        obj = self.create_enex_object(location, flags, angle)
        obj.scale = scale

        settings = obj.dff.enex
        settings.exit_offset = exit_offset
        settings.exit_angle = exit_angle
        settings.interior = int(enex.targetInterior)
        settings.interior_name = enex.name.strip('"')
        settings.sky = int(enex.sky)
        settings.peds = int(enex.numPedsToSpawn)
        settings.time_on = int(enex.timeOn)
        settings.time_off = int(enex.timeOff)

        return obj

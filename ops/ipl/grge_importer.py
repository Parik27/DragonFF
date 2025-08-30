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
class grge_importer:

    """ Helper class for GRGE importing """

    #######################################################
    @staticmethod
    def create_grge_object(location, scale, flags, angle=0):
        obj = bpy.data.objects.new("grge", None)
        obj.empty_display_type = 'CUBE'
        obj.show_axis = True
        obj.location = location
        obj.rotation_euler = (0, 0, angle)
        obj.scale = scale
        obj.dff.type = 'GRGE'

        obj.lock_rotation[0] = True
        obj.lock_rotation[1] = True
        obj.lock_rotation_w = True

        settings = obj.dff.grge
        settings.flags = {str(1 << i) for i in range(3) if flags & (1 << i)}

        return obj

    #######################################################
    @staticmethod
    def import_grge(grge):
        self = grge_importer

        start_pos = Vector((float(grge.posX), float(grge.posY), float(grge.posZ)))
        front_pos = Vector((float(grge.lineX), float(grge.lineY), start_pos.z))
        end_pos = Vector((float(grge.cubeX), float(grge.cubeY), float(grge.cubeZ)))

        location = (end_pos + front_pos) * 0.5
        scale = Vector((
            (front_pos.xy - start_pos.xy).length * 0.5,
            (end_pos.xy - start_pos.xy).length * 0.5,
            (end_pos.z - start_pos.z) * 0.5,
        ))

        angle = atan2(front_pos.y - start_pos.y, front_pos.x - start_pos.x)
        flags = int(grge.doorType)

        obj = self.create_grge_object(location, scale, flags, angle)
        settings = obj.dff.grge
        settings.grge_type = int(grge.garageType)
        settings.grge_name = grge.name

        return obj

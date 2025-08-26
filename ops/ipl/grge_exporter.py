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

from math import cos, sin

#######################################################
class grge_exporter:

    """ Helper class for GRGE exporting """

    #######################################################
    @staticmethod
    def export_grge(obj):

        settings = obj.dff.grge
        grge_line = ""

        angle = obj.matrix_world.to_euler().z

        dir_x = -cos(angle)
        dir_y = sin(angle)

        center_x, center_y, center_z = obj.location.x, obj.location.y, obj.location.z
        scale_x, scale_y, scale_z = obj.scale.x, obj.scale.y, obj.scale.z

        start_pos_x = center_x + scale_y * dir_y + scale_x * dir_x
        start_pos_y = center_y + scale_y * dir_x - scale_x * dir_y
        start_pos_z = center_z - scale_z

        front_pos_x = center_x + scale_y * dir_y - scale_x * dir_x
        front_pos_y = center_y + scale_y * dir_x + scale_x * dir_y

        end_pos_x = center_x - scale_y * dir_y + scale_x * dir_x
        end_pos_y = center_y - scale_y * dir_x - scale_x * dir_y
        end_pos_z = center_z + scale_z

        flags = 0
        for fl in settings.flags:
            flags |= int(fl)

        grge_line += f"{start_pos_x:.6f}, {start_pos_y:.6f}, {start_pos_z:.6f}"
        grge_line += f", {front_pos_x:.6f}, {front_pos_y:.6f}"
        grge_line += f", {end_pos_x:.6f}, {end_pos_y:.6f}, {end_pos_z:.6f}"
        grge_line += f", {flags}, {settings.grge_type}, {settings.grge_name}"

        return grge_line

    #######################################################
    @staticmethod
    def export_objects(objects):

        """ Export GRGE objects to list of strings"""

        grge_objects = [obj for obj in objects if obj.dff.type == 'GRGE']

        grges = []
        for obj in grge_objects:
            grge = grge_exporter.export_grge(obj)
            grges.append(grge)

        return grges

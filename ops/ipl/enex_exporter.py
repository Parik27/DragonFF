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

from math import degrees

#######################################################
class enex_exporter:

    """ Helper class for ENEX exporting """

    #######################################################
    @staticmethod
    def export_enex(obj):

        settings = obj.dff.enex
        enex_line = ""

        location = obj.matrix_world.to_translation()
        angle = obj.matrix_world.to_euler().z
        size = obj.matrix_world.to_scale()

        exit_location = location + settings.exit_offset
        exit_angle = degrees(settings.exit_angle)

        flags = 0
        for fl in settings.flags:
            flags |= int(fl)

        enex_line += f"{location.x:.6f}, {location.y:.6f}, {location.z:.6f}, {angle:.6f}"
        enex_line += f", {size.x:.6f}, {size.y:.6f}, 8"
        enex_line += f", {exit_location.x:.6f}, {exit_location.y:.6f}, {exit_location.z:.6f}, {exit_angle:.2f}"
        enex_line += f", {settings.interior}, {flags}, \"{settings.interior_name}\", {settings.sky}"
        enex_line += f", {settings.peds}, {settings.time_on}, {settings.time_off}"

        return enex_line

    #######################################################
    @staticmethod
    def export_objects(objects):

        """ Export ENEX objects to list of strings"""

        enex_objects = [obj for obj in objects if obj.dff.type == 'ENEX']

        enexes = []
        for obj in enex_objects:
            enex = enex_exporter.export_enex(obj)
            enexes.append(enex)

        return enexes

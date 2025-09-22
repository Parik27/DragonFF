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

from math import tan

from ..gtaLib.data.map_data import game_version

#######################################################
class cull_exporter:

    """ Helper class for CULL exporting """

    #######################################################
    @staticmethod
    def export_cull(obj, game_id):

        settings = obj.dff.cull
        cull_line = ""

        flags = 0
        for fl in settings.flags:
            flags |= int(fl)

        if game_id in (game_version.III, game_version.VC):
            center_x, center_y, center_z = obj.location.xyz

            lower_left_x = center_x - obj.scale.x
            lower_left_y = center_y - obj.scale.y
            lower_left_z = center_z - obj.scale.z

            upper_right_x = center_x + obj.scale.x
            upper_right_y = center_y + obj.scale.y
            upper_right_z = center_z + obj.scale.z

            wanted_level_drop = settings.wanted_level_drop

            cull_line += f"{center_x:.6f}, {center_y:.6f}, {center_z:.6f}"
            cull_line += f", {lower_left_x:.6f}, {lower_left_y:.6f}, {lower_left_z:.6f}"
            cull_line += f", {upper_right_x:.6f}, {upper_right_y:.6f}, {upper_right_z:.6f}"
            cull_line += f", {flags}, {wanted_level_drop}"

        else:
            center_x = obj.location.x
            center_y = obj.location.y
            center_z = obj.location.z - obj.scale.z

            width_x = obj.scale.x
            width_y = obj.scale.y

            top_z = obj.location.z + obj.scale.z
            bottom_z = center_z

            angle = obj.matrix_world.to_euler().z

            skew_x = -tan(angle) * width_y
            skew_y = tan(angle) * width_x

            cull_line += f"{center_x:.6f}, {center_y:.6f}, {center_z:.6f}"
            cull_line += f", {skew_x:.6f}, {width_y:.6f}, {bottom_z:.6f}, {width_x:.6f}, {skew_y:.6f}, {top_z:.6f}"
            cull_line += f", {flags}"

            if settings.mirror_enabled:
                if settings.mirror_axis == 'AXIS_X':
                    vx, vy, vz = 1, 0, 0
                elif settings.mirror_axis == 'AXIS_Y':
                    vx, vy, vz = 0, 1, 0
                elif settings.mirror_axis == 'AXIS_Z':
                    vx, vy, vz = 0, 0, 1
                elif settings.mirror_axis == 'AXIS_NEGATIVE_X':
                    vx, vy, vz = -1, 0, 0
                elif settings.mirror_axis == 'AXIS_NEGATIVE_Y':
                    vx, vy, vz = 0, -1, 0
                elif settings.mirror_axis == 'AXIS_NEGATIVE_Z':
                    vx, vy, vz = 0, 0, -1
                cm = settings.mirror_coordinate

                cull_line += f", {vx}, {vy}, {vz}, {cm:.6f}"

            else:
                cull_line += f", 0"

        return cull_line

    #######################################################
    @staticmethod
    def export_objects(objects, game_id):

        """ Export CULL objects to list of strings"""

        cull_objects = [obj for obj in objects if obj.dff.type == 'CULL']
        # cull_objects.sort(key=lambda obj: obj.name)

        culls = []
        for obj in cull_objects:
            cull = cull_exporter.export_cull(obj, game_id)
            culls.append(cull)

        return culls

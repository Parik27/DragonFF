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

from ..gtaLib.map import TextIDEData, MapDataUtility

#######################################################
class ide_exporter:

    only_selected = False

    objs_objects = []
    tobj_objects = []

    #######################################################
    @staticmethod
    def collect_objects(context):
        """Collect objects that have IDE data"""

        self = ide_exporter

        self.objs_objects = []
        self.tobj_objects = []

        ide_objects = {}  # Group by ID to avoid duplicates

        for obj in context.scene.objects:
            if self.only_selected and not obj.select_get():
                continue

            if obj.dff.type == 'OBJ':
                if hasattr(obj, 'ide') and obj.ide.obj_id and obj.ide.txd_name:
                    obj_id = obj.ide.obj_id

                    # Only add if we haven't seen this ID before
                    if obj_id not in ide_objects:
                        ide_objects[obj_id] = obj

        # Separate objects by type
        for obj in ide_objects.values():
            if obj.ide.obj_type == 'tobj':
                self.tobj_objects.append(obj)
            else:
                self.objs_objects.append(obj)

    #######################################################
    @staticmethod
    def get_draw_distances(obj):
        """Get draw distances for the object"""
        distances = []

        # Check for single draw distance
        if obj.ide.draw_distance:
            distances.append(obj.ide.draw_distance)

        # Check for multiple draw distances
        if obj.ide.draw_distance1:
            distances.append(obj.ide.draw_distance1)
        if obj.ide.draw_distance2:
            distances.append(obj.ide.draw_distance2)
        if obj.ide.draw_distance3:
            distances.append(obj.ide.draw_distance3)

        # Default to single distance of 100 if none found
        if not distances:
            distances = ['100']

        return distances

    #######################################################
    @staticmethod
    def format_objs_line(obj):
        """Format an object as an objs line"""

        self = ide_exporter

        obj_id = obj.ide.obj_id
        model_name = obj.ide.model_name or obj.name
        txd_name = obj.ide.txd_name or model_name
        flags = obj.ide.flags or '0'

        distances = self.get_draw_distances(obj)

        # Format based on number of draw distances
        if len(distances) == 1:
            # Format: ID, ModelName, TxdName, DrawDistance, Flags
            return f"{obj_id}, {model_name}, {txd_name}, {distances[0]}, {flags}"

        elif len(distances) == 2:
            # Format: ID, ModelName, TxdName, MeshCount, DrawDistance1, DrawDistance2, Flags
            mesh_count = '1'  # Default to 1 for now
            return f"{obj_id}, {model_name}, {txd_name}, {mesh_count}, {distances[0]}, {distances[1]}, {flags}"

        elif len(distances) == 3:
            # Format: ID, ModelName, TxdName, MeshCount, DrawDistance1, DrawDistance2, DrawDistance3, Flags
            mesh_count = '1'  # Default to 1 for now
            return f"{obj_id}, {model_name}, {txd_name}, {mesh_count}, {distances[0]}, {distances[1]}, {distances[2]}, {flags}"

        else:
            # Default format
            return f"{obj_id}, {model_name}, {txd_name}, {distances[0]}, {flags}"

    #######################################################
    @staticmethod
    def format_tobj_line(obj):
        """Format an object as a tobj line"""

        self = ide_exporter

        obj_id = obj.ide.obj_id
        model_name = obj.ide.model_name or obj.name
        txd_name = obj.ide.txd_name or model_name
        flags = obj.ide.flags or '0'
        time_on = obj.ide.time_on or '0'
        time_off = obj.ide.time_off or '24'

        distances = self.get_draw_distances(obj)

        # Format based on number of draw distances
        if len(distances) == 1:
            # Format: ID, ModelName, TxdName, DrawDistance, Flags, TimeOn, TimeOff
            return f"{obj_id}, {model_name}, {txd_name}, {distances[0]}, {flags}, {time_on}, {time_off}"

        elif len(distances) == 2:
            # Format: ID, ModelName, TxdName, MeshCount, DrawDistance1, DrawDistance2, Flags, TimeOn, TimeOff
            mesh_count = '1'  # Default to 1 for now
            return f"{obj_id}, {model_name}, {txd_name}, {mesh_count}, {distances[0]}, {distances[1]}, {flags}, {time_on}, {time_off}"

        elif len(distances) == 3:
            # Format: ID, ModelName, TxdName, MeshCount, DrawDistance1, DrawDistance2, DrawDistance3, Flags, TimeOn, TimeOff
            mesh_count = '1'  # Default to 1 for now
            return f"{obj_id}, {model_name}, {txd_name}, {mesh_count}, {distances[0]}, {distances[1]}, {distances[2]}, {flags}, {time_on}, {time_off}"

        else:
            # Default format
            return f"{obj_id}, {model_name}, {txd_name}, {distances[0]}, {flags}, {time_on}, {time_off}"

    #######################################################
    @staticmethod
    def export_ide(filename):
        self = ide_exporter

        self.collect_objects(bpy.context)

        total_objects_num = len(self.objs_objects) + len(self.tobj_objects)
        if not total_objects_num:
            return

        objs_instances = [self.format_objs_line(obj) for obj in self.objs_objects]
        tobj_instances = [self.format_tobj_line(obj) for obj in self.tobj_objects]

        ide_data = TextIDEData(
            objs_instances,
            tobj_instances,
        )

        MapDataUtility.write_ide_data(filename, ide_data)

#######################################################
def export_ide(options):
    """Main export function"""

    ide_exporter.only_selected = options['only_selected']

    ide_exporter.export_ide(options['file_name'])

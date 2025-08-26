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

from ..gtaLib.data.map_data import game_version
from ..gtaLib.map import TextIPLData, MapDataUtility
from ..ops.ipl.cull_exporter import cull_exporter
from ..ops.ipl.grge_exporter import grge_exporter

#######################################################
class ipl_exporter:

    only_selected = False
    game_id = None
    export_inst = True
    export_cull = False
    export_grge = False

    inst_objects = []
    cull_objects = []
    grge_objects = []
    total_objects_num = 0

    #######################################################
    @staticmethod
    def collect_objects(context):
        """Collect objects that have IPL data"""

        self = ipl_exporter

        self.inst_objects = []
        self.cull_objects = []
        self.grge_objects = []
        self.total_objects_num = 0

        for obj in context.scene.objects:
            if self.only_selected and not obj.select_get():
                continue

            if self.export_inst and obj.dff.type == 'OBJ':
                if hasattr(obj, 'ide') and obj.ide.obj_id and not obj.parent:
                    self.inst_objects.append(obj)
                    self.total_objects_num += 1

            if self.export_cull and obj.dff.type == 'CULL':
                self.cull_objects.append(obj)
                self.total_objects_num += 1

            if self.export_grge and obj.dff.type == 'GRGE':
                self.grge_objects.append(obj)
                self.total_objects_num += 1

    #######################################################
    @staticmethod
    def format_inst_line(obj):
        """Format an object as an inst line based on game version"""

        self = ipl_exporter

        # Get data from ide/ipl properties
        obj_id = obj.ide.obj_id
        model_name = obj.ide.model_name or obj.name
        interior = obj.ipl.interior or '0'
        lod = obj.ipl.lod or '-1'

        # Get transformation data
        loc = obj.location
        rot = obj.rotation_quaternion
        scale = obj.scale

        # Note: the W component is negated
        rot_w = -rot.w
        rot_x = rot.x
        rot_y = rot.y
        rot_z = rot.z

        if self.game_id == game_version.III:
            # GTA III format: ID, ModelName, PosX, PosY, PosZ, ScaleX, ScaleY, ScaleZ, RotX, RotY, RotZ, RotW
            return f"{obj_id}, {model_name}, {loc.x:.6f}, {loc.y:.6f}, {loc.z:.6f}, {scale.x:.6f}, {scale.y:.6f}, {scale.z:.6f}, {rot_x:.6f}, {rot_y:.6f}, {rot_z:.6f}, {rot_w:.6f}"

        elif self.game_id == game_version.VC:
            # GTA VC format: ID, ModelName, Interior, PosX, PosY, PosZ, ScaleX, ScaleY, ScaleZ, RotX, RotY, RotZ, RotW
            return f"{obj_id}, {model_name}, {interior}, {loc.x:.6f}, {loc.y:.6f}, {loc.z:.6f}, {scale.x:.6f}, {scale.y:.6f}, {scale.z:.6f}, {rot_x:.6f}, {rot_y:.6f}, {rot_z:.6f}, {rot_w:.6f}"

        elif self.game_id == game_version.SA:
            # GTA SA format: ID, ModelName, Interior, PosX, PosY, PosZ, RotX, RotY, RotZ, RotW, LOD
            # Note: SA doesn't have scale in IPL
            return f"{obj_id}, {model_name}, {interior}, {loc.x:.6f}, {loc.y:.6f}, {loc.z:.6f}, {rot_x:.6f}, {rot_y:.6f}, {rot_z:.6f}, {rot_w:.6f}, {lod}"

        else:
            # Default to SA format
            return f"{obj_id}, {model_name}, {interior}, {loc.x:.6f}, {loc.y:.6f}, {loc.z:.6f}, {rot_x:.6f}, {rot_y:.6f}, {rot_z:.6f}, {rot_w:.6f}, {lod}"

    #######################################################
    @staticmethod
    def export_ipl(filename):
        self = ipl_exporter

        self.collect_objects(bpy.context)

        if not self.total_objects_num:
            return

        object_instances = [self.format_inst_line(obj) for obj in self.inst_objects]
        cull_instacnes = cull_exporter.export_objects(self.cull_objects, self.game_id)
        grge_instacnes = grge_exporter.export_objects(self.grge_objects)

        ipl_data = TextIPLData(
            object_instances,
            cull_instacnes,
            grge_instacnes,
        )

        MapDataUtility.write_ipl_data(filename, self.game_id, ipl_data)

#######################################################
def export_ipl(options):
    """Main export function"""

    ipl_exporter.only_selected = options['only_selected']
    ipl_exporter.game_id       = options['game_id']
    ipl_exporter.export_inst   = options['export_inst']
    ipl_exporter.export_cull   = options['export_cull']
    ipl_exporter.export_grge   = options['export_grge']

    ipl_exporter.export_ipl(options['file_name'])

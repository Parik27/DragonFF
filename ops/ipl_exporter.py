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
import os
from mathutils import Matrix, Quaternion
from .importer_common import game_version


class IPLExporter:
    
    def __init__(self):
        self.game_version = None
        self.objects = []
        self.selected_only = False
        
    def collect_objects(self, context):
        """Collect objects that have IPL data"""
        objects_to_export = []
        
        if self.selected_only:
            objects = context.selected_objects
        else:
            objects = context.scene.objects
            
        for obj in objects:
            # Export objects that have an ID set
            if hasattr(obj, 'ide') and obj.ide.obj_id and not obj.parent:
                objects_to_export.append(obj)
                    
        return objects_to_export
    
    def format_inst_line(self, obj):
        """Format an object as an inst line based on game version"""
        
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
        
        if self.game_version == game_version.III:
            # GTA III format: ID, ModelName, PosX, PosY, PosZ, ScaleX, ScaleY, ScaleZ, RotX, RotY, RotZ, RotW
            return f"{obj_id}, {model_name}, {loc.x:.6f}, {loc.y:.6f}, {loc.z:.6f}, {scale.x:.6f}, {scale.y:.6f}, {scale.z:.6f}, {rot_x:.6f}, {rot_y:.6f}, {rot_z:.6f}, {rot_w:.6f}"
            
        elif self.game_version == game_version.VC:
            # GTA VC format: ID, ModelName, Interior, PosX, PosY, PosZ, ScaleX, ScaleY, ScaleZ, RotX, RotY, RotZ, RotW
            return f"{obj_id}, {model_name}, {interior}, {loc.x:.6f}, {loc.y:.6f}, {loc.z:.6f}, {scale.x:.6f}, {scale.y:.6f}, {scale.z:.6f}, {rot_x:.6f}, {rot_y:.6f}, {rot_z:.6f}, {rot_w:.6f}"
            
        elif self.game_version == game_version.SA:
            # GTA SA format: ID, ModelName, Interior, PosX, PosY, PosZ, RotX, RotY, RotZ, RotW, LOD
            # Note: SA doesn't have scale in IPL
            return f"{obj_id}, {model_name}, {interior}, {loc.x:.6f}, {loc.y:.6f}, {loc.z:.6f}, {rot_x:.6f}, {rot_y:.6f}, {rot_z:.6f}, {rot_w:.6f}, {lod}"
            
        else:
            # Default to SA format
            return f"{obj_id}, {model_name}, {interior}, {loc.x:.6f}, {loc.y:.6f}, {loc.z:.6f}, {rot_x:.6f}, {rot_y:.6f}, {rot_z:.6f}, {rot_w:.6f}, {lod}"
    
    def export(self, context, filepath):
        """Export IPL file"""
        
        # Collect objects
        objects_to_export = self.collect_objects(context)
        
        if not objects_to_export:
            return {'CANCELLED'}, "No objects with IPL data found"
            
        # Write IPL file
        try:
            with open(filepath, 'w') as f:
                # Write inst section
                f.write("inst\n")
                
                for obj in objects_to_export:
                    line = self.format_inst_line(obj)
                    f.write(line + "\n")
                    
                f.write("end\n")
                
            return {'FINISHED'}, f"Exported {len(objects_to_export)} objects to IPL"
            
        except Exception as e:
            return {'CANCELLED'}, f"Failed to export IPL: {str(e)}"


def export_ipl(filepath, game_version, selected_only=False):
    """Main export function"""
    exporter = IPLExporter()
    exporter.game_version = game_version
    exporter.selected_only = selected_only
    
    return exporter.export(bpy.context, filepath) 
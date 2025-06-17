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
from .importer_common import game_version


class IDEExporter:
    
    def __init__(self):
        self.game_version = None
        self.objects = []
        self.selected_only = False
        
    def collect_objects(self, context):
        """Collect objects that have IDE data"""
        objects_to_export = []
        ide_objects = {}  # Group by ID to avoid duplicates
        
        if self.selected_only:
            objects = context.selected_objects
        else:
            objects = context.scene.objects
            
        for obj in objects:
            # Export objects that have IDE data
            if hasattr(obj, 'ide') and obj.ide.obj_id and obj.ide.txd_name:
                obj_id = obj.ide.obj_id
                # Only add if we haven't seen this ID before
                if obj_id not in ide_objects:
                    ide_objects[obj_id] = obj
                    
        return list(ide_objects.values())
    
    def get_draw_distances(self, obj):
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
    
    def format_objs_line(self, obj):
        """Format an object as an objs line based on game version"""
        
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
    
    def format_tobj_line(self, obj):
        """Format an object as a tobj line"""
        
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
    
    def export(self, context, filepath):
        """Export IDE file"""
        
        # Collect objects
        objects_to_export = self.collect_objects(context)
        
        if not objects_to_export:
            return {'CANCELLED'}, "No objects with IDE data found"
        
        # Separate objects by type
        objs_objects = []
        tobj_objects = []
        
        for obj in objects_to_export:
            ide_type = obj.ide.obj_type
            if ide_type == 'tobj':
                tobj_objects.append(obj)
            else:
                objs_objects.append(obj)
        
        # Write IDE file
        try:
            with open(filepath, 'w') as f:
                if objs_objects:
                    f.write("objs\n")
                    for obj in objs_objects:
                        line = self.format_objs_line(obj)
                        f.write(line + "\n")
                    f.write("end\n")
                
                # Write tobj section if we have time objects
                if tobj_objects:
                    f.write("tobj\n")
                    for obj in tobj_objects:
                        line = self.format_tobj_line(obj)
                        f.write(line + "\n")
                    f.write("end\n")
                
                total_count = len(objs_objects) + len(tobj_objects)
                return {'FINISHED'}, f"Exported {total_count} objects to IDE ({len(objs_objects)} objs, {len(tobj_objects)} tobj)"
                
        except Exception as e:
            return {'CANCELLED'}, f"Failed to export IDE: {str(e)}"


def export_ide(filepath, game_version, selected_only=False):
    """Main export function"""
    exporter = IDEExporter()
    exporter.game_version = game_version
    exporter.selected_only = selected_only
    
    return exporter.export(bpy.context, filepath) 
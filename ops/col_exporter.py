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
import bmesh
import os
import math
import mathutils

from ..gtaLib import col

class col_exporter:

    coll = None
    filename = ""
    version = None
    collection = None
    memory = False # Whether it will return a bytes file (not write to a file)
    only_selected = False

    #######################################################
    def _process_mesh(obj, verts, faces):

        mesh = obj.data
        bm   = bmesh.new()

        bm.from_mesh(mesh)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])

        vert_offset = len(verts)
        
        # Vertices
        for vert in bm.verts:
            verts.append((*vert.co,))

        for face in bm.faces:

            bm.verts.index_update()
            surface = [0, 0, 0, 0]
            try:
                mat = obj.data.materials[face.material_index]
                surface[0] = mat.dff.col_mat_index
                surface[1] = mat.dff.col_flags
                surface[2] = mat.dff.col_brightness
                surface[3] = mat.dff.col_light
                
            except IndexError:
                pass

            if col.Sections.version == 1:
                faces.append(col.TFace._make(
                    [vert.index + vert_offset for vert in face.verts] + [
                        col.TSurface(*surface)
                    ]
                ))

            else:
                faces.append(col.TFace._make(
                    [vert.index + vert_offset for vert in face.verts] + [
                        surface[0], surface[3]
                    ]
                ))

    #######################################################
    def _update_bounds(obj):
        self = col_exporter

        if self.coll.bounds is None:
            self.coll.bounds = [
                [-math.inf] * 3,
                [math.inf] * 3
            ]

        dimensions = obj.dimensions
            
        # Empties don't have a dimensions array
        if obj.type == 'EMPTY':
            
            # Multiplied by 2 because empty_display_size is a radius
            dimensions = [
                max(x * obj.empty_display_size * 2 for x in obj.scale)] * 3
        
        upper_bounds = [x + (y/2) for x, y in zip(obj.location, dimensions)]
        lower_bounds = [x - (y/2) for x, y in zip(obj.location, dimensions)]

        self.coll.bounds = [
            [max(x, y) for x,y in zip(self.coll.bounds[0], upper_bounds)],
            [min(x, y) for x,y in zip(self.coll.bounds[1], lower_bounds)]
        ]

    #######################################################
    def _convert_bounds():
        self = col_exporter

        radius = 0.0
        center = [0, 0, 0]
        rect_min = [0, 0, 0]
        rect_max  = [0, 0, 0]

        if self.coll.bounds is not None:
            rect_min = self.coll.bounds[0]
            rect_max  = self.coll.bounds[1]
            center = [(x + y) / 2 for x, y in zip(*self.coll.bounds)]
            radius = (
                mathutils.Vector(rect_min) - mathutils.Vector(rect_max)
            ).magnitude / 2

        self.coll.bounds = col.TBounds(max = col.TVector(*rect_min),
                                       min = col.TVector(*rect_max),
                                       center = col.TVector(*center),
                                       radius = radius
        )   
        
        pass
        
    #######################################################
    def _process_spheres(obj):
        self = col_exporter
        
        radius = max(x * obj.empty_display_size for x in obj.scale)
        centre = col.TVector(*obj.location)
        surface = col.TSurface(
            obj.dff.col_material,
            obj.dff.col_flags,
            obj.dff.col_brightness,
            obj.dff.col_light
        )

        self.coll.spheres.append(col.TSphere(radius=radius,
                                         surface=surface,
                                         center=centre
        ))
        
        pass
                
    #######################################################
    def _process_obj(obj):
        self = col_exporter
        
        if obj.type == 'MESH':
            # Meshes
            if obj.dff.type == 'SHA':
                self._process_mesh(obj,
                                   self.coll.shadow_verts,
                                   self.coll.shadow_faces
                )
                
            else:
                self._process_mesh(obj,
                                   self.coll.mesh_verts,
                                   self.coll.mesh_faces
                )
                    
        elif obj.type == 'EMPTY':
            self._process_spheres(obj)
        
        self._update_bounds(obj)
        
    
    #######################################################
    def export_col(name):
        self = col_exporter
        self.file_name = name

        col.Sections.init_sections(self.version)

        self.coll = col.ColModel()
        self.coll.version = self.version
        self.coll.model_name = os.path.basename(name)

        objects = bpy.data.objects
        if self.collection is not None:
            objects = self.collection.objects

        total_objects = 0
        for obj in objects:
            if obj.dff.type == 'COL' or obj.dff.type == 'SHA':
                if not self.only_selected or obj.select_get():
                    self._process_obj(obj)
                    total_objects += 1
                
        self._convert_bounds()
        
        if self.memory:
            if total_objects > 0:
                return col.coll(self.coll).write_memory()
            return b''

        col.coll(self.coll).write_file(name)

#######################################################
def export_col(options):
    
    col_exporter.memory = options['memory']
    col_exporter.version = options['version']
    col_exporter.collection = options['collection']
    col_exporter.only_selected = options['only_selected']

    if options['mass_export']:
        output = b'';
        
        root_collection = bpy.context.scene.collection
        collections = root_collection.children.values() + [root_collection]
        col_exporter.memory = True

        for collection in collections:
            col_exporter.collection = collection
            name = collection.name

            # Strip stuff like vehicles.col. from the name so that
            # for example vehicles.col.infernus changes to just infernus
            try:
                name = name[name.index(".col.") + 5:]
                
            except ValueError:
                pass
            
            output += col_exporter.export_col(name)

        if options['memory']:
            return output

        with open(options['file_name'], mode='wb') as file:
            file.write(output)
            return
        
    return col_exporter.export_col(options['file_name'])

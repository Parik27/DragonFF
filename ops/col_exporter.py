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

from .importer_common import create_bmesh_for_mesh
from ..gtaLib import col

class col_exporter:

    coll = None
    filename = "" # Whether it will return a bytes file (not write to a file), if no file name is specified
    version = None
    apply_transformations = True
    only_selected = False

    #######################################################
    def _process_mesh(obj, verts, faces, face_groups=None):
        self = col_exporter

        mesh = obj.data
        bm = create_bmesh_for_mesh(mesh, obj.mode)

        if self.apply_transformations:
            matrix = obj.matrix_world
        else:
            matrix = mathutils.Matrix.Identity(4)
            matrix[0][0], matrix[1][1], matrix[2][2] = obj.scale

        bm = bm.copy()
        bm.transform(matrix)

        bmesh.ops.triangulate(bm, faces=bm.faces[:])

        vert_offset = len(verts)
        
        # Vertices
        for vert in bm.verts:
            verts.append((*vert.co,))

        # Setup for Face Groups
        layer = bm.faces.layers.int.get("face group")
        start_idx = fg_idx = 0
        fg_min = [256] * 3
        fg_max = [-256] * 3

        for i, face in enumerate(bm.faces):

            # Face Groups
            if layer and col.Sections.version > 1:
                lastface = i == len(bm.faces)-1
                idx = face[layer]

                # Evaluate bounds if still the same face group index or this is the last face in the list
                if idx == fg_idx or lastface:
                    fg_min = [min(x, y) for x, y in zip(fg_min, face.verts[0].co)]
                    fg_max = [max(x, y) for x, y in zip(fg_max, face.verts[0].co)]
                    fg_min = [min(x, y) for x, y in zip(fg_min, face.verts[1].co)]
                    fg_max = [max(x, y) for x, y in zip(fg_max, face.verts[1].co)]
                    fg_min = [min(x, y) for x, y in zip(fg_min, face.verts[2].co)]
                    fg_max = [max(x, y) for x, y in zip(fg_max, face.verts[2].co)]

                # Create the face group if the face group index changed or this is the last face in the list
                if idx != fg_idx or lastface:
                    end_idx = i if lastface else i-1
                    face_groups.append(col.TFaceGroup._make([fg_min, fg_max, start_idx, end_idx]))
                    fg_min = [256] * 3
                    fg_max = [-256] * 3
                    start_idx = i
                fg_idx = idx

            bm.verts.index_update()
            surface = [0, 0, 0, 0]
            try:
                mat = obj.data.materials[face.material_index]
                surface[0] = mat.dff.col_mat_index
                surface[1] = mat.dff.col_flags
                surface[2] = mat.dff.col_brightness
                surface[3] = mat.dff.col_day_light | (mat.dff.col_night_light << 4)

            except (IndexError, AttributeError):
                pass

            if col.Sections.version == 1:
                faces.append(col.TFace._make(
                    [vert.index + vert_offset for vert in (face.verts[0], face.verts[2], face.verts[1])] + [
                        col.TSurface(*surface)
                    ]
                ))

            else:
                faces.append(col.TFace._make(
                    [vert.index + vert_offset for vert in (face.verts[0], face.verts[2], face.verts[1])] + [
                        surface[0], surface[3]
                    ]
                ))

    #######################################################
    def _convert_bounds():
        self = col_exporter

        radius = 0.0
        center = [0, 0, 0]
        rect_min = [0, 0, 0]
        rect_max = [0, 0, 0]

        if self.coll.bounds is not None:
            rect_max, rect_min = self.coll.bounds
            center = [(x + y) / 2 for x, y in zip(*self.coll.bounds)]
            radius = (
                mathutils.Vector(rect_max) - mathutils.Vector(rect_min)
            ).magnitude / 2

        self.coll.bounds = col.TBounds(max = col.TVector(*rect_max),
                                       min = col.TVector(*rect_min),
                                       center = col.TVector(*center),
                                       radius = radius
        )

    #######################################################
    def _process_spheres(obj):
        self = col_exporter
        
        radius = max(x * obj.empty_display_size for x in obj.scale)
        centre = col.TVector(*obj.location)
        surface = col.TSurface(
            obj.dff.col_material,
            obj.dff.col_flags,
            obj.dff.col_brightness,
            obj.dff.col_day_light | (obj.dff.col_night_light << 4)
        )

        self.coll.spheres.append(col.TSphere(radius=radius,
                                         surface=surface,
                                         center=centre
        ))
        
        pass
                
    #######################################################
    def _process_boxes(obj):
        self = col_exporter

        min = col.TVector(*(obj.location - obj.scale))
        max = col.TVector(*(obj.location + obj.scale))

        surface = col.TSurface(
            obj.dff.col_material,
            obj.dff.col_flags,
            obj.dff.col_brightness,
            obj.dff.col_day_light | (obj.dff.col_night_light << 4)
        )

        self.coll.boxes.append(col.TBox(min=min,
                                        max=max,
                                        surface=surface,
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
                                   self.coll.mesh_faces,
                                   self.coll.face_groups
                )
                    
        elif obj.type == 'EMPTY':
            if obj.empty_display_type == 'SPHERE':
                self._process_spheres(obj)
            else:
                self._process_boxes(obj)

    #######################################################
    def export_col(collection, name):
        self = col_exporter

        col.Sections.init_sections(self.version)

        self.coll = col.ColModel()
        self.coll.version = self.version
        self.coll.model_name = os.path.basename(name)

        total_objects = 0
        bounds_objects = []
        for obj in collection.objects:
            if self.only_selected and not obj.select_get():
                continue

            if obj.dff.type == 'COL' or obj.dff.type == 'SHA':
                self._process_obj(obj)
                total_objects += 1

            if obj.dff.type == 'COL':
                bounds_objects.append(obj)

        if total_objects == 0 and (col_exporter.only_selected or collection.dff.auto_bounds):
            return b''

        # Get native bounds from collection (some collisions come in as just bounds with no other items)
        if collection.dff.auto_bounds:
            self.coll.bounds = calculate_bounds(bounds_objects, self.apply_transformations)
        else:
            self.coll.bounds = [collection.dff.bounds_max, collection.dff.bounds_min]

        self._convert_bounds()

        return col.coll(self.coll).write_memory()

#######################################################
def get_col_collection_name(collection, parent_collection=None):
    name = collection.name

    # Strip stuff like vehicles.col. from the name so that
    # for example vehicles.col.infernus changes to just infernus
    if parent_collection and parent_collection != collection:
        prefix = parent_collection.name + "."
        if name.startswith(prefix):
            name = name[len(prefix):]

    return name

#######################################################
def calculate_bounds(objects, apply_transformations=True):
    if not objects:
        return [[0, 0, 0], [0, 0, 0]]

    bounds = [
        [-math.inf] * 3,
        [math.inf] * 3
    ]

    for obj in objects:
        dimensions = obj.dimensions
        center = obj.location

        # Empties don't have a dimensions array
        if obj.type == 'EMPTY':

            if obj.empty_display_type == 'SPHERE':
                # Multiplied by 2 because empty_display_size is a radius
                dimensions = [
                    max(x * obj.empty_display_size * 2 for x in obj.scale)] * 3
            elif obj.empty_display_type == 'CUBE':
                dimensions = obj.scale * 2
            else:
                dimensions = obj.scale

        # And Meshes require their proper center to be calculated because their transform is identity
        else:
            local_center = sum((mathutils.Vector(b) for b in obj.bound_box), mathutils.Vector()) / 8.0
            if apply_transformations:
                center = obj.matrix_world @ local_center
            else:
                center = local_center

        upper_bounds = [x + (y/2) for x, y in zip(center, dimensions)]
        lower_bounds = [x - (y/2) for x, y in zip(center, dimensions)]

        bounds = [
            [max(x, y) for x,y in zip(bounds[0], upper_bounds)],
            [min(x, y) for x,y in zip(bounds[1], lower_bounds)]
        ]

    return bounds

#######################################################
def export_col(options):

    col_exporter.version = options['version']
    col_exporter.collection = options['collection']
    col_exporter.apply_transformations = options['apply_transformations']
    col_exporter.only_selected = options['only_selected']

    file_name = options['file_name']
    output = b''

    if not col_exporter.collection:
        if col_exporter.only_selected:
            root_collections = {c for obj in bpy.context.selected_objects for c in obj.users_collection}
        else:
            scene_collection = bpy.context.scene.collection
            root_collections = scene_collection.children.values() + [scene_collection]
    else:
        root_collections = [col_exporter.collection]

    exported_collections = []
    for root_collection in root_collections:
        if root_collection.dff.type == 'NON':
            continue

        for c in root_collection.children.values() + [root_collection]:
            if c.dff.type == 'NON':
                continue

            if c not in exported_collections:
                name = get_col_collection_name(c, root_collection)
                output += col_exporter.export_col(c, name)
                exported_collections.append(c)

    if file_name:
        with open(file_name, mode='wb') as file:
            file.write(output)
        return

    return output

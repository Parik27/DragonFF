# GTA Blender Tools - Tools to edit basic GTA formats
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
import mathutils

from dff import dff

#######################################################
class dff_importer:

    #######################################################
    def _init():
        self = dff_importer

        # Variables
        self.dff = None
        self.meshes = {}
        self.objects = []

    #######################################################
    def import_atomics():
        self = dff_importer

        # Import atomics (meshes)
        for atomic in self.dff.atomic_list:

            frame = self.dff.frame_list[atomic.frame]
            geom = self.dff.geometry_list[atomic.geometry]
            
            mesh = bpy.data.meshes.new(frame.name)
            bm   = bmesh.new()
            
            # Vertices
            for v in geom.vertices:
                bm.verts.new(v)

            bm.verts.ensure_lookup_table()

            # Faces (TODO: Materials)
            for f in geom.triangles:
                try:
                    bm.faces.new(
                        [
                            bm.verts[f.a],
                            bm.verts[f.b],
                            bm.verts[f.c]
                        ])
                except:
                    pass

            bm.to_mesh(mesh)
            bm.free()
            
            self.meshes[atomic.frame] = mesh

    #######################################################
    def import_frames():
        self = dff_importer

        for index,frame in enumerate(self.dff.frame_list):

            print(frame.name)
            
            if frame.name is None:
                continue

            # Check if the mesh for the frame has been loaded
            mesh = None
            if index in self.meshes:
                mesh = self.meshes[index]

            # Create and link the object
            obj = bpy.data.objects.new(frame.name, mesh)
            bpy.context.scene.objects.link(obj)

            # Load matrix
            matrix = mathutils.Matrix(
                (
                    frame.rotation_matrix.right,
                    frame.rotation_matrix.up,
                    frame.rotation_matrix.at
                )
            )
            
            matrix.transpose()

            obj.rotation_mode       = 'QUATERNION'
            obj.rotation_quaternion = matrix.to_quaternion()
            obj.location            = frame.position

            # Set empty display properties to something decent
            if mesh is None:
                obj.empty_draw_type = 'CUBE'
                obj.empty_draw_size = 0.05
            
            # set parent
            # Note: I have not considered if frames could have parents
            # that have not yet been defined. If I come across such
            # a model, the code will be modified to support that
            
            if  frame.parent != -1:
                obj.parent = self.objects[frame.parent]

            self.objects.append(obj)
    
    #######################################################
    def import_dff(file_name):
        self = dff_importer
        self._init()

        # Load the DFF
        self.dff = dff()
        self.dff.load_file(file_name)

        self.import_atomics()
        self.import_frames()

#######################################################
def import_dff(file_name):

    # Shadow function
    dff_importer.import_dff(file_name)

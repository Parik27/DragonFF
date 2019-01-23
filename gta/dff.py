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

from collections import namedtuple
from struct import unpack

Chunk = namedtuple("Chunk", "type size version")
Clump = namedtuple("Clump", "atomics lights cameras")
Vector = namedtuple("Vector", "x y z")
Matrix = namedtuple("Matrix", "right up at")
HAnimHeader = namedtuple("HAnimHeader", "version id bone_count")
Bone = namedtuple("Bone", "id index type")
RGBA = namedtuple("RGBA", "r g b a")
GeomSurfPro = namedtuple("GeometrySurfaceProperties",
                         "ambient specular diffuse")
TexCoords = namedtuple("TexCoords", "u v")
Sphere = namedtuple("Sphere", "x y z radius")
Triangle = namedtuple("Triangle", "b a material c")
Atomic = namedtuple("Atomic", "frame geometry flags unk")

# geometry flags
rpGEOMETRYTRISTRIP = 0x00000001
rpGEOMETRYPOSITIONS = 0x00000002
rpGEOMETRYTEXTURED = 0x00000004
rpGEOMETRYPRELIT = 0x00000008
rpGEOMETRYNORMALS = 0x00000010
rpGEOMETRYLIGHT = 0x00000020
rpGEOMETRYMODULATEMATERIALCOLOR = 0x00000040
rpGEOMETRYTEXTURED2 = 0x00000080
rpGEOMETRYNATIVE = 0x01000000


class Sections:
    #######################################################
    def read_vector(data):
        return Vector._make(unpack("<fff", data))

    #######################################################
    def read_matrix(data):
        return Matrix._make(
            [Sections.read_vector(data[:12]),
             Sections.read_vector(data[12:24]),
             Sections.read_vector(data[24:])]
        )

    #######################################################
    def read_chunk(data):
        return Chunk._make(unpack("<III", data))

    #######################################################
    def read_hanim_header(data):
        return HAnimHeader._make(unpack("<III", data))

    #######################################################
    def read_bone(data):
        return Bone._make(unpack("<III", data))

    #######################################################
    def get_rw_version(library_id):
        # see https://gtamods.com/wiki/RenderWare

        if library_id & 0xFFFF0000:
            return (library_id >> 14 & 0x3FF00) + 0x30000 | \
                (library_id >> 16 & 0x3F)
        pass

    #######################################################
    def read_rgba(data):
        return RGBA._make(unpack("<BBBB", data))

    #######################################################
    def read_geometry_surface_properties(data):
        return GeomSurfPro._make(unpack("<fff", data))

    #######################################################
    def read_tex_coords(data):
        return TexCoords._make(unpack("<ff", data))

    #######################################################
    def read_sphere(data):
        return Sphere._make(unpack("<ffff", data))

    #######################################################
    def read_triangle(data):
        return Triangle._make(unpack("<HHHH", data))

    #######################################################
    def read_texture(data):
        texture_data = unpack("<HH", data) + ("",) + ("",)
        return Texture._make(texture_data)

    #######################################################
    def read_atomic(data):
        return Atomic._make(unpack("<IIII", data))
    
    #######################################################
    def read_material(data):
        array_data = [unpack("<I", data[:4]),
                      Sections.read_rgba(data[4:8]),
                      unpack("<I", data[8:12]),
                      unpack("<I", data[12:16])]

        if len(data) > 16:
            array_data.append(
                Sections.read_geometry_surface_properties(data[16:]))
        else:
            array_data.append(GeomSurfPro._make((0, 0, 0)))

        array_data.append([])  # textures
        array_data.append([])  # plugins

        return Material._make(array_data)

#######################################################


class Texture:
    filters = None
    unknown = None
    name = ""
    mask = ""

    #######################################################
    def __init__(self, data):
        _Texture = namedtuple("_Texture", "filters unk")
        _tex = _Texture._make(unpack("<HH", data[:4]))
 
        self.filters = _tex.filters
        self.unknown = _tex.unk


#######################################################
class Material:

    flags = None
    colour = None
    is_textured = None
    surface_properties = None
    textures = None
    plugins = None

    #######################################################
    def __init__(self, data):
        array_data = [unpack("<I", data[:4]),
                      Sections.read_rgba(data[4:8]),
                      unpack("<I", data[8:12]),
                      unpack("<I", data[12:16])]

        if len(data) > 16:
            self.surface_properties = Sections.read_geometry_surface_properties(
                data[16:])

        self.flags = array_data[0]
        self.colour = array_data[1]
        self.is_textured = array_data[2]
        self.textures = []
        self.plugins = []
                
#######################################################


class Frame:

    rotation_matrix = None
    position = None
    parent = None
    creation_flags = None
    name = None
    bone_data = None

    def __init__(self, data):

        self.rotation_matrix = Sections.read_matrix(data[:36])
        self.position = Sections.read_vector(data[36:36+12])
        self.parent = unpack("<i", data[48:48+4])[0]
        self.creation_flags = unpack("<I", data[52:52+4])[0]

    def size():
        return 56

#######################################################


class HAnimPLG:

    header = 0
    bones = []

    def __init__(self, data):

        self.header = Sections.read_hanim_header(data[:12])
        if self.header.bone_count > 0:
            pos = 20  # offset to bone array

            for i in range(self.header.bone_count):
                bone = Sections.read_bone(data[pos:pos+12])
                self.bones.append(bone)

                pos += 12

#######################################################


class Geometry:

    flags = None
    triangles = None
    vertices = None
    surface_properties = None
    prelit_colours = None
    tex_coords = None
    bounding_sphere = None
    has_vertices = None
    has_normals = None
    normals = None
    materials = []

    #######################################################
    def __init__(self, data, parent_chunk):

        # Note: In the following function, I have used a loop
        #      to load the texture coordinates or prelit colours,
        #      although I feel that it might be more efficient to
        #      convert an array to an array of namedtuples.
        #      I have not found a way yet to implement such a function.

        self.flags = unpack("<I", data[:4])[0]

        num_triangles = unpack("<I", data[4:8])[0]
        num_vertices = unpack("<I", data[8:12])[0]

        rw_version = Sections.get_rw_version(parent_chunk.version)
        
        # read surface properties (only on rw below 0x34000)
        pos = 16
        if rw_version < 0x34000:
            self.surface_properties = Sections.read_geometry_surface_properties(
                data[16:28]
            )
            pos = 28

        if self.flags & rpGEOMETRYNATIVE == 0:

            # Read prelighting colours
            if self.flags & rpGEOMETRYPRELIT:
                self.prelit_colours = []
                
                for i in range(num_vertices):
                    prelit_colour = Sections.read_rgba(data[pos:pos+4])
                    self.prelit_colours.append(prelit_colour)

                    pos += 4

            # Read Texture Mapping coordinates
            if self.flags & (rpGEOMETRYTEXTURED | rpGEOMETRYTEXTURED2):
                texCount = self.flags & 0x00FF0000 % 65536
                if texCount == 0:
                    texCount = 2 if (self.flags & rpGEOMETRYTEXTURED2) else \
                        1 if (self.flags & rpGEOMETRYTEXTURED) else 0

                self.tex_coords = []
                for i in range(num_vertices*texCount):
                    tex_coord = Sections.read_tex_coords(data[pos:pos+8])
                    self.tex_coords.append(tex_coord)

                    pos += 8

            # Read Triangles
            self.triangles = []
            for i in range(num_triangles):
                triangle = Sections.read_triangle(data[pos:pos+8])
                self.triangles.append(triangle)
                
                pos += 8

        # Read  morph targets (This should be only once)
        self.bounding_sphere = Sections.read_sphere(data[pos:pos+16])

        pos += 16
        self.has_vertices = unpack("<I", data[pos:pos+4])
        self.has_normals = unpack("<I", data[pos+4:pos+8])
        pos += 24

        # read vertices
        if self.has_vertices == 1:
            self.vertices = []
            for i in range(num_vertices):
                vertice = Sections.read_vector(data[pos:pos+12])
                self.vertices.append(vertice)
                pos += 12
            
        # read normals
        if self.has_normals == 1:
            self.normals = []
            for i in range(num_vertices):
                normal = Sections.read_vector(data[pos:pos+12])
                self.normals.append(normal)
                pos += 12

#######################################################


class dff:

    frame_list = []
    geometry_list = []
    atomic_list = []
    light_list = []

    # read variables
    pos = 0
    data = ""

    #######################################################
    def raw(self, size, offset=None):
        if offset is None:
            offset = self.pos
        return self.data[offset:offset+size]

    #######################################################
    def read_chunk(self):
        chunk = Sections.read_chunk(self.raw(12))

        self.pos += 12
        return chunk

    #######################################################
    def read_frame_list(self, parent_chunk):

        parent_end = self.pos + parent_chunk.size
        chunk = self.read_chunk()
        frame_list_start = self.pos

        # read frames count
        frames_count = unpack("<I", self.raw(4))[0]
        self.pos += 4

        for i in range(frames_count):
            frame = Frame(self.data[self.pos:])

            self.frame_list.append(frame)
            self.pos += Frame.size()

        self.pos = frame_list_start+chunk.size  # just in case

        # read names
        i = 0
        while self.pos < parent_end:

            chunk = self.read_chunk()
            chunk_end = self.pos + chunk.size

            if chunk.size == 0:
                continue
            
            while self.pos < chunk_end:
                chunk = self.read_chunk()

                name = None
                bone_data = None

                if chunk.type == 39056126:  # FRAME
                    name = self.raw(chunk.size).decode("utf-8")
                elif chunk.type == 286:  # HANIM PLG
                    bone_data = HAnimPLG(self.raw(chunk.size))

                self.pos += chunk.size
                if name is not None:
                    self.frame_list[i].name = name
                if bone_data is not None:
                    self.frame_list[i].bone_data = bone_data
                
            i += 1
            

    #######################################################
    def read_mesh_plg(self, parent_chunk, geometry):
        # TODO: Add support for Triangle Strips
        geometry.triangles = []
        
        _Header = namedtuple("_Header","flags mesh_count total_indices")
        _SplitHeader = namedtuple("_SplitHeader","indices_count material")
        _Triangle = namedtuple("_Triangle", "a b c")
        
        header = _Header._make(unpack("<III", self.raw(12)))
        self.pos += 12
        
        opengl = 12 + header.mesh_count * 8 \
        + (header.total_indices * 4) > parent_chunk.size
        
        for i in range(header.mesh_count):

            # Read header
            
            split_header = _SplitHeader._make(unpack("<II", self.raw(8)))
            self.pos += 8

            unpack_format = "<HHH" if opengl else "<H2xH2xH2x"
            for j in range(0,split_header.indices_count,3):

                _triangle = _Triangle._make(unpack(unpack_format,
                                                  self.raw(6 if opengl else 12)))

                self.pos += 6 if opengl else 12
                triangle = Triangle._make((_triangle.a,
                                          _triangle.b,
                                           split_header.material,
                                           _triangle.c))
                    
                geometry.triangles.append(triangle)
                pass
            
    #######################################################
    def read_material_list(self, parent_chunk):
        list_end = parent_chunk.size + self.pos
        chunk = self.read_chunk()

        if chunk.type == 1:  # STRUCT
            materials_count = unpack("<I", self.raw(4))[0]
            self.pos += 4

            materials_indices = []

            for i in range(materials_count):
                materials_indices.append(unpack("<i", self.raw(4))[0])
                self.pos += 4

            while self.pos < list_end:

                chunk = self.read_chunk()
                chunk_end = self.pos + chunk.size

                if chunk.type == 7:  # MATERIAL
                    chunk = self.read_chunk()

                    # Read header
                    if chunk.type == 1:
                        material = Material(self.data[self.pos:self.pos+chunk.size])
                        self.pos += chunk.size

                    # Read textures and extensions
                    while self.pos < chunk_end:
                        chunk = self.read_chunk()

                        if chunk.type == 6:  # TEXTURE

                            chunk = self.read_chunk()  # STRUCT

                            # Read a  texture
                            texture = Texture(
                                self.data[self.pos:self.pos+chunk.size]
                            )
                            
                            self.pos += chunk.size
                            
                            chunk = self.read_chunk()  # Texture Name
                            texture.name = self.data[self.pos : self.pos +
                                                     chunk.size].decode("utf-8")
                            self.pos += chunk.size

                            chunk = self.read_chunk()  # Mask Name
                            texture.mask = self.data[self.pos:self.pos +
                                                     chunk.size].decode("utf-8")
                            self.pos += chunk.size
                            material.textures.append(texture)

                        elif chunk.type == 3: #EXTENSION
                            if chunk.size > 0:
                                
                                chunk_end = chunk.size + self.pos

                                # Read extensions
                                while self.pos < chunk_end:
                                    chunk = self.read_chunk()

                                    #TODO: Extensions
                                    self.pos += chunk.size
                                    
                            self.pos += chunk.size
                            
                        else:
                            self.pos += chunk.size

                    self.geometry_list[-1].materials.append(material)
                    
                self.pos = chunk_end

    #######################################################
    def read_geometry_list(self, parent_chunk):

        chunk = self.read_chunk()

        if chunk.type == 1:  # STRUCT
            geometries = unpack("<I", self.raw(4))[0]
            self.pos += 4

            # Read geometries
            for i in range(geometries):
                chunk = self.read_chunk()
                if chunk.type == 15:  # GEOMETRY
                    chunk_end = self.pos + chunk.size

                    chunk = self.read_chunk()
                    geometry = Geometry(self.data[self.pos:], parent_chunk)

                    self.pos += chunk.size

                    self.geometry_list.append(geometry)

                    while self.pos < chunk_end:
                        chunk = self.read_chunk()
                        if chunk.type == 8:  # MATERIAL LIST
                            self.read_material_list(chunk)
                            
                        elif chunk.type == 3:  # EXTENSION
                            pass # will fallthrough
                        
                        #elif chunk.type == 0x50E: #BIN MESH PLG
                        #   self.read_mesh_plg(chunk,geometry)
                            
                        else:
                            self.pos += chunk.size

                    self.pos = chunk_end

    #######################################################
    def read_atomic(self, parent_chunk):

        chunk_end = self.pos + parent_chunk.size
        while True:
            chunk = self.read_chunk()

            if chunk.type == 1:
                atomic = Sections.read_atomic(self.data[self.pos:self.pos+chunk.size])
                self.atomic_list.append(atomic)
                break

        self.pos = chunk_end

    #######################################################
    def read_clump(self, root_chunk):
        chunk = self.read_chunk()
        root_end = self.pos + root_chunk.size

        if chunk.type == 1:  # STRUCT

            # read clump data
            root_clump = Clump._make(unpack("<III",
                                            self.raw(12)))
            self.pos += 12

            while self.pos < root_end-12:
                chunk = self.read_chunk()

                if chunk.type == 14:  # FRAMELIST
                    self.read_frame_list(chunk)
                elif chunk.type == 26:  # GEOMETRYLIST
                    self.read_geometry_list(chunk)
                elif chunk.type == 20:  # ATOMIC
                    self.read_atomic(chunk)
                else: #TODO: Extensions (Collision models)
                    self.pos += chunk.size

    #######################################################
    def load_memory(self, data: str):
        self.data = data
        root = self.read_chunk()

        if root.type == 16:
            self.read_clump(root)

    #######################################################
    def unload(self):
            self.frame_list = []
            self.geometry_list = []
            self.atomic_list = []
            self.light_list = []
            self.pos = 0
            self.data = ""
            
    #######################################################
    def load_file(self, filename: str):

        with open(filename, mode='rb') as file:
            content = file.read()
            self.load_memory(content)

test = dff()
test.load_file("/home/parik/playa.dff")
#print(test.geometry_list[2].triangles)

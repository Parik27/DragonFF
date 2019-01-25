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
from struct import unpack_from

# Data types
Chunk       = namedtuple("Chunk"                     , "type size version")
Clump       = namedtuple("Clump"                     , "atomics lights cameras")
Vector      = namedtuple("Vector"                    , "x y z")
Matrix      = namedtuple("Matrix"                    , "right up at")
HAnimHeader = namedtuple("HAnimHeader"               , "version id bone_count")
Bone        = namedtuple("Bone"                      , "id index type")
RGBA        = namedtuple("RGBA"                      , "r g b a")
GeomSurfPro = namedtuple("GeomSurfPro"               , "ambient specular diffuse")
TexCoords   = namedtuple("TexCoords"                 , "u v")
Sphere      = namedtuple("Sphere"                    , "x y z radius")
Triangle    = namedtuple("Triangle"                  , "b a material c")
Atomic      = namedtuple("Atomic"                    , "frame geometry flags unk")

# geometry flags
rpGEOMETRYTRISTRIP              = 0x00000001
rpGEOMETRYPOSITIONS             = 0x00000002
rpGEOMETRYTEXTURED              = 0x00000004
rpGEOMETRYPRELIT                = 0x00000008
rpGEOMETRYNORMALS               = 0x00000010
rpGEOMETRYLIGHT                 = 0x00000020
rpGEOMETRYMODULATEMATERIALCOLOR = 0x00000040
rpGEOMETRYTEXTURED2             = 0x00000080
rpGEOMETRYNATIVE                = 0x01000000

# Block types

types = {
    "Frame"         : 39056126,
    "HAnim PLG"     : 286,
    "Struct"        : 1,
    "Material"      : 7,
    "Texture"       : 6,
    "Extension"     : 3,
    "Geometry"      : 15,
    "Material List" : 8,
    "Bin Mesh PLG"  : 0x50E,
    "Frame List"    : 14,
    "Geometry List" : 26,
    "Atomic"        : 20,
    "Clump"         : 16
}

#######################################################
def strlen(bytes, offset):

    # A helper function to find length of byte null terminated strings
    
    i = offset
    while i < len(bytes):
       
        if bytes[i] == 0:
            break

        i += 1
        
    return i-offset-2

#######################################################
class Sections:

    # Unpack/pack format for above data types
    unpackers =  {
        Chunk       : "<3I",
        Clump       : "<3I",
        Vector      : "<3f",
        HAnimHeader : "<3I",
        Bone        : "<3I",
        RGBA        : "<4B",
        GeomSurfPro : "<3f",
        Sphere      : "<4f",
        Triangle    : "<4H",
        Atomic      : "<4I",
        TexCoords   : "<2f"
    }
    
    #######################################################
    def read(type, data, offset=0):

        # These are simple non-nested data types that can be returned in a single
        # unpack calls, and thus do not need any special functions
        if type in Sections.unpackers:
            unpacker = Sections.unpackers[type]
            return type._make(unpack_from(unpacker,data,offset))

        elif type is Matrix:
            return Matrix._make(
                (
                    Sections.read(Vector, data, offset),
                    Sections.read(Vector, data, offset+12),
                    Sections.read(Vector, data, offset+24)
                )
            )
        else:
            raise NotImplementedError("unknown type", type)
        
     ########################################################
    def get_rw_version(library_id):
        #see https://gtamods.com/wiki/RenderWare
        
        if library_id & 0xFFFF0000:
            return (library_id >> 14 & 0x3FF00) + 0x30000 | \
                (library_id >> 16 & 0x3F)
        
#######################################################
class Texture:

    def __init__(self):
        self.flags              = None
        self.colour             = None
        self.is_textured        = None
        self.surface_properties = None
        self.textures           = None
        self.plugins            = None
    
    #######################################################
    def from_mem(data):

        self = Texture()
        
        _Texture = namedtuple("_Texture", "filters unk")
        _tex = _Texture._make(unpack_from("<2H", data))
 
        self.filters = _tex.filters
        self.unknown = _tex.unk

        return self

#######################################################
class Material:

    #######################################################
    def __init__(self):

        self.flags              = None
        self.colour             = None
        self.is_textured        = None
        self.surface_properties = None
        self.textures           = None
        self.plugins            = None

    
    #######################################################
    def from_mem(data):

        self = Material()
        
        array_data = [unpack_from("<I", data)[0],
                      Sections.read(RGBA, data, 4),
                      unpack_from("<I", data, 8)[0],
                      unpack_from("<I", data, 12)[0]]

        if len(data) > 16:
            self.surface_properties = Sections.read(GeomSurfPro, data, 16)

        self.flags       = array_data[0]
        self.colour      = array_data[1]
        self.is_textured = array_data[3]
        self.textures    = []
        self.plugins     = []

        return self
                
#######################################################
class Frame:

    ##################################################################
    def __init__(self):
        self.rotation_matrix = None
        self.position        = None
        self.parent          = None
        self.creation_flags  = None
        self.name            = None
        self.bone_data       = None

    ##################################################################
    def from_mem(data):

        self = Frame()
        
        self.rotation_matrix = Sections.read(Matrix,data)
        self.position        = Sections.read(Vector,data,36)
        self.parent          = unpack_from("<i", data,48)[0]
        self.creation_flags  = unpack_from("<I", data,52)[0]

        return self

    ##################################################################
    def size():
        return 56

#######################################################
class HAnimPLG:

    #######################################################
    def __init__(self):
        self.header = 0
        self.bones = []

    #######################################################
    def from_mem(data):

        self = HAnimPLG()
        
        self.header = Sections.read(HAnimHeader,data)
        if self.header.bone_count > 0:
            pos = 20  # offset to bone array

            for i in range(self.header.bone_count):
                bone = Sections.read(Bone, data, pos)
                self.bones.append(bone)

                pos += 12

        return self

#######################################################
class Geometry:

    ##################################################################
    def __init__(self):
        self.flags              = None
        self.triangles          = None
        self.vertices           = None
        self.surface_properties = None
        self.prelit_colours     = None
        self.uv_layers          = None
        self.bounding_sphere    = None
        self.has_vertices       = None
        self.has_normals        = None
        self.normals            = None
        self.materials          = []

    #######################################################
    def from_mem(data, parent_chunk):

        # Note: In the following function, I have used a loop
        #      to load the texture coordinates or prelit colours,
        #      although I feel that it might be more efficient to
        #      convert an array to an array of namedtuples.
        #      I have not found a way yet to implement such a function.

        self = Geometry()
        
        self.flags    = unpack_from("<I", data)[0]
        num_triangles = unpack_from("<I", data,4)[0]
        num_vertices  = unpack_from("<I", data,8)[0]
        rw_version    = Sections.get_rw_version(parent_chunk.version)
        
        # read surface properties (only on rw below 0x34000)
        pos = 16
        if rw_version < 0x34000:
            self.surface_properties = Sections.read(GeomSurfPro, data, pos)
            pos = 28

        if self.flags & rpGEOMETRYNATIVE == 0:

            # Read prelighting colours
            if self.flags & rpGEOMETRYPRELIT:
                self.prelit_colours = []
                
                for i in range(num_vertices):
                    prelit_colour = Sections.read(RGBA, data, pos)
                    self.prelit_colours.append(prelit_colour)

                    pos += 4

            # Read Texture Mapping coordinates
            # TODO: Fix multiple UV maps
            if self.flags & (rpGEOMETRYTEXTURED | rpGEOMETRYTEXTURED2):
                texCount = self.flags & 0x00FF0000 % 65536
                if texCount == 0:
                    texCount = 2 if (self.flags & rpGEOMETRYTEXTURED2) else \
                        1 if (self.flags & rpGEOMETRYTEXTURED) else 0

                self.uv_layers = []
                for i in range(texCount):

                    self.uv_layers.append([]) #add empty new layer
                    
                    for j in range(num_vertices):
                        
                        tex_coord = Sections.read(TexCoords, data, pos)
                        self.uv_layers[i].append(tex_coord)
                        pos += 8

            # Read Triangles
            self.triangles = []
            for i in range(num_triangles):
                triangle = Sections.read(Triangle, data, pos)
                self.triangles.append(triangle)
                
                pos += 8

        # Read  morph targets (This should be only once)
        self.bounding_sphere = Sections.read(Sphere, data, pos)
        print(self.bounding_sphere)
        
        pos += 16
        self.has_vertices = unpack_from("<I", data, pos)[0]
        self.has_normals = unpack_from("<I", data, pos + 4)[0]
        pos += 8

        # read vertices
        if self.has_vertices:
            self.vertices = []
            for i in range(num_vertices):
                vertice = Sections.read(Vector, data, pos)
                self.vertices.append(vertice)
                pos += 12
            
        # read normals
        if self.has_normals:
            self.normals = []
            for i in range(num_vertices):
                normal = Sections.read(Vector, data, pos)
                self.normals.append(normal)
                pos += 12

        return self

#######################################################


class dff:

    #######################################################
    def _read(self, size):
        current_pos = self.pos
        self.pos += size
        
        return current_pos

    #######################################################
    def raw(self, size, offset=None):

        if offset is None:
            offset = self.pos
        
        return self.data[offset:offset+size]

    #######################################################
    def read_chunk(self):
        chunk = Sections.read(Chunk, self.data, self._read(12))
        return chunk

    #######################################################
    def read_frame_list(self, parent_chunk):

        parent_end       = self.pos + parent_chunk.size
        chunk            = self.read_chunk()
        frame_list_start = self.pos

        # read frames count
        frames_count = unpack_from("<I", self.data, self._read(4))[0]

        for i in range(frames_count):
            frame = Frame.from_mem(self.data[self.pos:])

            self.frame_list.append(frame)
            self._read(Frame.size())

        self.pos = frame_list_start+chunk.size  # just in case

        # read names
        i = 0
        while self.pos < parent_end:

            chunk     = self.read_chunk()
            chunk_end = self.pos + chunk.size

            if chunk.size == 0:
                continue
            
            while self.pos < chunk_end:
                chunk = self.read_chunk()

                name = None
                bone_data = None

                if chunk.type == types["Frame"]:
                    name = self.raw(strlen(self.data,self.pos)).decode("utf-8")
                    
                elif chunk.type == types["HAnim PLG"]:
                    bone_data = HAnimPLG.from_mem(self.raw(chunk.size))

                self._read(chunk.size)
                if name is not None:
                    self.frame_list[i].name = name
                if bone_data is not None:
                    self.frame_list[i].bone_data = bone_data
                
            i += 1
            

    #######################################################
    def read_mesh_plg(self, parent_chunk, geometry):
        # TODO: Add support for Triangle Strips
        geometry.triangles = []
        
        _Header      = namedtuple("_Header","flags mesh_count total_indices")
        _SplitHeader = namedtuple("_SplitHeader","indices_count material")
        _Triangle    = namedtuple("_Triangle", "a b c")
        
        header = _Header._make(unpack_from("<III", self.data, self._read(12)))

        # calculate if the indices are stored in 32 bit or 16 bit
        opengl = 12 + header.mesh_count * 8 \
        + (header.total_indices * 4) > parent_chunk.size
        
        for i in range(header.mesh_count):

            # Read header
            
            split_header = _SplitHeader._make(unpack_from("<II",
                                                          self.data,
                                                          self._read(8)))

            unpack_format = "<HHH" if opengl else "<H2xH2xH2x"
            for j in range(0,split_header.indices_count,3):

                _triangle = _Triangle._make
                (
                    unpack_from
                    (
                        unpack_format,
                        self.data,
                        self._read(6 if opengl else 12)
                    )
                )

                self.pos += 6 if opengl else 12
                triangle = Triangle._make
                (
                    (_triangle.a,
                     _triangle.b,
                     split_header.material,
                     _triangle.c)
                )
                    
                geometry.triangles.append(triangle)
                pass
            
    #######################################################
    def read_material_list(self, parent_chunk):
        list_end = parent_chunk.size + self.pos
        chunk = self.read_chunk()

        if chunk.type == types["Struct"]:
            materials_count = unpack_from("<I", self.data, self._read(4))[0]
            materials_indices = []

            for i in range(materials_count):

                materials_indices.append
                (
                    unpack_from
                    (
                        "<i",
                        self.data,
                        self._read(4)
                    )[0]
                )
                
            while self.pos < list_end:

                chunk = self.read_chunk()
                chunk_end = self.pos + chunk.size

                if chunk.type == types["Material"]:
                    chunk = self.read_chunk()

                    # Read header
                    if chunk.type == types["Struct"]:
                        material = Material.from_mem(
                            self.data[self.pos:self.pos+chunk.size]
                        )
                        self.pos += chunk.size

                    # Read textures and extensions
                    while self.pos < chunk_end:
                        chunk = self.read_chunk()

                        if chunk.type == types["Texture"]:

                            chunk = self.read_chunk() 

                            # Read a  texture
                            texture = Texture.from_mem(
                                self.data[self.pos:self.pos+chunk.size]
                            )
                            
                            self._read(chunk.size)

                            # Texture Name
                            chunk = self.read_chunk()
                            texture.name = self.raw(
                                strlen(self.data,self.pos)
                            ).decode("utf-8")
                            
                            self._read(chunk.size)

                            # Mask Name
                            chunk = self.read_chunk()  
                            texture.mask = self.raw(
                                strlen(self.data,self.pos)
                            ).decode("utf-8")

                            self._read(chunk.size)
                            material.textures.append(texture)

                        elif chunk.type == types["Extension"]: 
                            if chunk.size > 0:
                                
                                chunk_end = chunk.size + self.pos

                                # Read extensions
                                while self.pos < chunk_end:
                                    chunk = self.read_chunk()

                                    #TODO: Extensions
                                    self.pos += chunk.size
                                    
                            self._read(chunk.size)
                            
                        else:
                            self._read(chunk.size)

                    self.geometry_list[-1].materials.append(material)
                    
                self.pos = chunk_end

    #######################################################
    def read_geometry_list(self, parent_chunk):

        chunk = self.read_chunk()

        if chunk.type == types["Struct"]:
            geometries = unpack_from("<I", self.data, self._read(4))[0]

            # Read geometries
            for i in range(geometries):
                chunk = self.read_chunk()

                # GEOMETRY
                if chunk.type == types["Geometry"]:  
                    chunk_end = self.pos + chunk.size

                    chunk = self.read_chunk()
                    geometry = Geometry.from_mem(self.data[self.pos:], parent_chunk)

                    self._read(chunk.size)

                    self.geometry_list.append(geometry)

                    while self.pos < chunk_end:

                        chunk = self.read_chunk()

                        # MATERIAL LIST
                        if chunk.type == types["Material List"]:  
                            self.read_material_list(chunk)

                        # EXTENSION
                        elif chunk.type == types["Extension"]:  
                            pass # will fallthrough

                        #BIN MESH PLG
                        #elif chunk.type == types["Bin Mesh PLG"]: 
                        #   self.read_mesh_plg(chunk,geometry)

                        #OTHER
                        else:
                            self._read(chunk.size)

                    self.pos = chunk_end

    #######################################################
    def read_atomic(self, parent_chunk):

        chunk_end = self.pos + parent_chunk.size
        while True:
            chunk = self.read_chunk()

            # STRUCT
            if chunk.type == types["Struct"]:
                atomic = Sections.read(Atomic, self.data, self.pos)
                self.atomic_list.append(atomic)
                break

        self.pos = chunk_end

    #######################################################
    def read_clump(self, root_chunk):
        chunk = self.read_chunk()
        root_end = self.pos + root_chunk.size

        # STRUCT
        if chunk.type == types["Struct"]:  

            # read clump data
            root_clump = Sections.read(Clump, self.data, self._read(12))

            while self.pos < root_end-12:
                chunk = self.read_chunk()

                # FRAMELIST
                if chunk.type == types["Frame List"]:  
                    self.read_frame_list(chunk)

                # GEOMETRYLIST
                elif chunk.type == types["Geometry List"]:  
                    self.read_geometry_list(chunk)

                # ATOMIC
                elif chunk.type == types["Atomic"]:  
                    self.read_atomic(chunk)

                #TODO: Extensions (Collision models)
                else: 
                    self.pos += chunk.size

    #######################################################
    def load_memory(self, data: str):

        self.data = data
        root = self.read_chunk()

        if root.type == types["Clump"]:
            self.read_clump(root)

    #######################################################
    def clear(self):
            self.frame_list    = []
            self.geometry_list = []
            self.atomic_list   = []
            self.light_list    = []
            self.pos           = 0
            self.data          = ""
            
    #######################################################
    def load_file(self, filename: str):

        with open(filename, mode='rb') as file:
            content = file.read()
            self.load_memory(content)

    #######################################################
    def __init__(self):
        
        self.clear()

#test = dff()
#test.load_file("/home/parik/Downloads/androm.dff")
#print(test.geometry_list[2].triangles)

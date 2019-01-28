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
from struct import unpack_from, calcsize, pack

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
    "Frame"           : 39056126,
    "HAnim PLG"       : 286,
    "Struct"          : 1,
    "Material"        : 7,
    "Texture"         : 6,
    "Extension"       : 3,
    "Geometry"        : 15,
    "Material List"   : 8,
    "Bin Mesh PLG"    : 0x50E,
    "Frame List"      : 14,
    "Geometry List"   : 26,
    "Atomic"          : 20,
    "Clump"           : 16,
    "Skin PLG"        : 278,
    "String"          : 2,
    "Right to Render" : 31
}

#######################################################
def strlen(bytes, offset):

    # A helper function to find length of byte null terminated strings
    
    i = offset
    while i < len(bytes):

        # 32  -> ' ' and 126 -> '~'
        if bytes[i] < 32 or bytes[i] > 126:
            break

        i += 1
        
    return i-offset

#######################################################
class Sections:

    # Unpack/pack format for above data types
    formats =  {
        Chunk       : "<3I",
        Clump       : "<3I",
        Vector      : "<3f",
        HAnimHeader : "<3I",
        Bone        : "<3i",
        RGBA        : "<4B",
        GeomSurfPro : "<3f",
        Sphere      : "<4f",
        Triangle    : "<4H",
        Atomic      : "<4I",
        TexCoords   : "<2f"
    }

    library_id = 0 # used for writing
    
    #######################################################
    def read(type, data, offset=0):

        # These are simple non-nested data types that can be returned in a single
        # unpack calls, and thus do not need any special functions
        if type in Sections.formats:
            unpacker = Sections.formats[type]
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

    #######################################################
    def pad_string(str):

        str_len = len(str)
        return str.encode('utf8')
        
    #######################################################
    def write(type, data, chunk_type=None):
        _data = b''
        
        if type in Sections.formats:
            packer = Sections.formats[type]
            _data = pack(packer, *data)
            
        elif type is Matrix:
            _data += Sections.write(Vector, data.right)
            _data += Sections.write(Vector, data.up)
            _data += Sections.write(Vector, data.at)
            
        if chunk_type is not None:
            _data = Sections.write_chunk(_data, chunk_type)

        return _data
        

    #######################################################
    def write_chunk(data, type):
        return pack("<III", type, len(data), Sections.library_id) + data
        
     ########################################################
    def get_rw_version(library_id=None):
        #see https://gtamods.com/wiki/RenderWare

        if library_id is None:
            library_id = Sections.library_id
        
        if library_id & 0xFFFF0000:
            return (library_id >> 14 & 0x3FF00) + 0x30000 | \
                (library_id >> 16 & 0x3F)

    #######################################################
    def get_library_id(version, build):
        #see https://gtamods.com/wiki/RenderWare
        
        if version <= 0x31000:
            return version >> 8

        return (version-0x30000 & 0x3FF00) << 14 | (version & 0x3F) << 16 | \
               (build & 0xFFFF)

    #######################################################
    def set_library_id(version, build):
        Sections.library_id = Sections.get_library_id(version,build)
        
#######################################################
class Texture:

    __slots__ = [
        'filters',
        'name',
        'mask'
    ]
    
    def __init__(self):
        self.filters            = None
        self.name               = ""
        self.mask               = ""
    
    #######################################################
    def from_mem(data):

        self = Texture()
        
        _Texture = namedtuple("_Texture", "filters unk")
        _tex = _Texture._make(unpack_from("<2H", data))
 
        self.filters = _tex.filters

        return self

    #######################################################
    def to_mem(self):

        data = b''
        data += pack("<H2x", self.filters)

        data  = Sections.write_chunk(data, types["Struct"])
        data += Sections.write_chunk(Sections.pad_string(self.name), types["String"])
        data += Sections.write_chunk(Sections.pad_string(self.mask), types["String"])
        data += Sections.write_chunk(b'', types["Extension"])

        return Sections.write_chunk(data, types["Texture"])

#######################################################
class Material:

    __slots__ = [
        'flags',
        'colour',
        'is_textured',
        'surface_properties',
        'textures',
        'plugins'
    ]
    
    #######################################################
    def __init__(self):

        self.flags              = None
        self.colour             = None
        self.is_textured        = None
        self.surface_properties = None
        self.textures           = []
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
    def to_mem(self):

        data = b''
        data += pack("<4x")
        data += Sections.write(RGBA, self.colour)
        data += pack("<II", len(self.textures) > 0, 1)

        if Sections.get_rw_version() > 0x30400:
            data += Sections.write(GeomSurfPro, self.surface_properties)

        data = Sections.write_chunk(data, types["Struct"])

        # Only 1 texture is supported (I think)
        if len(self.textures) > 0:
            data += self.textures[0].to_mem()

        data += Sections.write_chunk(b"", types["Extension"])
        return Sections.write_chunk(data, types["Material"])
                
#######################################################
class Frame:

    __slots__ = [
        'rotation_matrix',
        'position',
        'parent',
        'creation_flags',
        'name',
        'bone_data'
    ]
    
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

    #######################################################
    def header_to_mem(self):

        data = b''
        data += Sections.write(Matrix, self.rotation_matrix)
        data += Sections.write(Vector, self.position)
        data += pack("<iI", self.parent, self.creation_flags)

        return data

    #######################################################
    def extensions_to_mem(self):

        data = b''

        if self.name is not None and self.name != "unknown":
            data += Sections.write_chunk(Sections.pad_string(self.name), types["Frame"])

        if self.bone_data is not None:
            data += self.bone_data.to_mem()
        
        return Sections.write_chunk(data, types["Extension"])

    ##################################################################
    def size():
        return 56

#######################################################
class HAnimPLG:

    __slots__ = [
        'header',
        'bones'
    ]
    
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
    def to_mem(self):

        data = b''

        data += Sections.write(HAnimHeader, self.header)
        if len(self.bones) > 0:
            data += pack("<II", 0, 36)
            
        for bone in self.bones:
            data += Sections.write(Bone, bone)

        return Sections.write_chunk(data, types["HAnim PLG"])

#######################################################
class SkinPLG:

    __slots__ = [
        "num_bones",
        "num_used_bones",
        "max_weights_per_vertex",
        "bones_used",
        "vertex_bone_indices",
        "vertex_bone_weights",
        "bone_matrices"
    ]

    ##################################################################
    def __init__(self):
        
        self.num_bones = None
        self.num_used_bones = None
        self.max_weights_per_vertex = None
        self.bones_used = []
        self.vertex_bone_indices = None
        self.vertex_bone_weights = None
        self.bone_matrices = []

    ##################################################################
    def to_mem(self):

        data = b''
        data += pack("<B3x", self.num_bones)
        
        # 4x Indices
        for indices in self.vertex_bone_indices:
            data += pack("<4B", *indices)

        # 4x Weight
        for weight in self.vertex_bone_weights:
            data += pack("<4f", *weight)

        # 4x4 Matrix
        for matrix in self.bone_matrices:
            data += pack("<I", 0xDEADDEAD) # interesting value :eyes:
            for i in matrix:
                data += pack("<4f", *i)

        return Sections.write_chunk(data, types["Skin PLG"])
        
    ##################################################################
    def from_mem(data, geometry):

        self = SkinPLG()

        _data = unpack_from("<3Bx", data)
        self.num_bones, self.num_used_bones, self.max_weights_per_vertex = _data
        
        # Used bones array starts at offset 4
        pos = 4
        for i in range(self.num_used_bones):
            self.bones_used.append(unpack_from("<B", data, pos))
            pos += 1

        vertices_count = len(geometry.vertices)

        # Read vertex bone indices
        _data = unpack_from("<%dB" % (vertices_count * 4), data, pos)
        self.vertex_bone_indices = list(
            _data[i : i+4] for i in range(0, 4 * vertices_count, 4)
        )
        pos += vertices_count * 4
        
        # Read vertex bone weights        
        _data = unpack_from("<%df" % (vertices_count * 4), data, pos)
        self.vertex_bone_weights = list(
            _data[i : i+4] for i in range(0, 4 * vertices_count, 4)
        )
        pos += vertices_count * 4 * 4 #floats have size 4 bytes
       
        # According to gtamods, there is an extra unknown integer here
        # if the weights per vertex is zero.
        unpack_format = "<16f"
        if self.num_used_bones == 0:
            unpack_format = "<4x16f"

        # Read bone matrices
        
        for i in range(self.num_bones):

            _data = list(unpack_from(unpack_format, data, pos))
            _data[ 3] = 0.0
            _data[ 7] = 0.0
            _data[11] = 0.0
            _data[15] = 1.0
            
            self.bone_matrices.append(
                [_data[0:4], _data[4:8], _data[8:12],
                 _data[12:16]]
            )

            pos += calcsize(unpack_format)
            
        return self
    
#######################################################
class Geometry:

    __slots__ = [
        
        'flags',
        'triangles',
        'vertices',
        'surface_properties',
        'prelit_colours',
        'uv_layers',
        'bounding_sphere',
        'has_vertices',
        'has_normals',
        'normals',
        'materials',
        'extensions',
        'export_flags'
    ]
    
    ##################################################################
    def __init__(self):
        self.flags              = None
        self.triangles          = []
        self.vertices           = []
        self.surface_properties = None
        self.prelit_colours     = []
        self.uv_layers          = []
        self.bounding_sphere    = None
        self.has_vertices       = None
        self.has_normals        = None
        self.normals            = []
        self.materials          = []
        self.extensions         = {}

        # used for export
        self.export_flags = {
            "light"              : True,
            "modulate_colour"    : False
            }

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
            for i in range(num_triangles):
                triangle = Sections.read(Triangle, data, pos)
                self.triangles.append(triangle)
                
                pos += 8

        # Read  morph targets (This should be only once)
        self.bounding_sphere = Sections.read(Sphere, data, pos)
        
        pos += 16
        self.has_vertices = unpack_from("<I", data, pos)[0]
        self.has_normals = unpack_from("<I", data, pos + 4)[0]
        pos += 8

        # read vertices
        if self.has_vertices:
            for i in range(num_vertices):
                vertice = Sections.read(Vector, data, pos)
                self.vertices.append(vertice)
                pos += 12
            
        # read normals
        if self.has_normals:
            for i in range(num_vertices):
                normal = Sections.read(Vector, data, pos)
                self.normals.append(normal)
                pos += 12

        return self

    #######################################################
    def material_list_to_mem(self):
        # TODO: Support instance materials

        data = b''
        
        data += pack("<I", len(self.materials))
        for i in range(len(self.materials)):
            data += pack("<i", -1)

        data = Sections.write_chunk(data, types["Struct"])

        for material in self.materials:
            data += material.to_mem()

        return Sections.write_chunk(data, types["Material List"])

    #######################################################
    def extensions_to_mem(self):

        data = b''
        for extension in self.extensions:
            data += self.extensions[extension].to_mem()

        return Sections.write_chunk(data, types["Extension"])
        
    #######################################################
    def to_mem(self):

        # Set flags
        flags = rpGEOMETRYPOSITIONS
        if len(self.uv_layers) > 0:
            flags |= rpGEOMETRYTEXTURED
        if len(self.uv_layers) > 1:
            flags |= rpGEOMETRYTEXTURED2
        if len(self.prelit_colours) > 0:
            flags |= rpGEOMETRYPRELIT
        if self.normals is not None:
            flags |= rpGEOMETRYNORMALS
        if self.export_flags["light"]:
            flags |= rpGEOMETRYLIGHT
        if self.export_flags["modulate_colour"]:
            flags |= rpGEOMETRYMODULATEMATERIALCOLOR

        data = b''
        data += pack("<IIII", flags, len(self.triangles), len(self.vertices), 1)

        # Only present in older RW
        if Sections.get_rw_version() < 0x34000:
            data += Sections.write(GeomSurfPro, self.surface_properties)

        # Write pre-lit colours
        if flags & rpGEOMETRYPRELIT:
            for colour in self.prelit_colours:
                data += Sections.write(RGBA, colour)

        # Write UV Layers
        for uv_layer in self.uv_layers:
            for tex_coord in uv_layer:
                data += Sections.write(TexCoords, tex_coord)

        # Write Triangles
        for triangle in self.triangles:
            data += Sections.write(Triangle, triangle)

        # Bounding sphere and has_vertices, has_normals
        data += Sections.write(Sphere, self.bounding_sphere)
        data += pack("<II",
                     1 if len(self.vertices) > 0 else 0,
                     1 if len(self.normals) > 0 else 0)

        # Write Vertices
        for vertex in self.vertices:
            data += Sections.write(Vector, vertex)

        # Write Normals
        for normal in self.normals:
            data += Sections.write(Vector, normal)

        data = Sections.write_chunk(data, types["Struct"])
        
        # Write Material List and extensions
        data += self.material_list_to_mem()
        data += self.extensions_to_mem()
        return Sections.write_chunk(data, types["Geometry"])

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

            if self.frame_list[i].name is None:
                self.frame_list[i].name = "unnamed"
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

                        elif chunk.type == types["Skin PLG"]:
                            
                            skin = SkinPLG.from_mem(self.data[self.pos:], geometry)
                            geometry.extensions["skin"] = skin
                            
                            self._read(chunk.size)
                        
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
    def write_frame_list(self):

        data = b''

        data += pack("<I", len(self.frame_list)) # length

        for frame in self.frame_list:
            data += frame.header_to_mem()

        data = Sections.write_chunk(data, types["Struct"])
        
        for frame in self.frame_list:
            data += frame.extensions_to_mem()

        return Sections.write_chunk(data, types["Frame List"])

    #######################################################
    def write_geometry_list(self):

        data = b''
        data += pack("<I", len(self.geometry_list))

        data = Sections.write_chunk(data, types["Struct"])
        
        for geometry in self.geometry_list:
            data += geometry.to_mem()
        
        return Sections.write_chunk(data, types["Geometry List"])

    #######################################################
    def write_atomic(self, atomic):

        data = Sections.write(Atomic, atomic, types["Struct"])

        ext_data = b''
        if "skin" in self.geometry_list[atomic.geometry].extensions:
            ext_data += Sections.write_chunk(
                pack("<II", 0x0116, 1),
                types["Right to Render"]
            )
        data += Sections.write_chunk(ext_data, types["Extension"])
        return Sections.write_chunk(data, types["Atomic"])
    
    #######################################################
    def write_memory(self, version):

        data = b''
        Sections.set_library_id(version, 0xFFFF)

        data += Sections.write(Clump, (len(self.atomic_list), 0,0), types["Struct"])
        data += self.write_frame_list()
        data += self.write_geometry_list()

        for atomic in self.atomic_list:
            data += self.write_atomic(atomic)

        data += Sections.write_chunk(b"", types["Extension"])
            
        return Sections.write_chunk(data, types["Clump"])
            
    #######################################################
    def write_file(self, filename: str, version):

        with open(filename, mode='wb') as file:
            content = self.write_memory(version)
            file.write(content)
            
    #######################################################
    def __init__(self):
        
        self.clear()

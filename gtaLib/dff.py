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

from collections import namedtuple
from struct import unpack_from, calcsize, pack
from enum import Enum, IntEnum

# Data types
Chunk       = namedtuple("Chunk"       , "type size version")
Clump       = namedtuple("Clump"       , "atomics lights cameras")
Vector      = namedtuple("Vector"      , "x y z")
Matrix      = namedtuple("Matrix"      , "right up at")
HAnimHeader = namedtuple("HAnimHeader" , "version id bone_count")
Bone        = namedtuple("Bone"        , "id index type")
RGBA        = namedtuple("RGBA"        , "r g b a")
GeomSurfPro = namedtuple("GeomSurfPro" , "ambient specular diffuse")
TexCoords   = namedtuple("TexCoords"   , "u v")
Sphere      = namedtuple("Sphere"      , "x y z radius")
Triangle    = namedtuple("Triangle"    , "b a material c")
Atomic      = namedtuple("Atomic"      , "frame geometry flags unk")
UVFrame     = namedtuple("UVFrame"     , "time uv prev")
BumpMapFX   = namedtuple("BumpMapFX"   , "intensity bump_map height_map")
EnvMapFX    = namedtuple("EnvMapFX"    , "coefficient use_fb_alpha env_map")
DualFX      = namedtuple("DualFX"      , "src_blend dst_blend texture")
ReflMat     = namedtuple("ReflMat"     , "s_x s_y o_x o_y intensity")
SpecularMat = namedtuple("SpecularMap" , "level texture")

UserDataSection = namedtuple("UserDataSection", "name data")

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

# MatFX Dual Texture Blend Mode
class BlendMode(Enum):

    NOBLEND      = 0x00
    ZERO         = 0x01
    ONE          = 0x02
    SRCCOLOR     = 0x03
    INVSRCCOLOR  = 0x04
    SRCALPHA     = 0x05
    INVSRCALPHA  = 0x06
    DESTALPHA    = 0x07
    INVDESTALPHA = 0x08
    DESTCOLOR    = 0x09
    INVDESTCOLOR = 0x0A
    SRCALPHASAT  = 0x0B

# User Data PLG Type
class UserDataType(IntEnum):
    USERDATANA = 0
    USERDATAINT = 1
    USERDATAFLOAT = 2
    USERDATASTRING = 3
    
# Block types
types = {
    "Struct"                  : 1,
    "String"                  : 2,
    "Extension"               : 3,
    "Texture"                 : 6,
    "Material"                : 7,
    "Material List"           : 8,
    "Frame List"              : 14,
    "Geometry"                : 15,
    "Clump"                   : 16,
    "Atomic"                  : 20,
    "Geometry List"           : 26,
    "Animation Anim"          : 27,
    "Right to Render"         : 31,
    "UV Animation Dictionary" : 43,
    "Skin PLG"                : 278,
    "HAnim PLG"               : 286,
    "User Data PLG"           : 287,
    "Material Effects PLG"    : 288,
    "UV Animation PLG"        : 309,
    "Bin Mesh PLG"            : 1294,
    "Pipeline Set"            : 39056115,
    "Specular Material"       : 39056118,
    "2d Effect"               : 39056120,
    "Extra Vert Color"        : 39056121,
    "Collision Model"         : 39056122,
    "Reflection Material"     : 39056124,
    "Frame"                   : 39056126,
}

#######################################################
def strlen(bytes, offset=0):

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
        HAnimHeader : "<3i",
        Bone        : "<3i",
        RGBA        : "<4B",
        GeomSurfPro : "<3f",
        Sphere      : "<4f",
        Triangle    : "<4H",
        Atomic      : "<4I",
        TexCoords   : "<2f",
        ReflMat     : "<5f4x",
        SpecularMat : "<f24s"
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

        elif type is UVFrame:
            return UVFrame(
                unpack_from("<f", data, offset)[0], #Time
                list(unpack_from("<6f", data, offset + 4)), #UV
                unpack_from("<i", data, offset + 28)[0] #Prev
            )
        else:
            raise NotImplementedError("unknown type", type)

    #######################################################
    def pad_string(str):

        str_len = len(str)
        str_len += 1

        # pad to next power of 4 if current number is not divisible by 4
        str_len = (str_len // 4 + (0 if str_len % 4 == 0 else 1)) * 4
        return pack("%ds" % str_len, str.encode('utf8'))
        
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

        elif type is UVFrame:
            _data +=  pack("<f6fi", data.time, *data.uv, data.prev)
            
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

        return (library_id << 8)

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
        self.filters            = 0
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
        data += Sections.write_chunk(Sections.pad_string(self.name),
                                     types["String"])
        data += Sections.write_chunk(Sections.pad_string(self.mask),
                                     types["String"])
        data += Sections.write_chunk(b'', types["Extension"])
        
        return Sections.write_chunk(data, types["Texture"])

#######################################################
class Material:

    __slots__ = [
        'flags',
        'color',
        'is_textured',
        'surface_properties',
        'textures',
        'plugins',
        '_hasMatFX'
    ]
    
    #######################################################
    def __init__(self):

        self.flags              = None
        self.color              = None
        self.is_textured        = None
        self.surface_properties = None
        self.textures           = []
        self.plugins            = {}
        self._hasMatFX          = False #Used only internally for export
    
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
        self.color       = array_data[1]
        self.is_textured = array_data[3]
        self.textures    = []
        self.plugins     = {}

        return self

    #######################################################
    def add_plugin(self, key, plugin):

        if plugin is None:
            return

        if key not in self.plugins:
            self.plugins[key] = []

        try:
            self.plugins[key].append(plugin)

        # This shouldn't happen
        except AttributeError:
            self.plugins[key] = []
            self.plugins[key].append(plugin)

    #######################################################
    def bumpfx_to_mem(self):

        data = b''
        bump_map = self.plugins['bump_map'][0]
        
        data += pack("<IfI", 1, bump_map.intensity, bump_map.bump_map is not None)
        if bump_map.bump_map is not None:
            data += bump_map.bump_map.to_mem()

        data += pack("<I", bump_map.height_map is not None)
        if bump_map.height_map is not None:
            data += bump_map.height_map.to_mem()

        return data

    #######################################################
    def envfx_to_mem(self):
        env_map = self.plugins['env_map'][0]
        
        data = pack("<IfII",
                    2,
                    env_map.coefficient,
                    env_map.use_fb_alpha,
                    env_map.env_map is not None
        )
        if env_map.env_map is not None:
            data += env_map.env_map.to_mem()

        return data

    #######################################################
    def plugins_to_mem(self):
        data = self.matfx_to_mem()

        # Specular Material
        if 'spec' in self.plugins:
            data += Sections.write(
                SpecularMat,
                self.plugins['spec'][0],
                types["Specular Material"]
            )

        # Reflection Material
        if 'refl' in self.plugins:
            data += Sections.write(
                ReflMat,
                self.plugins['refl'][0],
                types["Reflection Material"]
            )

        # UV Animation PLG
        if 'uv_anim' in self.plugins:
            _data = pack("<I", len(self.plugins['uv_anim']))
            for frame_name in self.plugins['uv_anim']:
                _data += pack("<32s", frame_name.encode('ascii'))

            _data = Sections.write_chunk(_data, types["Struct"])
            data += Sections.write_chunk(_data, types["UV Animation PLG"])

        if 'udata' in self.plugins:
            data += self.plugins['udata'][0].to_mem()
            
        return data
    
    #######################################################
    def matfx_to_mem(self):
        data = b''

        effectType = 0
        if 'bump_map' in self.plugins:
            data += self.bumpfx_to_mem()
            effectType = 1
            
            if 'env_map' in self.plugins: #rwMATFXEFFECTBUMPENVMAP
                data += self.envfx_to_mem()
                effectType = 3
                
            
        elif 'env_map' in self.plugins:
            data += self.envfx_to_mem()
            effectType = 2
            
        elif 'dual' in self.plugins:
            effectType = 4
            
            if 'uv_anim' in self.plugins: #rwMATFXEFFECTDUALUVTTRANSFORM
                effectType = 6

        elif 'uv_anim' in self.plugins:
            effectType = 5
            data += pack("<I", 5)

        if effectType == 0:
            self._hasMatFX = False
            return b''
            
        if effectType != 3 or effectType != 6: #Both effects are set
            data += pack("<I", 0)

        self._hasMatFX = True
        data = pack("<I", effectType) + data
        return Sections.write_chunk(data, types["Material Effects PLG"])
        
    #######################################################
    def to_mem(self):

        data = pack("<4x")
        data += Sections.write(RGBA, self.color)
        data += pack("<II", 1, len(self.textures) > 0)

        if Sections.get_rw_version() > 0x30400:
            data += Sections.write(GeomSurfPro, self.surface_properties)

        data = Sections.write_chunk(data, types["Struct"])

        # Only 1 texture is supported (I think)
        if len(self.textures) > 0:
            data += self.textures[0].to_mem()

        data += Sections.write_chunk(self.plugins_to_mem(), types["Extension"])
        return Sections.write_chunk(data, types["Material"])

    #######################################################
    def __hash__(self):
        return hash(self.to_mem())

#######################################################
class UserData:

    __slots__ = ['sections']
    
    #######################################################
    def __init__(self):
        self.sections = []

    #######################################################
    def from_mem(data):

        self = UserData()
        
        num_sections = unpack_from("<I", data)[0]
        offset = 4
        
        for i in range(num_sections):

            # Section name
            name_len = unpack_from("<I", data, offset)[0]
            name = unpack_from("<%ds" % (name_len), data,
                               offset + 4)[0].decode('ascii')

            offset += name_len + 4

            # Elements
            element_type, num_elements = unpack_from("<II", data, offset)
            offset += 8
            
            elements = []
            if element_type == UserDataType.USERDATAINT:
                elements = list(unpack_from("<%dI" % (num_elements), data, offset))
                offset += 4 * num_elements

            elif element_type == UserDataType.USERDATAFLOAT:
                elements = list(unpack_from("<%df" % (num_elements), data, offset))
                offset += 4 * num_elements

            elif element_type == UserDataType.USERDATASTRING:
                for j in range(num_elements):
                    str_len = unpack_from("<I", data, offset)[0]
                    string = unpack_from("<%ds" % (str_len), data, offset + 4)[0]
                    elements.append(string.decode('ascii'))
                    
                    offset += 4 + str_len

            self.sections.append (UserDataSection(name, elements))

        return self

    #######################################################
    def to_mem (self):
        data = b''

        data += pack("<I", len(self.sections))
        for section in self.sections:
            section:UserDataSection

            # Write name
            data += pack("<I%ds" % (len(section.name)),
                         len(section.name), section.name.encode("ascii"))

            userTypes = {
                int: UserDataType.USERDATAINT,
                float: UserDataType.USERDATAFLOAT,
                str: UserDataType.USERDATASTRING
            }

            data_type = UserDataType.USERDATANA
            total_elements = len(section.data)
            if total_elements > 0 and type(section.data[0]) in userTypes:
                data_type = userTypes[type(section.data[0])]

            # Write Elements
            data += pack("<II", data_type, total_elements)
            if data_type == UserDataType.USERDATAINT:
                data += pack("<%dI" % (total_elements), *section.data)
            elif data_type == UserDataType.USERDATAFLOAT:
                data += pack("<%df" % (total_elements), *section.data)
            elif data_type == UserDataType.USERDATASTRING:
                for string in section.data:
                    data += pack("<I%ds" % len(string), len(string), string.encode("ascii"))

        return Sections.write_chunk(data, types["User Data PLG"])
    
#######################################################
class Frame:

    __slots__ = [
        'rotation_matrix',
        'position',
        'parent',
        'creation_flags',
        'name',
        'bone_data',
        'user_data'
    ]
    
    ##################################################################
    def __init__(self):
        self.rotation_matrix = None
        self.position        = None
        self.parent          = None
        self.creation_flags  = None
        self.name            = None
        self.bone_data       = None
        self.user_data       = None

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
            data += Sections.write_chunk(Sections.pad_string(self.name),
                                         types["Frame"])

        if self.bone_data is not None:
            data += self.bone_data.to_mem()

        if self.user_data is not None:
            data += self.user_data.to_mem()
        
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
class UVAnim:
    __slots__ = [
        "type_id",
        "flags",
        "duration",
        "name",
        "node_to_uv",
        "frames"
    ]

    #######################################################
    def __init__(self):
        self.type_id = 0x1C1
        self.flags = 0
        self.duration = 0
        self.name = ""
        self.node_to_uv = [0] * 8
        self.frames = []

    #######################################################
    def from_mem(data):
        self = UVAnim()

        _data = unpack_from("<4xiiif4x32s", data)
        self.type_id, num_frames, self.flags, self.duration, self.name = _data

        _data = unpack_from("8f", data, 56)
        self.node_to_uv = list(_data)

        for pos in range(88, 88 + num_frames * 32, 32):
            self.frames.append(
                Sections.read(UVFrame, data, pos)
            )

        self.name = self.name[:strlen(self.name)].decode('ascii')
            
        return self

    #######################################################
    def to_mem(self):

        data = pack("<iiiif4x32s8f",
                    0x100,
                    self.type_id,
                    len(self.frames),
                    self.flags,
                    self.duration,
                    self.name.encode('ascii'),
                    *self.node_to_uv)

        for frame in self.frames:
            data += Sections.write(UVFrame, frame)

        return Sections.write_chunk(data, types["Animation Anim"])
    
#######################################################
class SkinPLG:

    __slots__ = [
        "num_bones",
        "_num_used_bones",
        "max_weights_per_vertex",
        "bones_used",
        "vertex_bone_indices",
        "vertex_bone_weights",
        "bone_matrices"
    ]
    ##################################################################
    def __init__(self):
        
        self.num_bones = None
        self._num_used_bones = 0
        self.max_weights_per_vertex = 0
        self.bones_used = []
        self.vertex_bone_indices = []
        self.vertex_bone_weights = []
        self.bone_matrices = []

    ##################################################################
    def calc_max_weights_per_vertex (self):
        for i, bone_indices in enumerate(self.vertex_bone_indices):
            for j in range(len(bone_indices)):
                if self.vertex_bone_weights[i][j] > 0:
                    if self.max_weights_per_vertex >= 4:
                        return
                    self.max_weights_per_vertex += 1

    ##################################################################
    def calc_used_bones (self):
        self.bones_used = []
        tmp_used = {}

        for i, bone_indices in enumerate(self.vertex_bone_indices):
            for j, bone_index in enumerate(bone_indices):
                if self.vertex_bone_weights[i][j] > 0:
                    if bone_index not in tmp_used:
                        self.bones_used.append(bone_index)
                        tmp_used[bone_index] = True

        self.bones_used.sort()

    ##################################################################
    def to_mem(self):

        oldver = Sections.get_rw_version() < 0x34000

        self.calc_max_weights_per_vertex ()
        self.calc_used_bones ()

        data = b''
        print(self.num_bones, len(self.bones_used), self.max_weights_per_vertex)
        data += pack("<3Bx", self.num_bones, len(self.bones_used),
                     self.max_weights_per_vertex)

        # Used Bones
        data += pack(f"<{len(self.bones_used)}B", *self.bones_used)
        print(self.bones_used, self.max_weights_per_vertex)
        
        # 4x Indices
        for indices in self.vertex_bone_indices:
            data += pack("<4B", *indices)

        # 4x Weight
        for weight in self.vertex_bone_weights:
            data += pack("<4f", *weight)

        # 4x4 Matrix
        for matrix in self.bone_matrices:
            if oldver:
                data += pack("<I", 0xDEADDEAD) # interesting value :eyes:

            for i in matrix:
                data += pack("<4f", *i)

        # Skin split, just write (0, 0, 0) for now.
        # TODO: Support skin split?
        if not oldver:
            data += pack("<12x")

        return Sections.write_chunk(data, types["Skin PLG"])

    ##################################################################
    @staticmethod
    def from_mem(data, geometry):

        self = SkinPLG()

        _data = unpack_from("<3Bx", data)
        self.num_bones, self._num_used_bones, self.max_weights_per_vertex = _data

        # num used bones and max weights per vertex apparently didn't exist in old versions.
        oldver = self._num_used_bones == 0
        
        # Used bones array starts at offset 4
        for pos in range(4, self._num_used_bones + 4):
            self.bones_used.append(unpack_from("<B", data, pos)[0])

        pos = 4 + self._num_used_bones
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

        # Old version has additional 4 bytes 0xdeaddead
        unpack_format = "<16f"
        if oldver:
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

        # TODO: (maybe) read skin split data for new version
        # if not oldver:
        #     readSkinSplit(...)
            
        return self

#######################################################
class ExtraVertColorExtension:

    #######################################################
    def __init__(self, colors):
        self.colors = colors

    #######################################################
    @staticmethod
    def from_mem(data, offset, geometry):

        magic = unpack_from("<I", data, offset)[0]
        if magic != 0:
            colors = []
            for i in range(len(geometry.vertices)):

                offset += 4
                colors.append(
                    Sections.read(
                        RGBA, data, offset
                    )
                )
                
            return ExtraVertColorExtension(colors)
                
    #######################################################
    def to_mem(self):
        
        data = pack("<I", 1)
        for color in self.colors:
            data += Sections.write(RGBA, color)

        return Sections.write_chunk(data, types["Extra Vert Color"])

#######################################################
class Light2dfx:

    #######################################################
    class Flags1(Enum):
        CORONA_CHECK_OBSTACLES = 1
        FOG_TYPE = 2
        FOG_TYPE2 = 4
        WITHOUT_CORONA = 8
        CORONA_ONLY_AT_LONG_DISTANCE = 16
        AT_DAY = 32
        AT_NIGHT = 64
        BLINKING1 = 128

    #######################################################
    class Flags2(Enum):
        CORONA_ONLY_FROM_BELOW = 1
        BLINKING2 = 2
        UDPDATE_HEIGHT_ABOVE_GROUND = 4
        CHECK_DIRECTION = 8
        BLINKING3 = 16
        
    #######################################################
    def __init__(self, loc):

        self.effect_id = 0

        self.loc = loc
        self.color = [0,0,0]
        self.coronaFarClip = 0
        self.pointlightRange = 0
        self.coronaSize = 0
        self.shadowSize = 0
        self.coronaShowMode = 0
        self.coronaEnableReflection = 0
        self.coronaFlareType = 0
        self.shadowColorMultiplier = 0
        self._flags1 = 0
        self.coronaTexName = ""
        self.shadowTexName = ""
        self.shadowZDistance = 0
        self._flags2 = 0
        self.lookDirection = None
    
    #######################################################
    @staticmethod
    def from_mem(loc, data, offset, size):
        self = Light2dfx(loc)

        self.color = Sections.read(RGBA, data, offset)
        
        self.coronaFarClip   , self.pointlightRange        , \
        self.coronaSize      , self.shadowSize             , \
        self.coronaShowMode  , self.coronaEnableReflection , \
        self.coronaFlareType , self.shadowColorMultiplier  , \
        self._flags1         , self.coronaTexName          , \
        self.shadowTexName   , self.shadowZDistance        , \
        self._flags2 =  unpack_from("<ffffBBBBB24s24sBB", data, offset + 4)

        # 80 bytes structure
        if size > 76:
            self.lookDirection = unpack_from("<BBB", data, offset + 76)

        # Convert byte arrays to strings here
        self.coronaTexName = self.coronaTexName[:strlen(self.coronaTexName)]
        self.shadowTexName = self.shadowTexName[:strlen(self.shadowTexName)]

        self.coronaTexName = self.coronaTexName.decode('ascii')
        self.shadowTexName = self.shadowTexName.decode('ascii')
            
        return self

    #######################################################
    def to_mem(self):
        data = Sections.write(RGBA, self.color)

        # 76 bytes
        data += pack(
            "<ffffBBBBB24s24sBB",
            self.coronaFarClip   , self.pointlightRange,
            self.coronaSize      , self.shadowSize,
            self.coronaShowMode  , self.coronaEnableReflection,
            self.coronaFlareType , self.shadowColorMultiplier,
            self._flags1         , self.coronaTexName,
            self.shadowTexName   , self.shadowZDistance,
            self._flags2
        )

        # 80 bytes
        if self.lookDirection is not None:
            data += pack("<BBB2x", *self.lookDirection)

        # 76 bytes (padding)
        else:
            data += pack("<x")

        return data
    
    #######################################################
    def set_flag(self, flag):
        self._flag |= flag

    #######################################################
    def set_flag2(self, flag):
        self._flag2 |= flag

#######################################################
class Particle2dfx:

    #######################################################
    def __init__(self, loc):
        self.loc = loc
        self.effect_id = 1
        self.effect = ""

    #######################################################
    @staticmethod
    def from_mem(loc, data, offset, size):

        self = Particle2dfx(loc)
        self.effect = data[offset:strlen(data, offset)].decode('ascii')
                
        return self

    #######################################################
    def to_mem(self):
        return pack("<24s", self.effect)

#######################################################
class PedAttractor2dfx:

    #######################################################
    # See: https://gtamods.com/wiki/2d_Effect_(RW_Section)
    #######################################################
    class Types(Enum):

        PED_ATM_ATTRACTOR = 0
        PED_SEAT_ATTRACTOR = 1
        PED_STOP_ATTRACTOR = 2
        PED_PIZZA_ATTRACTOR = 3
        PED_SHELTER_ATTRACTOR = 4
        PED_TRIGGER_SCRIPT_ATTRACTOR = 5
        PED_LOOK_AT_ATTRACTOR = 6
        PED_SCRIPTED_ATTRACTOR = 7
        PED_PARK_ATTRACTOR = 8
        PED_STEP_ATTRACTOR = 9
        
    #######################################################
    def __init__(self, loc):

        self.effect_id = 3
        
        self.loc = loc
        self.type = 0
        self.rotation_matrix = None
        self.external_script = ""
        self.ped_existing_probability = 0

    #######################################################
    @staticmethod
    def from_mem(loc, data, offset, size):
        self = PedAttractor2dfx(loc)

        self.type = unpack_from("<I", data, offset)[0]
        self.rotation_matrix = Sections.read(Matrix, data, offset + 4)
        self.external_script = data[offset + 40: strlen(data, offset + 40)]
        self.ped_existing_probabiliy = unpack_from("<I", data, offset + 48)[0]

        self.external_script = self.external_script.decode('ascii')
        
        return self

    #######################################################
    def to_mem(self):
        data = pack("<I", self.type)
        data += Sections.write(Matrix, self.rotation_matrix)
        data += pack("<8sI", self.external_script, self.ped_existing_probability)

        return data

#######################################################
class SunGlare2dfx:

    #######################################################
    def __init__(self, loc):
        self.loc = loc
        self.effect_id = 4

    #######################################################
    @staticmethod
    def from_mem(loc, data, offset, size):
        return SunGlare2dfx(loc)

    #######################################################
    def to_mem(self):
        return b''
        
#######################################################
class Extension2dfx:

    #######################################################
    def __init__(self):
        self.entries = []

    #######################################################
    def append_entry(self, entry):
        self.entries.append(entry)

    #######################################################
    @staticmethod
    def from_mem(data, offset):

        self = Extension2dfx()
        entries_count = unpack_from("<I", data, offset)[0]

        pos = 4 + offset
        for i in range(entries_count):

            # Stores classes for each effect
            entries_funcs = {
                0: Light2dfx,
                1: Particle2dfx,
                3: PedAttractor2dfx,
                4: SunGlare2dfx
            }
            
            loc = Sections.read(Vector, data, pos)
            entry_type, size = unpack_from("<II", data, pos + 12)

            pos += 20
            if entry_type in entries_funcs:
                self.append_entry(
                    entries_funcs[entry_type].from_mem(loc, data, pos, size)
                )
            else:
                print("Unimplemented Effect: %d" % (entry_type))

            pos += size

        return self

    #######################################################
    def to_mem(self):

        # Write only if there are entries
        if len(self.entries) == 0:
            return b''
        
        # Entries length
        data = pack("<I", len(self.entries))

        # Entries
        for entry in self.entries:
            entry_data = entry.to_mem()

            data += pack("<II", entry.effect_id)
            data += entry_data

        return Sections.write_chunk(data, types['2d Effect'])
            
    #######################################################
    def __add__(self, other):
        self.entries += other.entries # concatinate entries
        return self
    
#######################################################
class Geometry:

    __slots__ = [
        
        'flags',
        'triangles',
        'vertices',
        'surface_properties',
        'prelit_colors',
        'uv_layers',
        'bounding_sphere',
        'has_vertices',
        'has_normals',
        'normals',
        'materials',
        'extensions',
        'export_flags',
        'pipeline',
        '_hasMatFX'
    ]
    
    ##################################################################
    def __init__(self):
        self.flags              = None
        self.triangles          = []
        self.vertices           = []
        self.surface_properties = None
        self.prelit_colors      = []
        self.uv_layers          = []
        self.bounding_sphere    = None
        self.has_vertices       = None
        self.has_normals        = None
        self.normals            = []
        self.materials          = []
        self.extensions         = {}
        self.pipeline           = None

        # used for export
        self.export_flags = {
            "light"              : True,
            "modulate_color"     : True,
            "export_normals"     : True,
            "write_mesh_plg"     : True
        }
        self._hasMatFX = False

    #######################################################
    @staticmethod
    def from_mem(data, parent_chunk):

        # Note: In the following function, I have used a loop
        #      to load the texture coordinates or prelit colors,
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

            # Read prelighting colors
            if self.flags & rpGEOMETRYPRELIT:
                self.prelit_colors = []
                
                for i in range(num_vertices):
                    prelit_color = Sections.read(RGBA, data, pos)
                    self.prelit_colors.append(prelit_color)

                    pos += 4

            # Read Texture Mapping coordinates
            if self.flags & (rpGEOMETRYTEXTURED | rpGEOMETRYTEXTURED2):
                texCount = (self.flags & 0x00FF0000) >> 16
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
            self._hasMatFX = material._hasMatFX if not self._hasMatFX else True

        return Sections.write_chunk(data, types["Material List"])

    #######################################################
    # TODO: Triangle Strips support
    # TODO: OpenGL support
    def write_bin_split(self):
        
        data = b''
        
        meshes = {}

        for triangle in self.triangles:
            
            if triangle.material not in meshes:
                meshes[triangle.material] = []
                
            meshes[triangle.material] += [triangle.a, triangle.b, triangle.c]

        data += pack("<III", 0, len(meshes), len(self.triangles) * 3)
        
        for mesh in meshes:
            data += pack("<II", len(meshes[mesh]), mesh)
            data += pack("<%dI" % (len(meshes[mesh])), *meshes[mesh])

        return Sections.write_chunk(data, types["Bin Mesh PLG"])
    
    #######################################################
    def extensions_to_mem(self, extra_extensions = []):

        data = b''

        # Write Bin Mesh PLG
        if self.export_flags['write_mesh_plg']:
            data += self.write_bin_split()
        
        for extension in self.extensions:
            if self.extensions[extension] is not None:
                data += self.extensions[extension].to_mem()

        # Write extra extensions
        for extra_extension in extra_extensions:
            data += extra_extension.to_mem()
            
        return Sections.write_chunk(data, types["Extension"])
        
    #######################################################
    def to_mem(self, extra_extensions = []):

        # Set flags
        flags = rpGEOMETRYPOSITIONS
        if len(self.uv_layers) > 1:
            flags |= rpGEOMETRYTEXTURED2
        elif len(self.uv_layers) > 0:
            flags |= rpGEOMETRYTEXTURED
        if len(self.prelit_colors) > 0:
            flags |= rpGEOMETRYPRELIT
        if len(self.normals) > 0 and self.export_flags["export_normals"]:
            flags |= rpGEOMETRYNORMALS
        flags |= rpGEOMETRYLIGHT * self.export_flags["light"]
        flags |= rpGEOMETRYMODULATEMATERIALCOLOR * \
            self.export_flags["modulate_color"]

        flags |= (len(self.uv_layers) & 0xff) << 16
        
        data = b''
        data += pack("<IIII", flags, len(self.triangles), len(self.vertices), 1)

        # Only present in older RW
        if Sections.get_rw_version() < 0x34000:
            data += Sections.write(GeomSurfPro, self.surface_properties)

        # Write pre-lit colors
        if flags & rpGEOMETRYPRELIT:
            for color in self.prelit_colors:
                data += Sections.write(RGBA, color)

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
                     1 if flags & rpGEOMETRYNORMALS else 0)

        # Write Vertices
        for vertex in self.vertices:
            data += Sections.write(Vector, vertex)

        # Write Normals
        if flags & rpGEOMETRYNORMALS:
            for normal in self.normals:
                data += Sections.write(Vector, normal)

        data = Sections.write_chunk(data, types["Struct"])
        
        # Write Material List and extensions
        data += self.material_list_to_mem()
        data += self.extensions_to_mem(extra_extensions)
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
                user_data = None

                if chunk.type == types["Frame"]:
                    name = self.raw(strlen(self.data,self.pos)).decode("utf-8")
                    
                elif chunk.type == types["HAnim PLG"]:
                    bone_data = HAnimPLG.from_mem(self.raw(chunk.size))

                elif chunk.type == types["User Data PLG"]:
                    user_data = UserData.from_mem(self.raw(chunk.size))

                self._read(chunk.size)
                if name is not None:
                    self.frame_list[i].name = name
                if bone_data is not None:
                    self.frame_list[i].bone_data = bone_data
                if user_data is not None:
                    self.frame_list[i].user_data = user_data

            if self.frame_list[i].name is None:
                self.frame_list[i].name = "unnamed"
            i += 1
            

    #######################################################
    def read_mesh_plg(self, parent_chunk, geometry):
        triangles = []
        
        _Header      = namedtuple("_Header","flags mesh_count total_indices")
        _SplitHeader = namedtuple("_SplitHeader","indices_count material")
        _Triangle    = namedtuple("_Triangle", "a b c")
        
        header = _Header._make(unpack_from("<III", self.data, self._read(12)))

        # calculate if the indices are stored in 32 bit or 16 bit
        calculated_size = 12 + header.mesh_count * 8 + (header.total_indices * 2)
        opengl = calculated_size >= parent_chunk.size
        
        is_tri_strip = header.flags == 1
        for i in range(header.mesh_count):
            
            # Read header
            split_header = _SplitHeader._make(unpack_from("<II",
                                                          self.data,
                                                          self._read(8)))

            unpack_format = "<H" if opengl else "<H2x"
            total_iterations = split_header.indices_count
            
            # Read 3 integers instead of 1 incase of triangle lists
            if not is_tri_strip: 
                unpack_format = "<" + (unpack_format[1:] * 3)
                total_iterations //= 3

            previous_vertices = []
            for j in range(total_iterations):

                # Read Triangle Strip
                if is_tri_strip:

                    vertex = unpack_from(
                        unpack_format,
                        self.data,
                        self._read(2 if opengl else 4)
                    )[0]

                    if len(previous_vertices) < 2:
                        previous_vertices.append(vertex)
                        continue

                    if(j % 2 == 0):
                        triangle = Triangle(
                            previous_vertices[1],
                            previous_vertices[0],
                            split_header.material,
                            vertex
                        )
                    else:
                        triangle = Triangle(
                            previous_vertices[0],
                            previous_vertices[1],
                            split_header.material,
                            vertex
                        )
                
                    previous_vertices[0] = previous_vertices[1]
                    previous_vertices[1] = vertex

                # Read Triangle List
                else:

                    _triangle = _Triangle._make(
                        unpack_from(
                            unpack_format,
                            self.data,
                            self._read(6 if opengl else 12)
                        )
                    )

                    triangle = Triangle._make(
                        (
                            _triangle.b,
                            _triangle.a,
                            split_header.material,
                            _triangle.c
                        )
                    )

                triangles.append(triangle)

        geometry.extensions['mat_split'] = triangles

    #######################################################
    def read_matfx_bumpmap(self):
        bump_map   = None
        intensity  = 0.0
        height_map = None
        
        intensity, contains_bump_map = unpack_from("<fI",
                                                   self.data,
                                                   self._read(8))
        # Read Bump Map
        if contains_bump_map:
            bump_chunk = self.read_chunk()
            chunk_end = self.pos + bump_chunk.size
            
            if bump_chunk.type != types["Texture"]:
                raise RuntimeError("Invalid format")

            bump_map = self.read_texture()
            self.pos = chunk_end

        contains_height_map = unpack_from("<I", self.data, self._read(4))[0]

        # Read height map
        if contains_height_map:
            height_chunk = self.read_chunk()
            chunk_end = self.pos + height_chunk.size
            
            if height_chunk.type != types["Texture"]:
                raise RuntimeError("Invalid format")
            
            height_map = self.read_texture()
            self.pos = chunk_end

        return BumpMapFX(intensity, bump_map, height_map)        

    #######################################################
    def read_matfx_envmap(self):
        env_map      = None
        coefficient  = 1.0
        use_fb_alpha = False #fb = frame buffer
    
        coefficient, use_fb_alpha, contains_envmap = unpack_from("<fII",
                                                                 self.data,
                                                                 self._read(12))

        # Read environment map texture
        if contains_envmap:
            env_chunk = self.read_chunk()
            chunk_end = self.pos + env_chunk.size
            
            if env_chunk.type != types["Texture"]:
                raise RuntimeError("Invalid format")
            
            env_map = self.read_texture()
            self.pos = chunk_end

        return EnvMapFX(coefficient, use_fb_alpha, env_map)

    #######################################################
    def read_matfx_dual(self):
        src_blend = 0
        dst_blend = 0
        texture   = None

        src_blend, dst_blend, has_texture = unpack_from("<III",
                                                        self.data,
                                                        self._read(12))

        # Read Texture
        if has_texture:
            tex_chunk = self.read_chunk()
            chunk_end = self.pos + tex_chunk.size
            
            if tex_chunk.type != types["Texture"]:
                raise RuntimeError("Invalid format")
            
            texture = self.read_texture()
            self.pos = chunk_end

        return DualFX(src_blend, dst_blend, texture)
    
    #######################################################
    def read_matfx(self, material, chunk):

        self._read(4) #header - effect type (not really required to be read)
        for i in range(2):
            effect_type = unpack_from("<I", self.data, self._read(4))[0]
            
            # Bump Map
            if effect_type == 1:
                material.add_plugin('bump_map', self.read_matfx_bumpmap())

            # Environment Mapping
            if effect_type == 2:
                material.add_plugin('env_map', self.read_matfx_envmap())

            # Dual Texturing
            if effect_type == 4:
                material.add_plugin('dual', self.read_matfx_dual())

    #######################################################
    def read_texture(self):
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
        return texture
        
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

                            _chunk_end = self.pos + chunk.size
                            texture = self.read_texture()

                            material.textures.append(texture)
                            self.pos = _chunk_end

                        elif chunk.type == types["Extension"]:
                            if chunk.size > 0:
                                _chunk_end = chunk.size + self.pos

                                # Read extensions
                                while self.pos < _chunk_end:
                                    chunk = self.read_chunk()
                                    __chunk_end = self.pos + chunk.size
                                    
                                    if chunk.type == types["Material Effects PLG"]:
                                        self.read_matfx(material, chunk)

                                    if chunk.type == types["Specular Material"]:

                                        material.add_plugin(
                                            "spec",
                                            Sections.read(SpecularMat,
                                                          self.data,
                                                          self.pos)
                                        )

                                    if chunk.type == types["Reflection Material"]:
                                        material.add_plugin(
                                            "refl",
                                            Sections.read(ReflMat,
                                                          self.data,
                                                          self.pos)
                                        )

                                    if chunk.type == types["User Data PLG"]:
                                        material.add_plugin (
                                            "udata",
                                            UserData.from_mem(self.data[self.pos:]))
                                        
                                    if chunk.type == types["UV Animation PLG"]:

                                        chunk = self.read_chunk()
                                        
                                        anim_count = unpack_from("<I",
                                                                 self.data,
                                                                 self._read(4))

                                        # Read n animations
                                        for i in range(anim_count[0]):
                                            material.add_plugin('uv_anim',
                                                                self.raw(
                                                                    strlen(
                                                                        self.data,
                                                                        self.pos
                                                                    ),
                                                                    self._read(32)
                                                                ).decode('ascii')
                                            )
                                            
                                    self.pos = __chunk_end
                                    
                                    
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

                        if chunk.type == types["Material List"]:  
                            self.read_material_list(chunk)

                        elif chunk.type == types["Extension"]:  
                            pass # will fallthrough

                        elif chunk.type == types["Skin PLG"]:
                            
                            skin = SkinPLG.from_mem(self.data[self.pos:], geometry)
                            geometry.extensions["skin"] = skin
                            
                            self._read(chunk.size)

                        elif chunk.type == types["Extra Vert Color"]:
                            
                            geometry.extensions['extra_vert_color'] = \
                                ExtraVertColorExtension.from_mem (
                                    self.data, self._read(chunk.size), geometry
                                )

                        elif chunk.type == types["User Data PLG"]:
                            geometry.extensions['user_data'] = \
                                UserData.from_mem(self.data[self.pos:])

                        # 2dfx (usually at the last geometry index)
                        elif chunk.type == types["2d Effect"]:
                            self.ext_2dfx += Extension2dfx.from_mem(
                                self.data,
                                self._read(chunk.size)
                            )
                            
                        elif chunk.type == types["Bin Mesh PLG"]: 
                           self.read_mesh_plg(chunk,geometry)

                        else:
                            self._read(chunk.size)

                    self.pos = chunk_end

    #######################################################
    def read_atomic(self, parent_chunk):

        chunk_end = self.pos + parent_chunk.size
        
        atomic = None
        pipeline = None
        
        while self.pos < chunk_end:
            chunk = self.read_chunk()

            # STRUCT
            if chunk.type == types["Struct"]:
                atomic = Sections.read(Atomic, self.data, self.pos)
                self.atomic_list.append(atomic)

            if chunk.type == types["Extension"]:
                self.pos -= chunk.size

            if chunk.type == types["Pipeline Set"]:
                pipeline = unpack_from("<I", self.data, self.pos)[0]               
            self.pos += chunk.size

        # Set geometry's pipeline
        if pipeline and atomic:
            self.geometry_list[atomic.geometry].pipeline = pipeline

    #######################################################
    def read_clump(self, root_chunk):
        chunk = self.read_chunk()
        root_end = self.pos + root_chunk.size

        # STRUCT
        if chunk.type == types["Struct"]:  

            # read clump data
            self._read(12)
            if Sections.get_rw_version(chunk.version) < 0x33000:
                self._read(-8)
                        
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

                elif chunk.type == types["Collision Model"]:
                    self.collisions.append(
                        self.data[self.pos:self.pos + chunk.size]
                    )
                    self.pos += chunk.size
                    
                #Not incrementing the position here to read the next extensions
                #in the same loop
                elif chunk.type == types["Extension"]: 
                    pass

                else:
                    self.pos += chunk.size

    #######################################################
    def read_uv_anim_dict(self):
        chunk = self.read_chunk()
        
        if chunk.type == types["Struct"]:
            num_anims = unpack_from("<I", self.data, self._read(4))[0]

        for i in range(num_anims):
            
            chunk = self.read_chunk()

            if chunk.type == types["Animation Anim"]:
                self.uvanim_dict.append(
                    UVAnim.from_mem(self.data[self.pos:])
                )

            self._read(chunk.size)
            
    #######################################################
    def load_memory(self, data):

        self.data = data
        while self.pos < len(data) - 12:
            chunk = self.read_chunk()

            if chunk.type == types["Clump"]:
                self.read_clump(chunk)
                self.rw_version = Sections.get_rw_version(chunk.version)

            elif chunk.type == types["UV Animation Dictionary"]:
                self.read_uv_anim_dict()
                

    #######################################################
    def clear(self):
        self.frame_list    = []
        self.geometry_list = []
        self.collisions    = []
        self.atomic_list   = []
        self.uvanim_dict   = []
        self.light_list    = []
        self.ext_2dfx      = Extension2dfx()
        self.pos           = 0
        self.data          = ""
        self.rw_version    = ""
            
    #######################################################
    def load_file(self, filename):

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
        
        for index, geometry in enumerate(self.geometry_list):

            # Append 2dfx to extra extensions in the last geometry
            extra_extensions = []
            if index == len(self.geometry_list):
                extra_extensions.append(self.ext_2dfx)
            
            data += geometry.to_mem()
        
        return Sections.write_chunk(data, types["Geometry List"])

    #######################################################
    def write_atomic(self, atomic):

        data = Sections.write(Atomic, atomic, types["Struct"])
        geometry = self.geometry_list[atomic.geometry]
        
        ext_data = b''
        if "skin" in geometry.extensions:
            ext_data += Sections.write_chunk(
                pack("<II", 0x0116, 1),
                types["Right to Render"]
            )
        if geometry._hasMatFX:
            ext_data += Sections.write_chunk(
                pack("<I", 1),
                types["Material Effects PLG"]
            )
        if geometry.pipeline is not None:
            ext_data += Sections.write_chunk(
                pack("<I", geometry.pipeline),
                types["Pipeline Set"]
            )
            pass
        
        data += Sections.write_chunk(ext_data, types["Extension"])
        return Sections.write_chunk(data, types["Atomic"])

    #######################################################
    def write_uv_dict(self):

        if len(self.uvanim_dict) < 1:
            return b''
        
        data = pack("<I", len(self.uvanim_dict))
        data = Sections.write_chunk(data, types["Struct"])
        
        for dictionary in self.uvanim_dict:
            data += dictionary.to_mem()

        return Sections.write_chunk(data, types["UV Animation Dictionary"])

    #######################################################
    def write_clump(self):

        data = Sections.write(Clump, (len(self.atomic_list), 0,0), types["Struct"])

        # Old RW versions didn't have cameras and lights in their clump structure
        if Sections.get_rw_version() < 0x33000:
            data = Sections.write_chunk(Clump,
                                        pack("<I",
                                             len(self.atomic_list)),
                                        types["Clump"])
            
        data += self.write_frame_list()
        data += self.write_geometry_list()

        for atomic in self.atomic_list:
            data += self.write_atomic(atomic)

        for coll_data in self.collisions:
            _data = Sections.write_chunk(coll_data, types["Collision Model"])
            data += Sections.write_chunk(_data, types["Extension"])
            
        data += Sections.write_chunk(b'', types["Extension"])
            
        return Sections.write_chunk(data, types["Clump"])
    
    #######################################################
    def write_memory(self, version):

        data = b''
        Sections.set_library_id(version, 0xFFFF)

        data += self.write_uv_dict()
        data += self.write_clump()

        return data
            
    #######################################################
    def write_file(self, filename, version):

        with open(filename, mode='wb') as file:
            content = self.write_memory(version)
            file.write(content)
            
    #######################################################
    def __init__(self):
        self.clear()

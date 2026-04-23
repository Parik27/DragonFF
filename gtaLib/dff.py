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

from collections import defaultdict, namedtuple
from struct import unpack_from, calcsize, pack
from enum import Enum, IntEnum

from .pyffi.utils import tristrip

# Data types
Chunk         = namedtuple("Chunk"         , "type size version")
Clump         = namedtuple("Clump"         , "atomics lights cameras")
Vector        = namedtuple("Vector"        , "x y z")
Matrix        = namedtuple("Matrix"        , "right up at")
HAnimHeader   = namedtuple("HAnimHeader"   , "version id bone_count")
Bone          = namedtuple("Bone"          , "id index type")
RGBA          = namedtuple("RGBA"          , "r g b a")
GeomSurfPro   = namedtuple("GeomSurfPro"   , "ambient specular diffuse")
TexCoords     = namedtuple("TexCoords"     , "u v")
Sphere        = namedtuple("Sphere"        , "x y z radius")
Triangle      = namedtuple("Triangle"      , "b a material c")
UVFrame       = namedtuple("UVFrame"       , "time uv prev")
BumpMapFX     = namedtuple("BumpMapFX"     , "intensity bump_map height_map")
EnvMapFX      = namedtuple("EnvMapFX"      , "coefficient use_fb_alpha env_map")
DualFX        = namedtuple("DualFX"        , "src_blend dst_blend texture")
ReflMat       = namedtuple("ReflMat"       , "s_x s_y o_x o_y intensity")
SpecularMat   = namedtuple("SpecularMap"   , "level texture")
GeomBone      = namedtuple("GeomBone"      , "start_vertex vertices_count bone_id")
RightToRender = namedtuple("RightToRender" , "value1 value2")

TexDict = namedtuple("TexDict", "texture_count device_id")
PITexDict = namedtuple("PITexDict", "texture_count device_id")

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

# Native Platform Type
class NativePlatformType(IntEnum):
    D3D7        = 0x1
    OGL         = 0x2
    MAC         = 0x3
    PS2         = 0x4
    XBOX        = 0x5
    GC          = 0x6
    SOFTRAS     = 0x7
    D3D8        = 0x8
    D3D9        = 0x9
    PSP         = 0xa
    PS2FOURCC   = 0x00325350

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
    "Texture Native"          : 21,
    "Texture Dictionary"      : 22,
    "Image"                   : 24,
    "Geometry List"           : 26,
    "Animation Anim"          : 27,
    "Right to Render"         : 31,
    "PI Texture Dictionary"   : 35,
    "UV Animation Dictionary" : 43,
    "Morph PLG"               : 261,
    "Animation PLG"           : 264,
    "Bone PLG"                : 270,
    "Skin PLG"                : 278,
    "HAnim PLG"               : 286,
    "User Data PLG"           : 287,
    "Material Effects PLG"    : 288,
    "Delta Morph PLG"         : 290,
    "UV Animation PLG"        : 309,
    "NTL Material Extension"  : 375,
    "Bin Mesh PLG"            : 1294,
    "Native Data PLG"         : 1296,
    "SkyGFX"                  : 60909,
    "Pipeline Set"            : 39056115,
    "Specular Material"       : 39056118,
    "2d Effect"               : 39056120,
    "Extra Vert Color"        : 39056121,
    "Collision Model"         : 39056122,
    "Reflection Material"     : 39056124,
    "Breakable Model"         : 39056125,
    "Frame"                   : 39056126,
    "SAMP Collision Model"    : 39056127,
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
        Chunk         : "<3I",
        Clump         : "<3I",
        Vector        : "<3f",
        HAnimHeader   : "<3i",
        Bone          : "<3i",
        RGBA          : "<4B",
        GeomSurfPro   : "<3f",
        Sphere        : "<4f",
        Triangle      : "<4H",
        TexCoords     : "<2f",
        ReflMat       : "<5f4x",
        SpecularMat   : "<f24s",
        GeomBone      : "<3I",
        RightToRender : "<II",

        TexDict : "<2H",
        PITexDict: "<2H"
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
        _data = bytearray()
        
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
        'uv_addressing',
        'name',
        'mask'
    ]

    def __init__(self):
        self.filters            = 0
        self.uv_addressing      = 0
        self.name               = ""
        self.mask               = ""

    #######################################################
    def from_mem(data):

        self = Texture()

        _Texture = namedtuple("_Texture", "filters uv_addressing unk")
        _tex = _Texture._make(unpack_from("<2BH", data))

        self.filters = _tex.filters
        self.uv_addressing = _tex.uv_addressing

        return self

    #######################################################
    def to_mem(self):

        data = bytearray()
        data += pack("<2B2x", self.filters, self.uv_addressing)

        data  = Sections.write_chunk(data, types["Struct"])
        data += Sections.write_chunk(Sections.pad_string(self.name),
                                     types["String"])
        data += Sections.write_chunk(Sections.pad_string(self.mask),
                                     types["String"])
        data += Sections.write_chunk(bytearray(), types["Extension"])

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

        data = bytearray()
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
    def dualfx_to_mem(self):
        dual_fx = self.plugins['dual'][0]
        
        data = pack("<IIII",
                    4,
                    dual_fx.src_blend,
                    dual_fx.dst_blend,
                    dual_fx.texture is not None
        )
        if dual_fx.texture is not None:
            data += dual_fx.texture.to_mem()

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
            _data = pack("<I", (1 << len(self.plugins['uv_anim'])) - 1) #bitmask
            for frame_name in self.plugins['uv_anim']:
                _data += pack("<32s", frame_name.encode('ascii'))

            _data = Sections.write_chunk(_data, types["Struct"])
            data += Sections.write_chunk(_data, types["UV Animation PLG"])

        if 'udata' in self.plugins:
            data += self.plugins['udata'][0].to_mem()
            
        return data
    
    #######################################################
    def matfx_to_mem(self):
        data = bytearray()
        effectType = 0
        
        if 'dual' in self.plugins or 'uv_anim' in self.plugins:  
            if 'dual' in self.plugins and 'uv_anim' in self.plugins:  
                dual_fx = self.plugins['dual'][0]  
                if dual_fx.texture is None or dual_fx.texture.name == "":  
                    # Dual texture is empty, use UV transform only  
                    data += pack("<I", 5)  
                    effectType = 5  
                else:  
                    # Both present and dual texture is not empty  
                    data += pack("<I", 5)  
                    data += self.dualfx_to_mem()  
                    effectType = 6  
            elif 'dual' in self.plugins:  
                dual_fx = self.plugins['dual'][0]  
                if dual_fx.texture is None or dual_fx.texture.name == "":  
                    # Dual texture is empty, don't export anything  
                    effectType = 0  
                else:  
                    data += self.dualfx_to_mem()  
                    effectType = 4  
            else:  
                data += pack("<I", 5)  
                effectType = 5
        
        elif 'bump_map' in self.plugins or 'env_map' in self.plugins:
            if 'bump_map' in self.plugins and 'env_map' in self.plugins:
                data += self.bumpfx_to_mem()
                data += self.envfx_to_mem()
                effectType = 3
            elif 'bump_map' in self.plugins:
                data += self.bumpfx_to_mem()
                effectType = 1
            else:
                data += self.envfx_to_mem()
                effectType = 2

        if effectType == 0:
            self._hasMatFX = False
            return bytearray()
        
        if effectType not in (3, 6):
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
class Atomic:

    __slots__ = [
        'frame',
        'geometry',
        'flags',
        'unk',
        'extensions'
    ]

    ##################################################################
    def __init__(self):
        self.frame      = 0
        self.geometry   = 0
        self.flags      = 0
        self.unk        = 0
        self.extensions = {}

    ##################################################################
    def from_mem(data):

        self = Atomic()

        # Atomic with embedded geometry
        if len(data) == 12:
            _Atomic = namedtuple("_Atomic", "frame flags unk")
            _atomic = _Atomic._make(unpack_from("<3I", data))

        else:
            _Atomic = namedtuple("_Atomic", "frame geometry flags unk")
            _atomic = _Atomic._make(unpack_from("<4I", data))

            self.geometry = _atomic.geometry

        self.frame    = _atomic.frame
        self.flags    = _atomic.flags
        self.unk      = _atomic.unk

        return self

    #######################################################
    def to_mem(self):

        data = bytearray()
        data += pack("<4I", self.frame, self.geometry, self.flags, self.unk)
        return data

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
        data = bytearray()

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
        'user_data',
        'animation_data'
    ]
    
    ##################################################################
    def __init__(self):
        self.rotation_matrix = None
        self.position        = None
        self.parent          = -1
        self.creation_flags  = 0
        self.name            = None
        self.bone_data       = None
        self.user_data       = None
        self.animation_data  = None

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

        data = bytearray()
        data += Sections.write(Matrix, self.rotation_matrix)
        data += Sections.write(Vector, self.position)
        data += pack("<iI", self.parent, self.creation_flags)
        return data

    #######################################################
    def extensions_to_mem(self):

        data = bytearray()

        if self.bone_data is not None:
            data += self.bone_data.to_mem()

        if self.user_data is not None:
            data += self.user_data.to_mem()

        if self.name is not None and self.name != "unknown":
            frame_name = self.name.encode("utf-8")
            data += Sections.write_chunk(frame_name,
                                         types["Frame"])

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

        data = bytearray()

        data += Sections.write(HAnimHeader, self.header)
        if len(self.bones) > 0:
            data += pack("<II", 0, 36)
            
        for bone in self.bones:
            data += Sections.write(Bone, bone)

        return Sections.write_chunk(data, types["HAnim PLG"])

#######################################################
# TODO: AnimationPLG data
class AnimationPLG:

    __slots__ = [
        'id'
    ]

    #######################################################
    def __init__(self):
        self.id = -1

    #######################################################
    def from_mem(data):

        self = AnimationPLG()

        _data = unpack_from("<iI", data)
        self.id, num = _data

        return self

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

        _data = unpack_from("8I", data, 56)
        self.node_to_uv = list(_data)

        for pos in range(88, 88 + num_frames * 32, 32):
            self.frames.append(
                Sections.read(UVFrame, data, pos)
            )

        self.name = self.name[:strlen(self.name)].decode('ascii')
            
        return self

    #######################################################
    def to_mem(self):

        data = pack("<iiiif4x32s8I",
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

        if not oldver:
            self.calc_max_weights_per_vertex ()
            self.calc_used_bones ()
        else:
            self.max_weights_per_vertex = 0
            self.bones_used = []

        data = bytearray()
        data += pack("<3Bx", self.num_bones, len(self.bones_used),
                     self.max_weights_per_vertex)

        # Used Bones
        if self.bones_used:
            data += pack(f"<{len(self.bones_used)}B", *self.bones_used)

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
    def from_mem(data, geometry, frame=None):

        self = SkinPLG()

        # legacy Skin PLG
        if frame:
            _data = unpack_from("<2I", data)
            self.num_bones, vertices_count = _data
            self.max_weights_per_vertex = 4

            # Read vertex bone indices
            pos = 8
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

            bone_data = HAnimPLG()
            bone_data.header = HAnimHeader(None, 0, self.num_bones)

            # Read bones
            for _ in range(self.num_bones):
                _data = unpack_from(Sections.formats[Bone], data, pos)
                bone = Bone(_data[0], _data[1], _data[2] & 3)
                bone_data.bones.append(bone)
                pos += 12

                _data = list(unpack_from("<16f", data, pos))
                _data[ 3] = 0.0
                _data[ 7] = 0.0
                _data[11] = 0.0
                _data[15] = 1.0

                self.bone_matrices.append(
                    [_data[0:4], _data[4:8], _data[8:12],
                    _data[12:16]]
                )

                pos += 64

            frame.bone_data = bone_data

            return self

        if geometry.flags & rpGEOMETRYNATIVE == 0:
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
            for _ in range(self.num_bones):

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

        else:
            native_chunk = unpack_from("<3I", data)
            platform = unpack_from("<I", data, 12)[0]

            if platform == NativePlatformType.OGL:
                # Use the already created SkinPLG from NativeDataPLG
                self = geometry.extensions.get("skin", self)

                from .native_wdgl import NativeOGLSkin
                NativeOGLSkin.unpack(self, data[16:])
            elif platform == NativePlatformType.PS2:
                from .native_ps2 import NativePS2Skin
                NativePS2Skin.unpack(self, data[16:], geometry)
            elif platform == NativePlatformType.XBOX:
                from .native_xbox import NativeXboxSkin
                NativeXboxSkin.unpack(self, data[16:], geometry)
            elif platform == NativePlatformType.GC:
                from .native_gc import NativeGSSkin
                NativeGSSkin.unpack(self, data[16:], geometry)
            elif platform == NativePlatformType.PSP:
                from .native_psp import NativePSPSkin
                NativePSPSkin.unpack(self, data[16:], geometry)
            else:
                print("Unsupported native platform %d" % (platform))

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
        UPDATE_HEIGHT_ABOVE_GROUND = 4
        CHECK_DIRECTION = 8
        BLINKING3 = 16
        
    #######################################################
    def __init__(self, loc):

        self.effect_id = 0

        self.loc = loc
        self.color = [0,0,0,0]
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
            self.lookDirection = unpack_from("<bbb", data, offset + 75)

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
            self.coronaFarClip          , self.pointlightRange,
            self.coronaSize             , self.shadowSize,
            self.coronaShowMode         , self.coronaEnableReflection,
            self.coronaFlareType        , self.shadowColorMultiplier,
            self._flags1                , self.coronaTexName.encode(),
            self.shadowTexName.encode() , self.shadowZDistance,
            self._flags2
        )

        # 80 bytes
        if self.lookDirection is not None:
            data += pack("<bbb2x", *self.lookDirection)

        # 76 bytes (padding)
        else:
            data += pack("<x")

        return data

    #######################################################
    def check_flag(self, flag):
        return (self._flags1 & flag.value) != 0

    #######################################################
    def check_flag2(self, flag):
        return (self._flags2 & flag.value) != 0

    #######################################################
    def set_flag(self, flag):
        self._flags1 |= flag

    #######################################################
    def set_flag2(self, flag):
        self._flags2 |= flag

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
        effect = unpack_from("<24s", data, offset)[0]

        self = Particle2dfx(loc)
        self.effect = effect[:strlen(effect)].decode('ascii')
        return self

    #######################################################
    def to_mem(self):
        return pack("<24s", self.effect.encode())

#######################################################
class PedAttractor2dfx:

    #######################################################
    # See: https://gtamods.com/wiki/2d_Effect_(RW_Section)
    #######################################################
    class Types(IntEnum):

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
        self.queue_direction = [0, 0, 0]
        self.use_direction = [0, 0, 0]
        self.forward_direction = [0, 0, 0]
        self.external_script = "none"
        self.ped_existing_probability = 0
        self.unk = 0

    #######################################################
    @staticmethod
    def from_mem(loc, data, offset, size):
        self = PedAttractor2dfx(loc)

        self.type = unpack_from("<I", data, offset)[0]
        self.queue_direction = Sections.read(Vector, data, offset + 4)
        self.use_direction = Sections.read(Vector, data, offset + 16)
        self.forward_direction = Sections.read(Vector, data, offset + 28)
        external_script = data[offset + 40:offset + 48]
        self.ped_existing_probability, self.unk = unpack_from("<II", data, offset + 48)

        self.external_script = external_script[:strlen(external_script)].decode('ascii')

        return self

    #######################################################
    def to_mem(self):
        data = pack("<I", self.type)
        data += Sections.write(Vector, self.queue_direction)
        data += Sections.write(Vector, self.use_direction)
        data += Sections.write(Vector, self.forward_direction)
        data += pack("<8sII", self.external_script.encode(), self.ped_existing_probability, self.unk)

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
        return bytearray()

#######################################################
class EnterExit2dfx:

    #######################################################
    class Flags1(Enum):
        UNKNOWN_INTERIOR = 1
        UNKNOWN_PAIRING = 2
        CREATE_LINKED_PAIRING = 4
        REWARD_INTERIOR = 8
        USED_REWARD_ENTRANCE = 16
        CARS_AND_AIRCRAFT = 32
        BIKES_AND_MOTORCYCLES = 64
        DISABLE_ON_FOOT = 128

    #######################################################
    class Flags2(Enum):
        ACCEPT_NPC_GROUP = 1
        FOOD_DATE_FLAG = 2
        UNKNOWN_BURGLARY = 4
        DISABLE_EXIT = 8
        BURGLARY_ACCESS = 16
        ENTERED_WITHOUT_EXIT = 32
        ENABLE_ACCESS = 64
        DELETE_ENEX = 128

    #######################################################
    def __init__(self, loc):
        self.loc = loc
        self.effect_id = 6
        self.enter_angle = 0
        self.approximation_radius_x = 0
        self.approximation_radius_y = 0
        self.exit_location = [0, 0, 0]
        self.exit_angle = 0
        self.interior = 0
        self._flags1 = 0
        self.sky_color = 0
        self.interior_name = ""
        self.time_on = 0
        self.time_off = 0
        self._flags2 = 0
        self.unk = 0

    #######################################################
    @staticmethod
    def from_mem(loc, data, offset, size):

        self = EnterExit2dfx(loc)

        self.enter_angle, self.approximation_radius_x, \
        self.approximation_radius_y = unpack_from("<fff", data, offset)

        self.exit_location = Sections.read(Vector, data, offset + 12)

        self.exit_angle, self.interior, \
        self._flags1, self.sky_color, \
        interior_name = unpack_from("<fHBB8s", data, offset + 24)

        self.time_on, self.time_off ,\
        self._flags2, self.unk = unpack_from("<4B", data, offset + 40)

        self.interior_name = interior_name[:strlen(interior_name)].decode('ascii')

        return self

    #######################################################
    def to_mem(self):
        data = pack(
            "<fff",
            self.enter_angle,
            self.approximation_radius_x,
            self.approximation_radius_y
        )
        data += Sections.write(Vector, self.exit_location)
        data += pack(
            "<fHBB8s4B",
            self.exit_angle,
            self.interior,
            self._flags1,
            self.sky_color,
            self.interior_name.encode(),
            self.time_on, self.time_off,
            self._flags2, self.unk
        )

        return data

#######################################################
class RoadSign2dfx:

    #######################################################
    def __init__(self, loc):
        self.loc = loc
        self.effect_id = 7
        self.size = [1, 1]
        self.rotation = [0, 0, 0]
        self.flags = 0
        self.text1 = ""
        self.text2 = ""
        self.text3 = ""
        self.text4 = ""

    #######################################################
    @staticmethod
    def from_mem(loc, data, offset, size):

        self = RoadSign2dfx(loc)
        self.size = unpack_from("<ff", data, offset)
        self.rotation = Sections.read(Vector, data, offset + 8)
        self.flags, \
        self.text1, self.text2, \
        self.text3, self.text4 = unpack_from("<H16s16s16s16s2x", data, offset + 20)

        self.text1 = self.text1.decode('ascii')
        self.text2 = self.text2.decode('ascii')
        self.text3 = self.text3.decode('ascii')
        self.text4 = self.text4.decode('ascii')

        return self

    #######################################################
    def to_mem(self):
        data = pack("<ff", *self.size)
        data += Sections.write(Vector, self.rotation)
        data += pack(
            "<H16s16s16s16s2x",
            self.flags,
            self.text1.encode(), self.text2.encode(),
            self.text3.encode(), self.text4.encode()
        )

        return data

#######################################################
class TriggerPoint2dfx:

    #######################################################
    def __init__(self, loc):
        self.loc = loc
        self.effect_id = 8
        self.point_id = 0

    #######################################################
    @staticmethod
    def from_mem(loc, data, offset, size):

        self = TriggerPoint2dfx(loc)
        self.point_id = unpack_from("<I", data, offset)[0]
        return self

    #######################################################
    def to_mem(self):
        return pack("<I", self.point_id)

#######################################################
class CoverPoint2dfx:

    #######################################################
    def __init__(self, loc):
        self.loc = loc
        self.effect_id = 9
        self.direction_x = 0
        self.direction_y = 0
        self.cover_type = 0

    #######################################################
    @staticmethod
    def from_mem(loc, data, offset, size):

        self = CoverPoint2dfx(loc)
        self.direction_x, self.direction_y, \
        self.cover_type = unpack_from("<ffI", data, offset)
        return self

    #######################################################
    def to_mem(self):
        data = pack(
            "<ffI",
            self.direction_x, self.direction_y,
            self.cover_type
        )
        return data

#######################################################
class Escalator2dfx:

    #######################################################
    def __init__(self, loc):
        self.loc = loc
        self.effect_id = 10
        self.bottom = [0, 0, 0]
        self.top = [0, 0, 0]
        self.end = [0, 0, 0]
        self.direction = 0

    #######################################################
    @staticmethod
    def from_mem(loc, data, offset, size):

        self = Escalator2dfx(loc)
        self.bottom = Sections.read(Vector, data, offset)
        self.top = Sections.read(Vector, data, offset + 12)
        self.end = Sections.read(Vector, data, offset + 24)
        self.direction = unpack_from("<I", data, offset + 36)[0]
        return self

    #######################################################
    def to_mem(self):
        data = Sections.write(Vector, self.bottom)
        data += Sections.write(Vector, self.top)
        data += Sections.write(Vector, self.end)
        data += pack("<I", self.direction)
        return data

#######################################################
class Extension2dfx:

    #######################################################
    def __init__(self):
        self.entries = []

    #######################################################
    def append_entry(self, entry):
        self.entries.append(entry)

    #######################################################
    def is_empty(self):
        return len(self.entries) == 0

    #######################################################
    @staticmethod
    def from_mem(data, offset):

        self = Extension2dfx()
        entries_count = unpack_from("<I", data, offset)[0]

        pos = 4 + offset
        for _ in range(entries_count):

            # Stores classes for each effect
            entries_funcs = {
                0: Light2dfx,
                1: Particle2dfx,
                3: PedAttractor2dfx,
                4: SunGlare2dfx,
                6: EnterExit2dfx,
                7: RoadSign2dfx,
                8: TriggerPoint2dfx,
                9: CoverPoint2dfx,
                10: Escalator2dfx,
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
        if self.is_empty():
            return bytearray()

        # Entries length
        data = pack("<I", len(self.entries))

        # Entries
        for entry in self.entries:
            data += Sections.write(Vector, entry.loc)

            entry_data = entry.to_mem()

            data += pack("<II", entry.effect_id, len(entry_data))
            data += entry_data

        return Sections.write_chunk(data, types['2d Effect'])

    #######################################################
    def __add__(self, other):
        self.entries += other.entries # concatinate entries
        return self

#######################################################
class ExtensionBreakable:

    #######################################################
    def __init__(self):
        self.magic = 0
        self.pos_rule = 1
        self.positions = []
        self.uvs = []
        self.prelits = []
        self.triangles = []
        self.texture_names = []
        self.texture_masks = []
        self.ambient_colors = []

    #######################################################
    @staticmethod
    def from_mem(data, offset):
        self = ExtensionBreakable()

        _Triangle = namedtuple("_Triangle", "a b c")

        self.magic = unpack_from("<I", data, offset)[0]
        pos = 4 + offset

        if self.magic == 0:
            return self

        self.pos_rule = unpack_from("<I", data, pos)[0]
        pos += 4

        verts_num, pos_off, uv_off, prelit_off = unpack_from("<H2xIII", data, pos)
        pos += 16

        tris_num, vert_idx_off, mat_idx_off = unpack_from("<H2xII", data, pos)
        pos += 12

        mats_num, tex_off, tex_name_off, tex_mask_off, ambient_off = unpack_from("<H2xIIII", data, pos)
        pos += 20

        for _ in range(verts_num):
            self.positions.append(Sections.read(Vector, data, pos))
            pos += 12

        for _ in range(verts_num):
            self.uvs.append(Sections.read(TexCoords, data, pos))
            pos += 8

        for _ in range(verts_num):
            self.prelits.append(Sections.read(RGBA, data, pos))
            pos += 4

        _triangles = []
        for _ in range(tris_num):
            _tri = _Triangle._make(
                unpack_from("<3H", data, pos)
            )
            _triangles.append(_tri)
            pos += 6

        for _tri in _triangles:
            mat = unpack_from("<H", data, pos)[0]
            tri = Triangle._make(
                (
                    _tri.b,
                    _tri.a,
                    mat,
                    _tri.c
                )
            )
            self.triangles.append(tri)
            pos += 2

        for _ in range(mats_num):
            tex_name = data[pos:pos+strlen(data, pos)].decode("utf-8")
            self.texture_names.append(tex_name)
            pos += 32

        for _ in range(mats_num):
            tex_mask = data[pos:pos+strlen(data, pos)].decode("utf-8")
            self.texture_masks.append(tex_mask)
            pos += 32

        for _ in range(mats_num):
            self.ambient_colors.append(Sections.read(Vector, data, pos))
            pos += 12

        return self

    #######################################################
    def to_mem(self):

        data = bytearray()
        data += pack("<I", self.magic)

        if self.magic != 0:
            data += pack("<I", self.pos_rule)

            verts_num = len(self.positions)
            tris_num = len(self.triangles)
            mats_num = len(self.texture_names)

            data += pack("<H2x12x", verts_num)
            data += pack("<H2x8x", tris_num)
            data += pack("<H2x16x", mats_num)

            for p in self.positions:
                data += Sections.write(Vector, p)

            for uv in self.uvs:
                data += Sections.write(TexCoords, uv)

            for p in self.prelits:
                data += Sections.write(RGBA, p)

            for tri in self.triangles:
                data += pack("<3H", tri.a, tri.b, tri.c)

            for tri in self.triangles:
                data += pack("<H", tri.material)

            for tn in self.texture_names:
                data += pack("<32s", tn.encode("utf-8"))

            for tm in self.texture_masks:
                data += pack("<32s", tm.encode("utf-8"))

            for ac in self.ambient_colors:
                data += Sections.write(Vector, ac)

        return Sections.write_chunk(data, types["Breakable Model"])

#######################################################
class ExtensionColl:

    #######################################################
    def __init__(self, ext_type, data):
        self.ext_type = ext_type
        self.data = data

#######################################################
class DeltaMorph:

    #######################################################
    def __init__(self):

        self.name = ''
        self.lock_flags = 0
        self.indices = []
        self.positions = []
        self.normals = []
        self.prelits = []
        self.uvs = []
        self.bounding_sphere = None
        self.size = 0

    #######################################################
    def _decode_indices_rle(self, data):
        n = 0
        for p, b in enumerate(data):
            d = b & 0x7f
            if b & 0x80:
                self.indices += [n+i for i in range(d)]
            n += d

    #######################################################
    def _encode_indices_rle(self):
        def pack_filled():
            nonlocal n, data
            while n > 0x7f:
                data += pack("<B", 0xff)
                n -= 0x7f
            if n > 0:
                data += pack("<B", n | 0x80)

        def pack_skipped():
            nonlocal s, data
            while s > 0x7f:
                data += pack("<B", 0x7f)
                s -= 0x7f
            if s > 0:
                data += pack("<B", s)

        data = bytearray()
        n, li = 0, -1
        for i in self.indices:
            if i != li + 1:
                s = i - (li + 1)
                pack_filled()
                pack_skipped()
                n = 0
            li = i
            n += 1

        pack_filled()
        return data

    #######################################################
    def from_mem(data):
        self = DeltaMorph()

        str_len = unpack_from("<I", data)[0]
        self.name = unpack_from("<%ds" % (str_len), data, 4)[0].decode('ascii')
        pos = 4 + str_len

        flags, lock_flags, rle_size, verts_num = unpack_from("<IIII", data, pos)
        pos += 16

        self._decode_indices_rle(data[pos:pos+rle_size])
        pos += rle_size

        if flags & rpGEOMETRYPOSITIONS:
            self.positions = [Sections.read(Vector, data, pos + i * 12) for i in range(verts_num)]
            pos += verts_num * 12

        if flags & rpGEOMETRYNORMALS:
            self.normals = [Sections.read(Vector, data, pos + i * 12) for i in range(verts_num)]
            pos += verts_num * 12

        if flags & rpGEOMETRYPRELIT:
            self.prelits = [unpack_from("<I", data, pos + i * 4) for i in range(verts_num)]
            pos += verts_num * 4

        if flags & rpGEOMETRYTEXTURED:
            self.uvs = [Sections.read(TexCoords, data, pos + i * 8) for i in range(verts_num)]
            pos += verts_num * 8

        self.bounding_sphere = Sections.read(Sphere, data, pos)
        pos += 16

        self.size = pos
        return self

    #######################################################
    def to_mem(self):

        str_len = len(self.name) + 1
        data = pack("<I", str_len)
        data += pack("%ds" % str_len, self.name.encode('ascii'))

        flags = 0
        if self.positions:
            flags |= rpGEOMETRYPOSITIONS
        if self.normals:
            flags |= rpGEOMETRYNORMALS
        if self.prelits:
            flags |= rpGEOMETRYPRELIT
        if self.uvs:
            flags |= rpGEOMETRYTEXTURED

        verts_num = len(self.indices)
        indices_rle = self._encode_indices_rle()

        # TODO: testing
        lock_flags = flags # self.lock_flags

        data += pack("<IIII", flags, lock_flags, len(indices_rle), verts_num)
        data += indices_rle

        for p in self.positions:
            data += Sections.write(Vector, p)

        for n in self.normals:
            data += Sections.write(Vector, n)

        for p in self.prelits:
            data += pack("<I", p)

        for uv in self.uvs:
            data += Sections.write(TexCoords, uv)

        data += Sections.write(Sphere, self.bounding_sphere)
        return data

#######################################################
class DeltaMorphPLG:

    __slots__ = [
        'entries'
    ]

   #######################################################
    def __init__(self):
        self.entries = []

    #######################################################
    def append_entry(self, entry):
        self.entries.append(entry)

    #######################################################
    def from_mem(data):

        self = DeltaMorphPLG()
        entries_count = unpack_from("<I", data)[0]

        pos = 4
        for i in range(entries_count):
            dm = DeltaMorph.from_mem(data[pos:])
            self.append_entry(dm)
            pos += dm.size

        return self

    #######################################################
    def to_mem(self):

        if not self.entries:
            return bytearray()

        data = pack("<I", len(self.entries))
        for entry in self.entries:
            data += entry.to_mem()

        return Sections.write_chunk(data, types['Delta Morph PLG'])

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
        'split_headers',
        'extensions',
        'export_flags',
        'native_platform_type',
        '_num_triangles',
        '_num_vertices',
        '_vertex_bone_weights',
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
        self.split_headers      = []
        self.extensions         = {}

        # user for native plg
        self.native_platform_type = 0
        self._num_triangles = 0
        self._num_vertices = 0
        self._vertex_bone_weights = []

        # used for export
        self.export_flags = {
            "light"              : True,
            "modulate_color"     : True,
            "export_normals"     : True,
            "write_mesh_plg"     : True,
            "triangle_strip"     : False,
            "exclude_geo_faces"  : False,
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
        self._num_triangles = unpack_from("<I", data,4)[0]
        self._num_vertices  = unpack_from("<I", data,8)[0]
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
                
                for i in range(self._num_vertices):
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
                    
                    for j in range(self._num_vertices):
                        
                        tex_coord = Sections.read(TexCoords, data, pos)
                        self.uv_layers[i].append(tex_coord)
                        pos += 8

            # Read Triangles
            for i in range(self._num_triangles):
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
            for i in range(self._num_vertices):
                vertice = Sections.read(Vector, data, pos)
                self.vertices.append(vertice)
                pos += 12
            
        # read normals
        if self.has_normals:
            for i in range(self._num_vertices):
                normal = Sections.read(Vector, data, pos)
                self.normals.append(normal)
                pos += 12

        return self

    #######################################################
    def material_list_to_mem(self):
        # TODO: Support instance materials

        data = bytearray()
        
        data += pack("<I", len(self.materials))
        for i in range(len(self.materials)):
            data += pack("<i", -1)

        data = Sections.write_chunk(data, types["Struct"])

        for material in self.materials:
            data += material.to_mem()
            self._hasMatFX = material._hasMatFX if not self._hasMatFX else True

        return Sections.write_chunk(data, types["Material List"])

    #######################################################
    def write_bin_split(self):

        data = bytearray()

        meshes = defaultdict(list)
        is_tri_strip = self.export_flags["triangle_strip"]

        if is_tri_strip:
            for triangle in self.triangles:
                meshes[triangle.material].append([triangle.a, triangle.b, triangle.c])

            for mesh in meshes:
                meshes[mesh] = tristrip.stripify(meshes[mesh], True)[0]

        else:
            for triangle in self.triangles:
                meshes[triangle.material].extend([triangle.a, triangle.b, triangle.c])

        total_indices = sum(len(triangles) for triangles in meshes.values())
        data += pack("<III", int(is_tri_strip), len(meshes), total_indices)

        for mesh in meshes:
            data += pack("<II", len(meshes[mesh]), mesh)
            data += pack("<%dI" % (len(meshes[mesh])), *meshes[mesh])

        return Sections.write_chunk(data, types["Bin Mesh PLG"])
    
    #######################################################
    def extensions_to_mem(self, extra_extensions = []):

        data = bytearray()

        # Write Bin Mesh PLG
        if self.export_flags['write_mesh_plg'] or self.export_flags['exclude_geo_faces']:
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
        if self.export_flags["triangle_strip"]:
            flags |= rpGEOMETRYTRISTRIP
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

        data = bytearray()
        data += pack("<IIII",
                     flags,
                     len(self.triangles) if not self.export_flags["exclude_geo_faces"] else 0,
                     len(self.vertices),
                     1)

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
        if not self.export_flags["exclude_geo_faces"]:
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
                animation_data = None

                if chunk.type == types["Frame"]:
                    name = self.raw(strlen(self.data,self.pos)).decode("utf-8")
                    
                elif chunk.type == types["HAnim PLG"]:
                    bone_data = HAnimPLG.from_mem(self.raw(chunk.size))

                elif chunk.type == types["User Data PLG"]:
                    user_data = UserData.from_mem(self.raw(chunk.size))

                elif chunk.type == types["Animation PLG"]:
                    animation_data = AnimationPLG.from_mem(self.data[self.pos:])

                self._read(chunk.size)
                if name is not None:
                    self.frame_list[i].name = name
                if bone_data is not None:
                    self.frame_list[i].bone_data = bone_data
                if user_data is not None:
                    self.frame_list[i].user_data = user_data
                    for section in user_data.sections:
                        if section.name == "name\0":
                            self.frame_list[i].name = section.data[0]
                            break
                if animation_data is not None:
                    self.frame_list[i].animation_data = animation_data

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

        # Native geometry usually doesn't store triangles in this section
        has_indices = parent_chunk.size > 12 + header.mesh_count * 8

        geometry.split_headers = []

        is_tri_strip = header.flags == 1
        for i in range(header.mesh_count):
            
            # Read header
            split_header = _SplitHeader._make(unpack_from("<II",
                                                          self.data,
                                                          self._read(8)))

            geometry.split_headers.append(split_header)

            if geometry.flags & rpGEOMETRYNATIVE != 0:
                # War Drum OpenGL stores indices here instead of other native geometry
                if not has_indices:
                    continue

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
    def read_native_data_plg(self, parent_chunk, geometry):
        native_chunk = self.read_chunk() # wrong size

        if native_chunk.type == types["Struct"]:
            chunk_size = parent_chunk.size - 16

            platform = unpack_from("<I", self.data, self._read(4))[0]

            if platform == NativePlatformType.PS2:
                from .native_ps2 import NativePS2Geometry
                NativePS2Geometry.unpack(geometry, self.raw(chunk_size))
            elif platform == NativePlatformType.XBOX:
                from .native_xbox import NativeXboxGeometry
                NativeXboxGeometry.unpack(geometry, self.raw(chunk_size))
            elif platform == NativePlatformType.GC:
                from .native_gc import NativeGCGeometry
                NativeGCGeometry.unpack(geometry, self.raw(chunk_size))
            elif platform == NativePlatformType.PSP:
                from .native_psp import NativePSPGeometry
                NativePSPGeometry.unpack(geometry, self.raw(chunk_size))
            else:
                print("Unsupported native platform %d" % (platform))

            geometry.native_platform_type = platform

        else:
            chunk_size = parent_chunk.size
            self.pos -= 12

            from .native_wdgl import NativeWDGLGeometry
            NativeWDGLGeometry.unpack(geometry, self.data[self.pos:])

        self._read(chunk_size)

    #######################################################
    def read_bone_plg(self, parent_chunk, geometry):
        chunk_end = self.pos + parent_chunk.size

        geom_bones = []
        while self.pos < chunk_end:
            bone = Sections.read(GeomBone, self.data, self._read(12))
            if bone.vertices_count > 0:
                geom_bones.append(bone)

        geometry.extensions['bones'] = geom_bones

    #######################################################
    def read_matfx_bumpmap(self):
        intensity  = 0.0
        bump_map   = None
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

        return BumpMapFX(intensity, height_map, bump_map)        

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
                                        
                                        # Number of animations is a bitmask
                                        mask = unpack_from("<I", self.data, self._read(4))[0]
                                        anim_count = bin(mask & 0xFF).count('1')

                                        # Read n animations
                                        for i in range(anim_count):
                                            material.add_plugin('uv_anim',
                                                                self.raw(
                                                                    strlen(
                                                                        self.data,
                                                                        self.pos
                                                                    ),
                                                                    self._read(32)
                                                                ).decode('ascii')
                                            )

                                    if chunk.type == types["NTL Material Extension"]:
                                        # TODO: Have no idea how to read this extension, so fill it with zeros
                                        self.data = self.data[:self.pos] + (b'\0' * chunk.size) + self.data[self.pos:]

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
            for _ in range(geometries):
                chunk = self.read_chunk()

                # GEOMETRY
                if chunk.type == types["Geometry"]:
                    self.read_geometry(chunk)

    #######################################################
    def read_geometry(self, parent_chunk):

        chunk_end = self.pos + parent_chunk.size

        chunk = self.read_chunk()
        geometry = Geometry.from_mem(self.data[self.pos:], parent_chunk)

        self._read(chunk.size)

        self.geometry_list.append(geometry)

        while self.pos < chunk_end:

            chunk = self.read_chunk()

            if chunk.type == types["Material List"]:
                self.read_material_list(chunk)

            elif chunk.type == types["Extension"]:
                pass

            elif chunk.type == types["Delta Morph PLG"]:
                delta_morph = DeltaMorphPLG.from_mem(self.data[self.pos:])
                geometry.extensions["delta_morph"] = delta_morph

                self._read(chunk.size)

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

                self._read(chunk.size)

            elif chunk.type == types["Breakable Model"]:
                geometry.extensions["breakable_model"] = ExtensionBreakable.from_mem(
                    self.data,
                    self._read(chunk.size)
                )

            # 2dfx (usually at the last geometry index)
            elif chunk.type == types["2d Effect"]:
                self.ext_2dfx += Extension2dfx.from_mem(
                    self.data,
                    self._read(chunk.size)
                )

            elif chunk.type == types["Bin Mesh PLG"]:
                self.read_mesh_plg(chunk,geometry)

            elif chunk.type == types["Native Data PLG"]:
                self.read_native_data_plg(chunk,geometry)

            elif chunk.type == types["Bone PLG"]:
                self.read_bone_plg(chunk,geometry)

            else:
                self._read(chunk.size)

        self.pos = chunk_end

    #######################################################
    def read_atomic(self, parent_chunk):

        chunk_end = self.pos + parent_chunk.size

        atomic = None

        while self.pos < chunk_end:
            chunk = self.read_chunk()

            # STRUCT
            if chunk.type == types["Struct"]:
                atomic = Atomic.from_mem(
                    self.data[self.pos:self.pos+chunk.size]
                )
                self.pos += chunk.size

            elif chunk.type == types["Geometry"]:
                self.read_geometry(chunk)
                atomic.geometry = len(self.geometry_list) - 1

            elif chunk.type == types["Extension"]:
                _chunk_end = chunk.size + self.pos

                while self.pos < _chunk_end:
                    chunk = self.read_chunk()

                    if chunk.type == types["Right to Render"]:
                        right_to_render = Sections.read(RightToRender, self.data, self._read(chunk.size))
                        atomic.extensions["right_to_render"] = right_to_render

                    elif chunk.type == types["Pipeline Set"]:
                        pipeline = unpack_from("<I", self.data, self._read(chunk.size))[0]
                        atomic.extensions["pipeline"] = pipeline

                    # legacy Skin PLG
                    elif chunk.type == types["Skin PLG"]:
                        frame = self.frame_list[atomic.frame]
                        geometry = self.geometry_list[atomic.geometry]

                        skin = SkinPLG.from_mem(self.data[self.pos:], geometry, frame)
                        geometry.extensions["skin"] = skin

                        bone_frames = self.frame_list[atomic.frame + 1:]
                        for bone in frame.bone_data.bones[1:]:
                            for frame in bone_frames:
                                if frame.animation_data and frame.animation_data.id == bone.id:
                                    frame.bone_data = HAnimPLG()
                                    frame.bone_data.header = HAnimHeader(None, bone.id, 0)

                        self._read(chunk.size)

                    elif chunk.type == types["SkyGFX"]:
                        if chunk.size > 0:
                            sky_gfx = unpack_from("<B", self.data, self._read(chunk.size))[0]
                            atomic.extensions["sky_gfx"] = sky_gfx

                    else:
                        self._read(chunk.size)

                self.pos = _chunk_end

            else:
                self.pos += chunk.size

        if atomic:
            self.atomic_list.append(atomic)

    #######################################################
    def read_clump(self, root_chunk):
        chunk = self.read_chunk()

        data_len = len(self.data)

        if root_chunk.size > 0:
            root_end = self.pos + root_chunk.size

            # Check the actual clump size
            if root_end > data_len:
                root_end = data_len
        else:
            root_end = data_len

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

                elif chunk.type in (types["Collision Model"], types["SAMP Collision Model"]):
                    self.collisions.append(
                        ExtensionColl(chunk.type, self.data[self.pos:self.pos + chunk.size])
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

            elif chunk.type == types["Atomic"]:
                self.read_atomic(chunk)
                self.rw_version = Sections.get_rw_version(chunk.version)

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

        data = bytearray()

        data += pack("<I", len(self.frame_list)) # length

        for frame in self.frame_list:
            data += frame.header_to_mem()

        data = Sections.write_chunk(data, types["Struct"])
        
        for frame in self.frame_list:
            data += frame.extensions_to_mem()

        return Sections.write_chunk(data, types["Frame List"])

    #######################################################
    def write_geometry_list(self):
        data = bytearray()
        data += pack("<I", len(self.geometry_list))

        data = Sections.write_chunk(data, types["Struct"])
        
        for index, geometry in enumerate(self.geometry_list):

            # Append 2dfx to extra extensions in the last geometry
            extra_extensions = []
            if index == len(self.geometry_list) - 1 and not self.ext_2dfx.is_empty():
                extra_extensions.append(self.ext_2dfx)
            
            data += geometry.to_mem(extra_extensions)
        
        return Sections.write_chunk(data, types["Geometry List"])

    #######################################################
    def write_atomic(self, atomic):

        data = atomic.to_mem()
        data = Sections.write_chunk(data, types["Struct"])
        geometry = self.geometry_list[atomic.geometry]

        ext_data = bytearray()
        if "skin" in geometry.extensions:
            right_to_render = atomic.extensions.get("right_to_render")
            if not right_to_render:
                right_to_render = RightToRender._make((0x0116, 1))
            ext_data += Sections.write_chunk(
                pack("<II", right_to_render.value1, right_to_render.value2),
                types["Right to Render"]
            )

        if geometry._hasMatFX:
            ext_data += Sections.write_chunk(
                pack("<I", 1),
                types["Material Effects PLG"]
            )

        pipeline = atomic.extensions.get("pipeline")
        if pipeline is not None:
            ext_data += Sections.write_chunk(
                pack("<I", pipeline),
                types["Pipeline Set"]
            )

        sky_gfx = atomic.extensions.get("sky_gfx")
        if sky_gfx is not None:
            ext_data += Sections.write_chunk(
                pack("<B", sky_gfx),
                types["SkyGFX"]
            )

        data += Sections.write_chunk(ext_data, types["Extension"])
        return Sections.write_chunk(data, types["Atomic"])

    #######################################################
    def write_uv_dict(self):

        if len(self.uvanim_dict) < 1:
            return bytearray()
        
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
            data = Sections.write_chunk(pack("<I",
                                             len(self.atomic_list)),
                                        types["Struct"])
            
        data += self.write_frame_list()
        data += self.write_geometry_list()

        for atomic in self.atomic_list:
            data += self.write_atomic(atomic)

        for coll in self.collisions:
            _data = Sections.write_chunk(coll.data, coll.ext_type)
            data += Sections.write_chunk(_data, types["Extension"])
            
        data += Sections.write_chunk(bytearray(), types["Extension"])
            
        return Sections.write_chunk(data, types["Clump"])
    
    #######################################################
    def write_memory(self, version):

        data = bytearray()
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

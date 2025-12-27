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

from struct import unpack_from

from .dff import SkinPLG, RGBA, TexCoords, Vector, ExtraVertColorExtension

ATTRIB_ID_COORD       = 0
ATTRIB_ID_TEX_COORD   = 1
ATTRIB_ID_NORMAL      = 2
ATTRIB_ID_PRELIT      = 3
ATTRIB_ID_BONE_WEIGHT = 4
ATTRIB_ID_BONE_INDEX  = 5
ATTRIB_ID_EXTRA_COLOR = 6

ATTRIB_TYPE_FLOAT  = 0
ATTRIB_TYPE_BYTE   = 1
ATTRIB_TYPE_UBYTE  = 2
ATTRIB_TYPE_SHORT  = 3
ATTRIB_TYPE_USHORT = 4

#######################################################
class NativeOGLSkin:

    #######################################################
    @staticmethod
    def unpack(skin, data):
        skin.num_bones = unpack_from("<I", data)[0]
        pos = 4

        # Read bone matrices
        skin.bone_matrices = []
        for _ in range(skin.num_bones):

            _data = list(unpack_from("<16f", data, pos))
            _data[ 3] = 0.0
            _data[ 7] = 0.0
            _data[11] = 0.0
            _data[15] = 1.0

            skin.bone_matrices.append(
                [_data[0:4], _data[4:8], _data[8:12],
                _data[12:16]]
            )

            pos += 64

#######################################################
class NativeWDGLGeometry:
    __slots__ = [
        "attrib_descs",
        "coords",
        "tex_coords",
        "normals",
        "prelits",
        "bone_weights",
        "bone_indices",
        "extra_colors",
        "data",
        "_pos"
    ]

    #######################################################
    def __init__(self):
        self.attrib_descs = []
        self.coords = []
        self.tex_coords = []
        self.normals = []
        self.prelits = []
        self.bone_weights = []
        self.bone_indices = []
        self.extra_colors = []
        self.data = b""
        self._pos = 0

    #######################################################
    @staticmethod
    def unpack(geometry, data):
        self = NativeWDGLGeometry()
        self.data = data

        attribs_num = unpack_from("<I", data, self._read(4))[0]
        for _ in range(attribs_num):
            ad = NativeWDGLAttribDesc.from_mem(self._read_raw(24))
            self.attrib_descs.append(ad)

        readers = (
            self._read_coord,
            self._read_tex_coord,
            self._read_normal,
            self._read_prelit,
            self._read_bone_weight,
            self._read_bone_index,
            self._read_extra_color,
        )

        attribs_pos = self._pos
        for ad in self.attrib_descs:
            self._pos = attribs_pos + ad.offset
            reader = readers[ad.id]

            for _ in range(geometry._num_vertices):
                reader(ad)
                self._pos += ad.stride

        if self.coords:
            geometry.vertices = self.coords

        if self.tex_coords:
            geometry.uv_layers = [self.tex_coords]

        if self.normals:
            geometry.normals = self.normals

        if self.prelits:
            geometry.prelit_colors = self.prelits

        if self.bone_weights:
            skin = geometry.extensions.get("skin", SkinPLG())
            skin.vertex_bone_weights = self.bone_weights
            geometry.extensions["skin"] = skin

        if self.bone_indices:
            skin = geometry.extensions.get("skin", SkinPLG())
            skin.vertex_bone_indices = self.bone_indices
            geometry.extensions["skin"] = skin

        if self.extra_colors:
            geometry.extensions['extra_vert_color'] = ExtraVertColorExtension(self.extra_colors)

    #######################################################
    @staticmethod
    def unpack_attrib(data, offset, attrib_desc):
        attrib_type = attrib_desc.type

        if attrib_type == ATTRIB_TYPE_FLOAT:
            attrib = unpack_from('<%df' % (attrib_desc.size), data, offset)

        elif attrib_type == ATTRIB_TYPE_BYTE:
            attrib = unpack_from('<%db' % (attrib_desc.size), data, offset)
            if attrib_desc.is_normalized:
                attrib = tuple(a / 127.0 for a in attrib)

        elif attrib_type == ATTRIB_TYPE_UBYTE:
            attrib = unpack_from('<%dB' % (attrib_desc.size), data, offset)
            if attrib_desc.is_normalized:
                attrib = tuple(a / 255.0 for a in attrib)

        elif attrib_type == ATTRIB_TYPE_SHORT:
            attrib = unpack_from('<%dh' % (attrib_desc.size), data, offset)
            if attrib_desc.is_normalized:
                attrib = tuple(a / 32767.0 for a in attrib)

        elif attrib_type == ATTRIB_TYPE_USHORT:
            attrib = unpack_from('<%dH' % (attrib_desc.size), data, offset)
            if attrib_desc.is_normalized:
                attrib = tuple(a / 65435.0 for a in attrib)

        else:
            raise Exception("Unknown WDGL vertex attribute type")

        return attrib

    #######################################################
    def _read_coord(self, attrib_desc):
        attrib = NativeWDGLGeometry.unpack_attrib(self.data, self._pos, attrib_desc)

        coord = Vector(*attrib)
        self.coords.append(coord)

    #######################################################
    def _read_tex_coord(self, attrib_desc):
        attrib = NativeWDGLGeometry.unpack_attrib(self.data, self._pos, attrib_desc)
        attrib = tuple(a / 512.0 for a in attrib)

        tex_coord = TexCoords(*attrib)
        self.tex_coords.append(tex_coord)

    #######################################################
    def _read_normal(self, attrib_desc):
        attrib = NativeWDGLGeometry.unpack_attrib(self.data, self._pos, attrib_desc)

        normal = Vector(*attrib)
        self.normals.append(normal)

    #######################################################
    def _read_prelit(self, attrib_desc):
        attrib = NativeWDGLGeometry.unpack_attrib(self.data, self._pos, attrib_desc)
        attrib = tuple(int(a * 255.0) for a in attrib)

        prelit_color = RGBA(*attrib)
        self.prelits.append(prelit_color)

    #######################################################
    def _read_bone_weight(self, attrib_desc):
        attrib = NativeWDGLGeometry.unpack_attrib(self.data, self._pos, attrib_desc)
        self.bone_weights.append(attrib)

    #######################################################
    def _read_bone_index(self, attrib_desc):
        attrib = NativeWDGLGeometry.unpack_attrib(self.data, self._pos, attrib_desc)
        self.bone_indices.append(attrib)

    #######################################################
    def _read_extra_color(self, attrib_desc):
        attrib = NativeWDGLGeometry.unpack_attrib(self.data, self._pos, attrib_desc)
        attrib = tuple(int(a * 255.0) for a in attrib)

        extra_color = RGBA(*attrib)
        self.extra_colors.append(extra_color)

    #######################################################
    def _read(self, size):
        current_pos = self._pos
        self._pos += size

        return current_pos

    #######################################################
    def _read_raw(self, size):
        offset = self._read(size)
        return self.data[offset:offset+size]

#######################################################
class NativeWDGLAttribDesc:
    __slots__ = [
        "id",
        "type",
        "is_normalized",
        "size",
        "stride",
        "offset"
    ]

    #######################################################
    def __init__(self):
        self.id = 0
        self.type = 0
        self.is_normalized = False
        self.size = 0
        self.stride = 0
        self.offset = 0

    #######################################################
    @staticmethod
    def from_mem(data):
        self = NativeWDGLAttribDesc()

        self.id, self.type, self.is_normalized, self.size, self.stride, self.offset = \
            unpack_from("<IiIiII", data)
        self.is_normalized = self.is_normalized != 0

        return self

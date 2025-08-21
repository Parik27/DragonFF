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

from struct import unpack_from, calcsize

from .dff import RGBA, Sections, TexCoords, Triangle, Vector
from .txd import ImageDecoder, TextureNative, PaletteType

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

ptTRIANGLELIST  = 5
ptTRIANGLESTRIP = 6

# compressed formats
D3DFMT_DXT1 = 0x0000000C
D3DFMT_DXT2 = 0x0000000D
D3DFMT_DXT3 = 0x0000000E
D3DFMT_DXT5 = 0x0000000F

#######################################################
class NativeXboxSkin:

    #######################################################
    @staticmethod
    def unpack(skin, data, geometry):
        skin.num_bones = unpack_from("<I", data)[0]
        pos = 4

        bone_buff1 = unpack_from("<%di" % 0x100, data, pos)
        pos += 0x400

        bone_buff2 = unpack_from("<%di" % 0x100, data, pos)
        pos += 0x400

        _num_used_bones, skin.max_weights_per_vertex, unk, _vertex_len = unpack_from("<4I", data, pos)
        pos += 16

        skin.vertex_bone_indices = []
        skin.vertex_bone_weights = []

        vertices_count = len(geometry.vertices)
        for _ in range(vertices_count):

            # Read vertex bone weights
            _data = unpack_from("<%dB" % (skin.max_weights_per_vertex), data, pos)
            _extra = [0] * (4 - skin.max_weights_per_vertex)
            skin.vertex_bone_weights.append([w / 255 for w in _data] + _extra)
            pos += skin.max_weights_per_vertex

            # Read vertex bone indices
            _data = unpack_from("<%dH" % (skin.max_weights_per_vertex), data, pos)
            _extra = [0] * (4 - skin.max_weights_per_vertex)
            skin.vertex_bone_indices.append([bone_buff1[i//3] for i in _data] + _extra)
            pos += skin.max_weights_per_vertex * 2

        unpack_format = "<16f"

        # Read bone matrices
        skin.bone_matrices = []
        for _ in range(skin.num_bones):

            _data = list(unpack_from(unpack_format, data, pos))
            _data[ 3] = 0.0
            _data[ 7] = 0.0
            _data[11] = 0.0
            _data[15] = 1.0

            skin.bone_matrices.append(
                [_data[0:4], _data[4:8], _data[8:12],
                _data[12:16]]
            )

            pos += calcsize(unpack_format)

#######################################################
class NativeXboxGeometry:
    __slots__ = [
        "_pos"
    ]

    #######################################################
    def __init__(self):
        self._pos = 0

    #######################################################
    @staticmethod
    def unpack(geometry, data):
        self = NativeXboxGeometry()

        geometry.normals = []
        geometry.prelit_colors = []
        geometry.uv_layers = []
        geometry.vertices = []

        if geometry.flags & rpGEOMETRYTEXTURED != 0:
            geometry.uv_layers.append([])

        if geometry.flags & rpGEOMETRYTEXTURED2 != 0:
            geometry.uv_layers.append([])

        vertices_pos = unpack_from("<I", data, self._read(4))[0]
        unk, splits_num = unpack_from("<HH", data, self._read(4))

        primitive_type, vertices_num, vertex_len = unpack_from("<III", data, self._read(12))
        self._pos += 16

        if primitive_type == ptTRIANGLESTRIP:
            geometry.flags |= rpGEOMETRYTRISTRIP
        else:
            geometry.flags &= ~rpGEOMETRYTRISTRIP

        split_headers = []
        for _ in range(splits_num):
            vertex_start, vertex_end, indices_num = unpack_from("<III", data, self._read(12))
            split_headers.append(NativeXboxSplitHeader(vertex_start, vertex_end, indices_num))
            self._pos += 12

        indices = []
        for s in split_headers:
            padding = (self._pos - 8) % 0x10
            if padding:
                self._pos += 0x10 - padding

            indices.append(unpack_from("<%dH" % s.indices_num, data, self._read(2 * s.indices_num)))

        self._pos = vertices_pos

        is_compressed_normal = vertex_len != 0x28
        for _ in range(vertices_num):
            vertex = Sections.read(Vector, data, self._read(12))
            geometry.vertices.append(vertex)

            if geometry.flags & rpGEOMETRYNORMALS != 0:
                compressed_normal = unpack_from("<I", data, self._read(4))[0]
                x = (compressed_normal & 0x000007FF)
                y = (compressed_normal & 0x003FF800) >> 11
                z = (compressed_normal & 0xFFC00000) >> 22
                if x & 0x400 != 0:
                    x -= 0x800
                if y & 0x400 != 0:
                    y -= 0x800
                if z & 0x200 != 0:
                    z -= 0x400
                normal = Vector(x / 0x3FF, y / 0x3FF, z / 0x1FF)
                geometry.normals.append(normal)

            if geometry.flags & rpGEOMETRYPRELIT != 0:
                b, g, r, a = unpack_from("<4B", data, self._read(4))
                prelit_color = RGBA(r, g, b ,a)
                geometry.prelit_colors.append(prelit_color)

            if geometry.flags & rpGEOMETRYTEXTURED != 0:
                tex_coord = Sections.read(TexCoords, data, self._read(8))
                geometry.uv_layers[0].append(tex_coord)

            if geometry.flags & rpGEOMETRYTEXTURED2 != 0:
                tex_coord = Sections.read(TexCoords, data, self._read(8))
                geometry.uv_layers[1].append(tex_coord)

            if not is_compressed_normal:
                normal = Sections.read(Vector, data, self._read(12))
                geometry.normals.append(normal)

        # Generate triangles
        for split_index, split_header in enumerate(geometry.split_headers):
            tri_vertices = indices[split_index]

            if geometry.flags & rpGEOMETRYTRISTRIP:
                for i in range(len(tri_vertices) - 2):
                    if i % 2 == 0:
                        idx1 = i + 1
                        idx2 = i + 0
                    else:
                        idx1 = i + 0
                        idx2 = i + 1
                    idx3 = i + 2

                    vertex1, vertex2, vertex3 = tri_vertices[idx1], tri_vertices[idx2], tri_vertices[idx3]
                    if vertex1 != vertex2 and vertex1 != vertex3 and vertex2 != vertex3:
                        geometry.triangles.append(Triangle(vertex1, vertex2, split_header.material, vertex3))

            else:
                for i in range(0, len(tri_vertices) - 2, 3):
                    idx1 = i + 1
                    idx2 = i + 0
                    idx3 = i + 2
                    vertex1, vertex2, vertex3 = tri_vertices[idx1], tri_vertices[idx2], tri_vertices[idx3]
                    geometry.triangles.append(Triangle(vertex1, vertex2, split_header.material, vertex3))

    #######################################################
    def _read(self, size):
        current_pos = self._pos
        self._pos += size

        return current_pos


#######################################################
class NativeXboxSplitHeader:
    __slots__ = [
        "vertex_start",
        "vertex_end",
        "indices_num"
    ]

    #######################################################
    def __init__(self, vertex_start, vertex_end, indices_num):
        self.vertex_start = vertex_start
        self.vertex_end = vertex_end
        self.indices_num = indices_num

#######################################################
class NativeXboxTexture(TextureNative):

    #######################################################
    def __init__(self):
        super().__init__()
        self.compression = 0

    #######################################################
    def to_rgba(self, level=0):
        width  = self.get_width(level)
        height = self.get_height(level)
        pixels = self.pixels[level]
        compression = self.compression

        if compression:
            if compression == D3DFMT_DXT1:
                return ImageDecoder.bc1(pixels, width, height, 0x00)
            elif compression == D3DFMT_DXT2:
                return ImageDecoder.bc2(pixels, width, height, True)
            elif compression == D3DFMT_DXT3:
                return ImageDecoder.bc2(pixels, width, height, False)
            elif compression == D3DFMT_DXT5:
                return ImageDecoder.bc3(pixels, width, height, False)

        return super().to_rgba(level)

    #######################################################
    @staticmethod
    def from_mem(data):
        self = NativeXboxTexture()
        self.pos = 0
        self.data = data

        (
            self.platform_id, self.filter_mode, self.uv_addressing
        ) = unpack_from("<IHH", self.data, self._read(8))

        self.name = self._read_raw(32)
        self.name = self.name.decode("utf-8").replace('\0', '')

        self.mask = self._read_raw(32)
        self.mask = self.mask.decode("utf-8").replace('\0', '')

        (
            self.raster_format_flags, has_alpha, unk, self.width, self.height,
            self.depth, self.num_levels, self.raster_type, self.compression, pixels_len,
        ) = unpack_from("<I4H4BI", data, self._read(20))

        palette_format = self.get_raster_palette_type()

        if palette_format == PaletteType.PALETTE_8:
            self.palette = self._read_raw(1024)
        elif palette_format == PaletteType.PALETTE_4:
            self.palette = self._read_raw(128)

        self.convert_palette()

        for i in range(self.num_levels):
            width, height = self.get_width(i), self.get_height(i)

            if self.compression == D3DFMT_DXT1:
                data_len = max(width * height // 2, 8)
            elif self.compression:
                data_len = max(width * height, 16)
            else:
                data_len = width * height * self.depth // 8

            pixels = self._read_raw(data_len)
            if not self.compression:
                pixels = NativeXboxTexture.unswizzle(pixels, width, height, self.depth // 8)

            self.pixels.append(pixels)

        return self

    #######################################################
    def convert_palette(self):
        palette = self.palette

        if palette:
            res = bytearray(len(palette))
            for b in range(0, len(palette), 4):
                res[b+0] = palette[b+2]
                res[b+1] = palette[b+1]
                res[b+2] = palette[b+0]
                res[b+3] = palette[b+3]
            self.palette = res

    #######################################################
    @staticmethod
    def unswizzle(data, width, height, bpp):
        maskU = 0
        maskV = 0
        i = 1
        j = 1

        while True:
            if i < width:
                maskU |= j
                j <<= 1

            if i < height:
                maskV |= j
                j <<= 1

            i <<= 1
            if i >= width and i >= height:
                break

        res = bytearray(width * height * bpp)

        v = 0
        for y in range(height):
            u = 0
            for x in range(width):
                src_pos = (u | v) * bpp
                dst_pos = (y * width + x) * bpp
                res[dst_pos:dst_pos+bpp] = data[src_pos:src_pos+bpp]
                u = (u - maskU) & maskU
            v = (v - maskV) & maskV

        return res

    #######################################################
    def _read(self, size):
        current_pos = self.pos
        self.pos += size

        return current_pos

    #######################################################
    def _read_raw(self, size):
        offset = self._read(size)
        return self.data[offset:offset+size]

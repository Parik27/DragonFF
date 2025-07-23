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

from .dff import RGBA, TexCoords, Triangle, Vector
from .txd import TextureNative, PaletteType

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

#######################################################
class NativePSPSkin:

    #######################################################
    @staticmethod
    def unpack(skin, data, geometry):

        skin.num_bones, _num_used_bones, skin.max_weights_per_vertex = unpack_from("<3Bx", data)

        unpack_format = "<16f"
        pos = 4

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

        pos += 20

        bone_limit, splits_num, bone_pal_num = unpack_from("<3I", data, pos)
        pos += 12

        skin.bones_used = []
        if not splits_num:
            return

        for _ in range(skin.num_bones):
            skin.bones_used.append(unpack_from("<B", data, pos)[0])
            pos += 1

        table1_offset = pos
        table2_offset = pos + splits_num * 2
        bone_idx_list = []

        for i in range(splits_num):
            ig = []

            pos = table1_offset + i * 2
            table2_idx, num_idx = unpack_from("<2B", data, pos)

            pos = table2_offset + table2_idx * 2
            for _ in range(num_idx):
                bone_idx, bones_num = unpack_from("<2B", data, pos)
                for bi in range(bones_num):
                    ig.append(bone_idx + bi)
                pos += 2

            bone_idx_list.append(ig)

        weights = geometry._vertex_bone_weights
        indices = []

        for split_index, split_header in enumerate(geometry.split_headers):
            for _ in range(split_header.indices_count):
                indices.append(bone_idx_list[split_index])

        skin.vertex_bone_indices = indices
        skin.vertex_bone_weights = weights

#######################################################
class NativePSPGeometry:
    __slots__ = [
        "_pos",
        "_indices_map"
    ]

    #######################################################
    def __init__(self):
        self._pos = 0
        self._indices_map = []

    #######################################################
    @staticmethod
    def unpack(geometry, data):
        self = NativePSPGeometry()

        geometry.normals = []
        geometry.prelit_colors = []
        geometry.triangles = []
        geometry.uv_layers = []
        geometry._vertex_bone_weights = []
        geometry.vertices = []

        if geometry.flags & (rpGEOMETRYTEXTURED | rpGEOMETRYTEXTURED2):
            tex_count = (geometry.flags & 0x00FF0000) >> 16
            if tex_count == 0:
                tex_count = 2 if (geometry.flags & rpGEOMETRYTEXTURED2) else \
                    1 if (geometry.flags & rpGEOMETRYTEXTURED) else 0
        else:
            tex_count = 1

        for _ in range(tex_count):
            geometry.uv_layers.append([])

        chunk_size, strip, splits_num = unpack_from("<IHH", data, self._read(8))

        self._pos += splits_num * 32 # skip
        self._pos += 16 # skip

        next_strip_offset = self._pos
        prev_indices_offset = 0

        # Read split data
        for _ in range(splits_num):

            # Read header
            self._pos = next_strip_offset

            self._pos += 16 # skip
            fmt, indices_map_len, indices_num, indices_offset, indices_map_offset = \
                unpack_from("<3I2i", data, self._read(20))
            self._pos += 12 # skip
            info_offset, stride, matrix_offset, unk2 = unpack_from("<i3I", data, self._read(16))
            index_format = (fmt >> 11) & 3

            next_strip_offset = self._pos

            # Read scale matrix
            self._pos = matrix_offset
            scale_matrix = unpack_from("<16f", data, self._read(64))

            # Read indices map
            if index_format == 2:
                self._pos = indices_map_offset
                indices = unpack_from("<%dH" % indices_map_len, data, self._read(indices_map_len * 2))
            elif index_format == 0:
                o = len(geometry.vertices)
                indices = list(o + i for i in range(indices_num))
            self._indices_map.append(indices)

            # Read split geometry
            if prev_indices_offset != indices_offset:
                self._pos = indices_offset
                self._read_split_geometry(geometry, data, indices_num, fmt, scale_matrix)

            prev_indices_offset = indices_offset

        self._generate_triangles(geometry)

        if geometry.vertices:
            geometry.has_vertices = 1

        if geometry.normals:
            geometry.has_normals = 1

        if geometry.prelit_colors:
            geometry.flags |= rpGEOMETRYPRELIT
        else:
            geometry.flags &= ~rpGEOMETRYPRELIT

        if geometry.uv_layers and not geometry.uv_layers[0]:
            geometry.uv_layers = []

    #######################################################
    def _read(self, size):
        current_pos = self._pos
        self._pos += size

        return current_pos

    #######################################################
    def _read_split_geometry(self, geometry, data, indices_num, fmt, scale_matrix):
        uv_format     = fmt & 3
        color_format  = (fmt >> 2) & 7
        normal_format = (fmt >> 5) & 3
        vertex_format = (fmt >> 7) & 3
        weight_format = (fmt >> 9) & 3
        weights_num   = ((fmt >> 14) & 7) + 1
        vertices_num  = ((fmt >> 18) & 7) + 1
        coord_type    = (fmt >> 23) & 1

        for _ in range(indices_num):
            if weight_format == 1:
                wn = (weights_num + 3) // 4 * 4
                weights = unpack_from("<%dB" % wn, data, self._read(wn))
                geometry._vertex_bone_weights.append(tuple(
                    1.0 if w == 128 else w / 127.0 for w in weights
                ))

            if uv_format == 1:
                tu, tv = unpack_from("<2b", data, self._read(2))
                geometry.uv_layers[0].append(TexCoords(tu / 127.0, tv / 127.0))
                for uv in geometry.uv_layers[1:]:
                    uv.append(TexCoords(0, 0))

            elif uv_format == 2:
                tu, tv = unpack_from("<2h", data, self._read(4))
                geometry.uv_layers[0].append(TexCoords(tu / 32767.0, tv / 32767.0))
                for uv in geometry.uv_layers[1:]:
                    uv.append(TexCoords(0, 0))

            elif uv_format == 3:
                tu, tv = unpack_from("<2f", data, self._read(8))
                geometry.uv_layers[0].append(TexCoords(tu, tv))
                for uv in geometry.uv_layers[1:]:
                    uv.append(TexCoords(0, 0))

            if color_format > 3:
                if color_format == 6:
                    color = unpack_from("<H", data, self._read(2))[0]
                    geometry.prelit_colors.append(RGBA(
                        (color << 4) & 0xF0,
                        (color & 0xF0),
                        (color >> 4) & 0xF0,
                        (color >> 8) & 0xF0
                        ))

                elif color_format == 7:
                    color = unpack_from("<I", data, self._read(4))[0]
                    geometry.prelit_colors.append(RGBA(
                        (color & 0xFF),
                        (color >> 8) & 0xFF,
                        (color >> 16) & 0xFF,
                        (color >> 24) & 0xFF
                        ))

            if normal_format == 1:
                nx, ny, nz = unpack_from("<3bx", data, self._read(4))
                nx /= 127.0
                ny /= 127.0
                nz /= 127.0
                geometry.normals.append(Vector(nx, ny, nz))

            elif normal_format == 2:
                nx, ny, nz = unpack_from("<3h", data, self._read(6))
                nx /= 32767.0
                ny /= 32767.0
                nz /= 32767.0
                geometry.normals.append(Vector(nx, ny, nz))

            elif normal_format == 3:
                nx, ny, nz = unpack_from("<3f", data, self._read(12))
                geometry.normals.append(Vector(nx, ny, nz))

            if vertex_format == 1:
                x, y, z = unpack_from("<3bx", data, self._read(4))
                vx = ( x / 127.0) * scale_matrix[0]
                vy = ( y / 127.0) * scale_matrix[5]
                vz = ( z / 127.0) * scale_matrix[10]
                geometry.vertices.append(Vector(vx, vy, vz))

            elif vertex_format == 2:
                x, y, z = unpack_from("<3h", data, self._read(6))
                vx = ( x / 32767.0) * scale_matrix[0]
                vy = ( y / 32767.0) * scale_matrix[5]
                vz = ( z / 32767.0) * scale_matrix[10]
                geometry.vertices.append(Vector(vx, vy, vz))

            elif vertex_format == 3:
                x, y, z = unpack_from("<3f", data, self._read(12))
                vx = x * scale_matrix[0]
                vy = y * scale_matrix[5]
                vz = z * scale_matrix[10]
                geometry.vertices.append(Vector(vx, vy, vz))

    #######################################################
    def _generate_triangles(self, geometry):
        for split, split_header in enumerate(geometry.split_headers):
            indices_map = self._indices_map[split]

            for i in range(split_header.indices_count - 2):
                idx1 = indices_map[i + 0]
                idx2 = indices_map[i + 1]
                idx3 = indices_map[i + 2]

                v1 = geometry.vertices[idx1]
                v2 = geometry.vertices[idx2]
                v3 = geometry.vertices[idx3]
                if v1 == v2 or v1 == v3 or v2 == v3:
                    continue

                if i % 2 == 0:
                    triangle = Triangle(
                        idx2,
                        idx1,
                        split_header.material,
                        idx3
                    )
                else:
                    triangle = Triangle(
                        idx1,
                        idx2,
                        split_header.material,
                        idx3
                    )

                geometry.triangles.append(triangle)

#######################################################
class NativePSPTexture(TextureNative):

    #######################################################
    def to_rgba(self, level=0):
        width  = self.get_width(level)
        height = self.get_height(level)
        pixels = self.pixels[level]
        palette = self.palette

        if palette and self.get_raster_palette_type() == PaletteType.PALETTE_4:
            return NativePSPTexture.decode_pal4(pixels, palette, width, height)

        return super().to_rgba(level)

    #######################################################
    @staticmethod
    def from_mem(data):
        self = NativePSPTexture()
        self.pos = 0
        self.data = data

        (
            self.raster_format_flags, self.width, self.height, self.depth,
            self.num_levels, texture_format, bit_flag, unk_flag
        ) = unpack_from("<I2H3BbI", self.data, self._read(16))

        self.pos += 76
        unk1, unk2 = unpack_from("<II", self.data, self._read(8))

        (
            self.platform_id, self.filter_mode, self.uv_addressing
        ) = unpack_from("<IHH", self.data, self._read(8))

        self.name = self._read_raw(64)
        self.name = self.name.decode("utf-8").replace('\0', '')

        palette_format = self.get_raster_palette_type()

        if palette_format == PaletteType.PALETTE_8:
            self.palette = self._read_raw(1024)
        elif palette_format == PaletteType.PALETTE_4:
            self.palette = self._read_raw(64)

        for i in range(self.num_levels):
            width, height = self.get_width(i), self.get_height(i)
            data_len = width * height * self.depth // 8

            pixels = self._read_raw(data_len)
            pixels = NativePSPTexture.unswizzle(pixels, width, height, self.depth)

            self.pixels.append(pixels)

        return self

    #######################################################
    @staticmethod
    def unswizzle(data, width, height, depth):
        width = (width * depth) >> 3
        res = bytearray(width * height)

        row_blocks = width // 16
        block_size = 16 * 8

        for y in range(height):
            block_y = y // 8
            y_in_block = y % 8

            for x in range(width):
                block_x = x // 16
                x_in_block = x % 16

                block_idx = block_x + (block_y * row_blocks)
                src_off = (block_idx * block_size) + x_in_block + y_in_block * 16
                dst_off = y * width + x

                res[dst_off] = data[src_off]

        return res

    #######################################################
    @staticmethod
    def decode_pal4(data, palette, width, height):
        pos = 0
        ret = bytearray(4 * width * height)

        for i in data:
            idx1, idx2 = i & 0xf, (i >> 4) & 0xf
            ret[pos+0:pos+4] = palette[idx1*4:idx1*4+4]
            ret[pos+4:pos+8] = palette[idx2*4:idx2*4+4]
            pos += 8

        return bytes(ret)

    #######################################################
    def _read(self, size):
        current_pos = self.pos
        self.pos += size

        return current_pos

    #######################################################
    def _read_raw(self, size):
        offset = self._read(size)
        return self.data[offset:offset+size]

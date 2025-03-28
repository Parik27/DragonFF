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

from struct import unpack_from, calcsize, pack

from .dff import Chunk, RGBA, Sections, TexCoords, Triangle, Vector
from .dff import ExtraVertColorExtension
from .txd import TextureNative, RasterFormat, PaletteType

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
class NativePS2Skin:

    #######################################################
    @staticmethod
    def unpack(skin, data, geometry):

        skin.num_bones, _num_used_bones, skin.max_weights_per_vertex = unpack_from("<3Bx", data)

        skin.bones_used = []
        for pos in range(4, _num_used_bones + 4):
            skin.bones_used.append(unpack_from("<B", data, pos)[0])

        unpack_format = "<16f"
        pos = _num_used_bones + 4

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

        weights = geometry._vertex_bone_weights
        indices = []

        if not geometry.normals and not geometry.uv_layers and not geometry.prelit_colors:
            index_div = 3
        else:
            index_div = 4

        for _, wg in enumerate(weights):
            ig = []
            for j in range(4):
                index = pack("<f", wg[j])[0]
                if index > 0:
                    index = index // index_div - 1
                    ig.append(index)
            indices.append(ig)

        skin.vertex_bone_indices = indices
        skin.vertex_bone_weights = weights

#######################################################
class NativePS2Geometry:
    __slots__ = [
        "_pos",
        "_indices",
        "_vertex_index"
    ]

    #######################################################
    def __init__(self):
        self._pos = 0
        self._indices = []
        self._vertex_index = 0

    #######################################################
    @staticmethod
    def unpack(geometry, data):
        self = NativePS2Geometry()

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

        read_types = []

        for split_index, split_header in enumerate(geometry.split_headers):
            split_size, no_pointers = unpack_from("<II", data, self._read(8))

            self._indices.append([])

            split_start = self._pos
            split_end = split_start + split_size

            section_a_last, section_b_last = False, False
            data_a_read = False

            while self._pos < split_end:

                # Section A
                reached_end = False
                while not reached_end and not section_a_last:
                    chunk8 = unpack_from("16B", data, self._pos)
                    chunk32 = unpack_from("<4I", data, self._read(16))

                    if chunk8[3] == 0x30:
                        # read all split data when we find the
                        # first data block and ignore all
                        # other blocks
                        if data_a_read:
                            # skip dummy data
                            self._pos += 16
                            continue

                        old_pos = self._pos
                        data_pos = split_start + chunk32[1] * 16
                        self._pos = data_pos
                        self._read_geometry(geometry, data, split_index, split_header.indices_count, chunk32[3])
                        self._pos = old_pos + 16
                    elif chunk8[3] == 0x60:
                        section_a_last = True
                        reached_end = True
                        data_a_read = True
                    elif chunk8[3] == 0x10:
                        reached_end = True
                        data_a_read = True

                # Section B
                reached_end = False
                while not reached_end and not section_b_last:
                    chunk8 = unpack_from("16B", data, self._pos)
                    chunk32 = unpack_from("<4I", data, self._read(16))

                    if chunk8[3] == 0x00 or chunk8[3] == 0x07:
                        self._read_geometry(geometry, data, split_index, chunk8[14], chunk32[3])
                        read_types.append(chunk32[3])
                    elif chunk8[3] == 0x04:
                        # if (chunk8[7] == 0x15)
                        #     # first
                        # else if (chunk8[7] == 0x17)
                        #     # not first

                        if (chunk8[11] == 0x11 and chunk8[15] == 0x11) or (chunk8[11] == 0x11 and chunk8[15] == 0x06):
                            #  last
                            self._pos = split_end
                            read_types = []
                            section_b_last = True
                        elif chunk8[11] == 0 and chunk8[15] == 0 and geometry.flags & rpGEOMETRYTRISTRIP != 0:
                            self._delete_split_overlapping(geometry, read_types, split_index)
                            read_types = []
                            # not last
                        reached_end = True

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
    def _read_geometry(self, geometry, data, split_index, indices_count, split_type):
        size = 0
        split_type &= 0xFF00FFFF

        # Read vertices
        if split_type == 0x68008000:
            size = 12

            for _ in range(indices_count):
                vertex = Sections.read(Vector, data, self._read(size))
                geometry.vertices.append(vertex)
                self._indices[split_index].append(self._vertex_index)
                self._vertex_index += 1

        elif split_type == 0x6D008000:
            size = 8

            vertex_scale = (1.0/128.0) if (geometry.flags & rpGEOMETRYPRELIT) > 0 else (1.0/1024.0)
            for _ in range(indices_count):
                x, y, z, flag = unpack_from("<4h", data, self._read(size))
                vertex = Vector(x * vertex_scale, y * vertex_scale, z * vertex_scale)
                geometry.vertices.append(vertex)

                if flag & 0xFFFF == 0x8000:
                    self._indices[split_index].append(self._vertex_index - 1)
                    self._indices[split_index].append(self._vertex_index - 1)

                self._indices[split_index].append(self._vertex_index)
                self._vertex_index += 1

        elif split_type == 0x6c008000:
            size = 16

            for _ in range(indices_count):
                x, y, z, flag = unpack_from("<3fI", data, self._read(size))
                vertex = Vector(x, y, z)
                geometry.vertices.append(vertex)

                if flag & 0xFFFF == 0x8000:
                    self._indices[split_index].append(self._vertex_index - 1)
                    self._indices[split_index].append(self._vertex_index - 1)

                self._indices[split_index].append(self._vertex_index)
                self._vertex_index += 1

        # Read texture mapping coordinates
        elif split_type == 0x64008001:
            size = 8

            for _ in range(indices_count):
                tex_coord = Sections.read(TexCoords, data, self._read(size))
                geometry.uv_layers[0].append(tex_coord)

            for uv in geometry.uv_layers[1:]:
                for _ in range(indices_count):
                    uv.append(TexCoords(0, 0))

        elif split_type == 0x6D008001:
            size = 4

            for _ in range(indices_count):
                for uv in geometry.uv_layers:
                    u, v = unpack_from("<2h", data, self._read(size))
                    tex_coord = TexCoords(u / 4096.0, v / 4096.0)
                    uv.append(tex_coord)

            size *= len(geometry.uv_layers)

        elif split_type == 0x65008001:
            size = 4

            for _ in range(indices_count):
                u, v = unpack_from("<2h", data, self._read(size))
                tex_coord = TexCoords(u / 4096.0, v / 4096.0)
                geometry.uv_layers[0].append(tex_coord)

            for uv in geometry.uv_layers[1:]:
                for _ in range(indices_count):
                    uv.append(TexCoords(0, 0))

        # Read normals
        elif split_type in (0x6E008002, 0x6E008003):
            size = 4

            for _ in range(indices_count):
                x, y, z = unpack_from("3b", data, self._read(3))
                normal = Vector(x / 128.0, y / 128.0, z / 128.0)
                geometry.normals.append(normal)
                self._pos += 1

        elif split_type in (0x6A008002, 0x6A008003):
            size = 3

            for _ in range(indices_count):
                x, y, z = unpack_from("3b", data, self._read(3))
                normal = Vector(x / 128.0, y / 128.0, z / 128.0)
                geometry.normals.append(normal)

        # Read prelighting colors
        elif split_type == 0x6E00C002:
            size = 4

            for _ in range(indices_count):
                prelit_color = Sections.read(RGBA, data, self._read(size))
                geometry.prelit_colors.append(prelit_color)

        elif split_type == 0x6D00C002:
            size = 8

            extension = geometry.extensions.get('extra_vert_color')
            if not extension:
                extension = ExtraVertColorExtension([])
                geometry.extensions['extra_vert_color'] = extension

            for _ in range(indices_count):
                colors = unpack_from("8B", data, self._read(size))
                prelit_color = RGBA(colors[0], colors[2], colors[4], colors[6])
                geometry.prelit_colors.append(prelit_color)
                extra_color = RGBA(colors[1], colors[3], colors[5], colors[7])
                extension.colors.append(extra_color)

        # Read vertex bone weights
        elif split_type in (0x6C008004, 0x6C008003, 0x6C008001):
            size = 16

            for _ in range(indices_count):
                weights = unpack_from("<4f", data, self._read(size))
                geometry._vertex_bone_weights.append(weights)

        else:
            print("Unknown Native PS2 data:", hex(split_type))

        padding = indices_count * size & 0xF
        if padding:
            self._pos += 16 - padding

    #######################################################
    def _delete_split_overlapping(self, geometry, read_types, split_index):
        for split_type in read_types:
            split_type &= 0xFF00FFFF
            if split_type in (0x68008000, 0x6D008000, 0x6c008000):
                geometry.vertices = geometry.vertices[:-2]
                self._indices[split_index] = self._indices[split_index][:-2]
                self._vertex_index -= 2
            elif split_type in (0x64008001, 0x65008001, 0x6D008001):
                for i in range(len(geometry.uv_layers)):
                    geometry.uv_layers[i] = geometry.uv_layers[i][:-2]
            elif split_type in (0x6E008002, 0x6E008003, 0x6A008002, 0x6A008003):
                geometry.normals = geometry.normals[:-2]
            elif split_type in (0x6E00C002,):
                geometry.prelit_colors = geometry.prelit_colors[:-2]
            elif split_type in (0x6D00C002,):
                geometry.prelit_colors = geometry.prelit_colors[:-2]
                extension = geometry.extensions['extra_vert_color']
                extension.colors = extension.colors[:-2]
            elif split_type in (0x6C008004, 0x6C008003, 0x6C008001):
                geometry._vertex_bone_weights = geometry._vertex_bone_weights[:-2]

    #######################################################
    def _generate_triangles(self, geometry):
        geometry.triangles = []

        for split_index, split_header in enumerate(geometry.split_headers):
            indices = self._indices[split_index]
            if geometry.flags & rpGEOMETRYTRISTRIP != 0:
                for i in range(len(indices) - 2):
                    v1 = geometry.vertices[indices[i+0]]
                    v2 = geometry.vertices[indices[i+1]]
                    v3 = geometry.vertices[indices[i+2]]
                    if v1 == v2 or v1 == v3 or v2 == v3:
                        continue

                    if i % 2 == 0:
                        triangle = Triangle(
                            indices[i+1],
                            indices[i+0],
                            split_header.material,
                            indices[i+2]
                        )
                    else:
                      triangle = Triangle(
                            indices[i+0],
                            indices[i+1],
                            split_header.material,
                            indices[i+2]
                        )

                    geometry.triangles.append(triangle)
            else:
                for i in range(0, len(indices) - 2, 3):
                    triangle = Triangle(
                            indices[i+1],
                            indices[i+0],
                            split_header.material,
                            indices[i+2]
                        )
                    geometry.triangles.append(triangle)

#######################################################
class NativePS2Texture(TextureNative):

    #######################################################
    @staticmethod
    def from_mem(data):
        self = NativePS2Texture()
        self.pos = 0
        self.data = data

        (
            self.platform_id, self.filter_mode, self.uv_addressing
        ) = unpack_from("<IHH", self.data, self._read(8))

        str_chunk = self._read_chunk()
        self.name = self._read_raw(str_chunk.size)
        self.name = self.name.decode("utf-8").replace('\0', '')

        str_chunk = self._read_chunk()
        self.mask = self._read_raw(str_chunk.size)
        self.mask = self.mask.decode("utf-8").replace('\0', '')

        native_chunk = self._read_chunk()
        raster_chunk = self._read_chunk()

        (
            self.width, self.height, self.depth, self.raster_format_flags,
            tex0_gs_reg, tex1_gs_reg, miptbp1_gs_reg, miptbp2_gs_reg,
            pixels_size, palette_size, gpu_data_aligned_size, sky_mipmap_val
        ) = unpack_from("<4I4Q4I", self.data, self._read(raster_chunk.size))

        texture_chunk = self._read_chunk()

        palette_format = self.get_raster_palette_type()
        raster_format = self.get_raster_format_type()

        if raster_format == RasterFormat.RASTER_8888:
            if palette_size > 0:
                pixels_size -= 80
                palette_size -= 80

                self._read(80) # skip pixels header
                pixels = self._read_raw(pixels_size)

                self._read(80) # skip palette header
                if palette_format == PaletteType.PALETTE_8:
                    self.palette = self._read_palette(1024)
                elif palette_format == PaletteType.PALETTE_4:
                    self.palette = self._read_palette(64)
                    self._read(palette_size - 64) # skip padding

                if self.depth == 8:
                    self.palette = NativePS2Texture.unswizzle_palette(self.palette)
                    pixels = NativePS2Texture.unswizzle8(pixels, self.width, self.height)
                elif self.depth == 4:
                    pixels = NativePS2Texture.unswizzle4(pixels, self.width, self.height)

                self.pixels.append(pixels)

            elif self.depth == 32:
                pixels = self._read_raw(pixels_size)
                self.pixels.append(pixels)

        return self

    #######################################################
    @staticmethod
    def unswizzle8(data, width, height):
        res = bytearray(width * height)
        for y in range(height):
            block_y = (y & ~0xf) * width
            posY = (((y & ~3) >> 1) + (y & 1)) & 0x7
            swap_selector = (((y + 2) >> 2) & 0x1) * 4
            base_column_location = posY * width * 2

            for x in range(width):
                block_x = (x & ~0xf) * 2
                column_location = base_column_location + ((x + swap_selector) & 0x7) * 4
                byte_num = ((y >> 1) & 1) + ((x >> 2) & 2)
                swizzleid = block_y + block_x + column_location + byte_num
                res[y * width + x] = data[swizzleid]

        return res

    #######################################################
    @staticmethod
    def unswizzle4(data, width, height):
        pixels = bytearray(width * height)
        for i in range(width * height // 2):
            index = data[i]
            pixels[i*2] = index & 0xf
            pixels[i*2+1] = (index >> 4) & 0xf

        pixels = NativePS2Texture.unswizzle8(pixels, width, height)

        res = bytearray(width * height // 2)
        for i in range(width * height // 2):
            idx1 = pixels[i*2]
            idx2 = pixels[i*2+1]
            res[i] = (idx2 << 4) | idx1

        return res

    #######################################################
    @staticmethod
    def unswizzle_palette(data):
        palette = bytearray(1024)
        for p in range(256):
            pos_l = ((p & 231) | ((p & 8) << 1) | ((p & 16) >> 1)) * 4
            pos_r = p * 4
            palette[pos_l:pos_l+4] = data[pos_r:pos_r+4]
        return bytes(palette)

    #######################################################
    def _read_palette(self, size):
        palette = bytearray(size)
        data = self._read_raw(size)
        for i in range(0, size, 4):
            r, g, b, a = data[i:i+4]
            palette[i:i+3] = r, g, b
            palette[i+3] = min(a * 2, 255)
        return bytes(palette)

    #######################################################
    def _read(self, size):
        current_pos = self.pos
        self.pos += size

        return current_pos

    #######################################################
    def _read_raw(self, size):
        offset = self._read(size)
        return self.data[offset:offset+size]

    #######################################################
    def _read_chunk(self):
        chunk = Sections.read(Chunk, self.data, self._read(12))
        return chunk

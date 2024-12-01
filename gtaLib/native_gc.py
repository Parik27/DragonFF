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
from collections import namedtuple

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

# section types
GC_SECTIONTYPE_VERTEX              = 0x09
GC_SECTIONTYPE_NORMAL              = 0x0a
GC_SECTIONTYPE_COLOR               = 0x0b
GC_SECTIONTYPE_TEXCOORD            = 0x0d
GC_SECTIONTYPE_TEXCOORD2           = 0x0e

# pixel format
GVRPIX_NO_PALETTE = -1
GVRPIX_LUM_ALPHA  = 0
GVRPIX_RGB565     = 1
GVRPIX_RGB5A3     = 2

# texture format
GVRFMT_LUM_4BIT       = 0
GVRFMT_LUM_8BIT       = 1
GVRFMT_LUM_4BIT_ALPHA = 2
GVRFMT_LUM_8BIT_ALPHA = 3
GVRFMT_RGB565         = 4
GVRFMT_RGB5A3         = 5
GVRFMT_RGBA8888       = 6
GVRFMT_PAL_4BIT       = 8
GVRFMT_PAL_8BIT       = 9
GVRFMT_CMP            = 14

# raster format
GCRASTER_DEFAULT = 0
GCRASTER_565     = 2
GCRASTER_RGB5A3  = 3
GCRASTER_8888    = 5
GCRASTER_888     = 6

#######################################################
class NativeGSSkin:

    #######################################################
    @staticmethod
    def unpack(skin, data, geometry):

        skin.num_bones, _num_used_bones, skin.max_weights_per_vertex = unpack_from("<3Bx", data)

        skin.bones_used = []
        for pos in range(4, _num_used_bones + 4):
            skin.bones_used.append(unpack_from("<B", data, pos)[0])

        pos = _num_used_bones + 4
        vertices_count = len(geometry.vertices)

        if _num_used_bones > 1:
            # Read vertex bone indices
            skin.vertex_bone_indices = []
            for _ in range(vertices_count):
                _data = unpack_from("<%dB" % (skin.max_weights_per_vertex), data, pos)
                _extra = [0] * (4 - skin.max_weights_per_vertex)
                skin.vertex_bone_indices.append(list(_data) + _extra)
                pos += skin.max_weights_per_vertex

            # Read vertex bone weights
            skin.vertex_bone_weights = []
            for _ in range(vertices_count):
                _data = unpack_from("<%dB" % (skin.max_weights_per_vertex), data, pos)
                _extra = [0] * (4 - skin.max_weights_per_vertex)
                skin.vertex_bone_weights.append([w / 128 for w in _data] + _extra)
                pos += skin.max_weights_per_vertex
        else:
            skin.vertex_bone_indices = list((skin.bones_used[0], 0, 0, 0) for _ in range(vertices_count))
            skin.vertex_bone_weights = list((1, 0, 0, 0) for _ in range(vertices_count))

        unpack_format = ">16f"

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
class NativeGCGeometry:
    __slots__ = [
        "section_headers",
        "triangle_section_headers",
        "normals",
        "prelit_colors",
        "tex_coords",
        "tex_coords2",
        "_pos",
        "_header_size",
        "_data_size"
    ]

    #######################################################
    def __init__(self):
        self.section_headers = []
        self.triangle_section_headers = []
        self.normals = []
        self.prelit_colors = []
        self.tex_coords = []
        self.tex_coords2 = []
        self._pos = 0
        self._header_size = 0
        self._data_size = 0

    #######################################################
    @staticmethod
    def unpack(geometry, data):
        self = NativeGCGeometry()

        self._header_size, self._data_size = unpack_from("<II", data, self._read(8))

        data_pos = self._pos + self._header_size

        # Read Header
        unk1, mesh_index, unk2, sections_num = unpack_from(">HHII", data, self._read(12))

        splits_num = len(geometry.split_headers)
        section_header_len = (data_pos - self._pos - splits_num * 8) // sections_num

        for _ in range(sections_num):
            section_offset, section_type, entry_size, byte_type, pad = unpack_from(">IBBBB", data, self._read(8))
            self.section_headers.append(NativeGCSectionHeader(section_offset, section_type, entry_size, byte_type))

            # TODO: Determine which RW version contain additional section header data
            self._pos += section_header_len - 8

        for _ in range(splits_num):
            section_offset, section_size = unpack_from(">II", data, self._read(8))
            self.triangle_section_headers.append(NativeGCTriangleSectionHeader(section_offset, section_size))

        # Read Data
        self._read_sections(geometry, data, data_pos)

        try:
            self._read_triangles(geometry, data, data_pos, False)
        except BaseException:
            self._read_triangles(geometry, data, data_pos, True)

    #######################################################
    def _read(self, size):
        current_pos = self._pos
        self._pos += size

        return current_pos

    #######################################################
    def _read_sections(self, geometry, data, data_pos):
        geometry.vertices = []

        last_section_index = len(self.section_headers) - 1

        for s, hdr in enumerate(self.section_headers):
            if s == last_section_index:
                next_section_offset = self._data_size
            else:
                next_section_offset = self.section_headers[s + 1].section_offset
            entries_num = (next_section_offset - hdr.section_offset) // hdr.entry_size

            self._pos = data_pos + hdr.section_offset
            if hdr.section_type == GC_SECTIONTYPE_VERTEX:
                for _ in range(geometry._num_vertices):
                    vertex = Vector._make(unpack_from(">3f", data, self._read(hdr.entry_size)))
                    geometry.vertices.append(vertex)
                    geometry.has_vertices = 1

            elif hdr.section_type == GC_SECTIONTYPE_NORMAL:
                for _ in range(entries_num):
                    normal = Vector._make(unpack_from(">3f", data, self._read(hdr.entry_size)))
                    self.normals.append(normal)
                    geometry.has_normals = 1

            elif hdr.section_type == GC_SECTIONTYPE_COLOR:
                for _ in range(entries_num):
                    prelit_color = Sections.read(RGBA, data, self._read(hdr.entry_size))
                    self.prelit_colors.append(prelit_color)

            elif hdr.section_type == GC_SECTIONTYPE_TEXCOORD:
                for _ in range(entries_num):
                    tex_coords = TexCoords._make(unpack_from(">2f", data, self._read(hdr.entry_size)))
                    self.tex_coords.append(tex_coords)

            elif hdr.section_type == GC_SECTIONTYPE_TEXCOORD2:
                for _ in range(entries_num):
                    tex_coords2 = TexCoords._make(unpack_from(">2f", data, self._read(hdr.entry_size)))
                    self.tex_coords2.append(tex_coords2)

            else:
                raise Exception("Unknown GC section")

    #######################################################
    def _read_triangles(self, geometry, data, data_pos, skip_byte):
        geometry.normals = []
        geometry.prelit_colors = []
        geometry.triangles = []
        geometry.uv_layers = []

        if self.tex_coords:
            geometry.uv_layers.append([])

        if self.tex_coords2:
            geometry.uv_layers.append([])

        for split_index, hdr in enumerate(self.triangle_section_headers):
            split_header = geometry.split_headers[split_index]

            self._pos = data_pos + hdr.section_offset
            end_pos = self._pos + hdr.section_size

            while self._pos < end_pos:
                b1 = unpack_from(">B", data, self._read(1))[0]
                if b1 == 0:
                    continue

                if b1 != 0x98:
                    raise Exception("Unexpected value")

                unk, entries_num = unpack_from(">BB", data, self._read(2))

                tri_vertices = []
                tri_normals = []
                tri_prelit_colors = []
                tri_tex_coords = []
                tri_tex_coords2 = []

                for _ in range(entries_num):
                    if skip_byte:
                        self._pos += 1

                    for sec_hdr in self.section_headers:
                        if sec_hdr.byte_type == 0x02:
                            val = unpack_from(">B", data, self._read(1))[0]
                        elif sec_hdr.byte_type == 0x03:
                            val = unpack_from(">H", data, self._read(2))[0]
                        else:
                            raise Exception("Unexpected value")

                        if sec_hdr.section_type == GC_SECTIONTYPE_VERTEX:
                            tri_vertices.append(val)
                        elif sec_hdr.section_type == GC_SECTIONTYPE_NORMAL:
                            tri_normals.append(val)
                        elif sec_hdr.section_type == GC_SECTIONTYPE_COLOR:
                            tri_prelit_colors.append(val)
                        elif sec_hdr.section_type == GC_SECTIONTYPE_TEXCOORD:
                            tri_tex_coords.append(val)
                        elif sec_hdr.section_type == GC_SECTIONTYPE_TEXCOORD2:
                            tri_tex_coords2.append(val)

                for i in range(len(tri_vertices) - 2):
                    if i % 2 == 0:
                        idx1 = i + 1
                        idx2 = i + 0
                    else:
                        idx1 = i + 0
                        idx2 = i + 1
                    idx3 = i + 2

                    vertex1, vertex2, vertex3 = tri_vertices[idx1], tri_vertices[idx2], tri_vertices[idx3]
                    if vertex1 == vertex2 or vertex1 == vertex3 or vertex2 == vertex3:
                        continue

                    geometry.triangles.append(Triangle(vertex1, vertex2, split_header.material, vertex3))

                    if tri_normals:
                        geometry.normals.append(self.normals[tri_normals[idx2]])
                        geometry.normals.append(self.normals[tri_normals[idx1]])
                        geometry.normals.append(self.normals[tri_normals[idx3]])

                    if tri_prelit_colors:
                        geometry.prelit_colors.append(self.prelit_colors[tri_prelit_colors[idx2]])
                        geometry.prelit_colors.append(self.prelit_colors[tri_prelit_colors[idx1]])
                        geometry.prelit_colors.append(self.prelit_colors[tri_prelit_colors[idx3]])

                    if tri_tex_coords:
                        geometry.uv_layers[0].append(self.tex_coords[tri_tex_coords[idx2]])
                        geometry.uv_layers[0].append(self.tex_coords[tri_tex_coords[idx1]])
                        geometry.uv_layers[0].append(self.tex_coords[tri_tex_coords[idx3]])

                    if tri_tex_coords2:
                        geometry.uv_layers[1].append(self.tex_coords2[tri_tex_coords2[idx2]])
                        geometry.uv_layers[1].append(self.tex_coords2[tri_tex_coords2[idx1]])
                        geometry.uv_layers[1].append(self.tex_coords2[tri_tex_coords2[idx3]])

#######################################################
class NativeGCSectionHeader:
    __slots__ = [
        "section_offset",
        "section_type",
        "entry_size",
        "byte_type"
    ]

    #######################################################
    def __init__(self, section_offset, section_type, entry_size, byte_type):
        self.section_offset = section_offset
        self.section_type = section_type
        self.entry_size = entry_size
        self.byte_type = byte_type

#######################################################
class NativeGCTriangleSectionHeader:
    __slots__ = [
        "section_offset",
        "section_size"
    ]

    #######################################################
    def __init__(self, section_offset, section_size):
        self.section_offset = section_offset
        self.section_size = section_size

#######################################################
class NativeGCTexture(TextureNative):

    #######################################################
    def __init__(self):
        super().__init__()
        self.texture_format = GVRFMT_RGBA8888
        self.pixel_format   = GVRPIX_NO_PALETTE

    #######################################################
    def to_rgba(self, level=0):
        width  = self.get_width(level)
        height = self.get_height(level)
        pixels = self.pixels[level]

        if self.texture_format == GVRFMT_LUM_4BIT:
            return NativeGCTexture.decode_lum4(pixels, width, height)

        elif self.texture_format == GVRFMT_LUM_8BIT:
            return NativeGCTexture.decode_lum8(pixels, width, height)

        elif self.texture_format == GVRFMT_LUM_4BIT_ALPHA:
            return NativeGCTexture.decode_lum4a4(pixels, width, height)

        elif self.texture_format == GVRFMT_LUM_8BIT_ALPHA:
            return NativeGCTexture.decode_lum8a8(pixels, width, height)

        elif self.texture_format == GVRFMT_RGB565:
            return NativeGCTexture.decode_bgr565(pixels, width, height)

        elif self.texture_format == GVRFMT_RGB5A3:
            return NativeGCTexture.decode_argb3555(pixels, width, height)

        elif self.texture_format == GVRFMT_RGBA8888:
            return NativeGCTexture.decode_argb8888(pixels, width, height)

        elif self.texture_format == GVRFMT_PAL_4BIT:
            if self.pixel_format == GVRPIX_LUM_ALPHA:
                palette = NativeGCTexture.decode_lum8a8(self.palette, 4, 4)

            elif self.pixel_format == GVRPIX_RGB565:
                palette = NativeGCTexture.decode_rgb565(self.palette, 4, 4)

            elif self.pixel_format == GVRPIX_RGB5A3:
                palette = NativeGCTexture.decode_argb3555(self.palette, 4, 4)

            return ImageDecoder.pal4(pixels, palette, width, height)

        elif self.texture_format == GVRFMT_PAL_8BIT:
            if self.pixel_format == GVRPIX_LUM_ALPHA:
                palette = NativeGCTexture.decode_lum8a8(self.palette, 16, 16)

            elif self.pixel_format == GVRPIX_RGB565:
                palette = NativeGCTexture.decode_rgb565(self.palette, 16, 16)

            elif self.pixel_format == GVRPIX_RGB5A3:
                palette = NativeGCTexture.decode_argb3555(self.palette, 16, 16)

            return ImageDecoder.pal8(pixels, palette, width, height)

        elif self.texture_format == GVRFMT_CMP:
            return NativeGCTexture.decode_bc1(pixels, width, height)

    #######################################################
    def has_alpha(self):
        return self.platform_properties.alpha != 0

    #######################################################
    @staticmethod
    def from_mem(data, rw_version):
        self = NativeGCTexture()
        self.pos = 0
        self.data = data

        (
            self.platform_id, self.filter_mode, self.uv_addressing
        ) = unpack_from(">IHH", self.data, self._read(8))

        if rw_version >= 0x33000:
            unk1, unk2, unk3, unk4 = unpack_from(">4I", self.data, self._read(16))

        self.name = self._read_raw(32)
        self.name = self.name.decode("utf-8").replace('\0', '')

        self.mask = self._read_raw(32)
        self.mask = self.mask.decode("utf-8").replace('\0', '')

        if rw_version >= 0x33002:
            (
                self.raster_format_flags, self.width, self.height, self.depth,
                self.num_levels, self.texture_format, self.pixel_format, has_alpha
            ) = unpack_from(">I2H3BbI", self.data, self._read(16))

        else:
            (
                self.raster_format_flags, has_alpha, self.width, self.height,
                self.depth, self.num_levels, raster_type, is_compressed,
            ) = unpack_from(">2I2H3B?", self.data, self._read(16))

            if is_compressed:
                self.texture_format = GVRFMT_CMP

            else:
                palette_format = self.get_raster_palette_type()
                raster_format = self.get_raster_format_type()

                if palette_format != PaletteType.PALETTE_NONE:
                    if palette_format == PaletteType.PALETTE_8:
                        self.texture_format = GVRFMT_PAL_8BIT
                    elif palette_format == PaletteType.PALETTE_4_LSB:
                        self.texture_format = GVRFMT_PAL_4BIT

                    if raster_format == GCRASTER_565:
                        self.pixel_format = GVRPIX_RGB565
                    elif raster_format == GCRASTER_RGB5A3:
                        self.pixel_format = GVRPIX_RGB5A3

                else:
                    if raster_format == GCRASTER_565:
                        self.texture_format = GVRFMT_RGB565
                    elif raster_format == GCRASTER_RGB5A3:
                        self.texture_format = GVRFMT_RGB5A3
                    elif raster_format == GCRASTER_888:
                        self.texture_format = GVRFMT_RGBA8888

        PlatformProperties = namedtuple(
            "PlatformProperties",
            ["alpha"]
        )
        self.platform_properties = PlatformProperties(has_alpha)

        if self.texture_format == GVRFMT_PAL_8BIT:
            self.palette = self._read_raw(512)
        elif self.texture_format == GVRFMT_PAL_4BIT:
            self.palette = self._read_raw(32)

        pixels_len = unpack_from(">I", self.data, self._read(4))[0]
        end_pos = self.pos + pixels_len

        is_swizzled = NativeGCTexture.is_swizzled_texture(self.texture_format)

        self.pixels = []
        for i in range(self.num_levels):
            width, height = self.get_width(i), self.get_height(i)
            data_len = NativeGCTexture.get_texture_format_len(width, height, self.texture_format)
            pixels = self._read_raw(data_len)
            if is_swizzled:
                pixels = NativeGCTexture.unswizzle(pixels, width, height, self.texture_format)
            self.pixels.append(pixels)

        self.pos = end_pos

        return self

    #######################################################
    @staticmethod
    def is_swizzled_texture(texture_format):
        if texture_format in (GVRFMT_LUM_4BIT, GVRFMT_LUM_4BIT_ALPHA, GVRFMT_LUM_8BIT_ALPHA, GVRFMT_RGB565,
                              GVRFMT_RGB5A3, GVRFMT_PAL_4BIT, GVRFMT_PAL_8BIT):
            return True
        return False

    #######################################################
    @staticmethod
    def get_texture_block_attributes(texture_format):
        # bpp, block width, block height
        if texture_format in (GVRFMT_LUM_4BIT, GVRFMT_PAL_4BIT, GVRFMT_CMP):
            return 4, 8, 8
        elif texture_format in (GVRFMT_LUM_4BIT_ALPHA, GVRFMT_LUM_8BIT, GVRFMT_PAL_8BIT):
            return 8, 8, 4
        elif texture_format in (GVRFMT_LUM_8BIT_ALPHA, GVRFMT_RGB565, GVRFMT_RGB5A3):
            return 16, 4, 4
        elif texture_format == GVRFMT_RGBA8888:
            return 32, 4, 4

    #######################################################
    @staticmethod
    def get_aligned_len(l, bl):
        return (l + bl - 1) // bl * bl

    #######################################################
    @staticmethod
    def get_texture_format_len(width, height, texture_format):
        bpp, bw, bh    = NativeGCTexture.get_texture_block_attributes(texture_format)
        aligned_width  = NativeGCTexture.get_aligned_len(width, bw)
        aligned_height = NativeGCTexture.get_aligned_len(height, bh)
        return aligned_width * aligned_height * bpp // 8

    #######################################################
    @staticmethod
    def unswizzle(data, width, height, texture_format):
        bpp, bw, bh = NativeGCTexture.get_texture_block_attributes(texture_format)
        aligned_width  = NativeGCTexture.get_aligned_len(width, bw)
        aligned_height = NativeGCTexture.get_aligned_len(height, bh)
        strip_size = bpp * bw // 8

        res = bytearray(aligned_width * aligned_height * bpp // 8)
        pos = 0

        for y in range(0, aligned_height, bh):
            for x in range(0, aligned_width, bw):
                for y2 in range(bh):
                    idx = (((y + y2) * aligned_width) + x) * bpp // 8
                    res[idx : idx+strip_size] = data[pos : pos+strip_size]
                    pos += strip_size

        return NativeGCTexture.crop(res, aligned_width, aligned_height, bpp, width, height)

    #######################################################
    @staticmethod
    def crop(data, width, height, bpp, new_width, new_height):
        if width == new_width and height == new_height:
            return data

        res = bytearray(new_width * new_height * bpp // 8)
        lw = min(width, new_width) * bpp // 8

        for y in range(min(height, new_height)):
            dst = y * new_width * bpp // 8
            src = y * width * bpp // 8
            res[dst: dst + lw] = data[src: src + lw]

        return bytes(res)

    #######################################################
    @staticmethod
    def decode_bc1(data, width, height):
        pos = 0
        ret = bytearray(4 * width * height)

        for tile_y in range(0, height, 8):
            for tile_x in range(0, width, 8):
                for block in range(4):
                    color0, color1, bits = unpack_from(">HHI", data, pos)
                    pos += 8

                    x = tile_x + (block % 2) * 4
                    y = tile_y + (block // 2) * 4
                    if x >= width or y >= height:
                        continue

                    r0, g0, b0 = ImageDecoder._decode565(color0)
                    r1, g1, b1 = ImageDecoder._decode565(color1)

                    # Decode this block into 4x4 pixels
                    shift = 32
                    for j in range(4):
                        for i in range(4):
                            # Get next control op and generate a pixel
                            shift -= 2
                            control = (bits >> shift) & 3
                            if control == 0:
                                r, g, b, a = r0, g0, b0, 0xff
                            elif control == 1:
                                r, g, b, a = r1, g1, b1, 0xff
                            elif control == 2:
                                if color0 > color1:
                                    r, g, b, a = ImageDecoder._c2a(r0, r1), ImageDecoder._c2a(g0, g1), ImageDecoder._c2a(b0, b1), 0xff
                                else:
                                    r, g, b, a = ImageDecoder._c2b(r0, r1), ImageDecoder._c2b(g0, g1), ImageDecoder._c2b(b0, b1), 0xff
                            elif control == 3:
                                if color0 > color1:
                                    r, g, b, a = ImageDecoder._c3(r0, r1),ImageDecoder. _c3(g0, g1), ImageDecoder._c3(b0, b1), 0xff
                                else:
                                    r, g, b, a = 0, 0, 0, 0

                            idx = 4 * ((y + j) * width + (x + i))
                            ret[idx:idx+4] = bytes([r, g, b, a])

        return bytes(ret)

    #######################################################
    @staticmethod
    def decode_lum4(data, width, height):
        ret = bytearray(4 * width * height)
        for i, b in enumerate(data):
            c1 = (b >> 4) * 17
            c2 = (b & 0xf) * 17
            pos = i * 8
            ret[pos+0:pos+4] = c1, c1, c1, 0xff
            ret[pos+4:pos+8] = c2, c2, c2, 0xff
        return bytes(ret)

    #######################################################
    @staticmethod
    def decode_lum4a4(data, width, height):
        ret = bytearray(4 * width * height)
        for i, b in enumerate(data):
            a = (b >> 4) * 17
            c = (b & 0xf) * 17
            pos = i * 4
            ret[pos:pos+4] = c, c, c, a
        return bytes(ret)

    #######################################################
    @staticmethod
    def decode_lum8(data, width, height):
        ret = bytearray(4 * width * height)
        for i, c in enumerate(data):
            pos = i * 4
            ret[pos:pos+4] = c, c, c, 0xff
        return bytes(ret)

    #######################################################
    @staticmethod
    def decode_lum8a8(data, width, height):
        pos = 0
        ret = bytearray(4 * width * height)

        for i in range(0, len(data), 2):
            a, c = data[i], data[i+1]
            ret[pos:pos+4] = c, c, c, a
            pos += 4
        return bytes(ret)

    #######################################################
    @staticmethod
    def decode_argb3555(data, width, height):
        pos = 0
        ret = bytearray(width * height * 4)

        for i in range(0, len(data), 2):
            color = unpack_from(">H", data, i)[0]
            if color & 0x8000 != 0:
                r, g, b = ImageDecoder._decode555(color)
                ret[pos:pos+4] = r, g, b, 0xff
            else:
                a, r, g, b = ImageDecoder._decode4443(color)
                ret[pos:pos+4] = r, g, b, a
            pos += 4
        return bytes(ret)

    #######################################################
    @staticmethod
    def decode_bgr565(data, width, height):
        pos = 0
        ret = bytearray(width * height * 4)

        for i in range(0, len(data), 2):
            color = unpack_from(">H", data, i)[0]
            r, g, b = ImageDecoder._decode565(color)
            ret[pos:pos+4] = b, g, r, 0xff
            pos += 4
        return bytes(ret)

    #######################################################
    @staticmethod
    def decode_rgb565(data, width, height):
        pos = 0
        ret = bytearray(width * height * 4)

        for i in range(0, len(data), 2):
            color = unpack_from(">H", data, i)[0]
            r, g, b = ImageDecoder._decode565(color)
            ret[pos:pos+4] = r, g, b, 0xff
            pos += 4
        return bytes(ret)

    #######################################################
    @staticmethod
    def decode_argb8888(data, width, height):
        aligned_width  = NativeGCTexture.get_aligned_len(width, 4)
        aligned_height = NativeGCTexture.get_aligned_len(height, 4)

        pos = 0
        ret = bytearray(aligned_width * aligned_height * 4)

        for y in range(0, aligned_height, 4):
            for x in range(0, aligned_width, 4):
                for y2 in range(4):
                    for x2 in range(4):
                        idx = (((y + y2) * aligned_width) + (x + x2)) * 4
                        ret[idx + 0] = data[pos + 33]
                        ret[idx + 1] = data[pos + 32]
                        ret[idx + 2] = data[pos + 1]
                        ret[idx + 3] = data[pos + 0]
                        pos += 2
                pos += 32

        return NativeGCTexture.crop(ret, aligned_width, aligned_height, 32, width, height)

    #######################################################
    def _read(self, size):
        current_pos = self.pos
        self.pos += size

        return current_pos

    #######################################################
    def _read_raw(self, size):
        offset = self._read(size)
        return self.data[offset:offset+size]

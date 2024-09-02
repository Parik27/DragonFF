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

from enum import IntEnum
from math import ceil
from struct import unpack_from
from collections import namedtuple

from .dff import Sections, NativePlatformType
from .dff import types, Chunk, TexDict, PITexDict, Texture
from .dff import strlen

class RasterFormat(IntEnum):
    RASTER_DEFAULT = 0x00
    RASTER_1555    = 0x01
    RASTER_565     = 0x02
    RASTER_4444    = 0x03
    RASTER_LUM     = 0x04
    RASTER_8888    = 0x05
    RASTER_888     = 0x06
    RASTER_555     = 0x0a

#######################################################
class ImageDecoder:

    @staticmethod
    def _decode1555(bits):
        a = ((bits >> 15) & 0x1) * 0xff
        b = ((bits >> 10) & 0x1f) << 3
        c = ((bits >> 5) & 0x1f) << 3
        d = (bits & 0x1f) << 3
        return a, b, c, d

    @staticmethod
    def _decode4444(bits):
        a = ((bits >> 12) & 0xf) << 4
        b = ((bits >> 8) & 0xf) << 4
        c = ((bits >> 4) & 0xf) << 4
        d = (bits & 0xf) << 4
        return a, b, c, d

    @staticmethod
    def _decode565(bits):
        a = ((bits >> 11) & 0x1f) << 3
        b = ((bits >> 5) & 0x3f) << 2
        c = (bits & 0x1f) << 3
        return a, b, c

    @staticmethod
    def _decode555(bits):
        a = ((bits >> 10) & 0x1f) << 3
        b = ((bits >> 5) & 0x1f) << 3
        c = (bits & 0x1f) << 3
        return a, b, c

    @staticmethod
    def _c2a(a, b):
        return (2 * a + b) // 3

    @staticmethod
    def _c2b(a, b):
        return (a + b) // 2

    @staticmethod
    def _c3(a, b):
        return (2 * b + a) // 3

    @staticmethod
    def dxt1(data, width, height, alpha_flag):
        pos = 0
        ret = bytearray(4 * width * height)

        for y in range(0, height, 4):
            for x in range(0, width, 4):
                color0, color1, bits = unpack_from("<HHI", data, pos)
                pos += 8

                r0, g0, b0 = ImageDecoder._decode565(color0)
                r1, g1, b1 = ImageDecoder._decode565(color1)

                # Decode this block into 4x4 pixels
                for j in range(4):
                    for i in range(4):
                        # Get next control op and generate a pixel
                        control = bits & 3
                        bits = bits >> 2
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
                        ret[idx:idx+4] = bytes([r, g, b, a | alpha_flag])

        return bytes(ret)

    @staticmethod
    def dxt3(data, width, height):
        pos = 0
        ret = bytearray(4 * width * height)

        for y in range(0, height, 4):
            for x in range(0, width, 4):
                alpha0, alpha1, alpha2, alpha3, color0, color1, bits = unpack_from("<4H2HI", data, pos)
                pos += 16

                r0, g0, b0 = ImageDecoder._decode565(color0)
                r1, g1, b1 = ImageDecoder._decode565(color1)
                alphas = (alpha0, alpha1, alpha2, alpha3)

                # Decode this block into 4x4 pixels
                for j in range(4):
                    for i in range(4):
                        # Get next control op and generate a pixel
                        control = bits & 3
                        bits = bits >> 2
                        if control == 0:
                            r, g, b = r0, g0, b0
                        elif control == 1:
                            r, g, b = r1, g1, b1
                        elif control == 2:
                            if color0 > color1:
                                r, g, b = ImageDecoder._c2a(r0, r1), ImageDecoder._c2a(g0, g1), ImageDecoder._c2a(b0, b1)
                            else:
                                r, g, b = ImageDecoder._c2b(r0, r1), ImageDecoder._c2b(g0, g1), ImageDecoder._c2b(b0, b1)
                        elif control == 3:
                            if color0 > color1:
                                r, g, b = ImageDecoder._c3(r0, r1),ImageDecoder. _c3(g0, g1), ImageDecoder._c3(b0, b1)
                            else:
                                r, g, b = 0, 0, 0

                        a = ((alphas[j] >> (i * 4)) & 0xf) * 0x11
                        idx = 4 * ((y + j) * width + (x + i))
                        ret[idx:idx+4] = bytes([r, g, b, a])

        return bytes(ret)

    @staticmethod
    def bgra1555(data, width, height):
        pos = 0
        ret = bytearray(4 * width * height)

        for i in range(0, len(data), 2):
            color = unpack_from("<H", data, i)[0]
            a, r, g, b = ImageDecoder._decode1555(color)
            ret[pos:pos+4] = r, g, b, a
            pos += 4
        return bytes(ret)

    @staticmethod
    def bgra4444(data, width, height):
        pos = 0
        ret = bytearray(4 * width * height)

        for i in range(0, len(data), 2):
            color = unpack_from("<H", data, i)[0]
            a, r, g, b = ImageDecoder._decode4444(color)
            ret[pos:pos+4] = r, g, b, a
            pos += 4
        return bytes(ret)

    @staticmethod
    def bgra555(data, width, height):
        pos = 0
        ret = bytearray(4 * width * height)

        for i in range(0, len(data), 2):
            color = unpack_from("<H", data, i)[0]
            r, g, b = ImageDecoder._decode555(color)
            ret[pos:pos+4] = r, g, b, 0xff
            pos += 4
        return bytes(ret)

    @staticmethod
    def bgra565(data, width, height):
        pos = 0
        ret = bytearray(4 * width * height)

        for i in range(0, len(data), 2):
            color = unpack_from("<H", data, i)[0]
            r, g, b = ImageDecoder._decode565(color)
            ret[pos:pos+4] = r, g, b, 0xff
            pos += 4
        return bytes(ret)

    @staticmethod
    def bgra888(data, width, height):
        ret = bytearray(4 * width * height)
        for i in range(0, len(data), 4):
            ret[i:i+4] = data[i+2], data[i+1], data[i+0], 0xff
        return bytes(ret)

    @staticmethod
    def bgra8888(data, width, height):
        ret = bytearray(4 * width * height)
        for i in range(0, len(data), 4):
            ret[i:i+4] = data[i+2], data[i+1], data[i+0], data[i+3]
        return bytes(ret)

    @staticmethod
    def lum8(data, width, height):
        ret = bytearray(4 * width * height)
        for i, c in enumerate(data):
            pos = i * 4
            ret[pos:pos+4] = c, c, c, 0xff
        return bytes(ret)

    @staticmethod
    def lum8a8(data, width, height):
        pos = 0
        ret = bytearray(4 * width * height)

        for i in range(0, len(data), 2):
            c, a = data[i], data[i+1]
            ret[pos:pos+4] = c, c, c, a
            pos += 4
        return bytes(ret)

    @staticmethod
    def pal4(data, palette, width, height):
        pos = 0
        ret = bytearray(4 * width * height)

        shift = 0
        for i in data:
            idx = (i >> shift) & 0xf
            ret[pos+0:pos+4] = palette[idx*4:idx*4+4]
            shift ^= 4
            pos += 4

        return bytes(ret)

    @staticmethod
    def pal8(data, palette, width, height):
        pos = 0
        ret = bytearray(4 * width * height)

        for idx in data:
            ret[pos:pos+4] = palette[idx*4:idx*4+4]
            pos += 4

        return bytes(ret)

#######################################################
class TextureNative:

    #######################################################
    def __init__(self):
        # Header
        self._platform_id = 0
        self._filter_mode = 0

        self.uv_addressing = 0

        self.name = ""
        self.mask = ""

        self.raster_format = 0
        self.width         = 0
        self.height        = 0
        self.depth         = 0
        self.num_levels    = 1
        self.raster_type   = 0

        self.image_properties = None

        # Palette
        self.palette = b''

        # Raster Data
        self.pixels = []

    #######################################################
    def to_rgba(self, level=0):
        width  = self.get_width(level)
        height = self.get_height(level)
        pixels = self.pixels[level]

        if self.palette:
            palette_format = self.raster_format & 0xf000

            if palette_format > 0:
                if palette_format == 0x2000:
                    return ImageDecoder.pal8(pixels, self.palette, width, height)
                elif palette_format == 0x4000:
                    if self.depth == 4:
                        return ImageDecoder.pal4(pixels, self.palette, width, height)
                    else:
                        return ImageDecoder.pal8(pixels, self.palette, width, height)

        else:
            # TODO: improve format definition
            pixels_format = (self.raster_format >> 8) & 0x0f

            if self.image_properties.compressed:
                if pixels_format == RasterFormat.RASTER_DEFAULT:
                    return ImageDecoder.lum8a8(pixels, width, height)
                if pixels_format == RasterFormat.RASTER_1555:
                    return ImageDecoder.dxt1(pixels, width, height, 0x00)
                elif pixels_format == RasterFormat.RASTER_565:
                    return ImageDecoder.dxt1(pixels, width, height, 0xff)
                elif pixels_format == RasterFormat.RASTER_4444:
                    return ImageDecoder.dxt3(pixels, width, height)
            else:
                if pixels_format == RasterFormat.RASTER_1555:
                    # return ImageDecoder.bgra1555(pixels, width, height)
                    return ImageDecoder.dxt1(pixels, width, height, 0x00)
                elif pixels_format == RasterFormat.RASTER_565:
                    # return ImageDecoder.bgra565(pixels, width, height)
                    return ImageDecoder.dxt1(pixels, width, height, 0xff)
                elif pixels_format == RasterFormat.RASTER_4444:
                    # return ImageDecoder.bgra4444(pixels, width, height)
                    return ImageDecoder.dxt3(pixels, width, height)
                elif pixels_format == RasterFormat.RASTER_LUM:
                    return ImageDecoder.lum8(pixels, width, height)
                elif pixels_format == RasterFormat.RASTER_8888:
                    return ImageDecoder.bgra8888(pixels, width, height)
                elif pixels_format == RasterFormat.RASTER_888:
                    return ImageDecoder.bgra888(pixels, width, height)
                elif pixels_format == RasterFormat.RASTER_555:
                    return ImageDecoder.bgra555(pixels, width, height)

    #######################################################
    def get_width(self, level=0):
        return max(self.width >> level, 1)

    #######################################################
    def get_height(self, level=0):
        return max(self.height >> level, 1)

    #######################################################
    def read_pixels(self, data, offset):
        pixels_len = unpack_from("<I", data, offset)[0]
        return data[offset+4:offset+4+pixels_len]

    #######################################################
    def read_palette(self, data, offset):
        palette_format = self.raster_format & 0xf000

        if palette_format > 0:
            if palette_format == 0x2000:
                return data[offset:offset+1024]

            if palette_format == 0x4000:
                if self.depth == 4:
                    return data[offset:offset+64]

                return data[offset:offset+128]

        return b''

    #######################################################
    def read_image_properties(self, data, offset):

        ImageProperties = namedtuple(
            "ImageProperties",
            [
                "alpha", "cube_texture", "auto_mipmaps",
                "compressed"]
        )

        prop = unpack_from("<B", data, offset)[0]
        return ImageProperties(prop & 0b0001 != 0,
                               prop & 0b0010 != 0,
                               prop & 0b0100 != 0,
                               prop & 0b1000 != 0)

    #######################################################
    def from_mem(data):

        self = TextureNative()

        TextureFormat = namedtuple(
            "Header",
            [
                'platform_id' , 'filter_mode' , 'uv_addressing' ,
                'name'        , 'mask_name']
        )

        RasterHeader  = namedtuple(
            "RasterHeader",
            [
                'raster_format' , 'sa_format_3vc_hasAlpha' , 'width'      ,
                'height'        , 'depth'                  , 'num_levels' ,
                'raster_type'   , 'image_properties']
        )

        pos = 0
        tex_format = TextureFormat._make(unpack_from("<IHH32s32s", data, pos))
        pos += 72

        (
            self._platform_id, self._filter_mode, self.uv_addressing, self.name,
            self.mask
        ) = tex_format

        self.name = self.name.decode("utf-8").replace('\0', '')
        try:
            self.mask = self.mask.decode("utf-8").replace('\0', '')
        except UnicodeDecodeError:
            self.mask = ''

        raster_header = RasterHeader(
            *unpack_from("<IIHHBBB", data, pos),
            self.read_image_properties(data, pos + 15)
        )
        pos += 16

        (
            self.raster_format, sa_format_3vc_hasAlpha, self.width, self.height,
            self.depth, self.num_levels, self.raster_type, self.image_properties
        ) = raster_header

        self.palette = self.read_palette(data, pos)
        pos += len(self.palette)

        self.pixels = []
        for _ in range(self.num_levels):
            pixels = self.read_pixels(data, pos)
            self.pixels.append(pixels)
            pos += 4 + len(pixels)

        return self

#######################################################
class Image:

    width = 0
    height = 0
    depth = 0
    pitch = 0

    # Palette
    palette = b''

    # Raster Data
    pixels = b''

    #######################################################
    def _crop_pixels(self):
        src_width = len(self.pixels) // self.height
        dst_width = ceil(self.width * self.depth / 8)

        if src_width == dst_width:
            return self.pixels

        pixels = bytearray(dst_width * self.height)

        for y in range(self.height):
            src_pos = y * src_width
            dst_pos = y * dst_width
            pixels[dst_pos:dst_pos+dst_width] = self.pixels[src_pos:src_pos+src_width]

        return bytes(pixels)

    #######################################################
    def to_rgba(self, level=0):
        pixels = self._crop_pixels()

        if self.depth == 32:
            return ImageDecoder.bgra8888(pixels, self.width, self.height)
        elif self.depth == 8:
            return ImageDecoder.pal8(pixels, self.palette, self.width, self.height)
        elif self.depth == 4:
            return ImageDecoder.pal4(pixels, self.palette, self.width, self.height)

    #######################################################
    def from_mem(data):
        self = Image()

        self.width, self.height, self.depth, self.pitch = unpack_from("<4I", data)

        return self

#######################################################
class txd:

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
    def read_texture_native(self, parent_chunk):

        chunk_end = self.pos + parent_chunk.size

        while self.pos < chunk_end:
            chunk = self.read_chunk()

            # STRUCT
            if chunk.type == types["Struct"]:
                platform_id = unpack_from("<I", self.data, self.pos)[0]
                texture = None

                if self.device_id == 0:
                    if platform_id in (NativePlatformType.XBOX, NativePlatformType.D3D8, NativePlatformType.D3D9):
                        texture = TextureNative.from_mem(
                                self.data[self.pos:self.pos+chunk.size]
                        )
                    elif platform_id == NativePlatformType.PS2FOURCC:
                        from .native_ps2 import NativePS2Texture
                        texture = NativePS2Texture.from_mem(self.data[self.pos:])
                        self._read(texture.pos - chunk.size)

                elif self.device_id in (1, 2):
                    texture = TextureNative.from_mem(
                            self.data[self.pos:self.pos+chunk.size]
                    )

                elif self.device_id == 6:
                    from .native_ps2 import NativePS2Texture
                    texture = NativePS2Texture.from_mem(self.data[self.pos:])
                    self._read(texture.pos - chunk.size)

                if texture:
                    self.native_textures.append(texture)

            elif chunk.type == types["Extension"]:
                pass

            self._read(chunk.size)

    #######################################################
    def read_image(self, parent_chunk):

        chunk = self.read_chunk()

        # Read an image
        image = Image.from_mem(
            self.data[self.pos:self.pos+chunk.size]
        )

        self._read(chunk.size)

        # Pixels
        pixels_len = image.pitch * image.height
        image.pixels = self.raw(pixels_len)
        self._read(pixels_len)

        # Palette
        palette_len = 0
        if image.depth == 8:
            palette_len = 1024
        elif image.depth == 4:
            palette_len = 64

        image.palette = self.raw(palette_len)
        self._read(palette_len)

        return image

    #######################################################
    def read_texture(self, parent_chunk):

        chunk = self.read_chunk()

        # Read a texture
        texture = Texture.from_mem(
            self.data[self.pos:self.pos+chunk.size]
        )

        self._read(chunk.size)

        # Texture Name
        chunk = self.read_chunk()
        texture.name = self.raw(
            strlen(self.data, self.pos)
        ).decode("utf-8")

        self._read(chunk.size)

        # Mask Name
        chunk = self.read_chunk()
        texture.mask = self.raw(
            strlen(self.data, self.pos)
        ).decode("utf-8")

        self._read(chunk.size)

        return texture

    #######################################################
    def read_texture_dictionary(self, root_chunk):

        chunk_end = self.pos + root_chunk.size

        while self.pos < chunk_end:
            chunk = self.read_chunk()

            # STRUCT
            if chunk.type == types["Struct"]:

                text_dict = Sections.read(TexDict, self.data, self._read(chunk.size))
                self.device_id = text_dict.device_id # 1 for D3D8, 2 for D3D9, 6 for PlayStation 2, 8 for XBOX, 9 for PSP

                for _ in range(text_dict.texture_count):
                    chunk = self.read_chunk()

                    # TEXTURENATIVE
                    if chunk.type == types["Texture Native"]:
                        self.read_texture_native(chunk)

            else:
                self._read(chunk.size)

    #######################################################
    def read_pi_texture_dictionary(self, root_chunk):
        text_dict = Sections.read(TexDict, self.data, self._read(4))
        self.device_id = text_dict.device_id

        for _ in range(text_dict.texture_count):
            mips_num = unpack_from("<I", self.data, self._read(4))[0]
            images = []

            for _ in range(mips_num):
                chunk = self.read_chunk()
                if chunk.type != types["Image"]:
                    raise RuntimeError("Invalid format")

                images.append(self.read_image(chunk))

            self.images.append(images)

            chunk = self.read_chunk()
            if chunk.type != types["Texture"]:
                raise RuntimeError("Invalid format")

            texture = self.read_texture(chunk)
            self.textures.append(texture)

            chunk = self.read_chunk()
            if chunk.type != types["Extension"]:
                raise RuntimeError("Invalid format")

            self._read(chunk.size)

    #######################################################
    def load_memory(self, data):
        self.data = data

        chunk = self.read_chunk()
        if chunk.type == types["Texture Dictionary"]:
            self.read_texture_dictionary(chunk)
        elif chunk.type == types["PI Texture Dictionary"]:
            self.read_pi_texture_dictionary(chunk)

        self.rw_version = Sections.get_rw_version(chunk.version)

    #######################################################
    def clear(self):
        self.native_textures = []
        self.textures        = []
        self.images          = []
        self.pos             = 0
        self.data            = ""
        self.rw_version      = ""
        self.device_id       = 0

    #######################################################
    def load_file(self, filename):

        with open(filename, mode='rb') as file:
            content = file.read()
            self.load_memory(content)

    #######################################################
    def __init__(self):
        self.clear()

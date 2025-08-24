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
from struct import unpack_from, pack
from collections import namedtuple

from .dff import Sections, NativePlatformType
from .dff import types, Chunk, TexDict, PITexDict, Texture
from .dff import strlen

#######################################################
class RasterFormat(IntEnum):
    RASTER_DEFAULT = 0x00
    RASTER_1555    = 0x01
    RASTER_565     = 0x02
    RASTER_4444    = 0x03
    RASTER_LUM     = 0x04
    RASTER_8888    = 0x05
    RASTER_888     = 0x06
    RASTER_16      = 0x07
    RASTER_24      = 0x08
    RASTER_32      = 0x09
    RASTER_555     = 0x0a

#######################################################
class D3DFormat(IntEnum):
    D3D_8888 = 21
    D3D_888  = 22
    D3D_565  = 23
    D3D_555  = 24
    D3D_1555 = 25
    D3D_4444 = 26

    D3DFMT_L8   = 50
    D3DFMT_A8L8 = 51

    D3D_DXT1 = 827611204
    D3D_DXT2 = 844388420
    D3D_DXT3 = 861165636
    D3D_DXT4 = 877942852
    D3D_DXT5 = 894720068

#######################################################
class D3DCompressType(IntEnum):
    DXT1 = 1
    DXT2 = 2
    DXT3 = 3
    DXT4 = 4
    DXT5 = 5

#######################################################
class PaletteType(IntEnum):
    PALETTE_NONE  = 0
    PALETTE_8     = 1
    PALETTE_4     = 2
    PALETTE_4_LSB = 3

#######################################################
class DeviceType(IntEnum):
    DEVICE_NONE = 0
    DEVICE_D3D8 = 1
    DEVICE_D3D9 = 2
    DEVICE_GC   = 3 # probably
    DEVICE_PS2  = 6
    DEVICE_XBOX = 8
    DEVICE_PSP  = 9

#######################################################
class ImageEncoder:
    
    @staticmethod
    def rgba_to_bgra8888(rgba_data):
        ret = bytearray()
        for i in range(0, len(rgba_data), 4):
            r, g, b, a = rgba_data[i:i+4]
            ret.extend([b, g, r, a])
        return bytes(ret)
    
    @staticmethod
    def rgba_to_bgra888(rgba_data):
        ret = bytearray()
        for i in range(0, len(rgba_data), 4):
            r, g, b = rgba_data[i:i+3]
            ret.extend([b, g, r])
        return bytes(ret)

#######################################################
class ImageDecoder:

    @staticmethod
    def _decode1555(bits):
        a = ((bits >> 15) & 0x1) * 0xff
        b = ((bits >> 10) & 0x1f) * 0xff // 0x1f
        c = ((bits >> 5) & 0x1f) * 0xff // 0x1f
        d = (bits & 0x1f) * 0xff // 0x1f
        return a, b, c, d

    @staticmethod
    def _decode4443(bits):
        a = ((bits >> 12) & 0x7) * 0xff // 0x7
        b = ((bits >> 8) & 0xf) * 0xff // 0xf
        c = ((bits >> 4) & 0xf) * 0xff // 0xf
        d = (bits & 0xf) * 0xff // 0xf
        return a, b, c, d

    @staticmethod
    def _decode4444(bits):
        a = ((bits >> 12) & 0xf) * 0xff // 0xf
        b = ((bits >> 8) & 0xf) * 0xff // 0xf
        c = ((bits >> 4) & 0xf) * 0xff // 0xf
        d = (bits & 0xf) * 0xff // 0xf
        return a, b, c, d

    @staticmethod
    def _decode565(bits):
        a = ((bits >> 11) & 0x1f) * 0xff // 0x1f
        b = ((bits >> 5) & 0x3f) * 0xff // 0x3f
        c = (bits & 0x1f) * 0xff // 0x1f
        return a, b, c

    @staticmethod
    def _decode555(bits):
        a = ((bits >> 10) & 0x1f) * 0xff // 0x1f
        b = ((bits >> 5) & 0x1f) * 0xff // 0x1f
        c = (bits & 0x1f) * 0xff // 0x1f
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
    def bc1(data, width, height, alpha_flag):
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
    def bc2(data, width, height, premultiplied):
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
                        if premultiplied and a > 0:
                            r = min(round(r * 255 / a), 255)
                            g = min(round(g * 255 / a), 255)
                            b = min(round(b * 255 / a), 255)
                        ret[idx:idx+4] = bytes([r, g, b, a])

        return bytes(ret)

    @staticmethod
    def bc3(data, width, height, premultiplied):
        pos = 0
        ret = bytearray(4 * width * height)

        for y in range(0, height, 4):
            for x in range(0, width, 4):
                alpha0 = data[pos]
                alpha1 = data[pos + 1]
                alpha_bits = unpack_from("<6B", data, pos + 2)
                pos += 8

                # Combine alpha bits into 48-bit integer
                alpha_indices = (alpha_bits[0] | (alpha_bits[1] << 8) | (alpha_bits[2] << 16) |
                                (alpha_bits[3] << 24) | (alpha_bits[4] << 32) | (alpha_bits[5] << 40))

                color0, color1, bits = unpack_from("<2HI", data, pos)
                pos += 8

                r0, g0, b0 = ImageDecoder._decode565(color0)
                r1, g1, b1 = ImageDecoder._decode565(color1)

                # Calculate alpha values
                if alpha0 > alpha1:
                    alphas = (
                        alpha0,
                        alpha1,
                        round(alpha0 * (6 / 7) + alpha1 * (1 / 7)),
                        round(alpha0 * (5 / 7) + alpha1 * (2 / 7)),
                        round(alpha0 * (4 / 7) + alpha1 * (3 / 7)),
                        round(alpha0 * (3 / 7) + alpha1 * (4 / 7)),
                        round(alpha0 * (2 / 7) + alpha1 * (5 / 7)),
                        round(alpha0 * (1 / 7) + alpha1 * (6 / 7))
                    )
                else:
                    alphas = (
                        alpha0,
                        alpha1,
                        round(alpha0 * (4 / 5) + alpha1 * (1 / 5)),
                        round(alpha0 * (3 / 5) + alpha1 * (2 / 5)),
                        round(alpha0 * (2 / 5) + alpha1 * (3 / 5)),
                        round(alpha0 * (1 / 5) + alpha1 * (4 / 5)),
                        0,
                        255
                    )

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
                                r, g, b = ImageDecoder._c3(r0, r1), ImageDecoder._c3(g0, g1), ImageDecoder._c3(b0, b1)
                            else:
                                r, g, b = 0, 0, 0

                        # Get alpha index (3 bits per pixel)
                        pixel_idx = j * 4 + i
                        alpha_index = (alpha_indices >> (3 * pixel_idx)) & 0x7
                        a = alphas[alpha_index]

                        idx = 4 * ((y + j) * width + (x + i))
                        if premultiplied and a > 0:
                            r = min(round(r * 255 / a), 255)
                            g = min(round(g * 255 / a), 255)
                            b = min(round(b * 255 / a), 255)
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

        for i in data:
            idx1, idx2 = (i >> 4) & 0xf, i & 0xf
            ret[pos+0:pos+4] = palette[idx1*4:idx1*4+4]
            ret[pos+4:pos+8] = palette[idx2*4:idx2*4+4]
            pos += 8

        return bytes(ret)

    @staticmethod
    def pal4_noalpha(data, palette, width, height):
        pos = 0
        ret = bytearray(4 * width * height)

        for i in data:
            idx1, idx2 = (i >> 4) & 0xf, i & 0xf
            ret[pos+0:pos+4] = palette[idx1*4:idx1*4+3] + b'\xff'
            ret[pos+4:pos+8] = palette[idx2*4:idx2*4+3] + b'\xff'
            pos += 8

        return bytes(ret)

    @staticmethod
    def pal8(data, palette, width, height):
        pos = 0
        ret = bytearray(4 * width * height)

        for idx in data:
            ret[pos:pos+4] = palette[idx*4:idx*4+4]
            pos += 4

        return bytes(ret)

    @staticmethod
    def pal8_noalpha(data, palette, width, height):
        pos = 0
        ret = bytearray(4 * width * height)

        for idx in data:
            ret[pos:pos+4] = palette[idx*4:idx*4+3] + b'\xff'
            pos += 4

        return bytes(ret)

#######################################################
class TextureNative:

    #######################################################
    def __init__(self):
        # Header
        self.platform_id = 0
        self.filter_mode = 0

        self.uv_addressing = 0

        self.name = ""
        self.mask = ""

        self.raster_format_flags = 0
        self.d3d_format          = 0
        self.width               = 0
        self.height              = 0
        self.depth               = 0
        self.num_levels          = 1
        self.raster_type         = 0

        self.platform_properties = None

        # Palette
        self.palette = b''

        # Raster Data
        self.pixels = []

    #######################################################
    def to_rgba(self, level=0):
        width  = self.get_width(level)
        height = self.get_height(level)
        pixels = self.pixels[level]

        # Texture with palette
        if self.palette:
            palette_format = self.get_raster_palette_type()

            if palette_format != PaletteType.PALETTE_NONE:
                if palette_format != PaletteType.PALETTE_8 and self.depth == 4:
                    if self.has_alpha():
                        return ImageDecoder.pal4(pixels, self.palette, width, height)
                    return ImageDecoder.pal4_noalpha(pixels, self.palette, width, height)

            if self.has_alpha():
                return ImageDecoder.pal8(pixels, self.palette, width, height)
            return ImageDecoder.pal8_noalpha(pixels, self.palette, width, height)

        # D3D8 specific texture
        elif self.platform_id == NativePlatformType.D3D8:
            if self.platform_properties.dxt_type == D3DCompressType.DXT1:
                return ImageDecoder.bc1(pixels, width, height, 0x00)
            elif self.platform_properties.dxt_type == D3DCompressType.DXT2:
                return ImageDecoder.bc2(pixels, width, height, True)
            elif self.platform_properties.dxt_type == D3DCompressType.DXT3:
                return ImageDecoder.bc2(pixels, width, height, False)
            elif self.platform_properties.dxt_type == D3DCompressType.DXT4:
                return ImageDecoder.bc3(pixels, width, height, True)
            elif self.platform_properties.dxt_type == D3DCompressType.DXT5:
                return ImageDecoder.bc3(pixels, width, height, False)

        # D3D9 specific texture
        elif self.platform_id == NativePlatformType.D3D9:
            if self.d3d_format == D3DFormat.D3D_8888:
                return ImageDecoder.bgra8888(pixels, width, height)
            elif self.d3d_format == D3DFormat.D3D_888:
                return ImageDecoder.bgra888(pixels, width, height)
            elif self.d3d_format == D3DFormat.D3D_565:
                return ImageDecoder.bgra565(pixels, width, height)
            elif self.d3d_format == D3DFormat.D3D_555:
                return ImageDecoder.bgra555(pixels, width, height)
            elif self.d3d_format == D3DFormat.D3D_1555:
                return ImageDecoder.bgra1555(pixels, width, height)
            elif self.d3d_format == D3DFormat.D3D_4444:
                return ImageDecoder.bgra4444(pixels, width, height)

            elif self.d3d_format == D3DFormat.D3DFMT_L8:
                return ImageDecoder.lum8(pixels, width, height)
            elif self.d3d_format == D3DFormat.D3DFMT_A8L8:
                return ImageDecoder.lum8a8(pixels, width, height)

            elif self.d3d_format == D3DFormat.D3D_DXT1:
                return ImageDecoder.bc1(pixels, width, height, 0x00)
            elif self.d3d_format == D3DFormat.D3D_DXT2:
                return ImageDecoder.bc2(pixels, width, height, True)
            elif self.d3d_format == D3DFormat.D3D_DXT3:
                return ImageDecoder.bc2(pixels, width, height, False)
            elif self.d3d_format == D3DFormat.D3D_DXT4:
                return ImageDecoder.bc3(pixels, width, height, True)
            elif self.d3d_format == D3DFormat.D3D_DXT5:
                return ImageDecoder.bc3(pixels, width, height, False)

        # Common raster cases
        raster_format = self.get_raster_format_type()
        if raster_format == RasterFormat.RASTER_1555:
            return ImageDecoder.bgra1555(pixels, width, height)
        elif raster_format == RasterFormat.RASTER_565:
            return ImageDecoder.bgra565(pixels, width, height)
        elif raster_format == RasterFormat.RASTER_4444:
            return ImageDecoder.bgra4444(pixels, width, height)
        elif raster_format == RasterFormat.RASTER_LUM:
            return ImageDecoder.lum8(pixels, width, height)
        elif raster_format == RasterFormat.RASTER_8888:
            return ImageDecoder.bgra8888(pixels, width, height)
        elif raster_format == RasterFormat.RASTER_888:
            return ImageDecoder.bgra888(pixels, width, height)
        elif raster_format == RasterFormat.RASTER_555:
            return ImageDecoder.bgra555(pixels, width, height)

    #######################################################
    def get_raster_format(self):
        return self.raster_format_flags & 0b1111

    #######################################################
    def get_raster_private_flags(self):
        return (self.raster_format_flags >> 4) & 0b1111

    #######################################################
    def get_raster_format_type(self):
        return (self.raster_format_flags >> 8) & 0b1111

    #######################################################
    def get_raster_auto_mipmaps(self):
        return (self.raster_format_flags >> 12) & 0b1

    #######################################################
    def get_raster_palette_type(self):
        return (self.raster_format_flags >> 13) & 0b11

    #######################################################
    def get_raster_has_mipmaps(self):
        return (self.raster_format_flags >> 15) & 0b1

    #######################################################
    def get_width(self, level=0):
        return max(self.width >> level, 1)

    #######################################################
    def get_height(self, level=0):
        return max(self.height >> level, 1)

    #######################################################
    def has_alpha(self):
        if self.platform_id == NativePlatformType.D3D9:
            return self.platform_properties.alpha != 0

        raster_format = self.get_raster_format_type()
        if raster_format in (RasterFormat.RASTER_565, RasterFormat.RASTER_LUM,
                             RasterFormat.RASTER_888, RasterFormat.RASTER_555):
            return False

        return True

    #######################################################
    def read_pixels(self, data, offset):
        pixels_len = unpack_from("<I", data, offset)[0]
        return data[offset+4:offset+4+pixels_len]

    #######################################################
    def read_palette(self, data, offset):
        palette_format = self.get_raster_palette_type()

        if palette_format != PaletteType.PALETTE_NONE:
            if palette_format == PaletteType.PALETTE_8:
                return data[offset:offset+1024]

            else:
                if self.depth == 4:
                    return data[offset:offset+64]

                return data[offset:offset+128]

        return b''

    #######################################################
    def read_platform_properties(self, data, offset):
        prop = unpack_from("<B", data, offset)[0]

        if self.platform_id == NativePlatformType.D3D8:
            PlatformProperties = namedtuple(
                "PlatformProperties",
                ["dxt_type"]
            )
            return PlatformProperties(prop)

        elif self.platform_id == NativePlatformType.D3D9:
            PlatformProperties = namedtuple(
                "PlatformProperties",
                ["alpha", "cube_texture", "auto_mipmaps", "compressed"]
            )
            return PlatformProperties(prop & 0b0001 != 0,
                                      prop & 0b0010 != 0,
                                      prop & 0b0100 != 0,
                                      prop & 0b1000 != 0)

    #######################################################
    def write_platform_properties(self):
        platform_properties = self.platform_properties
        prop = 0

        if self.platform_id == NativePlatformType.D3D8:
            if hasattr(platform_properties, 'dxt_type'):
                prop = platform_properties.dxt_type

        else:
            if hasattr(platform_properties, 'alpha') and platform_properties.alpha:
                prop |= 0b0001
            if hasattr(platform_properties, 'cube_texture') and platform_properties.cube_texture:
                prop |= 0b0010
            if hasattr(platform_properties, 'auto_mipmaps') and platform_properties.auto_mipmaps:
                prop |= 0b0100
            if hasattr(platform_properties, 'compressed') and platform_properties.compressed:
                prop |= 0b1000

        return pack('<B', prop)

    #######################################################
    def from_mem(data):

        self = TextureNative()

        pos = 0
        (
            self.platform_id, self.filter_mode, self.uv_addressing, unk, self.name,
            self.mask
        ) = unpack_from("<I2BH32s32s", data, pos)
        pos += 72

        self.name = self.name[:strlen(self.name)].decode("utf-8")
        self.mask = self.mask[:strlen(self.mask)].decode("utf-8")

        (
            self.raster_format_flags, self.d3d_format, self.width, self.height,
            self.depth, self.num_levels, self.raster_type
        ) = unpack_from("<IIHHBBB", data, pos)
        pos += 15

        self.platform_properties = self.read_platform_properties(data, pos)
        pos += 1

        self.palette = self.read_palette(data, pos)
        pos += len(self.palette)

        self.pixels = []
        for _ in range(self.num_levels):
            pixels = self.read_pixels(data, pos)
            self.pixels.append(pixels)
            pos += 4 + len(pixels)

        return self

    #######################################################
    def to_mem(self):

        data = bytearray()

        # Header: platform_id, filter_mode, uv_addressing, name(32), mask(32) = 72 bytes
        name_bytes = self.name.encode('utf-8')[:31].ljust(32, b'\0')
        mask_bytes = self.mask.encode('utf-8')[:31].ljust(32, b'\0')

        data.extend(pack('<I2B2x',
            self.platform_id,
            self.filter_mode,
            self.uv_addressing
        ))
        data.extend(name_bytes)
        data.extend(mask_bytes)

        # Raster info: format_flags, d3d_format, width, height, depth, num_levels, raster_type = 15 bytes
        data.extend(pack('<IIHHBBB',
            self.raster_format_flags,
            self.d3d_format,
            self.width,
            self.height,
            self.depth,
            self.num_levels,
            self.raster_type
        ))

        # Platform properties: 1 byte
        data.extend(self.write_platform_properties())

        # Palette data (if any)
        data.extend(self.palette)

        # Pixel data for each mipmap level
        for pixels in self.pixels:
            data.extend(pack('<I', len(pixels)))
            data.extend(pixels)

        return data

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

                if self.device_id == DeviceType.DEVICE_NONE:
                    if platform_id in (NativePlatformType.D3D8, NativePlatformType.D3D9):
                        texture = TextureNative.from_mem(
                                self.data[self.pos:self.pos+chunk.size]
                        )
                    elif platform_id == NativePlatformType.PS2FOURCC:
                        from .native_ps2 import NativePS2Texture
                        texture = NativePS2Texture.from_mem(self.data[self.pos:])
                        self._read(texture.pos - chunk.size)
                    elif platform_id == NativePlatformType.XBOX:
                        from .native_xbox import NativeXboxTexture
                        texture = NativeXboxTexture.from_mem(self.data[self.pos:])
                        self._read(texture.pos - chunk.size)
                    elif (platform_id >> 24) == NativePlatformType.GC:
                        from .native_gc import NativeGCTexture
                        texture = NativeGCTexture.from_mem(self.data[self.pos:], self.rw_version)
                        self._read(texture.pos - chunk.size)

                elif self.device_id in (DeviceType.DEVICE_D3D8, DeviceType.DEVICE_D3D9):
                    texture = TextureNative.from_mem(
                            self.data[self.pos:self.pos+chunk.size]
                    )

                elif self.device_id == DeviceType.DEVICE_PS2:
                    from .native_ps2 import NativePS2Texture
                    texture = NativePS2Texture.from_mem(self.data[self.pos:])
                    self._read(texture.pos - chunk.size)

                elif self.device_id == DeviceType.DEVICE_GC:
                    from .native_gc import NativeGCTexture
                    texture = NativeGCTexture.from_mem(self.data[self.pos:], self.rw_version)
                    self._read(texture.pos - chunk.size)

                elif self.device_id == DeviceType.DEVICE_PSP:
                    from .native_psp import NativePSPTexture
                    texture = NativePSPTexture.from_mem(self.data[self.pos:])
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
                self.device_id = text_dict.device_id

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
        self.rw_version = Sections.get_rw_version(chunk.version)

        if chunk.type == types["Texture Dictionary"]:
            self.read_texture_dictionary(chunk)
        elif chunk.type == types["PI Texture Dictionary"]:
            self.read_pi_texture_dictionary(chunk)

    #######################################################
    def clear(self):
        self.native_textures = []
        self.textures        = []
        self.images          = []
        self.pos             = 0
        self.data            = ""
        self.rw_version      = ""
        self.device_id       = DeviceType.DEVICE_NONE

    #######################################################
    def load_file(self, filename):

        with open(filename, mode='rb') as file:
            content = file.read()
            self.load_memory(content)

    #######################################################
    def write_native_texture(self, texture):

        data = Sections.write_chunk(texture.to_mem(), types["Struct"])
        data += Sections.write_chunk(bytearray(), types["Extension"])

        return Sections.write_chunk(data, types["Texture Native"])

    #######################################################
    def write_texture_dictionary(self):

        data = Sections.write(TexDict, (len(self.native_textures), self.device_id), types["Struct"])

        for texture in self.native_textures:
            data += self.write_native_texture(texture)

        data += Sections.write_chunk(bytearray(), types["Extension"])

        return Sections.write_chunk(data, types["Texture Dictionary"])

    #######################################################
    def write_memory(self, version):

        data = bytearray()
        Sections.set_library_id(version, 0xFFFF)

        data += self.write_texture_dictionary()

        return data

    #######################################################
    def write_file(self, filename, version):

        with open(filename, mode='wb') as file:
            content = self.write_memory(version)
            file.write(content)

    #######################################################
    def __init__(self):
        self.clear()

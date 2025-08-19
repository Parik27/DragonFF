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

import bpy
import os
import struct
from mathutils import Vector

from ..gtaLib import txd
from ..gtaLib.dff import Sections, Chunk, TexDict, PITexDict, Texture
from ..gtaLib.dff import types, NativePlatformType
from ..gtaLib.dff import strlen

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
class txd_exporter:

    mass_export = False
    export_version = "3.6.0.3"

    __slots__ = [
        'txd',
        'file_name'
    ]

    #######################################################
    def _init():
        self = txd_exporter
        
        self.txd = None
        self.file_name = ""

    #######################################################
    def _create_texture_native_from_image(image_name, image):
        pixels = list(image.pixels)
        width = image.size[0]
        height = image.size[1]
        
        rgba_data = []
        for i in range(len(pixels)):
            rgba_data.append(int(pixels[i] * 255))
        
        texture_native = txd.TextureNative()
        texture_native.platform_id = NativePlatformType.D3D9
        texture_native.filter_mode = 1
        texture_native.uv_addressing = 0x1111
        texture_native.name = image_name
        texture_native.mask = ""
        texture_native.raster_format_flags = 0x0500
        texture_native.d3d_format = txd.D3DFormat.D3D_8888
        texture_native.width = width
        texture_native.height = height
        texture_native.depth = 32
        texture_native.num_levels = 1
        texture_native.raster_type = 4
        
        texture_native.platform_properties = type('PlatformProperties', (), {
            'alpha': True,
            'cube_texture': False,
            'auto_mipmaps': False,
            'compressed': False
        })()
        
        pixel_data = ImageEncoder.rgba_to_bgra8888(bytes(rgba_data))
        texture_native.pixels = [pixel_data]
        
        return texture_native

    #######################################################
    def export_textures():
        self = txd_exporter
        
        for image in bpy.data.images:
            if image.name.startswith("//"):
                continue
            
            texture_native = txd_exporter._create_texture_native_from_image(
                image.name, image
            )
            self.txd.native_textures.append(texture_native)

    #######################################################
    def write_texture_native(texture_native):
        data = bytearray()
        
        name_bytes = texture_native.name.encode('utf-8').ljust(32, b'\0')
        mask_bytes = texture_native.mask.encode('utf-8').ljust(32, b'\0')
        
        data.extend(struct.pack('<IHH32s32s',
            texture_native.platform_id,
            texture_native.filter_mode,
            texture_native.uv_addressing,
            name_bytes[:32],
            mask_bytes[:32]
        ))
        
        data.extend(struct.pack('<IIHHBBB',
            texture_native.raster_format_flags,
            texture_native.d3d_format,
            texture_native.width,
            texture_native.height,
            texture_native.depth,
            texture_native.num_levels,
            texture_native.raster_type
        ))
        
        platform_prop = 0
        if hasattr(texture_native.platform_properties, 'alpha') and texture_native.platform_properties.alpha:
            platform_prop |= 0x01
        if hasattr(texture_native.platform_properties, 'cube_texture') and texture_native.platform_properties.cube_texture:
            platform_prop |= 0x02
        if hasattr(texture_native.platform_properties, 'auto_mipmaps') and texture_native.platform_properties.auto_mipmaps:
            platform_prop |= 0x04
        if hasattr(texture_native.platform_properties, 'compressed') and texture_native.platform_properties.compressed:
            platform_prop |= 0x08
            
        data.extend(struct.pack('<B', platform_prop))
        
        data.extend(texture_native.palette)
        
        for pixels in texture_native.pixels:
            data.extend(struct.pack('<I', len(pixels)))
            data.extend(pixels)
        
        return bytes(data)

    #######################################################
    def write_txd():
        self = txd_exporter
        
        data = bytearray()
        
        tex_count = len(self.txd.native_textures)
        device_id = txd.DeviceType.DEVICE_D3D9
        
        tex_dict_data = struct.pack('<HH', tex_count, device_id)
        
        tex_dict_chunk = Chunk()
        tex_dict_chunk.type = types["Struct"]
        tex_dict_chunk.size = len(tex_dict_data)
        tex_dict_chunk.version = 0x1803FFFF
        
        textures_data = bytearray()
        
        for texture_native in self.txd.native_textures:
            texture_data = txd_exporter.write_texture_native(texture_native)
            
            struct_chunk = Chunk()
            struct_chunk.type = types["Struct"]
            struct_chunk.size = len(texture_data)
            struct_chunk.version = 0x1803FFFF
            
            ext_chunk = Chunk()
            ext_chunk.type = types["Extension"]
            ext_chunk.size = 0
            ext_chunk.version = 0x1803FFFF
            
            native_chunk = Chunk()
            native_chunk.type = types["Texture Native"]
            native_chunk.size = struct_chunk.size + ext_chunk.size + 24
            native_chunk.version = 0x1803FFFF
            
            textures_data.extend(struct.pack('<III', native_chunk.type, native_chunk.size, native_chunk.version))
            textures_data.extend(struct.pack('<III', struct_chunk.type, struct_chunk.size, struct_chunk.version))
            textures_data.extend(texture_data)
            textures_data.extend(struct.pack('<III', ext_chunk.type, ext_chunk.size, ext_chunk.version))
        
        root_chunk = Chunk()
        root_chunk.type = types["Texture Dictionary"]
        root_chunk.size = len(tex_dict_data) + len(textures_data) + 12
        root_chunk.version = 0x1803FFFF
        
        data.extend(struct.pack('<III', root_chunk.type, root_chunk.size, root_chunk.version))
        data.extend(struct.pack('<III', tex_dict_chunk.type, tex_dict_chunk.size, tex_dict_chunk.version))
        data.extend(tex_dict_data)
        data.extend(textures_data)
        
        return bytes(data)

    #######################################################
    def export_txd(file_name):
        self = txd_exporter
        self._init()
        
        self.txd = txd.txd()
        self.file_name = file_name
        
        self.export_textures()
        
        data = self.write_txd()
        
        with open(file_name, 'wb') as f:
            f.write(data)

#######################################################
def export_txd(options):
    
    txd_exporter.mass_export = options.get('mass_export', False)
    txd_exporter.export_version = options.get('export_version', "3.6.0.3")
    
    if txd_exporter.mass_export:
        for obj in bpy.context.selected_objects:
            if obj.name.endswith('.txd'):
                file_name = os.path.join(options['directory'], obj.name)
                txd_exporter.export_txd(file_name)
    else:
        txd_exporter.export_txd(options['file_name'])
    
    return txd_exporter
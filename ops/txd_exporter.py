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
import re
from mathutils import Vector

from ..gtaLib import txd
from ..gtaLib.txd import ImageEncoder
from ..gtaLib.dff import Sections, Chunk, TexDict, PITexDict, Texture
from ..gtaLib.dff import types, NativePlatformType
from ..gtaLib.dff import strlen

#######################################################
class txd_exporter:

    mass_export = False
    only_used_textures = False

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
        texture_native.filter_mode = 0x06  # Linear Mip Linear (Trilinear)
        texture_native.uv_addressing = 0x1111  # Wrap for both U and V
        
        # Clean texture name - remove invalid characters and limit length
        clean_name = "".join(c for c in image_name if c.isalnum() or c in "_-.")
        clean_name = clean_name[:31]  # Limit to 31 chars (32 with null terminator)
        if not clean_name:
            clean_name = "texture"
        texture_native.name = clean_name
        texture_native.mask = ""
        
        # Raster format flags for RGBA8888: format type (8888=5) at bit 8-11, no mipmaps, no palette
        texture_native.raster_format_flags = (txd.RasterFormat.RASTER_8888 << 8) | 0x05
        texture_native.d3d_format = txd.D3DFormat.D3D_8888
        texture_native.width = width
        texture_native.height = height
        texture_native.depth = 32
        texture_native.num_levels = 1
        texture_native.raster_type = 4  # Texture
        
        texture_native.platform_properties = type('PlatformProperties', (), {
            'alpha': True,
            'cube_texture': False,
            'auto_mipmaps': False,
            'compressed': False
        })()
        
        # No palette for RGBA8888 format
        texture_native.palette = b''
        
        # Convert RGBA to BGRA8888 format
        pixel_data = ImageEncoder.rgba_to_bgra8888(bytes(rgba_data))
        texture_native.pixels = [pixel_data]
        
        return texture_native

    #######################################################
    def extract_texture_name(image_name):
        """Extract texture name from TXD import naming pattern"""
        pattern = r'^[^/]+\.txd/([^/]+)/\d+$'
        match = re.match(pattern, image_name)
        return match.group(1) if match else image_name

    #######################################################
    def get_used_texture_names(objects_to_scan=None):
        """Collect texture names that are used in scene materials based on node.label"""
        used_textures = set()
        
        # Use provided objects or all scene objects
        objects = objects_to_scan if objects_to_scan is not None else bpy.context.scene.objects
        
        for obj in objects:
            for mat_slot in obj.material_slots:
                mat = mat_slot.material
                if not mat:
                    continue

                node_tree = mat.node_tree
                if not node_tree:
                    continue

                for node in node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.label:
                        # Extract texture name from node.label (in case it follows TXD naming pattern)
                        texture_name = txd_exporter.extract_texture_name(node.label.strip())
                        used_textures.add(texture_name)
        
        return used_textures

    #######################################################
    def export_textures(objects_to_scan=None):
        self = txd_exporter
        
        # Determine which textures to export based on context
        if objects_to_scan is not None:
            # Mass export mode: only export textures used by specific objects
            used_textures = txd_exporter.get_used_texture_names(objects_to_scan)
        elif hasattr(self, 'only_used_textures') and self.only_used_textures:
            # Single export with "only used textures" option
            used_textures = txd_exporter.get_used_texture_names()
        else:
            # Single export, all textures
            used_textures = None
        
        for image in bpy.data.images:
            # Skip invalid/system textures
            if (image.name.startswith("//") or 
                image.name in ["Render Result", "Viewer Node"] or
                not image.name.strip() or
                image.size[0] == 0 or image.size[1] == 0):
                continue
            
            # Skip images without pixel data
            if not hasattr(image, 'pixels') or len(image.pixels) == 0:
                continue
            
            # If we have a used_textures filter, check if this texture is used
            if used_textures is not None:
                # Extract texture name from image name (handles TXD import naming pattern)
                image_texture_name = txd_exporter.extract_texture_name(image.name)
                if image_texture_name not in used_textures:
                    continue
                
            texture_native = txd_exporter._create_texture_native_from_image(
                image.name, image
            )
            self.txd.native_textures.append(texture_native)

    #######################################################
    def write_texture_native(texture_native):
        data = bytearray()
        
        # Header: platform_id, filter_mode, uv_addressing, name(32), mask(32) = 72 bytes
        name_bytes = texture_native.name.encode('utf-8')[:31].ljust(32, b'\0')
        mask_bytes = texture_native.mask.encode('utf-8')[:31].ljust(32, b'\0')
        
        data.extend(struct.pack('<IHH',
            texture_native.platform_id,
            texture_native.filter_mode,
            texture_native.uv_addressing
        ))
        data.extend(name_bytes)
        data.extend(mask_bytes)
        
        # Raster info: format_flags, d3d_format, width, height, depth, num_levels, raster_type = 15 bytes  
        data.extend(struct.pack('<IIHHBBB',
            texture_native.raster_format_flags,
            texture_native.d3d_format,
            texture_native.width,
            texture_native.height,
            texture_native.depth,
            texture_native.num_levels,
            texture_native.raster_type
        ))
        
        # Platform properties: 1 byte
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
        
        # Palette data (if any)
        data.extend(texture_native.palette)
        
        # Pixel data for each mipmap level
        for pixels in texture_native.pixels:
            data.extend(struct.pack('<I', len(pixels)))
            data.extend(pixels)
        
        return bytes(data)

    #######################################################
    def write_txd():
        self = txd_exporter
        
        tex_count = len(self.txd.native_textures)
        device_id = txd.DeviceType.DEVICE_D3D9
        
        # Write texture dictionary struct data
        tex_dict_data = struct.pack('<HH', tex_count, device_id)
        
        # Write texture natives
        textures_data = bytearray()
        
        for texture_native in self.txd.native_textures:
            texture_data = txd_exporter.write_texture_native(texture_native)
            
            # Write Texture Native chunk
            native_size = len(texture_data) + 12  # struct chunk header size
            textures_data.extend(struct.pack('<III', 
                types["Texture Native"], 
                native_size, 
                0x1803FFFF
            ))
            
            # Write Struct chunk 
            textures_data.extend(struct.pack('<III',
                types["Struct"],
                len(texture_data),
                0x1803FFFF
            ))
            
            # Write texture data
            textures_data.extend(texture_data)
            
            # Write Extension chunk (empty)
            textures_data.extend(struct.pack('<III',
                types["Extension"],
                0,
                0x1803FFFF
            ))
        
        # Calculate total size
        struct_size = len(tex_dict_data)
        total_size = struct_size + len(textures_data) + 12  # +12 for struct chunk header
        
        # Write final TXD data
        data = bytearray()
        
        # Root Texture Dictionary chunk
        data.extend(struct.pack('<III',
            types["Texture Dictionary"],
            total_size,
            0x1803FFFF
        ))
        
        # Struct chunk containing dictionary data
        data.extend(struct.pack('<III',
            types["Struct"],
            struct_size,
            0x1803FFFF
        ))
        
        # Dictionary data
        data.extend(tex_dict_data)
        
        # Texture natives
        data.extend(textures_data)
        
        return bytes(data)

    #######################################################
    def export_txd(file_name, objects_to_scan=None):
        self = txd_exporter
        self._init()
        
        self.txd = txd.txd()
        self.file_name = file_name
        
        self.export_textures(objects_to_scan)
        
        data = self.write_txd()
        
        with open(file_name, 'wb') as f:
            f.write(data)

#######################################################
def export_txd(options):
    
    txd_exporter.mass_export = options.get('mass_export', False)
    txd_exporter.only_used_textures = options.get('only_used_textures', False)
    
    if txd_exporter.mass_export:
        # Export TXD files per selected object
        selected_objects = bpy.context.selected_objects
        
        if not selected_objects:
            print("No objects selected for mass export, exporting all textures to single file")
            txd_exporter.export_txd(options['file_name'])
            return txd_exporter
        
        for obj in selected_objects:
            # Only export for objects that have materials
            if obj.material_slots:
                # Create filename based on object name
                safe_name = "".join(c for c in obj.name if c.isalnum() or c in "_-.")
                file_name = os.path.join(options['directory'], f"{safe_name}.txd")
                print(f"Exporting textures for object '{obj.name}' to {file_name}")
                
                # Export textures used by this specific object only
                txd_exporter.export_txd(file_name, [obj])
        
        print(f"Mass export completed for {len([obj for obj in selected_objects if obj.material_slots])} objects")
    else:
        txd_exporter.export_txd(options['file_name'])
    
    return txd_exporter
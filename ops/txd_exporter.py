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

from .exporter_common import (
    clear_extension, extract_texture_info_from_name)

from ..gtaLib import txd
from ..gtaLib.txd import ImageEncoder
from ..gtaLib.dff import NativePlatformType

#######################################################
class txd_exporter:

    mass_export = False
    only_used_textures = True
    has_mipmaps = False
    version = None
    file_name = ""
    path = ""
    txd = None

    #######################################################
    @staticmethod
    def _create_texture_native_from_image(image, image_name):
        pixels = list(image.pixels)
        width, height = image.size

        rgba_data = bytearray()
        for h in range(height - 1, -1, -1):
            offset = h * width * 4
            row_pixels = pixels[offset:offset + width * 4]
            rgba_data.extend(int(round(p * 0xff)) for p in row_pixels)

        texture_native = txd.TextureNative()
        texture_native.platform_id = NativePlatformType.D3D9
        texture_native.filter_mode = 0x06  # Linear Mip Linear (Trilinear)
        texture_native.uv_addressing = 0b00010001  # Wrap for both U and V
        
        # Clean texture name - remove invalid characters and limit length
        clean_name = "".join(c for c in image_name if c.isalnum() or c in "_-.")
        clean_name = clean_name[:31]  # Limit to 31 chars (32 with null terminator)
        if not clean_name:
            clean_name = "texture"
        texture_native.name = clean_name
        texture_native.mask = ""
        
        # Raster format flags for RGBA8888: format type (8888=5) at bit 8-11, no mipmaps, no palette
        texture_native.raster_format_flags = txd.RasterFormat.RASTER_8888 << 8
        texture_native.d3d_format = txd_exporter.get_d3d_from_raster(texture_native.get_raster_format_type())
        texture_native.width = width
        texture_native.height = height
        texture_native.depth = txd_exporter.get_depth_from_raster(texture_native.get_raster_format_type())
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

        # Generate mipmaps
        if txd_exporter.has_mipmaps:
            mip_levels = txd_exporter.generate_mipmaps(rgba_data, width, height)
            texture_native.raster_format_flags |= (1 << 15)  # has_mipmaps
        else:
            mip_levels = [(width, height, rgba_data)]

        texture_native.num_levels = len(mip_levels)

        encoder = txd_exporter.get_encoder_from_raster(texture_native.get_raster_format_type())

        # Convert and pad each level
        texture_native.pixels = [
            txd_exporter.pad_mipmap_level(
                encoder(level_data),
                mip_width,
                mip_height,
                texture_native.depth
            )
            for mip_width, mip_height, level_data in mip_levels
        ]

        return texture_native

    ########################################################
    @staticmethod
    def get_encoder_from_raster(raster_format):
        return {
            txd.RasterFormat.RASTER_8888: ImageEncoder.rgba_to_bgra8888,
            txd.RasterFormat.RASTER_888:  ImageEncoder.rgba_to_bgra888,
            txd.RasterFormat.RASTER_4444: ImageEncoder.rgba_to_rgba4444,
            txd.RasterFormat.RASTER_1555: ImageEncoder.rgba_to_rgba1555,
            txd.RasterFormat.RASTER_565:  ImageEncoder.rgba_to_rgb565,
            txd.RasterFormat.RASTER_555:  ImageEncoder.rgba_to_rgb555,
            txd.RasterFormat.RASTER_LUM:  ImageEncoder.rgba_to_lum8,
        }.get(raster_format, None)

    #######################################################
    @staticmethod
    def get_depth_from_raster(raster_format):
        return {
            txd.RasterFormat.RASTER_8888: 32,
            txd.RasterFormat.RASTER_888:  24,
            txd.RasterFormat.RASTER_4444: 16,
            txd.RasterFormat.RASTER_1555: 16,
            txd.RasterFormat.RASTER_565:  16,
            txd.RasterFormat.RASTER_555:  16,
            txd.RasterFormat.RASTER_LUM:   8,
        }.get(raster_format, 0)

    #######################################################
    @staticmethod
    def get_d3d_from_raster(raster_format):
        return {
            txd.RasterFormat.RASTER_8888: txd.D3DFormat.D3D_8888,
            txd.RasterFormat.RASTER_888:  txd.D3DFormat.D3D_888,
            txd.RasterFormat.RASTER_4444: txd.D3DFormat.D3D_4444,
            txd.RasterFormat.RASTER_1555: txd.D3DFormat.D3D_1555,
            txd.RasterFormat.RASTER_565:  txd.D3DFormat.D3D_565,
            txd.RasterFormat.RASTER_555:  txd.D3DFormat.D3D_555,
            txd.RasterFormat.RASTER_LUM:  txd.D3DFormat.D3DFMT_L8,
        }.get(raster_format, 0)

    #######################################################
    @staticmethod
    def pad_mipmap_level(pixel_data, width, height, depth):
        # Calculate D3D9-aligned row size
        row_bytes = (width * depth + 7) // 8
        row_size = ((row_bytes + 3) // 4) * 4
        aligned_size = row_size * height
        
        if len(pixel_data) < aligned_size:
            padded = bytearray(pixel_data)
            padded.extend(b'\x00' * (aligned_size - len(pixel_data)))
            return bytes(padded)
        
        return pixel_data

    #######################################################
    @staticmethod
    def generate_mipmaps(rgba_data, width, height):
        # Generates full mipmap chain including 1x1 similar to how magictxd does it with 2x2 box filter, edge clamp, float averaging + round to nearest
        mipmaps = [(width, height, rgba_data)]
      
        current_width = width
        current_height = height
        current_data = rgba_data
      
        while current_width > 1 or current_height > 1:
            new_width = max(1, current_width // 2)
            new_height = max(1, current_height // 2)
          
            new_data = bytearray(new_width * new_height * 4)
          
            for y in range(new_height):
                for x in range(new_width):
                    r_sum = g_sum = b_sum = a_sum = 0.0
                    for dy in range(2):
                        sy = min(y * 2 + dy, current_height - 1)
                        row_offset = sy * current_width * 4
                        for dx in range(2):
                            sx = min(x * 2 + dx, current_width - 1)
                            offset = row_offset + sx * 4
                          
                            r_sum += current_data[offset]
                            g_sum += current_data[offset + 1]
                            b_sum += current_data[offset + 2]
                            a_sum += current_data[offset + 3]
                    avg_r = round(r_sum / 4.0)
                    avg_g = round(g_sum / 4.0)
                    avg_b = round(b_sum / 4.0)
                    avg_a = round(a_sum / 4.0)
                  
                    out_offset = (y * new_width + x) * 4
                    new_data[out_offset] = int(avg_r)
                    new_data[out_offset + 1] = int(avg_g)
                    new_data[out_offset + 2] = int(avg_b)
                    new_data[out_offset + 3] = int(avg_a)
          
            mip_data = bytes(new_data)
            mipmaps.append((new_width, new_height, mip_data))
          
            current_width = new_width
            current_height = new_height
            current_data = mip_data
      
        return mipmaps

    #######################################################
    @staticmethod
    def get_used_textures(objects_to_scan=None):
        """Collect textures that are used in scene materials"""
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
                    if node.type == 'TEX_IMAGE':
                        texture_name = clear_extension(node.label or node.image.name)
                        used_textures.add((texture_name, node.image))

        return used_textures

    #######################################################
    @staticmethod
    def populate_textures(objects_to_scan=None):
        self = txd_exporter

        self.txd.native_textures = []

        # Determine which textures to export based on context
        if objects_to_scan is not None:
            # Mass export mode: only export textures used by specific objects
            used_textures = self.get_used_textures(objects_to_scan)
        elif self.only_used_textures:
            # Single export with "only used textures" option
            used_textures = self.get_used_textures()
        else:
            # Single export, all textures
            used_textures = set()
            for image in bpy.data.images:
                # Skip invalid/system textures
                if (image.name.startswith("//") or
                    image.name in ["Render Result", "Viewer Node"] or
                    not image.name.strip() or
                    image.size[0] == 0 or image.size[1] == 0):
                    continue

                # Extract texture name from node.label (in case it follows TXD naming pattern)
                texture_name, mipmap_level = extract_texture_info_from_name(image.name)

                # Skip mipmaps
                if mipmap_level > 0:
                    continue

                texture_name = clear_extension(texture_name)
                used_textures.add((texture_name, image))

        for texture_name, image in used_textures:
            # Skip images without pixel data
            if not hasattr(image, 'pixels') or len(image.pixels) == 0:
                continue

            texture_native = txd_exporter._create_texture_native_from_image(
                image, texture_name
            )
            self.txd.native_textures.append(texture_native)

    #######################################################
    @staticmethod
    def export_textures(objects_to_scan=None, file_name=None):
        self = txd_exporter

        self.txd = txd.txd()
        self.txd.device_id = txd.DeviceType.DEVICE_D3D9

        self.populate_textures(objects_to_scan)
        self.txd.write_file(file_name or self.file_name, self.version)

    #######################################################
    @staticmethod
    def export_txd(file_name):
        self = txd_exporter

        self.file_name = file_name

        if self.mass_export:
            # Export TXD files per selected object
            selected_objects = bpy.context.selected_objects

            if not selected_objects:
                print("No objects selected for mass export, exporting all textures to single file")
                self.export_textures()
                return

            selected_objects_num = 0

            for obj in bpy.context.selected_objects:
                # Only export for objects that have materials
                if not obj.material_slots:
                    continue

                # Create filename based on object name
                safe_name = "".join(c for c in obj.name if c.isalnum() or c in "_-.")
                file_name = os.path.join(self.path, f"{safe_name}.txd")
                print(f"Exporting textures for object '{obj.name}' to {file_name}")

                # Export textures used by this specific object only
                self.export_txd([obj], file_name)
                selected_objects_num += 1

            print(f"Mass export completed for {selected_objects_num} objects")

        else:
            self.export_textures()

#######################################################
def export_txd(options):

    txd_exporter.mass_export        = options.get('mass_export', False)
    txd_exporter.only_used_textures = options.get('only_used_textures', True)
    txd_exporter.version            = options.get('version', 0x36003)

    txd_exporter.path               = options['directory']

    txd_exporter.export_txd(options['file_name'])

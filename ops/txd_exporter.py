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
        pixel_data = ImageEncoder.rgba_to_bgra8888(rgba_data)
        texture_native.pixels = [pixel_data]
        
        return texture_native

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
                self.export_textures([obj], file_name)
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

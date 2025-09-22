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

from ..gtaLib import txd

#######################################################
class txd_importer:

    skip_mipmaps = True
    pack = True

    __slots__ = [
        'txd',
        'images',
        'file_name'
    ]

    #######################################################
    def _init():
        self = txd_importer

        # Variables
        self.txd = None
        self.images = {}
        self.file_name = ""

    #######################################################
    def _create_image(name, rgba, width, height, pack=False):
        pixels = []
        for h in range(height - 1, -1, -1):
            offset = h * width * 4
            pixels += list(map(lambda b: b / 0xff, rgba[offset:offset+width*4]))

        image = bpy.data.images.new(name, width, height, alpha=True)
        image.pixels = pixels

        if pack:
            image.pack()

        return image

    #######################################################
    def import_textures():
        self = txd_importer

        txd_name = os.path.basename(self.file_name).lower()

        # Import native textures
        for tex in self.txd.native_textures:
            images = []
            num_levels = tex.num_levels if not self.skip_mipmaps else 1

            for level in range(num_levels):
                image_name = "%s/%s/%d" % (txd_name, tex.name, level)
                image = bpy.data.images.get(image_name)
                if not image:
                    image = txd_importer._create_image(image_name,
                                                        tex.to_rgba(level),
                                                        tex.get_width(level),
                                                        tex.get_height(level),
                                                        self.pack)
                images.append(image)

            self.images[tex.name] = images

        # Import textures
        for tex, imgs in zip(self.txd.textures, self.txd.images):
            images = []
            num_levels = len(imgs) if not self.skip_mipmaps else 1

            for level in range(num_levels):
                img = imgs[level]
                image_name = "%s/%s/%d" % (txd_name, tex.name, level)
                image = txd_importer._create_image(image_name,
                                                    img.to_rgba(),
                                                    img.width,
                                                    img.height,
                                                    self.pack)
                images.append(image)

            self.images[tex.name] = images

    #######################################################
    def import_txd(file_name):
        self = txd_importer
        self._init()

        self.txd = txd.txd()
        self.txd.load_file(file_name)
        self.file_name = file_name

        self.import_textures()

#######################################################
def import_txd(options):

    txd_importer.skip_mipmaps = options['skip_mipmaps']
    txd_importer.pack = options['pack']

    txd_importer.import_txd(options['file_name'])

    return txd_importer

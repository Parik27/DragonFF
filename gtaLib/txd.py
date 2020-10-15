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
from collections import namedtuple

class TextureNative:

    # Header
    _platformId = 0
    _filterMode = 0

    uAddressing = 0
    vAddressing = 0

    name = ""
    mask = ""

    format = []
    width = 0
    height = 0
    depth = 0
    numLevels = 0
    rasterType = 0

    image_properties = None

    # Palette
    hasPalette = False
    palette = []

    # Raster Data
    _data = []

    #######################################################
    def read_image_properties(platformId, data, offset):

        ImageProperties = namedtuple(
            "ImageProperties",
            "alpha", "cubeTexture", "autoMipMaps", "compressed", "compression"
        )

        # San Andreas
        if platformId == 9:

            props = unpack_from("<I4x", data, offset)
            return ImageProperties(props[0] & 0b0001 != 0,
                                   props[0] & 0b0010 != 0,
                                   props[0] & 0b0100 != 0,
                                   props[0] & 0b1000 != 0
                                   -1)

        # Vice City, GTA 3
        elif platformId == 8:

            compression = unpack_from("<B", data, offset)
            return ImageProperties(False, False, False, False, compression)
    
    #######################################################
    def _from_mem_pc(self, data):

        TextureFormat = namedtuple(
            "Header",
            [
                'platformId' , 'filterMode' , 'uvAddressing' ,
                'name'       , 'maskName']
        )

        RasterFormat  = namedtuple(
            "RasterFormat",
            [
                'rasterFormat' , 'sa_format_3vc_hasAlpha'   , 'width'     ,
                'height'       ,  'depth'                   , 'numLevels' ,
                'rasterType'   , 'image_properties'
            ]
        )

        pos = 0
        tex_format = TextureFormat._make(unpack_from("<IHH16x32s32s", data, pos))
        pos += 88

        (
            self._platformId, self._filterMode, self.uAddressing, self.name,
            self.mask
        ) = tex_format

        self.name = self.name.decode('ascii')
        self.mask = self.mask.decode('ascii')

        
        raster_format = RasterFormat(
            *unpack_from("<IIHHbbb", pos),
            self.read_image_properties(data, pos + 15)
        )
    
    #######################################################
    def from_mem(data):

        self = TextureNative()
        platformId = unpack_from("<I", data)[0]
        
        if platformId == 8 or platformId == 9 or platformId == 5:
            self._from_mem_pc(data)
    
    pass

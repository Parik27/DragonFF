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

import re

#######################################################
def clear_extension(string):
    k = string.rfind('.')
    return string if k < 0 else string[:k]

#######################################################
def clear_numeric_suffix(string):
    """Drop the ".001"-style suffix Blender adds to duplicate datablocks"""
    return re.sub(r'\.\d{3}$', '', string)

#######################################################
def extract_texture_info_from_name(name):
    """Extract texture info from TXD import naming pattern"""
    pattern = r'^[^/]+\.txd/([^/]+)/(\d+)$'
    match = re.match(pattern, name)
    if match:
        return match.group(1), int(match.group(2))
    else:
        return name, 0

#######################################################
def texture_name_from_image_name(image_name):
    """Texture name to write to the DFF for a Blender image name"""
    image_name = clear_numeric_suffix(image_name)
    texture_name, _ = extract_texture_info_from_name(image_name)
    return clear_extension(texture_name)

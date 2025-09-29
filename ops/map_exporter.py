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

from dataclasses import fields

from ..gtaLib.map_format_types import MapSection
from ..gtaLib.map_formats import MAP_SECTION_TYPES

class MapFileExporter:
    def __init__ (self, objects, options = {}):
        self.objects = objects
        self.options = options

    def get_section_class_from_name (self, name) -> type[MapSection]:
        for section_type in MAP_SECTION_TYPES:
            if section_type.get_name() == name:
                return section_type
        return None

    def export_object (self, obj):
        section_name = obj.dff.map_props.section
        section_type = self.get_section_class_from_name (section_name)
        current_format = obj.dff.map_props.current_format

        section_props = getattr (obj.dff.map_props, section_name.lower() + "_data")
        kwargs = {}
        for field in fields(section_type):
            kwargs[field.name] = getattr (section_props, field.name, field.default)

        section_data = section_type (**kwargs)

        rotation = obj.matrix_local.to_3x3().transposed().to_quaternion()
        section_data.set_location (obj.location)
        section_data.set_rotation ((rotation.x, rotation.y, rotation.z, rotation.w))
        section_data.set_scale (obj.scale)

        return (current_format, section_data)

    def perform_export (self):
        entries = []
        for obj in self.objects:
            if obj.dff.type != "MAP":
                continue

            entries.append (self.export_object (obj))

        return entries

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

class MapFileExporter:
    def __init__ (self, objects, target_game, target_exporter, options = {}):
        self.objects = objects
        self.target_game = target_game
        self.target_exporter = target_exporter
        self.options = {}
        self.messages = []

    def export_object (self, obj):
        current_format = obj.dff.map_props.current_format
        section_data = obj.dff.map_props.to_section_object ()

        if not section_data:
            return None

        rotation = obj.matrix_local.to_3x3().transposed().to_quaternion()
        section_data.set_location (obj.location)
        section_data.set_rotation ((rotation.x, rotation.y, rotation.z, rotation.w))
        section_data.set_scale (obj.scale)

        best_format = section_data.choose_best_format_for_game (self.target_exporter,
                                                                self.target_game,
                                                                current_format)

        if best_format is None:
            return None

        return (best_format, section_data)

    def perform_export (self):
        entries = []
        for obj in self.objects:
            if obj.dff.type != "MAP":
                continue

            exported_object = self.export_object (obj)
            if exported_object is not None:
                entries.append (exported_object)
            else:
                self.messages.append (
                    ("ERROR", f"No exportable format found for {obj.name}")
                )

        return entries

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
import bpy
import os

from ..ops.importer_common import create_collection, link_object

#######################################################
class MapFileImporter:
    def __init__(self, entries):
        self.entries = entries
        self.collection = None

    def import_entry (self, entry):
        entry_obj = bpy.data.objects.new(name=str(entry), object_data=None)
        entry_obj.dff.type = 'MAP'

        section_format, section_data = entry
        section_name = section_data.get_name()
        entry_obj.dff.map_props.section = section_name
        entry_obj.dff.map_props.current_format = section_format
        entry_obj.location = section_data.get_location ()
        entry_obj.rotation_quaternion = section_data.get_rotation ()
        entry_obj.scale = section_data.get_scale ()

        section_props = getattr(entry_obj.dff.map_props, section_name.lower() + "_data")
        for field in fields(section_data):
            setattr(section_props, field.name, getattr(section_data, field.name))

        link_object (entry_obj, self.collection)
        pass

    def perform_import (self, options):
        collection = create_collection (options['collection_name'])
        self.collection = collection

        for entry in self.entries:
            self.import_entry (entry)

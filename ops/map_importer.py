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

from ..gtaLib.img import img
from ..gtaLib.dff import dff

from . import dff_importer

from ..gtaLib.map import MapFileText

from ..gtaLib.map_format_types import MapSection

from ..ops.importer_common import create_collection, link_object

#######################################################
class MapFileImporter:
    def __init__(self, entries):
        self.entries = entries
        self.imported_objects = []
        self.collection = None

    def find_dependency_collection (self, dependency):
        for coll in bpy.data.collections:
            if coll.name.lower() == dependency.lower():
                return coll
        return None

    def import_entry (self, entry : tuple[str, MapSection]):
        entry_obj = bpy.data.objects.new(name=str(entry), object_data=None)
        entry_obj.dff.type = 'MAP'

        section_format, section_data = entry
        section_name = section_data.get_name()
        entry_obj.dff.map_props.section = section_name
        entry_obj.dff.map_props.current_format = section_format
        entry_obj.location = section_data.get_location ()

        entry_obj.rotation_mode = 'QUATERNION'
        rotation = section_data.get_rotation ()
        entry_obj.rotation_quaternion.x = rotation[0]
        entry_obj.rotation_quaternion.y = rotation[1]
        entry_obj.rotation_quaternion.z = rotation[2]
        entry_obj.rotation_quaternion.w = -rotation[3]

        entry_obj.scale = section_data.get_scale ()

        entry_obj.dff.map_props.read_from_section_object (section_data)

        # Put into collection for instancing purposes
        entry_collection_name = section_data.get_collection_name ()
        if entry_collection_name is not None:
            entry_collection = create_collection (entry_collection_name, False)
            entry_collection.objects.link (entry_obj)
            self.collection.children.link (entry_collection)
        else:
            link_object (entry_obj, self.collection)

        self.imported_objects.append ((section_data, entry_obj))

    def set_object_instancing (self, entry : MapSection, obj):
        for link in entry.get_linked_entries ():
            collection = self.find_dependency_collection (link)

            if collection:
                obj.instance_type = 'COLLECTION'
                obj.instance_collection = collection
        pass

    def get_instancing_dependencies (self):
        dependencies = []
        for entry, _ in self.imported_objects:
            dependencies.extend(filter(lambda x: ".dff" in x, entry.get_linked_entries ()))

        return set(dependencies)

    def perform_instancing (self):
        for entry, obj in self.imported_objects:
            self.set_object_instancing (entry, obj)

    def perform_import (self, options):
        collection = create_collection (options['collection_name'])
        self.collection = collection

        for entry in self.entries:
            self.import_entry (entry)

#######################################################
def __handle_dff_search_in_folder (dff_folder, dependency, dependency_collection):
    file_path = bpy.path.resolve_ncase (f"{dff_folder}/{dependency}")
    if os.path.isfile (file_path) == False:
        print(f"Dependency DFF file not found: {file_path}")
        return None

    dff_file = dff ()
    dff_file.load_file (file_path)

    return dff_file

#######################################################
def __handle_dff_search_in_img_file (img_file_path, dependency, dependency_collection):
    img_file = img.open (img_file_path)
    entry_idx = img_file.find_entry_idx (dependency)

    if entry_idx == -1:
        return None

    entry_data = img_file.read_entry (entry_idx)[1]
    dff_file = dff()
    dff_file.load_memory (entry_data)

    return dff_file

#######################################################
def import_map_file (file, game, txd_images, dff_search_paths):
    map_file = MapFileText (game)
    map_file.load_file (file)

    importer = MapFileImporter (map_file.entries)
    collection_name = os.path.basename (file)
    importer.perform_import ({
        'collection_name': collection_name
    })

    dependency_collection = create_collection (collection_name + "_deps")
    dependency_collection.hide_viewport = True

    for dependency in importer.get_instancing_dependencies ():
        if importer.find_dependency_collection (dependency) is not None:
            continue

        for dff_folder in dff_search_paths:

            dff_file = None
            if os.path.isdir (dff_folder):
                dff_file = __handle_dff_search_in_folder (dff_folder, dependency, dependency_collection)
            elif os.path.isfile (dff_folder) and dff_folder.endswith(".img"):
                dff_file = __handle_dff_search_in_img_file (dff_folder, dependency, dependency_collection)

            if dff_file is not None:
                importer_dff = dff_importer.DffFileImporter (
                    dff_file = dff_file,
                    collection_name = dependency
                )
                dependency_collection.children.link (importer_dff.perform_import ())
                break

    importer.perform_instancing ()

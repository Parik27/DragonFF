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

import os
import struct

from dataclasses import dataclass
from io import BytesIO, BufferedReader, StringIO

from .data import map_data
from .img import img

#######################################################
@dataclass
class MapData:
    object_instances: list
    object_data: dict
    cull_instances: list

#######################################################
@dataclass
class TextIPLData:
    object_instances: list
    cull_instances: list

# Base for all IPL / IDE section reader / writer classes
#######################################################
class SectionUtility:

    def __init__(self, section_name, data_structures = []):
        self.section_name = section_name
        self.data_structures_dict = {len(ds._fields): ds for ds in data_structures}

    #######################################################
    def read(self, file_stream):

        entries = []

        line = file_stream.readline().strip()
        while line != "end":

            # Split line and trim individual elements
            line_params = [e.strip() for e in line.split(",")]

            # Append file name for IDEs (needed for collision lookups)
            filename = os.path.basename(file_stream.name)
            if filename.lower().endswith('.ide'):
                line_params.append(filename)

            # Get the correct data structure for this section entry
            data_structure = self.get_data_structure(line_params)

            # Validate data structure
            if data_structure is None:
                print(type(self).__name__, "Error: No appropriate data structure found")
                print("    Section name:", self.section_name)
                print("    Line parameters:", str(line_params))

            elif len(data_structure._fields) != len(line_params):
                print(
                    type(self).__name__, "Error: Number of line parameters "
                    "doesn't match the number of structure fields."
                )
                print("    Section name:", self.section_name)
                print("    Data structure name:", data_structure.__name__)
                print("    Data structure:", str(data_structure._fields))
                print("    Line parameters:", str(line_params))

            else:
                # Add entry
                entries.append(data_structure(*line_params))

            # Read next line
            line = file_stream.readline().strip()

        return entries

    #######################################################
    def get_data_structure(self, line_params):
        return self.data_structures_dict.get(len(line_params))

    #######################################################
    def write(self, file_stream, lines):
        file_stream.write(f"{self.section_name}\n")
        for line in lines:
            file_stream.write(f"{line}\n")
        file_stream.write("end\n")

# Utility for reading / writing to map data files (.IPL, .IDE)
#######################################################
class MapDataUtility:

    # Finds the path to a file case-insensitively
    #######################################################
    @staticmethod
    def find_path_case_insensitive(base_path, filename):
        current_path = os.path.join(base_path, filename)

        if os.path.isfile(current_path):
            return current_path

        current_path = base_path
        parts = os.path.normpath(filename).split(os.sep)

        for part in parts:
            try:
                entries = os.listdir(current_path)
            except FileNotFoundError:
                return None

            match = next((entry for entry in entries if entry.lower() == part.lower()), None)
            if match is None:
                return None
            current_path = os.path.join(current_path, match)

        return current_path

    # Check if file stream contains binary IPL data by reading its header
    #######################################################
    @staticmethod
    def is_binary_ipl_stream(file_stream):
        # Binary IPL files always start with the ASCII string "bnry"
        current_pos = file_stream.tell()
        try:
            header = file_stream.read(4)
            file_stream.seek(current_pos)
            return header == b'bnry'
        except (IOError, OSError):
            file_stream.seek(current_pos)
            return False

    # Get full path of file
    #######################################################
    @staticmethod
    def get_full_path(game_root, filename):
        # Check if file name is already an absolute path
        if os.path.isabs(filename):
            return filename

        fullpath = MapDataUtility.find_path_case_insensitive(game_root, filename)
        return fullpath or os.path.join(game_root, filename)

    # Merge Dictionaries of Lists
    #######################################################
    @staticmethod
    def merge_dols(dol1, dol2):
        result = dict(dol1, **dol2)
        result.update((k, dol1[k] + dol2[k])
                        for k in set(dol1).intersection(dol2))
        return result

    # Read binary IPL data from a file stream (credit to Allerek)
    #######################################################
    @staticmethod
    def read_binary_ipl_from_stream(file_stream, data_structures):
        sections = {}

        # Save the starting position (where the IPL file begins)
        start_pos = file_stream.tell()

        # Read and unpack the header
        header = file_stream.read(32)
        if len(header) < 32:
            print("Error: Invalid binary IPL file - header too short")
            return sections

        _, num_of_instances, _, _, _, _, _, instances_offset = struct.unpack('4siiiiiii', header)

        # Read and process instance definitions
        item_size = 40
        insts = []

        # Seek relative to the start of the IPL file
        file_stream.seek(start_pos + instances_offset)

        for i in range(num_of_instances):
            instances = file_stream.read(item_size)
            if len(instances) < item_size:
                print(f"Warning: Could not read instance {i}, reached end of file")
                break

            # Read binary instance
            x_pos, y_pos, z_pos, x_rot, y_rot, z_rot, w_rot, obj_id, interior, lod = struct.unpack('fffffffiii', instances)

            # Create value list (with values as strings) and map to the data struct
            vals = [obj_id, "", interior, x_pos, y_pos, z_pos, x_rot, y_rot, z_rot, w_rot, lod]
            insts.append(data_structures['inst'](*[str(v) for v in vals]))

        sections["inst"] = insts
        print("inst: %d entries" % len(insts))
        return sections

    # Read text-based IPL/IDE file from stream
    #######################################################
    @staticmethod
    def read_text_file_from_stream(file_stream, data_structures, aliases):
        sections = {}

        line = file_stream.readline().strip()

        while line:
            # Presume we have a section start
            section_name = line
            section_utility = None

            if section_name in aliases:
                available_data_structures = [data_structures[s] for s in aliases[line]]
                section_utility = SectionUtility(section_name, available_data_structures)

            elif section_name in data_structures:
                section_utility = SectionUtility(section_name, [data_structures[section_name]])

            if section_utility is not None:
                sections[section_name] = section_utility.read(file_stream)
                print("%s: %d entries" % (
                    section_name, len(sections[section_name])
                ))

            # Get next section
            line = file_stream.readline().strip()

        return sections

    # Returns a dictionary of sections found in the given file
    #######################################################
    @staticmethod
    def read_file(filepath, data_structures, aliases):
        self = MapDataUtility

        sections = {}
        try:
            with open(filepath, 'rb') as file_stream:
                if self.is_binary_ipl_stream(file_stream):
                    sections = self.read_binary_ipl_from_stream(file_stream, data_structures)
                else:
                    binary_data = file_stream.read()
                    text_data = binary_data.decode('latin-1')
                    text_stream = StringIO(text_data)
                    text_stream.name = filepath  # Set name attribute for IDE filename detection
                    sections = self.read_text_file_from_stream(text_stream, data_structures, aliases)

        except FileNotFoundError:
            print("File not found:", filepath)

        return sections

    ########################################################################
    @staticmethod
    def load_ide_data(game_root, ide_paths, data_structures, aliases):
        self = MapDataUtility

        ide = {}
        for file in ide_paths:
            fullpath = self.get_full_path(game_root, file)
            print('\nMapDataUtility reading:', fullpath)
            sections = self.read_file(fullpath, data_structures, aliases)
            ide = self.merge_dols(ide, sections)

        return ide

    ########################################################################
    @staticmethod
    def load_ipl_data(game_root, ipl_section, data_structures, aliases):
        self = MapDataUtility

        ipl = {}
        fullpath = self.get_full_path(game_root, ipl_section)
        print('\nMapDataUtility reading:', fullpath)

        if not os.path.isfile(fullpath):
             # If not found, look for it inside gta3.img
            imgpath = os.path.join(game_root, 'models/gta3.img')

            try:
                with img.open(imgpath) as img_file:
                    basename = os.path.basename(ipl_section)
                    entry_idx = img_file.find_entry_idx(basename)

                    if entry_idx > -1:
                        print("Read binary IPL from gta3.img:", basename)
                        _, data = img_file.read_entry(entry_idx)
                        file_stream = BufferedReader(BytesIO(data))
                        sections = MapDataUtility.read_binary_ipl_from_stream(file_stream, data_structures)
                        ipl = self.merge_dols(ipl, sections)
                        return ipl

            except FileNotFoundError:
                print("Warning: gta3.img not found at:", imgpath)

        sections = self.read_file(fullpath, data_structures, aliases)
        return self.merge_dols(ipl, sections)

    ########################################################################
    @staticmethod
    def load_map_data(game_id, game_root, ipl_section, is_custom_ipl):
        self = MapDataUtility

        data = map_data.data[game_id].copy()

        if is_custom_ipl:
            # Find paths to all IDEs
            ide_paths = []
            for root_path, _, files in os.walk(os.path.join(game_root, "data/maps")):
                for file in files:
                    if file.lower().endswith(".ide"):
                        fullpath = os.path.join(root_path, file)
                        ide_paths.append(os.path.relpath(fullpath, game_root))
            data['IDE_paths'] = ide_paths

        else:
            # Prune IDEs unrelated to current IPL section (SA only). First, make IDE_paths a mutable list, then iterate
            # over a copy so we can remove elements during iteration. This is a naive pruning which keeps all ides with a
            # few generic keywords in their name and culls anything else with a prefix different from the given ipl_section
            if game_id == map_data.game_version.SA:
                data['IDE_paths'] = list(data['IDE_paths'])
                for p in data['IDE_paths'].copy():
                    if p.startswith('DATA/MAPS/generic/') or p.startswith('DATA/MAPS/leveldes/') or 'xref' in p:
                        continue
                    ide_prefix = p.split('/')[-1].lower()
                    ipl_prefix = ipl_section.split('/')[-1].lower()[:3]
                    if not ide_prefix.startswith(ipl_prefix):
                        data['IDE_paths'].remove(p)

        # Load IDEs
        ide = self.load_ide_data(
            game_root,
            data['IDE_paths'],
            data['structures'],
            data['IDE_aliases']
        )

        # Load IPL
        ipl = self.load_ipl_data(
            game_root,
            ipl_section,
            data['structures'],
            data['IPL_aliases']
        )

        # Extract relevant sections
        object_instances = []
        cull_instances = []
        object_data = {}

        # Get all insts into a flat list (array)
        # Can't be an ID keyed dictionary, because there's many ipl
        # entries with the same ID - multiple pieces of
        # the same model (lamps, benches, trees etc.)
        if 'inst' in ipl:
            for entry in ipl['inst']:
                object_instances.append(entry)

        # Get all culls into a flat list (array)
        if 'cull' in ipl:
            for entry in ipl['cull']:
                cull_instances.append(entry)

        # Get all objs and tobjs into flat ID keyed dictionaries
        if 'objs' in ide:
            for entry in ide['objs']:
                if entry.id in object_data:
                    print('OJBS ERROR!! a duplicate ID!!')
                object_data[entry.id] = entry

        if 'tobj' in ide:
            for entry in ide['tobj']:
                if entry.id in object_data:
                    print('TOBJ ERROR!! a duplicate ID!!')
                object_data[entry.id] = entry

        return MapData(
            object_instances = object_instances,
            object_data = object_data,
            cull_instances = cull_instances
        )

    ########################################################################
    @staticmethod
    def write_text_ipl_to_stream(file_stream, game_id, ipl_data:TextIPLData):
        file_stream.write("# IPL generated with DragonFF\n")

        section_utility = SectionUtility("inst")
        section_utility.write(file_stream, ipl_data.object_instances)

        section_utility = SectionUtility("cull")
        section_utility.write(file_stream, ipl_data.cull_instances)

        if game_id == map_data.game_version.III:
            pass

        elif game_id == map_data.game_version.VC:
            section_utility = SectionUtility("pick")
            section_utility.write(file_stream, [])

            section_utility = SectionUtility("path")
            section_utility.write(file_stream, [])

        elif game_id == map_data.game_version.SA:
            section_utility = SectionUtility("path")
            section_utility.write(file_stream, [])

            section_utility = SectionUtility("grge")
            section_utility.write(file_stream, [])

            section_utility = SectionUtility("enex")
            section_utility.write(file_stream, [])

            section_utility = SectionUtility("pick")
            section_utility.write(file_stream, [])

            section_utility = SectionUtility("cars")
            section_utility.write(file_stream, [])

            section_utility = SectionUtility("jump")
            section_utility.write(file_stream, [])

            section_utility = SectionUtility("tcyc")
            section_utility.write(file_stream, [])

            section_utility = SectionUtility("auzo")
            section_utility.write(file_stream, [])

            section_utility = SectionUtility("mult")
            section_utility.write(file_stream, [])

    ########################################################################
    @staticmethod
    def write_ipl_data(filename, game_id, ipl_data:TextIPLData):
        self = MapDataUtility

        with open(filename, 'w') as file_stream:
            self.write_text_ipl_to_stream(file_stream, game_id, ipl_data)

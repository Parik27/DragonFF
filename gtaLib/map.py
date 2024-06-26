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
from ..data import map_data
from ..ops.importer_common import game_version
from collections import namedtuple
import struct

Vector = namedtuple("Vector", "x y z")

# Base for all IPL / IDE section reader / writer classes
#######################################################
class GenericSectionUtility: 

    def __init__(self, sectionName, dataStructures):
        self.sectionName = sectionName
        self.dataStructures = dataStructures

    #######################################################
    def read(self, fileStream):

        entries = []

        line = fileStream.readline().strip()
        while line != "end":

            # Split line and trim individual elements
            lineParams = [e.strip() for e in line.split(",")]

            # Append filename for IDEs (needed for collision lookups)
            fname = os.path.basename(fileStream.name)
            if fname.lower().endswith('.ide'):
                lineParams.append(fname)

            # Get the correct data structure for this section entry
            dataStructure = self.getDataStructure(lineParams)

            # Validate data structure
            if(dataStructure is None):
                print(type(self).__name__+
                      " error: No appropriate data structure found")
                print("    Section name: " + self.sectionName)
                print("    Line parameters: " + str(lineParams))
            elif(len(dataStructure._fields) != len(lineParams)):
                print(
                    type(self).__name__+" error: Number of line parameters "
                    "doesn't match the number of structure fields."
                )
                print("    Section name: " + self.sectionName)
                print("    Data structure name: " + dataStructure.__name__)
                print("    Data structure: " + str(dataStructure._fields))
                print("    Line parameters: " + str(lineParams))
            else:
                # Add entry
                entries.append(dataStructure(*lineParams))

            # Read next line
            line = fileStream.readline().strip()

        return entries

    #######################################################
    def getDataStructure(self, lineParams):
        return self.dataStructures[self.sectionName]

    #######################################################
    def write(self):
        pass

#######################################################
class OBJSSectionUtility(GenericSectionUtility):
    def getDataStructure(self, lineParams):

        if(len(lineParams) == 6):
            dataStructure = self.dataStructures["objs_1"]
        elif(len(lineParams) == 7):
            dataStructure = self.dataStructures["objs_2"]
        elif(len(lineParams) == 8):
            dataStructure = self.dataStructures["objs_3"]
        elif(len(lineParams) == 9):
            dataStructure = self.dataStructures["objs_4"]
        else:
            print(type(self).__name__ + " error: Unknown number of line parameters")
            dataStructure = None
        
        return dataStructure

#######################################################
class TOBJSectionUtility(GenericSectionUtility):
    def getDataStructure(self, lineParams):

        if(len(lineParams) == 8):
            dataStructure = self.dataStructures["tobj_1"]
        elif(len(lineParams) == 9):
            dataStructure = self.dataStructures["tobj_2"]
        elif(len(lineParams) == 10):
            dataStructure = self.dataStructures["tobj_3"]
        elif(len(lineParams) == 11):
            dataStructure = self.dataStructures["tobj_4"]
        else:
            print(type(self).__name__ + " error: Unknown number of line parameters")
            dataStructure = None
        
        return dataStructure

#######################################################
class CARSSectionUtility(GenericSectionUtility):
    def getDataStructure(self, lineParams):
        # TODO:
        print("'cars' not yet implemented")

# List of IPL/IDE sections which require a section utility that's different
# from the default one.
specialSections = {
    'objs': OBJSSectionUtility,
    'tobj': TOBJSectionUtility,
    'cars': CARSSectionUtility
}

# Utility for reading / writing to map data files (.IPL, .IDE)
#######################################################
class MapDataUtility:

    # Returns a dictionary of sections found in the given file
    #######################################################
    def readFile(filepath, filename, dataStructures):

        fullpath = "%s%s" % (filepath, filename)
        print('\nMapDataUtility reading: ' + fullpath)

        sections = {}

        try:
            fileStream = open(fullpath, 'r', encoding='latin-1')

        except FileNotFoundError:

            # If file doesn't exist, look for binary file inside gta3.img file (credit to Allerek)
            fullpath = "%s%s" % (filepath, 'models/gta3.img')
            with open(fullpath, 'rb') as img_file:
                # Read the first 8 bytes for the header and unpack
                header = img_file.read(8)
                magic, num_entries = struct.unpack('4sI', header)

                # Read and process directory entries
                entry_size = 32
                entries = []
                for i in range(num_entries):
                    entry_data = img_file.read(entry_size)
                    offset, streaming_size, _, name = struct.unpack('IHH24s', entry_data)
                    name = name.split(b'\x00', 1)[0].decode('utf-8')
                    entries.append((offset, streaming_size, name))

                # Look for ipl file in gta3.img
                for offset, streaming_size, name in entries:
                    if name == filename:

                        # Read and unpack the header
                        img_file.seek(offset * 2048)
                        header = img_file.read(32)
                        _, num_of_instances, _, _, _, _, _, instances_offset = struct.unpack('4siiiiiii', header)

                        # Read and process instance definitions
                        item_size = 40
                        read_base = offset * 2048 + instances_offset
                        insts = []
                        current_offset = read_base
                        for i in range(num_of_instances):
                            img_file.seek(current_offset)
                            instances = img_file.read(40)

                            # Read binary instance
                            x_pos, y_pos, z_pos, x_rot, y_rot, z_rot, w_rot, obj_id, interior, lod = struct.unpack('fffffffiii', instances)

                            # Create value list (with values as strings) and map to the data struct
                            vals = [obj_id, "", interior, x_pos, y_pos, z_pos, x_rot, y_rot, z_rot, w_rot, lod]
                            insts.append(dataStructures['inst'](*[str(v) for v in vals]))

                            # Prepare for reading of next instance inside of .ipl
                            current_offset = read_base + i * item_size

                        sections["inst"] = insts

        else:
            with fileStream:
                line = fileStream.readline().strip()

                while line:

                    # Presume we have a section start
                    sectionName = line
                    sectionUtility = None

                    if line in specialSections:
                        # Section requires some special reading / writing procedures
                        sectionUtility = specialSections[sectionName](
                            sectionName, dataStructures
                        )
                    elif line in dataStructures:
                        # Section is generic,
                        # can be read / written to with the default utility
                        sectionUtility = GenericSectionUtility(
                            sectionName, dataStructures
                        )

                    if sectionUtility is not None:
                        sections[sectionName] = sectionUtility.read(fileStream)
                        print("%s: %d entries" % (
                            sectionName, len(sections[sectionName]
                            )
                        ))

                    # Get next section
                    line = fileStream.readline().strip()

        return sections

    ########################################################################
    def getMapData(gameID, gameRoot, iplSection):
        
        data = map_data.data[gameID]

        # Prune IDEs unrelated to current IPL section (SA only). First, make IDE_paths a mutable list, then iterate
        # over a copy so we can remove elements during iteration. This is a naive pruning which keeps all ides with a
        # few generic keywords in their name and culls anything else with a prefix different from the given iplSection
        if gameID == game_version.SA:
            data['IDE_paths'] = list(data['IDE_paths'])
            for p in list(data['IDE_paths']):
                if p.startswith('DATA/MAPS/generic/') or p.startswith('DATA/MAPS/leveldes/') or 'xref' in p:
                    continue
                ide_prefix = p.split('/')[-1].lower()
                ipl_prefix = iplSection.split('/')[-1].lower()[:3]
                if not ide_prefix.startswith(ipl_prefix):
                    data['IDE_paths'].remove(p)

        ide = {}

        for file in data['IDE_paths']:
            sections = MapDataUtility.readFile(
                gameRoot, file,
                data['structures']
            )
            ide = MapDataUtility.merge_dols(ide, sections)

        ipl = {}

        sections = MapDataUtility.readFile(
            gameRoot, iplSection,
            data['structures']
        )
        ipl = MapDataUtility.merge_dols(ipl, sections)

        # Extract relevant sections
        object_instances = []
        object_data = {}

        # Get all insts into a flat list (array)
        # Can't be an ID keyed dictionary, because there's many ipl
        # entries with the same ID - multiple pieces of
        # the same model (lamps, benches, trees etc.)
        if 'inst' in ipl:
            for entry in ipl['inst']:
                object_instances.append(entry)
                
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

        return {
            'object_instances': object_instances,
            'object_data': object_data
            }

    # Merge Dictionaries of Lists
    #######################################################
    def merge_dols(dol1, dol2):
        result = dict(dol1, **dol2)
        result.update((k, dol1[k] + dol2[k])
                        for k in set(dol1).intersection(dol2))
        return result

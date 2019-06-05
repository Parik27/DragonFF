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

from enum import Enum
import os.path
from collections import namedtuple
from map_structures import III_structures, VC_structures, SA_structures

# Data types
Vector = namedtuple("Vector", "x y z")

# List of IPL/IDE sections which require a section utility that's different
# from the default one. E.g. sections with variable number of parameters in
# their data structures
specialSections = [
    'objs': OBJSSectionUtility,
    'tobj': TOBJSectionUtility
]

# Utility for reading / writing to map data files (.IPL, .IDE)
# Returns a dictionary of sections found in the given file
#######################################################
class MapDataUtility:

    #######################################################
    def read(filename, dataStructures):

        if not os.path.exists(filename):
            print("MapDataUtility error: File not found")
            return {}

        # File sections
        sections = {}

        with open(filename) as fileStream:

            # Read the file
            line = fileStream.readline().strip()
            while line:
                
                # Read a section if we recognize it's name
                if line in dataStructures:
                    
                    sectionName = line
                    if sectionName in specialSections:
                        # Section requires some special reading / writing procedures
                        sectionUtility = specialSections[sectionName](dataStructures[sectionName])
                    else
                        # Section is generic, can be read / written to with the default utility
                        sectionUtility = GenericSectionUtility(dataStructures[sectionName])

                    # Read section
                    sections[sectionName].read(fileStream)

                # Get next section
                line = fileStream.readline().strip()
        
        return sections

# Base for all IPL / IDE section reader / writer classes
#######################################################
class GenericSectionUtility: 

    def __init__(self, sectionDataStructure):
        self.sectionDataStructure = sectionDataStructure

    #######################################################
    def read(fileStream):

        # Section entries
        entries = []

        # Read the entire section
        line = fileStream.readline().strip()
        while line != "end":

            # Split line and trim individual elements
            lineParams = [e.strip() for e in line.split(",")]
            # Read the line
            entries.append(self.readLine(lineParams))
            # Read next line
            line = fileStream.readline().strip()

        return entries

    #######################################################
    def readLine(line):

        # Number of list elements and namedTuple fileds
        # must match.
        if(len(self.sectionDataStructure._fields) != len(lineParams)):
            print("GenericSectionUtility error: Number of line parameters doesn't match the number of structure fields.")
            print("Section name: " + self.sectionDataStructure.__name__)
            print("Section structure: " + self.sectionDataStructure._fields)
            print("Line parameters: " + lineParams)
            return None

        # Convert the parameter list into the appropriate
        # data structure's namedTuple.
        return self.sectionDataStructure(*lineParams)

    #######################################################
    def write(self):
        pass

class OBJSSectionUtility: 
    def readLine(line):
        pass

class TOBJSectionUtility: 
    def readLine(line):
        pass
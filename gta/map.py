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

# Initially ported from OpenRW
# https://github.com/rwengine/openrw/blob/master/rwengine/src/loaders/LoaderIPL.cpp

from enum import Enum
from collections import namedtuple

# Data types
Section_INST = namedtuple("Section_INST"  , "id model posX posY posZ scaleX "+
    "scaleY scaleZ rotX rotY rotZ rotW")
Section_PICK = namedtuple("Section_PICK"  , "")
Section_CULL = namedtuple("Section_CULL"  , "")
Section_ZONE = namedtuple("Section_ZONE"  , "name type minX minY minZ maxX maxY "+
    "maxZ island gangCarDensityDay gangCarDensityNight gangDensityDay"+
    "gangDensityNight pedGroupDay pedGroupNight")
Vector = namedtuple("Vector"			  , "x y z")

#######################################################
class IPLSection: 

    # Base for all IPL section classes
    # Shares loop for reading individual lines inside of assigned
    # section and calls readLine, which should be individually
    # overriden by inheriting classes

    #######################################################
    def __init__(self, iplLoader):
        self.iplLoader = iplLoader

    #######################################################
    def read(self, fileStream):

        line = fileStream.readline().strip()
        while line != "end":
            self.readLine(line)
            line = fileStream.readline().strip()

    #######################################################
    def readLine(self, line):
        pass

    #######################################################
    def write(self):
        pass

#######################################################
class IPLSection_INST(IPLSection):

    #######################################################
    def readLine(self, line):

        # Split line and trim individual elements
        array = [e.strip() for e in line.split(",")]
        
        # Convert list into the Section_INST namedTuple
        data = Section_INST(*array)
        self.iplLoader.inst_list.append(data)


#######################################################
class IPLSection_ZONE(IPLSection):

    def readLine(self, line):

        # Split line and trim individual elements
        array = [e.strip() for e in line.split(",")]
        
        # Convert list into the Section_ZONE namedTuple
        data = Section_ZONE(*array)
        self.iplLoader.zone_list.append(data)

#######################################################
class IPLSection_PICK(IPLSection):
    # TODO
    pass

#######################################################
class IPLSection_CULL(IPLSection):
    # TODO
    pass

#######################################################
class IPL:

    sections = {
        'inst': IPLSection_INST,
        'pick': IPLSection_PICK,
        'cull': IPLSection_CULL,
        'zone': IPLSection_ZONE
    }

    #######################################################
    def __init__(self):	
        self.inst_list = []
        self.pickup_list = []
        self.cull_list = []
        self.zone_list = []

    #######################################################
    def read(self, filename):

        with open(filename) as fileStream:

            line = fileStream.readline().strip()
            while line:

                # Read a section if we recognize it's name
                if line in IPL.sections:
                    section = IPL.sections[line](self)
                    section.read(fileStream)

                # Get next section
                line = fileStream.readline().strip()

    #######################################################
    def printContents(self):
        print(self.inst_list)
        print(self.pickup_list)
        print(self.cull_list)
        print(self.zone_list)
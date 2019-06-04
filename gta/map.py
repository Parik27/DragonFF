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
# IPL and IDE section formats taken from
# gta.fandom.com/wiki/Item_Placement
# gta.fandom.com/wiki/IDE

Vector = namedtuple("Vector", "x y z")

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

#######################################################
class RWUtility: 

    # Base for all IPL / IDE section reader / writer classes
    # readLine should be overridden by inheriting classes,
    # parsing the provided parameters appropriately according
    # to the individual section type

    #######################################################
    def __init__(self, iplObject):
        self.iplObject = iplObject

    #######################################################
    def read(self, fileStream):

        line = fileStream.readline().strip()
        while line != "end":

            # Split line and trim individual elements
            lineParams = [e.strip() for e in line.split(",")]

            # Call a specific readLine override
            self.readLine(lineParams)

            # Read next line
            line = fileStream.readline().strip()

    #######################################################
    def readLine(self, line):
        pass

    #######################################################
    def write(self):
        pass

#######################################################
class IPLSection_INST(RWUtility):

    #######################################################
    def readLine(self, lineParams):

        # Convert list into the Section_INST namedTuple
        data = Section_INST(*lineParams)
        self.iplObject.inst_list.append(data)


#######################################################
class IPLSection_ZONE(RWUtility):

    def readLine(self, line):

        # Convert list into the Section_ZONE namedTuple
        data = Section_ZONE(*lineParams)
        self.iplObject.zone_list.append(data)

#######################################################
class IPLSection_PICK(IPLSection):
    # TODO
    pass

#######################################################
class IPLSection_CULL(IPLSection):
    # TODO
    pass
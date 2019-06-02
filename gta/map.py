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

    #######################################################
    def __init__(self):	

        self.inst_list = []
        self.pickup_list = []
        self.cull_list = []
        self.zone_list = []

        self.sections = {
            'inst': IPLSection_INST,
            'pick': IPLSection_PICK,
            'cull': IPLSection_CULL,
            'zone': IPLSection_ZONE
        }

        self.currentSectionName = None

    #######################################################
    def read(self, filename):

        with open(filename) as fileStream:

            line = fileStream.readline().strip()
            while line:

                # Read a section if we recognize it's name
                if line in self.sections:
                    section = self.sections[line](self)
                    section.read(fileStream)

                # Get next section
                line = fileStream.readline().strip()

    #######################################################
    def printContents(self):
        print(self.inst_list)
        print(self.pickup_list)
        print(self.cull_list)
        print(self.zone_list)



# Experimentals... for future reference

# class IPLModel:
# 	def __init__(self):
# 		self.id = None
# 		self.model = None
# 		self.posX = 0
# 		self.posY = 0
# 		self.posZ = 0
# 		self.scaleX = 1
# 		self.scaleY = 1
# 		self.scaleZ = 1
# 		self.rotX = 0
# 		self.rotY = 0
# 		self.rotZ = 0
# 		self.rotW = 1

# class IPLZone:

# 	zone_gang_count = 13

# 	def __init__(self):
# 		self.name = None
# 		self.type = None
# 		self.minX = 0
# 		self.minY = 0
# 		self.minZ = 0
# 		self.maxX = 0
# 		self.maxY = 0
# 		self.maxZ = 0
# 		self.island = None
# 		self.gangCarDensityDay = [0] * IPLZone.zone_gang_count
# 		self.gangCarDensityNight = [0] * IPLZone.zone_gang_count
# 		self.gangDensityDay = [0] * IPLZone.zone_gang_count
# 		self.gangDensityNight = [0] * IPLZone.zone_gang_count
# 		self.pedGroupDay = 0
# 		self.pedGroupNight = 0

# class IPLSectionLoader_INST(IPLSectionLoaderBase):

# 	def processLine(self, line):
# 		params = line.split(",")

# 		model = IPLModel()
# 		model.id =     params[0].strip()
# 		model.model =  params[1].strip()
# 		model.posX =   params[2].strip()
# 		model.posY =   params[3].strip()
# 		model.posZ =   params[4].strip()
# 		model.scaleX = params[5].strip()
# 		model.scaleY = params[6].strip()
# 		model.scaleZ = params[7].strip()
# 		model.rotX =   params[8].strip()
# 		model.rotY =   params[9].strip()
# 		model.rotZ =   params[10].strip()
# 		model.rotW =   params[11].strip()

# 		self.iplLoader.inst_list.append(model)

# class IPLSectionLoader_ZONE(IPLSectionLoaderBase):

# 	def processLine(self, line):
# 		params = line.split(",")

# 		zone = IPLZone()
# 		zone.name =   params[0].strip()
# 		zone.type =   params[1].strip()
# 		zone.minX =   params[2].strip()
# 		zone.minY =   params[3].strip()
# 		zone.minZ =   params[4].strip()
# 		zone.maxX =   params[5].strip()
# 		zone.maxY =   params[6].strip()
# 		zone.maxZ =   params[7].strip()
# 		zone.island = params[8].strip()

# 		self.iplLoader.zone_list.append(zone)

# class IPLSectionLoader_PICK(IPLSectionLoaderBase): pass

# class IPLSectionLoader_CULL(IPLSectionLoaderBase): pass


        # inst = IPLModel()
        # inst.id =     params[0].strip()
        # inst.model =  params[1].strip()
        # inst.posX =   params[2].strip()
        # inst.posY =   params[3].strip()
        # inst.posZ =   params[4].strip()
        # inst.scaleX = params[5].strip()
        # inst.scaleY = params[6].strip()
        # inst.scaleZ = params[7].strip()
        # inst.rotX =   params[8].strip()
        # inst.rotY =   params[9].strip()
        # inst.rotZ =   params[10].strip()
        # inst.rotW =   params[11].strip()

        # lineData = Section_INST()
        # for i in range(len(Section_INST)):
        # 	lineData[i] = params[i]
            
        # self.iplLoader.inst_list.append(model)
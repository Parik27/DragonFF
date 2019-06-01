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


#######################################################

# Direct port of OpenRW's LoaderIPL.cpp ( https://github.com/rwengine/openrw/blob/master/rwengine/src/loaders/LoaderIPL.cpp )
# Seems to only support model INSTances and ZONEs. Though I believe the
# INSTances alone should give us enough info to import the entire maps
# of III / VC / SA.

import os 
from enum import Enum

#######################################################
class SectionTypes(Enum):
	INST = 1
	PICK = 2
	CULL = 3
	ZONE = 4
	NONE = 5

#######################################################
def loadIPL(filepath):

	section = SectionTypes.NONE

	with open(filepath) as fp:

		line = fp.readline()
		linesCount = 0
		while line:

			linesCount += 1
			line = line.strip()
			print("Line {}: {}".format(linesCount, line))
			
			if len(line) > 0 and line[0] == "#":
				# Nothing, just a comment
				pass

			elif line == "end":
				# Terminating a section
				section = SectionTypes.NONE

			# Section definers
			elif section == SectionTypes.NONE:
				if line == "inst":
					section = SectionTypes.INST
				
				if line == "pick":
					section = SectionTypes.PICK
				
				if line == "cull":
					section = SectionTypes.CULL
				
				if line == "zone":
					section = SectionTypes.ZONE
			
			# Actual data
			else :
				if section == SectionTypes.INST:

					params = line.split(",")

					id =     params[0].strip()
					model =  params[1].strip()
					posX =   params[2].strip()
					posY =   params[3].strip()
					posZ =   params[4].strip()
					scaleX = params[5].strip()
					scaleY = params[6].strip()
					scaleZ = params[7].strip()
					rotX =   params[8].strip()
					rotY =   params[9].strip()
					rotZ =   params[10].strip()
					rotW =   params[11].strip()

					# TODO: Call for a dff/txd import with given coordinates
					# or just save this model instance into memory and import
					# everything later.

					# TODO: We should probably create classes for objects in
					# which we could store all these parameters.

				elif section == SectionTypes.ZONE:

					params = line.split(",")

					name =   params[0].strip()
					type =   params[1].strip()
					minX =   params[2].strip()
					minY =   params[3].strip()
					minZ =   params[4].strip()
					maxX =   params[5].strip()
					maxY =   params[6].strip()
					maxZ =   params[7].strip()
					island = params[8].strip()

					# Gang spawn densities for this zone, apparently just arrays filled with zeroes at the moment...
					gangCarDensityDay = gangCarDensityNight = gangDensityDay = gangDensityNight = [0] * 13
					# Ped groups
					pedGroupDay = 0
					pedGroupNight = 0
		
			line = fp.readline()
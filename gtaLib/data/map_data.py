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

# This document specifies most of renderware era GTAs IPL/IDE data structures,
# taken directly from GTA wikis, sources available in each section.
# Sections listed in "Not present" were left out either because they seemed too
# complex or not useful enough to even bother with. Or they're not sufficiently
# documented.

from collections import namedtuple

game_version = namedtuple("game_version", "III VC SA LCS VCS")
game_version.III = 'III'
game_version.VC = 'VC'
game_version.SA = 'SA'
game_version.LCS = 'LCS'
game_version.VCS = 'VCS'

III_structures, III_IPL_aliases, III_IDE_aliases = {}, {}, {}
VC_structures, VC_IPL_aliases, VC_IDE_aliases = {}, {}, {}
SA_structures, SA_IPL_aliases, SA_IDE_aliases = {}, {}, {}

#############
#    IPL    #
#############

# Sources
# https://gtamods.com/wiki/Item_Placement
# https://www.grandtheftwiki.com/Item_Placement
# https://gta.fandom.com/wiki/Item_Placement

# Known missing:
# PATH
# MULT

# INST
# Places objects defined in objs, tobj, anim or tanm into the world
III_structures['inst'] = namedtuple("IPL_INST_3",  "id modelName posX posY posZ scaleX scaleY scaleZ rotX rotY rotZ rotW")
VC_structures['inst'] =  namedtuple("IPL_INST_VC", "id modelName interior posX posY posZ scaleX scaleY scaleZ rotX rotY rotZ rotW")
SA_structures['inst'] =  namedtuple("IPL_INST_SA", "id modelName interior posX posY posZ rotX rotY rotZ rotW lod")

# CULL
# Creates zones with special attributes
III_structures['cull'] = namedtuple("IPL_CULL_3",      "centerX centerY centerZ lowerLeftX lowerLeftY lowerLeftZ upperRightX upperRightY upperRightZ flags wantedLevelDrop")
VC_structures['cull'] =  namedtuple("IPL_CULL_VC",     "centerX centerY centerZ lowerLeftX lowerLeftY lowerLeftZ upperRightX upperRightY upperRightZ flags wantedLevelDrop")
SA_structures['cull_1'] =  namedtuple("IPL_CULL_SA_1", "centerX centerY centerZ skewX widthY bottomZ widthX skewY topZ flags unknown")
SA_structures['cull_2'] =  namedtuple("IPL_CULL_SA_2", "centerX centerY centerZ skewX widthY bottomZ widthX skewY topZ flags Vx Vy Vz cm")
SA_IPL_aliases['cull'] = ('cull_1', 'cull_2')

# ZONE
# Creates map, navigation, and info zones
III_structures['zone'] = namedtuple("IPL_ZONE_3",  "name type x1 y1 z1 x2 y2 z2 level")
VC_structures['zone'] =  namedtuple("IPL_ZONE_VC", "name type x1 y1 z1 x2 y2 z2 level")
SA_structures['zone'] =  namedtuple("IPL_ZONE_SA", "name type x1 y1 z1 x2 y2 z2 level")

# GRGE
# Creates a garage
SA_structures['grge'] = namedtuple("IPL_GRGE_SA", "posX posY posZ lineX lineY cubeX cubeY cubeZ doorType garageType name")

# ENEX
# Creates an entrance to an exit
SA_structures['enex'] = namedtuple("IPL_ENEX_SA", "x1 y1 z1 enterAngle sizeX sizeY sizeZ x2 y2 z2 exitAngle targetInterior flags name sky numPedsToSpawn timeOn timeOff")

# PICK
# Creates pickups. This section exists in GTA III, GTA Vice City, and GTA IV, but is only functional in GTA San Andreas
SA_structures['pick'] = namedtuple("IPL_PICK_SA", "id posX posY posZ")

# JUMP
# Creates a unique stunt jump
SA_structures['jump'] = namedtuple("IPL_JUMP_SA", "startLowerX startLowerY startLowerZ startUpperX startUpperY startUpperZ targetLowerX targetLowerY targetLowerZ targetUpperX targetUpperY targetUpperZ cameraX cameraY cameraZ reward")

# AUZO
# This creates an audio if you enter the zone
SA_structures['auzo_1'] = namedtuple("IPL_AUZO_SA_1", "name id switch x y z radius")
SA_structures['auzo_2'] = namedtuple("IPL_AUZO_SA_2", "name id switch x1 y1 z1 x2 y2 z2")
SA_IPL_aliases['auzo'] = ('auzo_1', 'auzo_2')

# CARS
# Creates a parked car generator
SA_structures['cars'] = namedtuple("IPL_CARS_SA", "posX posY posZ angle carId primCol secCol forceSpawn alarm doorLock unknown1 unknown2")

# OCCL
# Creates occlusion zones for separated rendering
VC_structures['occl'] = namedtuple("IPL_OCCL_VC", "midX midY bottomZ widthX widthY height rotation")
SA_structures['occl'] = namedtuple("IPL_OCCL_SA", "midX midY bottomZ widthX widthY height rotation")

# TCYC
SA_structures['occl'] = namedtuple("IPL_TCYC_SA", "x1 y1 z1 x2 y2 z2 farClip extraColor extraColorIntensity falloffDist unknown lodDistMult")

#############
#    IDE    #
#############

# Sources
# https://gtamods.com/wiki/Item_Definition
# https://www.grandtheftwiki.com/Item_Definition
# https://gta.fandom.com/wiki/IDE

# Known missing:
# PATH

# OBJS
# Defines simple objects. They can be placed into the world through the inst section of the item placement files.
III_structures['objs_1'] = namedtuple("IDE_OBJS_3_1",  "id modelName txdName drawDistance flags filename")
III_structures['objs_2'] = namedtuple("IDE_OBJS_3_2",  "id modelName txdName meshCount drawDistance flags filename")
III_structures['objs_3'] = namedtuple("IDE_OBJS_3_3",  "id modelName txdName meshCount drawDistance1 drawDistance2 flags filename")
III_structures['objs_4'] = namedtuple("IDE_OBJS_3_4",  "id modelName txdName meshCount drawDistance1 drawDistance2 drawDistance3 flags filename")
III_IDE_aliases['objs'] = ('objs_1', 'objs_2', 'objs_3', 'objs_4')

VC_structures['objs_1'] =  namedtuple("IDE_OBJS_VC_1",  "id modelName txdName drawDistance flags filename")
VC_structures['objs_2'] =  namedtuple("IDE_OBJS_VC_2",  "id modelName txdName meshCount drawDistance flags filename")
VC_structures['objs_3'] =  namedtuple("IDE_OBJS_VC_3",  "id modelName txdName meshCount drawDistance1 drawDistance2 flags filename")
VC_structures['objs_4'] =  namedtuple("IDE_OBJS_VC_4",  "id modelName txdName meshCount drawDistance1 drawDistance2 drawDistance3 flags filename")
VC_IDE_aliases['objs'] = ('objs_1', 'objs_2', 'objs_3', 'objs_4')

SA_structures['objs_1'] =  namedtuple("IDE_OBJS_SA_1",  "id modelName txdName drawDistance flags filename")
SA_structures['objs_2'] =  namedtuple("IDE_OBJS_SA_2",  "id modelName txdName meshCount drawDistance flags filename")
SA_structures['objs_3'] =  namedtuple("IDE_OBJS_SA_3",  "id modelName txdName meshCount drawDistance1 drawDistance2 flags filename")
SA_structures['objs_4'] =  namedtuple("IDE_OBJS_SA_4",  "id modelName txdName meshCount drawDistance1 drawDistance2 drawDistance3 flags filename")
SA_IDE_aliases['objs'] = ('objs_1', 'objs_2', 'objs_3', 'objs_4')

# TOBJ
# Defines time objects. The section functions similarly to objs but has two additional
# parameters defining the in-game time range the object can get rendered. These objects
# can be placed into the world through the inst section of the item placement files.
III_structures['tobj_1'] = namedtuple("IDE_TOBJ_3_1",  "id modelName txdName drawDistance flags timeOn timeOff filename")
III_structures['tobj_2'] = namedtuple("IDE_TOBJ_3_2",  "id modelName txdName meshCount drawDistance flags timeOn timeOff filename")
III_structures['tobj_3'] = namedtuple("IDE_TOBJ_3_3",  "id modelName txdName meshCount drawDistance1 drawDistance2 flags timeOn timeOff filename")
III_structures['tobj_4'] = namedtuple("IDE_TOBJ_3_4",  "id modelName txdName meshCount drawDistance1 drawDistance2 drawDistance3 flags timeOn timeOff filename")
III_IDE_aliases['tobj'] = ('tobj_1', 'tobj_2', 'tobj_3', 'tobj_4')

VC_structures['tobj_1'] =  namedtuple("IDE_TOBJ_VC_1",  "id modelName txdName drawDistance flags timeOn timeOff filename")
VC_structures['tobj_2'] =  namedtuple("IDE_TOBJ_VC_2",  "id modelName txdName meshCount drawDistance flags timeOn timeOff filename")
VC_structures['tobj_3'] =  namedtuple("IDE_TOBJ_VC_3",  "id modelName txdName meshCount drawDistance1 drawDistance2 flags timeOn timeOff filename")
VC_structures['tobj_4'] =  namedtuple("IDE_TOBJ_VC_4",  "id modelName txdName meshCount drawDistance1 drawDistance2 drawDistance3 flags timeOn timeOff filename")
VC_IDE_aliases['tobj'] = ('tobj_1', 'tobj_2', 'tobj_3', 'tobj_4')

SA_structures['tobj_1'] =  namedtuple("IDE_TOBJ_SA_1",  "id modelName txdName drawDistance flags timeOn timeOff filename")
SA_structures['tobj_2'] =  namedtuple("IDE_TOBJ_SA_2",  "id modelName txdName meshCount drawDistance flags timeOn timeOff filename")
SA_structures['tobj_3'] =  namedtuple("IDE_TOBJ_SA_3",  "id modelName txdName meshCount drawDistance1 drawDistance2 flags timeOn timeOff filename")
SA_structures['tobj_4'] =  namedtuple("IDE_TOBJ_SA_4",  "id modelName txdName meshCount drawDistance1 drawDistance2 drawDistance3 flags timeOn timeOff filename")
SA_IDE_aliases['tobj'] = ('tobj_1', 'tobj_2', 'tobj_3', 'tobj_4')

# ANIM
# Defines animated objects. The section functions similarly to objs but has one
# additional parameter indicating an IFP or WAD animation file to assign an
# animation to the object. 
SA_structures['anim'] = namedtuple("IDE_ANIM_SA", "id modelName textureName animName drawDist flags filename")

# PEDS
# Defines pedestrian objects (random NPC's)
III_structures['peds'] = namedtuple("IDE_PEDS_3",  "id modelName txdName pedType behavior animGroup vehClass")
VC_structures['peds'] =  namedtuple("IDE_PEDS_VC", "id modelName txdName pedType behavior animGroup vehClass animfile radio1 radio2")
SA_structures['peds'] =  namedtuple("IDE_PEDS_SA", "id modelName txdName pedType behavior animGroup vehClass flags animfile radio1 radio2 voiceArchive voice1 voice2")

# CARS
# Defines vehicle objects
# See: https://www.grandtheftwiki.com/CARS_(IDE_Section)
III_structures['cars_special'] = namedtuple("IDE_CARS_3_SPECIAL", "id modelName txdName type handlingId gameName vehicleClass frequency level compRules") # boat, train, heli
III_structures['cars_plane'] =   namedtuple("IDE_CARS_3_PLANE",   "id modelName txdName type handlingId gameName vehicleClass frequency level compRules lodModel")
III_structures['cars_car'] =     namedtuple("IDE_CARS_3_CAR",     "id modelName txdName type handlingId gameName vehicleClass frequency level compRules wheelId wheelScale")
III_IDE_aliases['cars'] = ('cars_special', 'cars_plane', 'cars_car')

VC_structures['cars_special'] = namedtuple("IDE_CARS_VC_SPECIAL", "id modelName txdName type handlingId gameName anims vehicleClass frequency level compRules") # boat, heli
VC_structures['cars_plane'] =   namedtuple("IDE_CARS_VC_PLANE",   "id modelName txdName type handlingId gameName anims vehicleClass frequency level compRules lodModel")
VC_structures['cars_car'] =     namedtuple("IDE_CARS_VC_CAR",     "id modelName txdName type handlingId gameName anims vehicleClass frequency level compRules wheelId wheelScale")
VC_structures['cars_bike'] =    namedtuple("IDE_CARS_VC_BIKE",    "id modelName txdName type handlingId gameName anims vehicleClass frequency level compRules steeringAngle wheelScale")
VC_IDE_aliases['cars'] = ('cars_special', 'cars_plane', 'cars_car', 'cars_bike')

SA_structures['cars'] =         namedtuple("IDE_CARS_SA",         "id modelName txdName type handlingId gameName anims vehicleClass frequency flags comprules wheelId wheelScaleFront wheelScaleRear unknownValue")

# HIER
# Defines clump objects for use in cutscenes
SA_structures['hier'] = namedtuple("IDE_HIER_SA", "id modelName txdName")

# TXDP
# Used as an extended texture archive
SA_structures['txpd'] = namedtuple("IDE_TXDP_SA", "txdName txdParentName")

# WEAP
# Used to define weapon objects
VC_structures['weap'] = namedtuple("IDE_WEAP_VC", "id modelName txdName animationName meshCount drawDistance")
SA_structures['weap'] = namedtuple("IDE_WEAP_SA", "id modelName txdName animationName meshCount drawDistance")



###################
#    IDE paths    #
###################

# Paths to IDE files for each game
# All IDEs should  be always loaded when importing maps

III_IDE = (
    'DATA/MAPS/generic.IDE',
    'DATA/MAPS/INDUSTNE/INDUSTNE.ide',
    'DATA/MAPS/INDUSTNW/INDUSTNW.ide',
    'DATA/MAPS/INDUSTSE/INDUSTSE.ide',
    'DATA/MAPS/INDUSTSW/INDUSTSW.ide',
    'DATA/MAPS/MAKING/MAKING.ide',
    'DATA/MAPS/TEMPPART/TEMPPART.ide',
    'DATA/MAPS/INDROADS/INDROADS.ide',
    'DATA/MAPS/COMNtop/COMNtop.ide',
    'DATA/MAPS/COMNbtm/COMNbtm.ide',
    'DATA/MAPS/COMSE/COMSE.ide',
    'DATA/MAPS/COMSW/COMSW.ide',
    'DATA/MAPS/COMROAD/COMROAD.ide',
    'DATA/MAPS/LANDne/LANDne.ide',
    'DATA/MAPS/LANDsw/LANDsw.ide',
    'DATA/MAPS/SUBROADS/SUBROADS.ide'
)

VC_IDE = (
    'DATA/MAPS/generic.IDE',
    'DATA/MAPS/littleha/littleha.IDE',
    'DATA/MAPS/downtown/downtown.IDE',
    'DATA/MAPS/downtows/downtows.IDE',
    'DATA/MAPS/docks/docks.IDE',
    'DATA/MAPS/washintn/washintn.IDE',
    'DATA/MAPS/washints/washints.IDE',
    'DATA/MAPS/oceandrv/oceandrv.IDE',
    'DATA/MAPS/oceandn/oceandn.IDE',
    'DATA/MAPS/golf/golf.IDE',
    'DATA/MAPS/bridge/bridge.IDE',
    'DATA/MAPS/starisl/starisl.IDE',
    'DATA/MAPS/nbeachbt/nbeachbt.IDE',
    'DATA/MAPS/nbeachw/nbeachw.IDE',
    'DATA/MAPS/nbeach/nbeach.IDE',
    'DATA/MAPS/bank/bank.IDE',
    'DATA/MAPS/mall/mall.IDE',
    'DATA/MAPS/yacht/yacht.IDE',
    'DATA/MAPS/cisland/cisland.IDE',
    'DATA/MAPS/club/club.IDE',
    'DATA/MAPS/hotel/hotel.IDE',
    'DATA/MAPS/lawyers/lawyers.IDE',
    'DATA/MAPS/stripclb/stripclb.IDE',
    'DATA/MAPS/airport/airport.IDE',
    'DATA/MAPS/airportN/airportN.IDE',
    'DATA/MAPS/haiti/haiti.IDE',
    'DATA/MAPS/haitin/haitin.IDE',
    'DATA/MAPS/concerth/concerth.IDE',
    'DATA/MAPS/mansion/mansion.IDE',
    'DATA/MAPS/islandsf/islandsf.IDE',
    'DATA/MAPS/stadint/stadint.IDE'
)

SA_IDE = (
    'DATA/MAPS/generic/vegepart.IDE',
    'DATA/MAPS/generic/barriers.IDE',
    'DATA/MAPS/generic/dynamic.IDE',
    'DATA/MAPS/generic/dynamic2.IDE',
    'DATA/MAPS/generic/multiobj.IDE',
    'DATA/MAPS/generic/procobj.IDE',
    'DATA/MAPS/LA/LAn.IDE',
    'DATA/MAPS/LA/LAn2.IDE',
    'DATA/MAPS/LA/LAs.IDE',
    'DATA/MAPS/LA/LAs2.IDE',
    'DATA/MAPS/LA/LAe.IDE',
    'DATA/MAPS/LA/LAe2.IDE',
    'DATA/MAPS/LA/LAw2.IDE',
    'DATA/MAPS/LA/LAw.IDE',
    'DATA/MAPS/LA/LAwn.IDE',
    'DATA/MAPS/LA/LAhills.IDE',
    'DATA/MAPS/LA/LAxref.IDE',
    'DATA/MAPS/SF/SFn.IDE',
    'DATA/MAPS/SF/SFs.IDE',
    'DATA/MAPS/SF/SFse.IDE',
    'DATA/MAPS/SF/SFe.IDE',
    'DATA/MAPS/SF/SFw.IDE',
    'DATA/MAPS/SF/SFxref.IDE',
    'DATA/MAPS/vegas/vegasN.IDE',
    'DATA/MAPS/vegas/vegasS.IDE',
    'DATA/MAPS/vegas/vegasE.IDE',
    'DATA/MAPS/vegas/vegasW.IDE',
    'DATA/MAPS/vegas/vegaxref.IDE',
    'DATA/MAPS/country/countryN.IDE',
    'DATA/MAPS/country/countN2.IDE',
    'DATA/MAPS/country/countryS.IDE',
    'DATA/MAPS/country/countryE.IDE',
    'DATA/MAPS/country/countryW.IDE',
    'DATA/MAPS/country/counxref.IDE',
    'DATA/MAPS/interior/int_LA.IDE',
    'DATA/MAPS/interior/int_SF.IDE',
    'DATA/MAPS/interior/int_veg.IDE',
    'DATA/MAPS/interior/int_cont.IDE',
    'DATA/MAPS/leveldes/levelmap.IDE',
    'DATA/MAPS/leveldes/levelxre.IDE',
    'DATA/MAPS/interior/gen_int1.IDE',
    'DATA/MAPS/interior/gen_int2.IDE',
    'DATA/MAPS/interior/gen_intb.IDE',
    'DATA/MAPS/interior/gen_int3.IDE',
    'DATA/MAPS/interior/gen_int4.IDE',
    'DATA/MAPS/interior/gen_int5.IDE',
    'DATA/MAPS/interior/savehous.IDE',
    'DATA/MAPS/interior/stadint.IDE',
    'DATA/MAPS/leveldes/seabed.IDE',
    'DATA/MAPS/interior/props.IDE',
    'DATA/MAPS/interior/props2.IDE',
    'DATA/MAPS/interior/propext.IDE',
    'DATA/MAPS/veh_mods/veh_mods.IDE'
)

LCS_IDE = (
    'DATA/MAPS/interior/interior_savehouse.IDE',
    'DATA/MAPS/generic/vegepart.IDE',
    'DATA/MAPS/generic/barriers.IDE',
    'DATA/MAPS/generic/dynamic.IDE',
    'DATA/MAPS/generic/dynamic2.IDE',
    'DATA/MAPS/generic/multiobj.IDE',
    'DATA/MAPS/generic/procobj.IDE',
    'DATA/MAPS/leveldes/levelxre.IDE',
    'DATA/MAPS/leveldes/seabed.IDE',
    'DATA/MAPS/generic/SALC.IDE',
    'DATA/MAPS/Portland/most1.IDE',
    'DATA/MAPS/Portland/mono.IDE',
    'DATA/MAPS/Portland/making.IDE',
    'DATA/MAPS/Portland/temppart.IDE',
    'DATA/MAPS/Portland/industNE.IDE',
    'DATA/MAPS/Portland/industNW.IDE',
    'DATA/MAPS/Portland/industSE.IDE',
    'DATA/MAPS/Portland/industSW.IDE',
    'DATA/MAPS/Portland/indroads.IDE',
    'DATA/MAPS/Portland/Portroads.IDE',
    'DATA/MAPS/Staunton/comNbtm.IDE',
    'DATA/MAPS/Staunton/comNtop.IDE',
    'DATA/MAPS/Staunton/comse.IDE',
    'DATA/MAPS/Staunton/comsw.IDE',
    'DATA/MAPS/Staunton/comroad.IDE',
    'DATA/MAPS/Staunton/comNroads.IDE',
    'DATA/MAPS/Staunton/STAroads.IDE',
    'DATA/MAPS/Ssv/subroads.IDE',
    'DATA/MAPS/Ssv/SSVroads.IDE',
    'DATA/MAPS/Ssv/landNE.IDE',
    'DATA/MAPS/Ssv/landSW.IDE',
    'DATA/MAPS/others/seafloor.IDE',
    'DATA/MAPS/interior/interior_fastfood.IDE',
    'DATA/MAPS/interior/interior_casinos.IDE',
    'DATA/MAPS/Horse.IDE',
    'DATA/MAPS/veh_mods/veh_mods.IDE',
    'DATA/TXDCUT.IDE'
)

VCS_IDE = (
    'DATA/MAPS/generic/vegepart.IDE',
    'DATA/MAPS/generic/barriers.IDE',
    'DATA/MAPS/generic/dynamic.IDE',
    'DATA/MAPS/generic/dynamic2.IDE',
    'DATA/MAPS/generic/multiobj.IDE',
    'DATA/MAPS/generic/procobj.IDE',
    'DATA/MAPS/leveldes/levelxre.IDE',
    'DATA/MAPS/airport/airport.IDE',
    'DATA/MAPS/littleha/littleha.IDE',
    'DATA/MAPS/airportN/airportN.IDE',
    'DATA/MAPS/docks/docks.IDE',
    'DATA/MAPS/mansion/mansion.IDE',
    'DATA/MAPS/starisl/starisl.IDE',
    'DATA/MAPS/haiti/haiti.IDE',
    'DATA/MAPS/haitiN/haitiN.IDE',
    'DATA/MAPS/bridge/bridge.IDE',
    'DATA/MAPS/golf/golf.IDE',
    'DATA/MAPS/downtowS/downtowS.IDE',
    'DATA/MAPS/downtowN/downtowN.IDE',
    'DATA/MAPS/cisland/cisland.IDE',
    'DATA/MAPS/nbeachw/nbeachw.IDE',
    'DATA/MAPS/islandsf/islandsf.IDE',
    'DATA/MAPS/oceandn/oceandn.IDE',
    'DATA/MAPS/oceandrv/oceandrv.IDE',
    'DATA/MAPS/nbeach/nbeach.IDE',
    'DATA/MAPS/nbeachbt/nbeachbt.IDE',
    'DATA/MAPS/washintN/washintN.IDE',
    'DATA/MAPS/washintS/washintS.IDE',
    'DATA/MAPS/mall/mall.IDE',
    'DATA/MAPS/shops/shops.IDE',
    'DATA/MAPS/empire/empire.IDE'
)


###################
#    IPL paths    #
###################

# Paths to IPL files for each game

III_IPL = (
    ('DATA/MAPS/INDUSTNE/INDUSTNE.IPL', 'industne', ''),
    ('DATA/MAPS/INDUSTNW/INDUSTNW.IPL', 'industnw', ''),
    ('DATA/MAPS/INDUSTSE/INDUSTSE.IPL', 'industse', ''),
    ('DATA/MAPS/INDUSTSW/INDUSTSW.IPL', 'industsw', ''),
    ('DATA/MAPS/COMNtop/COMNtop.IPL',   'comntop', ''),
    ('DATA/MAPS/COMNbtm/COMNbtm.IPL',   'comnbtm', ''),
    ('DATA/MAPS/COMSE/COMSE.IPL',       'comse', ''),
    ('DATA/MAPS/COMSW/COMSW.IPL',       'comsw', ''),
    ('DATA/MAPS/LANDne/LANDne.IPL',     'landne', ''),
    ('DATA/MAPS/LANDsw/LANDsw.IPL',     'landsw', ''),
    ('DATA/MAPS/overview.IPL',           'overview', ''),
    ('DATA/MAPS/props.IPL',              'props', ''),
    ('DATA/MAPS/CULL.IPL',               'cull', '')
)

VC_IPL = (
    ('DATA/MAPS/littleha/littleha.IPL', 'littleha', ''),
    ('DATA/MAPS/downtown/downtown.IPL', 'downtown', ''),
    ('DATA/MAPS/downtows/downtows.IPL', 'downtows', ''),
    ('DATA/MAPS/docks/docks.IPL',       'docks', ''),
    ('DATA/MAPS/washintn/washintn.IPL', 'washintn', ''),
    ('DATA/MAPS/washints/washints.IPL', 'washints', ''),
    ('DATA/MAPS/oceandrv/oceandrv.IPL', 'oceandrv', ''),
    ('DATA/MAPS/oceandn/oceandn.IPL',   'oceandn', ''),
    ('DATA/MAPS/golf/golf.IPL',         'golf', ''),
    ('DATA/MAPS/bridge/bridge.IPL',     'bridge', ''),
    ('DATA/MAPS/starisl/starisl.IPL',   'starisl', ''),
    ('DATA/MAPS/nbeachbt/nbeachbt.IPL', 'nbeachbt', ''),
    ('DATA/MAPS/nbeach/nbeach.IPL',     'nbeach', ''),
    ('DATA/MAPS/nbeachw/nbeachw.IPL',   'nbeachw', ''),
    ('DATA/MAPS/cisland/cisland.IPL',   'cisland', ''),
    ('DATA/MAPS/airport/airport.IPL',   'airport', ''),
    ('DATA/MAPS/airportN/airportN.IPL', 'airportN', ''),
    ('DATA/MAPS/haiti/haiti.IPL',       'haiti', ''),
    ('DATA/MAPS/haitin/haitin.IPL',     'haitin', ''),
    ('DATA/MAPS/islandsf/islandsf.IPL', 'islandsf', ''),
    ('DATA/MAPS/stadint/stadint.IPL',   'stadint', ''),
    ('DATA/MAPS/paths.ipl',              'paths', ''),
    ('DATA/MAPS/cull.ipl',               'cull', ''),
    ('DATA/occlu.ipl',                    'occlu', ''),
    ('DATA/MAPS/bank/bank.IPL',         'bank', ''),
    ('DATA/MAPS/mall/mall.IPL',         'mall', ''),
    ('DATA/MAPS/yacht/yacht.IPL',       'yacht', ''),
    ('DATA/MAPS/club/club.IPL',         'club', ''),
    ('DATA/MAPS/hotel/hotel.IPL',       'hotel', ''),
    ('DATA/MAPS/lawyers/lawyers.IPL',   'lawyers', ''),
    ('DATA/MAPS/stripclb/stripclb.IPL', 'stripclb', ''),
    ('DATA/MAPS/concerth/concerth.IPL', 'concerth', ''),
    ('DATA/MAPS/mansion/mansion.IPL',   'mansion', '')
)

SA_IPL = (
    ('DATA/MAPS/LA/LAn.IPL',            'LAn', ''),
    ('DATA/MAPS/LA/LAn2.IPL',           'LAn2', ''),
    ('DATA/MAPS/LA/LAs.IPL',            'LAs', ''),
    ('DATA/MAPS/LA/LAs2.IPL',           'LAs2', ''),
    ('DATA/MAPS/LA/LAe.IPL',            'LAe', ''),
    ('DATA/MAPS/LA/LAe2.IPL',           'LAe2', ''),
    ('DATA/MAPS/LA/LAw.IPL',            'LAw', ''),
    ('DATA/MAPS/LA/LAwn.IPL',           'LAwn', ''),
    ('DATA/MAPS/LA/LAw2.IPL',           'LAw2', ''),
    ('DATA/MAPS/LA/LAhills.IPL',        'LAhills', ''),
    ('DATA/MAPS/SF/SFn.IPL',            'SFn', ''),
    ('DATA/MAPS/SF/SFs.IPL',            'SFs', ''),
    ('DATA/MAPS/SF/SFse.IPL',           'SFse', ''),
    ('DATA/MAPS/SF/SFe.IPL',            'SFe', ''),
    ('DATA/MAPS/SF/SFw.IPL',            'SFw', ''),
    ('DATA/MAPS/vegas/vegasN.IPL',      'vegasN', ''),
    ('DATA/MAPS/vegas/vegasS.IPL',      'vegasS', ''),
    ('DATA/MAPS/vegas/vegasE.IPL',      'vegasE', ''),
    ('DATA/MAPS/vegas/vegasW.IPL',      'vegasW', ''),
    ('DATA/MAPS/country/countryN.IPL',  'countryN', ''),
    ('DATA/MAPS/country/countN2.IPL',   'countN2', ''),
    ('DATA/MAPS/country/countrys.IPL',  'countrys', ''),
    ('DATA/MAPS/country/countryE.IPL',  'countryE', ''),
    ('DATA/MAPS/country/countryW.IPL',  'countryW', ''),
    ('DATA/MAPS/interior/int_LA.IPL',   'int_LA', ''),
    ('DATA/MAPS/interior/int_SF.IPL',   'int_SF', ''),
    ('DATA/MAPS/interior/int_veg.IPL',  'int_veg', ''),
    ('DATA/MAPS/interior/int_cont.IPL', 'int_cont', ''),
    ('DATA/MAPS/interior/gen_int1.IPL', 'gen_int1', ''),
    ('DATA/MAPS/interior/gen_int2.IPL', 'gen_int2', ''),
    ('DATA/MAPS/interior/gen_intb.IPL', 'gen_intb', ''),
    ('DATA/MAPS/interior/gen_int3.IPL', 'gen_int3', ''),
    ('DATA/MAPS/interior/gen_int4.IPL', 'gen_int4', ''),
    ('DATA/MAPS/interior/gen_int5.IPL', 'gen_int5', ''),
    ('DATA/MAPS/interior/stadint.IPL',  'stadint', ''),
    ('DATA/MAPS/interior/savehous.IPL', 'savehous', ''),
    ('DATA/MAPS/leveldes/levelmap.IPL', 'levelmap', ''),
    ('DATA/MAPS/leveldes/seabed.IPL',   'seabed', ''),
    ('DATA/MAPS/paths.ipl',              'paths', ''),
    ('DATA/MAPS/paths2.ipl',             'paths2', ''),
    ('DATA/MAPS/paths3.ipl',             'paths3', ''),
    ('DATA/MAPS/paths4.ipl',             'paths4', ''),
    ('DATA/MAPS/paths5.ipl',             'paths5', ''),
    ('DATA/MAPS/cull.ipl',               'cull', ''),
    ('DATA/MAPS/tunnels.ipl',            'tunnels', ''),
    ('DATA/MAPS/occluSF.ipl',            'occluSF', ''),
    ('DATA/MAPS/occluveg.ipl',           'occluveg', ''),
    ('DATA/MAPS/occluLA.ipl',            'occluLA', ''),
    ('DATA/MAPS/occluint.ipl',           'occluint', ''),
    ('DATA/MAPS/audiozon.ipl',           'audiozon', ''),

    # Binary IPLs inside gta3.img...
    ('barriers1.ipl',                 'barriers1', ''),
    ('barriers2.ipl',                 'barriers2', ''),
    ('carter.ipl',                    'carter', ''),
    ('countn2_stream0.ipl',           'countn2_stream0', ''),
    ('countn2_stream1.ipl',           'countn2_stream1', ''),
    ('countn2_stream2.ipl',           'countn2_stream2', ''),
    ('countn2_stream3.ipl',           'countn2_stream3', ''),
    ('countn2_stream4.ipl',           'countn2_stream4', ''),
    ('countn2_stream5.ipl',           'countn2_stream5', ''),
    ('countn2_stream6.ipl',           'countn2_stream6', ''),
    ('countn2_stream7.ipl',           'countn2_stream7', ''),
    ('countn2_stream8.ipl',           'countn2_stream8', ''),
    ('countrye_stream0.ipl',          'countrye_stream0', ''),
    ('countrye_stream1.ipl',          'countrye_stream1', ''),
    ('countrye_stream10.ipl',         'countrye_stream10', ''),
    ('countrye_stream11.ipl',         'countrye_stream11', ''),
    ('countrye_stream12.ipl',         'countrye_stream12', ''),
    ('countrye_stream13.ipl',         'countrye_stream13', ''),
    ('countrye_stream2.ipl',          'countrye_stream2', ''),
    ('countrye_stream3.ipl',          'countrye_stream3', ''),
    ('countrye_stream4.ipl',          'countrye_stream4', ''),
    ('countrye_stream5.ipl',          'countrye_stream5', ''),
    ('countrye_stream6.ipl',          'countrye_stream6', ''),
    ('countrye_stream7.ipl',          'countrye_stream7', ''),
    ('countrye_stream8.ipl',          'countrye_stream8', ''),
    ('countrye_stream9.ipl',          'countrye_stream9', ''),
    ('countryn_stream0.ipl',          'countryn_stream0', ''),
    ('countryn_stream1.ipl',          'countryn_stream1', ''),
    ('countryn_stream2.ipl',          'countryn_stream2', ''),
    ('countryn_stream3.ipl',          'countryn_stream3', ''),
    ('countrys_stream0.ipl',          'countrys_stream0', ''),
    ('countrys_stream1.ipl',          'countrys_stream1', ''),
    ('countrys_stream2.ipl',          'countrys_stream2', ''),
    ('countrys_stream3.ipl',          'countrys_stream3', ''),
    ('countrys_stream4.ipl',          'countrys_stream4', ''),
    ('countryw_stream0.ipl',          'countryw_stream0', ''),
    ('countryw_stream1.ipl',          'countryw_stream1', ''),
    ('countryw_stream2.ipl',          'countryw_stream2', ''),
    ('countryw_stream3.ipl',          'countryw_stream3', ''),
    ('countryw_stream4.ipl',          'countryw_stream4', ''),
    ('countryw_stream5.ipl',          'countryw_stream5', ''),
    ('countryw_stream6.ipl',          'countryw_stream6', ''),
    ('countryw_stream7.ipl',          'countryw_stream7', ''),
    ('countryw_stream8.ipl',          'countryw_stream8', ''),
    ('crack.ipl',                     'crack', ''),
    ('lae2_stream0.ipl',              'lae2_stream0', ''),
    ('lae2_stream1.ipl',              'lae2_stream1', ''),
    ('lae2_stream2.ipl',              'lae2_stream2', ''),
    ('lae2_stream3.ipl',              'lae2_stream3', ''),
    ('lae2_stream4.ipl',              'lae2_stream4', ''),
    ('lae2_stream5.ipl',              'lae2_stream5', ''),
    ('lae2_stream6.ipl',              'lae2_stream6', ''),
    ('lae_stream0.ipl',               'lae_stream0', ''),
    ('lae_stream1.ipl',               'lae_stream1', ''),
    ('lae_stream2.ipl',               'lae_stream2', ''),
    ('lae_stream3.ipl',               'lae_stream3', ''),
    ('lae_stream4.ipl',               'lae_stream4', ''),
    ('lae_stream5.ipl',               'lae_stream5', ''),
    ('lahills_stream0.ipl',           'lahills_stream0', ''),
    ('lahills_stream1.ipl',           'lahills_stream1', ''),
    ('lahills_stream2.ipl',           'lahills_stream2', ''),
    ('lahills_stream3.ipl',           'lahills_stream3', ''),
    ('lahills_stream4.ipl',           'lahills_stream4', ''),
    ('lan2_stream0.ipl',           'lan2_stream0', ''),
    ('lan2_stream1.ipl',           'lan2_stream1', ''),
    ('lan2_stream2.ipl',           'lan2_stream2', ''),
    ('lan2_stream3.ipl',           'lan2_stream3', ''),
    ('lan_stream0.ipl',           'lan_stream0', ''),
    ('lan_stream1.ipl',           'lan_stream1', ''),
    ('lan_stream2.ipl',           'lan_stream2', ''),
    ('las2_stream0.ipl',           'las2_stream0', ''),
    ('las2_stream1.ipl',           'las2_stream1', ''),
    ('las2_stream2.ipl',           'las2_stream2', ''),
    ('las2_stream3.ipl',           'las2_stream3', ''),
    ('las2_stream4.ipl',           'las2_stream4', ''),
    ('las_stream0.ipl',           'las_stream0', ''),
    ('las_stream1.ipl',           'las_stream1', ''),
    ('las_stream2.ipl',           'las_stream2', ''),
    ('las_stream3.ipl',           'las_stream3', ''),
    ('las_stream4.ipl',           'las_stream4', ''),
    ('las_stream5.ipl',           'las_stream5', ''),
    ('law2_stream0.ipl',           'law2_stream0', ''),
    ('law2_stream1.ipl',           'law2_stream1', ''),
    ('law2_stream2.ipl',           'law2_stream2', ''),
    ('law2_stream3.ipl',           'law2_stream3', ''),
    ('law2_stream4.ipl',           'law2_stream4', ''),
    ('lawn_stream0.ipl',           'lawn_stream0', ''),
    ('lawn_stream1.ipl',           'lawn_stream1', ''),
    ('lawn_stream2.ipl',           'lawn_stream2', ''),
    ('lawn_stream3.ipl',           'lawn_stream3', ''),
    ('law_stream0.ipl',           'law_stream0', ''),
    ('law_stream1.ipl',           'law_stream1', ''),
    ('law_stream2.ipl',           'law_stream2', ''),
    ('law_stream3.ipl',           'law_stream3', ''),
    ('law_stream4.ipl',           'law_stream4', ''),
    ('law_stream5.ipl',           'law_stream5', ''),
    ('levelmap_stream0.ipl',           'levelmap_stream0', ''),
    ('seabed_stream0.ipl',           'seabed_stream0', ''),
    ('sfe_stream0.ipl',           'sfe_stream0', ''),
    ('sfe_stream1.ipl',           'sfe_stream1', ''),
    ('sfe_stream2.ipl',           'sfe_stream2', ''),
    ('sfe_stream3.ipl',           'sfe_stream3', ''),
    ('sfn_stream0.ipl',           'sfn_stream0', ''),
    ('sfn_stream1.ipl',           'sfn_stream1', ''),
    ('sfn_stream2.ipl',           'sfn_stream2', ''),
    ('sfse_stream0.ipl',           'sfse_stream0', ''),
    ('sfse_stream1.ipl',           'sfse_stream1', ''),
    ('sfse_stream2.ipl',           'sfse_stream2', ''),
    ('sfse_stream3.ipl',           'sfse_stream3', ''),
    ('sfse_stream4.ipl',           'sfse_stream4', ''),
    ('sfse_stream5.ipl',           'sfse_stream5', ''),
    ('sfse_stream6.ipl',           'sfse_stream6', ''),
    ('sfs_stream0.ipl',           'sfs_stream0', ''),
    ('sfs_stream1.ipl',           'sfs_stream1', ''),
    ('sfs_stream2.ipl',           'sfs_stream2', ''),
    ('sfs_stream3.ipl',           'sfs_stream3', ''),
    ('sfs_stream4.ipl',           'sfs_stream4', ''),
    ('sfs_stream5.ipl',           'sfs_stream5', ''),
    ('sfs_stream6.ipl',           'sfs_stream6', ''),
    ('sfs_stream7.ipl',           'sfs_stream7', ''),
    ('sfs_stream8.ipl',           'sfs_stream8', ''),
    ('sfw_stream0.ipl',           'sfw_stream0', ''),
    ('sfw_stream1.ipl',           'sfw_stream1', ''),
    ('sfw_stream2.ipl',           'sfw_stream2', ''),
    ('sfw_stream3.ipl',           'sfw_stream3', ''),
    ('sfw_stream4.ipl',           'sfw_stream4', ''),
    ('sfw_stream5.ipl',           'sfw_stream5', ''),
    ('truthsfarm.ipl',           'truthsfarm', ''),
    ('vegase_stream0.ipl',           'vegase_stream0', ''),
    ('vegase_stream1.ipl',           'vegase_stream1', ''),
    ('vegase_stream2.ipl',           'vegase_stream2', ''),
    ('vegase_stream3.ipl',           'vegase_stream3', ''),
    ('vegase_stream4.ipl',           'vegase_stream4', ''),
    ('vegase_stream5.ipl',           'vegase_stream5', ''),
    ('vegase_stream6.ipl',           'vegase_stream6', ''),
    ('vegase_stream7.ipl',           'vegase_stream7', ''),
    ('vegase_stream8.ipl',           'vegase_stream8', ''),
    ('vegasn_stream0.ipl',           'vegasn_stream0', ''),
    ('vegasn_stream1.ipl',           'vegasn_stream1', ''),
    ('vegasn_stream2.ipl',           'vegasn_stream2', ''),
    ('vegasn_stream3.ipl',           'vegasn_stream3', ''),
    ('vegasn_stream4.ipl',           'vegasn_stream4', ''),
    ('vegasn_stream5.ipl',           'vegasn_stream5', ''),
    ('vegasn_stream6.ipl',           'vegasn_stream6', ''),
    ('vegasn_stream7.ipl',           'vegasn_stream7', ''),
    ('vegasn_stream8.ipl',           'vegasn_stream8', ''),
    ('vegass_stream0.ipl',           'vegass_stream0', ''),
    ('vegass_stream1.ipl',           'vegass_stream1', ''),
    ('vegass_stream2.ipl',           'vegass_stream2', ''),
    ('vegass_stream3.ipl',           'vegass_stream3', ''),
    ('vegass_stream4.ipl',           'vegass_stream4', ''),
    ('vegass_stream5.ipl',           'vegass_stream5', ''),
    ('vegasw_stream0.ipl',           'vegasw_stream0', ''),
    ('vegasw_stream1.ipl',           'vegasw_stream1', ''),
    ('vegasw_stream10.ipl',          'vegasw_stream10', ''),
    ('vegasw_stream11.ipl',          'vegasw_stream11', ''),
    ('vegasw_stream2.ipl',           'vegasw_stream2', ''),
    ('vegasw_stream3.ipl',           'vegasw_stream3', ''),
    ('vegasw_stream4.ipl',           'vegasw_stream4', ''),
    ('vegasw_stream5.ipl',           'vegasw_stream5', ''),
    ('vegasw_stream6.ipl',           'vegasw_stream6', ''),
    ('vegasw_stream7.ipl',           'vegasw_stream7', ''),
    ('vegasw_stream8.ipl',           'vegasw_stream8', ''),
    ('vegasw_stream9.ipl',           'vegasw_stream9', ''),
)

LCS_IPL = (
    ('DATA/MAPS/interior/interior_savehouse.IPL', 'interior_savehouse', ''),
    ('DATA/MAPS/Staunton/comNbtm.IPL',            'comNbtm', ''),
    ('DATA/MAPS/Staunton/comse.IPL',              'comse', ''),
    ('DATA/MAPS/Staunton/comsw.IPL',              'comsw', ''),
    ('DATA/MAPS/Staunton/STAroads.IPL',           'STAroads', ''),
    ('DATA/MAPS/Staunton/comNtop.IPL',            'comNtop', ''),
    ('DATA/MAPS/Ssv/landNE.IPL',                  'landNE', ''),
    ('DATA/MAPS/Ssv/landSW.IPL',                  'landSW', ''),
    ('DATA/MAPS/Ssv/ssvtemp.IPL',                 'ssvtemp', ''),
    ('DATA/MAPS/Ssv/SSVroads.IPL',                'SSVroads', ''),
    ('DATA/MAPS/Portland/most1.IPL',              'most1', ''),
    ('DATA/MAPS/Portland/industNE.IPL',           'industNE', ''),
    ('DATA/MAPS/Portland/industNW.IPL',           'industNW', ''),
    ('DATA/MAPS/Portland/industSE.IPL',           'industSE', ''),
    ('DATA/MAPS/Portland/industSW.IPL',           'industSW', ''),
    ('DATA/MAPS/Portland/Portroads.IPL',          'Portroads', ''),
    ('DATA/MAPS/Portland/mono.IPL',               'mono', ''),
    ('DATA/MAPS/Portland/overview.IPL',           'overview', ''),
    ('DATA/MAPS/Portland/props.IPL',              'props', ''),
    ('DATA/MAPS/others/seafloor.IPL',             'seafloor', ''),
    ('DATA/MAPS/interior/interior_fastfood.IPL',  'interior_fastfood', ''),
    ('DATA/MAPS/interior/interior_casinos.IPL',   'interior_casinos', ''),
    ('DATA/MAPS/Ssv/XPEH.IPL',                    'XPEH', ''),
    ('DATA/MAPS/paths.ipl',                        'paths', '')
)

VCS_IPL = (
    ('DATA/MAPS/littleha/littleha.IPL', 'littleha', ''),
    ('DATA/MAPS/airport/airport.IPL',   'airport', ''),
    ('DATA/MAPS/airportN/airportN.IPL', 'airportN', ''),
    ('DATA/MAPS/docks/docks.IPL',       'docks', ''),
    ('DATA/MAPS/mansion/mansion.IPL',   'mansion', ''),
    ('DATA/MAPS/starisl/starisl.IPL',   'starisl', ''),
    ('DATA/MAPS/haiti/haiti.IPL',       'haiti', ''),
    ('DATA/MAPS/haitiN/haitiN.IPL',     'haitiN', ''),
    ('DATA/MAPS/bridge/bridge.IPL',     'bridge', ''),
    ('DATA/MAPS/golf/golf.IPL',         'golf', ''),
    ('DATA/MAPS/downtowS/downtowS.IPL', 'downtowS', ''),
    ('DATA/MAPS/downtowN/downtowN.IPL', 'downtowN', ''),
    ('DATA/MAPS/cisland/cisland.IPL',   'cisland', ''),
    ('DATA/MAPS/nbeachw/nbeachw.IPL',   'nbeachw', ''),
    ('DATA/MAPS/islandsf/islandsf.IPL', 'islandsf', ''),
    ('DATA/MAPS/oceandn/oceandn.IPL',   'oceandn', ''),
    ('DATA/MAPS/oceandrv/oceandrv.IPL', 'oceandrv', ''),
    ('DATA/MAPS/nbeach/nbeach.IPL',     'nbeach', ''),
    ('DATA/MAPS/nbeachbt/nbeachbt.IPL', 'nbeachbt', ''),
    ('DATA/MAPS/mall/mall.IPL',         'mall', ''),
    ('DATA/MAPS/washintN/washintN.IPL', 'washintN', ''),
    ('DATA/MAPS/washintS/washintS.IPL', 'washintS', ''),
    ('DATA/MAPS/shops/shops.IPL',       'shops', ''),
    ('DATA/MAPS/empire/empire.IPL',     'empire', '')
)

# Export
data = {
    game_version.III : {
        'structures': III_structures,
        'IDE_aliases': III_IDE_aliases,
        'IPL_aliases': III_IPL_aliases,
        'IDE_paths': III_IDE,
        'IPL_paths': III_IPL,
    },
    game_version.VC : {
        'structures': VC_structures,
        'IDE_aliases': VC_IDE_aliases,
        'IPL_aliases': VC_IPL_aliases,
        'IDE_paths': VC_IDE,
        'IPL_paths': VC_IPL,
    },
    game_version.SA : {
        'structures': SA_structures,
        'IDE_aliases': SA_IDE_aliases,
        'IPL_aliases': SA_IPL_aliases,
        'IDE_paths': SA_IDE,
        'IPL_paths': SA_IPL,
    },
    game_version.LCS : {
        'structures': SA_structures,
        'IDE_aliases': SA_IDE_aliases,
        'IPL_aliases': SA_IPL_aliases,
        'IDE_paths': LCS_IDE,
        'IPL_paths': LCS_IPL,
    },
    game_version.VCS : {
        'structures': SA_structures,
        'IDE_aliases': SA_IDE_aliases,
        'IPL_aliases': SA_IPL_aliases,
        'IDE_paths': VCS_IDE,
        'IPL_paths': VCS_IPL,
    },
}

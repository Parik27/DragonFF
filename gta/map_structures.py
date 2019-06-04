# This document specifies most of renderware era GTAs IPL/IDE data structures,
# taken directly from GTA wikis, sources available in each section.
# Sections listed in "Not present" were left out either because they seemed too
# complex or not useful enough to even bother with. Or they're not sufficiently
# documented.

# Most of these haven't been tested at all. Some of these have a variable number
# of parameters, which needs to be accounted for when reading into these
# structures. They're marked with suffixes _1, _2, _3, etc.

from collections import namedtuple

III_structures = {}
VC_structures = {}
SA_structures = {}

#############
#    IPL    #
#############

# Sources
# https://www.grandtheftwiki.com/Item_Placement
# https://gta.fandom.com/wiki/Item_Placement

# Not present
# PATH
# TCYC - couldn't confirm format
# MULT - couldn't confirm format

# INST
# Used to place objects in the world
III_structures['inst'] = namedtuple("IPL_INST_3",  "id modelName posX posY posZ scaleX scaleY scaleZ rotX rotY rotZ rotW")
VC_structures['inst'] =  namedtuple("IPL_INST_VC", "id modelName interior posX posY posZ scaleX scaleY scaleZ rotX rotY rotZ rotW")
SA_structures['inst'] =  namedtuple("IPL_INST_SA", "id modelName interior posX posY posZ rotX rotY rotZ rotW lod")

# CULL
# Create a culling zone
III_structures['cull'] = namedtuple("IPL_CULL_3",      "centerX centerY centerZ lowerLeftX lowerLeftY lowerLeftZ upperRightX upperRightY upperRightZ flags wantedLevelDrop")
VC_structures['cull'] =  namedtuple("IPL_CULL_VC",     "centerX centerY centerZ lowerLeftX lowerLeftY lowerLeftZ upperRightX upperRightY upperRightZ flags wantedLevelDrop")
SA_structures['cull_1'] =  namedtuple("IPL_CULL_SA_1", "centerX centerY centerZ unknown1 widthY bottomZ widthX unknown2 topZ flag unknown3")
SA_structures['cull_2'] =  namedtuple("IPL_CULL_SA_2", "centerX centerY centerZ unknown1 widthY bottomZ widthX unknown2 topZ flag Vx Vy Vz cm")

# ZONE
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
# Creates a weapon pickup
SA_structures['pick'] = namedtuple("IPL_PICK_SA", "id posX posY posZ")

# JUMP
# Creates a unique stunt jump
SA_structures['jump'] = namedtuple("IPL_JUMP_SA", "startLowerX startLowerY startLowerZ startUpperX startUpperY startUpperZ targetLowerX targetLowerY targetLowerZ targetUpperX targetUpperY targetUpperZ cameraX cameraY cameraZ reward")

# AUZO
# This creates an audio if you enter the zone
SA_structures['auzo_1'] = namedtuple("IPL_AUZO_SA_1", "name id switch x y z radius")
SA_structures['auzo_2'] = namedtuple("IPL_AUZO_SA_2", "name id switch x1 y1 z1 x2 y2 z2")

# CARS
# Creates a parked car generator
SA_structures['cars'] = namedtuple("IPL_CARS_SA", "posX posY posZ angle carId primCol secCol forceSpawn alarm doorLock unknown1 unknown2")

# OCCL
# Creates zones for separated rendering
VC_structures['occl'] = namedtuple("IPL_OCCL_VC", "midX midY bottomZ widthX widthY height rotation")
SA_structures['occl'] = namedtuple("IPL_OCCL_SA", "midX midY bottomZ widthX widthY height rotation")

#############
#    IDE    #
#############

# Sources
# https://www.grandtheftwiki.com/Item_Definition
# https://gta.fandom.com/wiki/IDE

# Not present
# PATH
# TXDP
# WEAP - couldn't confirm format, or even supporting games

# OBJS
# Used to define standard static map objects
III_structures['objs_1'] = namedtuple("IDE_OBJS_3_1",  "id modelName txdName drawDistance flags")
III_structures['objs_2'] = namedtuple("IDE_OBJS_3_2",  "id modelName txdName meshCount drawDistance flags")
III_structures['objs_3'] = namedtuple("IDE_OBJS_3_3",  "id modelName txdName meshCount drawDistance1 drawDistance2 flags")
III_structures['objs_4'] = namedtuple("IDE_OBJS_3_4",  "id modelName txdName meshCount drawDistance1 drawDistance2 drawDistance3 flags")

VC_structures['objs_1'] = namedtuple("IDE_OBJS_VC_1",  "id modelName txdName drawDistance flags")
VC_structures['objs_2'] = namedtuple("IDE_OBJS_VC_2",  "id modelName txdName meshCount drawDistance flags")
VC_structures['objs_3'] = namedtuple("IDE_OBJS_VC_3",  "id modelName txdName meshCount drawDistance1 drawDistance2 flags")
VC_structures['objs_4'] = namedtuple("IDE_OBJS_VC_4",  "id modelName txdName meshCount drawDistance1 drawDistance2 drawDistance3 flags")

SA_structures['objs_1'] = namedtuple("IDE_OBJS_SA_1",  "id modelName txdName drawDistance flags")
SA_structures['objs_2'] = namedtuple("IDE_OBJS_SA_2",  "id modelName txdName meshCount drawDistance flags")
SA_structures['objs_3'] = namedtuple("IDE_OBJS_SA_3",  "id modelName txdName meshCount drawDistance1 drawDistance2 flags")
SA_structures['objs_4'] = namedtuple("IDE_OBJS_SA_4",  "id modelName txdName meshCount drawDistance1 drawDistance2 drawDistance3 flags")

# TOBJ
# Used to define timed map objects. All but the last two columns are the same as the OBJS section.
III_structures['tobj_1'] = namedtuple("IDE_TOBJ_3_1",  "id modelName txdName drawDistance flags timeOn timeOff")
III_structures['tobj_2'] = namedtuple("IDE_TOBJ_3_2",  "id modelName txdName meshCount drawDistance flags timeOn timeOff")
III_structures['tobj_3'] = namedtuple("IDE_TOBJ_3_3",  "id modelName txdName meshCount drawDistance1 drawDistance2 flags timeOn timeOff")
III_structures['tobj_4'] = namedtuple("IDE_TOBJ_3_4",  "id modelName txdName meshCount drawDistance1 drawDistance2 drawDistance3 flags timeOn timeOff")

VC_structures['tobj_1'] =  namedtuple("IDE_TOBJ_VC_1",  "id modelName txdName drawDistance flags timeOn timeOff")
VC_structures['tobj_2'] =  namedtuple("IDE_TOBJ_VC_2",  "id modelName txdName meshCount drawDistance flags timeOn timeOff")
VC_structures['tobj_3'] =  namedtuple("IDE_TOBJ_VC_3",  "id modelName txdName meshCount drawDistance1 drawDistance2 flags timeOn timeOff")
VC_structures['tobj_4'] =  namedtuple("IDE_TOBJ_VC_4",  "id modelName txdName meshCount drawDistance1 drawDistance2 drawDistance3 flags timeOn timeOff")

SA_structures['tobj_1'] =  namedtuple("IDE_TOBJ_SA_1",  "id modelName txdName drawDistance flags timeOn timeOff")
SA_structures['tobj_2'] =  namedtuple("IDE_TOBJ_SA_2",  "id modelName txdName meshCount drawDistance flags timeOn timeOff")
SA_structures['tobj_3'] =  namedtuple("IDE_TOBJ_SA_3",  "id modelName txdName meshCount drawDistance1 drawDistance2 flags timeOn timeOff")
SA_structures['tobj_4'] =  namedtuple("IDE_TOBJ_SA_4",  "id modelName txdName meshCount drawDistance1 drawDistance2 drawDistance3 flags timeOn timeOff")

# ANIM
# Animated Map Objects
SA_structures['anim'] = namedtuple("IDE_ANIM_SA", "id modelName textureName animName drawDist flags")

# PEDS
# Used to define characters and pedestrians
III_structures['peds'] = namedtuple("IDE_PEDS_3",  "id modelName txdName pedType behavior animGroup vehClass")
VC_structures['peds'] =  namedtuple("IDE_PEDS_VC", "id modelName txdName pedType behavior animGroup vehClass animfile radio1 radio2")
SA_structures['peds'] =  namedtuple("IDE_PEDS_SA", "id modelName txdName pedType behavior animGroup vehClass flags animfile radio1 radio2 voiceArchive voice1 voice2")

# CARS
# Used to define vehicles
# See: https://www.grandtheftwiki.com/CARS_(IDE_Section)
III_structures['cars_boat'] =  namedtuple("IDE_CARS_3_BOAT",  "id modelName txdName type handlingId gameName vehicleClass frequency level compRules")
III_structures['cars_train'] = namedtuple("IDE_CARS_3_TRAIN", "id modelName txdName type handlingId gameName vehicleClass frequency level compRules")
III_structures['cars_heli'] =  namedtuple("IDE_CARS_3_HELI",  "id modelName txdName type handlingId gameName vehicleClass frequency level compRules")
III_structures['cars_plane'] = namedtuple("IDE_CARS_3_PLANE", "id modelName txdName type handlingId gameName vehicleClass frequency level compRules lodModel")
III_structures['cars_car'] =   namedtuple("IDE_CARS_3_CAR",   "id modelName txdName type handlingId gameName vehicleClass frequency level compRules wheelId wheelScale")

VC_structures['cars_boat'] =   namedtuple("IDE_CARS_VC_BOAT",  "id modelName txdName type handlingId gameName anims vehicleClass frequency level compRules")
VC_structures['cars_heli'] =   namedtuple("IDE_CARS_VC_HELI",  "id modelName txdName type handlingId gameName anims vehicleClass frequency level compRules")
VC_structures['cars_plane'] =  namedtuple("IDE_CARS_VC_PLANE", "id modelName txdName type handlingId gameName anims vehicleClass frequency level compRules lodModel")
VC_structures['cars_car'] =    namedtuple("IDE_CARS_VC_CAR",   "id modelName txdName type handlingId gameName anims vehicleClass frequency level compRules wheelId wheelScale")
VC_structures['cars_bike'] =   namedtuple("IDE_CARS_VC_BIKE",  "id modelName txdName type handlingId gameName anims vehicleClass frequency level compRules steeringAngle wheelScale")

SA_structures['cars'] =        namedtuple("IDE_CARS_SA", "id modelName txdName type handlingId gameName anims vehicleClass frequency flags comprules wheelId wheelScaleFront wheelScaleRear unknownValue")

# HIER
# Used to define cutscene objects
SA_structures['hier'] = namedtuple("IDE_HIER_SA", "id modelName txdName")

# TXDP
# Used as an extended texture archive
SA_structures['txpd'] = namedtuple("IDE_TXDP_SA", "txdName txdParentName")

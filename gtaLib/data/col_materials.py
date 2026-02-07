from enum import IntEnum


# --------------------------------------------------
# GROUPS
# --------------------------------------------------

class COL_GROUP(IntEnum):
    ROAD     =  0
    CONCRETE =  1
    GRAVEL   =  2
    GRASS    =  3
    DIRT     =  4
    SAND     =  5
    GLASS    =  6
    WOOD     =  7
    METAL    =  8
    ROCK     =  9
    BUSHES   = 10
    WATER    = 11
    MISC     = 12
    VEHICLE  = 13

COL_PRESET_GROUP = {
     0 : ["Road",     "303030"],
     1 : ["Concrete", "909090"],
     2 : ["Gravel",   "645E53"],
     3 : ["Grass",    "92C032"],
     4 : ["Dirt",     "775F40"],
     5 : ["Sand",     "E7E17E"],
     6 : ["Glass",    "A7E9FC"],
     7 : ["Wood",     "936944"],
     8 : ["Metal",    "BFC8D5"],
     9 : ["Rock",     "AFAAA0"],
    10 : ["Bushes",   "2EA563"],
    11 : ["Water",    "6493E1"],
    12 : ["Misc",     "F1AB07"],
    13 : ["Vehicle",  "FFD4FD"]
}


# --------------------------------------------------
# SAN ANDREAS
# --------------------------------------------------

class COL_FLAG_SA(IntEnum):
    NONE    =  0

    BODY    =  0
    HOOD    =  1
    BOOT    =  2
    BUMP_F  =  3
    BUMP_R  =  4
    DOOR_FL =  5
    DOOR_FR =  6
    DOOR_RL =  7
    DOOR_RR =  8
    WING_FL =  9
    WING_FR = 10
    WING_RL = 11
    WING_RR = 12
    WIND_SH = 19

COL_PRESET_SA = [
    # group, flag, material, name, procedural

    # Normal Materials (0-73)
    ( COL_GROUP.ROAD,     COL_FLAG_SA.NONE,      0, "Default",              False ),
    ( COL_GROUP.ROAD,     COL_FLAG_SA.NONE,      1, "Tarmac",               False ),
    ( COL_GROUP.ROAD,     COL_FLAG_SA.NONE,      2, "Tarmac (worn)",        False ),
    ( COL_GROUP.ROAD,     COL_FLAG_SA.NONE,      3, "Tarmac (very worn)",   False ),
    ( COL_GROUP.CONCRETE, COL_FLAG_SA.NONE,      4, "Pavement",             False ),
    ( COL_GROUP.CONCRETE, COL_FLAG_SA.NONE,      5, "Pavement (cracked)",   False ),
    ( COL_GROUP.GRAVEL,   COL_FLAG_SA.NONE,      6, "Gravel",               False ),
    ( COL_GROUP.CONCRETE, COL_FLAG_SA.NONE,      7, "Concrete (cracked)",   False ),
    ( COL_GROUP.CONCRETE, COL_FLAG_SA.NONE,      8, "Painted Ground",       False ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,      9, "Grass (short, lush)",  False ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,     10, "Grass (medium, lush)", False ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,     11, "Grass (long, lush)",   False ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,     12, "Grass (short, dry)",   False ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,     13, "Grass (medium, dry)",  False ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,     14, "Grass (long, dry)",    False ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,     15, "Golf Grass (rough)",   False ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,     16, "Golf Grass (smooth)",  False ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,     17, "Steep Slidy Grass",    False ),
    ( COL_GROUP.ROCK,     COL_FLAG_SA.NONE,     18, "Steep Cliff",          False ),
    ( COL_GROUP.DIRT,     COL_FLAG_SA.NONE,     19, "Flower Bed",           False ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,     20, "Meadow",               False ),
    ( COL_GROUP.DIRT,     COL_FLAG_SA.NONE,     21, "Waste Ground",         False ),
    ( COL_GROUP.DIRT,     COL_FLAG_SA.NONE,     22, "Woodland Ground",      False ),
    ( COL_GROUP.BUSHES,   COL_FLAG_SA.NONE,     23, "Vegetation",           False ),
    ( COL_GROUP.DIRT,     COL_FLAG_SA.NONE,     24, "Mud (wet)",            False ),
    ( COL_GROUP.DIRT,     COL_FLAG_SA.NONE,     25, "Mud (dry)",            False ),
    ( COL_GROUP.DIRT,     COL_FLAG_SA.NONE,     26, "Dirt",                 False ),
    ( COL_GROUP.DIRT,     COL_FLAG_SA.NONE,     27, "Dirt Track",           False ),
    ( COL_GROUP.SAND,     COL_FLAG_SA.NONE,     28, "Sand (deep)",          False ),
    ( COL_GROUP.SAND,     COL_FLAG_SA.NONE,     29, "Sand (medium)",        False ),
    ( COL_GROUP.SAND,     COL_FLAG_SA.NONE,     30, "Sand (compact)",       False ),
    ( COL_GROUP.SAND,     COL_FLAG_SA.NONE,     31, "Sand (arid)",          False ),
    ( COL_GROUP.SAND,     COL_FLAG_SA.NONE,     32, "Sand (more)",          False ),
    ( COL_GROUP.SAND,     COL_FLAG_SA.NONE,     33, "Sand (beach)",         False ),
    ( COL_GROUP.CONCRETE, COL_FLAG_SA.NONE,     34, "Concrete (beach)",     False ),
    ( COL_GROUP.ROCK,     COL_FLAG_SA.NONE,     35, "Rock (dry)",           False ),
    ( COL_GROUP.ROCK,     COL_FLAG_SA.NONE,     36, "Rock (wet)",           False ),
    ( COL_GROUP.ROCK,     COL_FLAG_SA.NONE,     37, "Rock (cliff)",         False ),
    ( COL_GROUP.WATER,    COL_FLAG_SA.NONE,     38, "Water (riverbed)",     False ),
    ( COL_GROUP.WATER,    COL_FLAG_SA.NONE,     39, "Water (shallow)",      False ),
    ( COL_GROUP.DIRT,     COL_FLAG_SA.NONE,     40, "Corn Field",           False ),
    ( COL_GROUP.BUSHES,   COL_FLAG_SA.NONE,     41, "Hedge",                False ),
    ( COL_GROUP.WOOD,     COL_FLAG_SA.NONE,     42, "Wood (crates)",        False ),
    ( COL_GROUP.WOOD,     COL_FLAG_SA.NONE,     43, "Wood (solid)",         False ),
    ( COL_GROUP.WOOD,     COL_FLAG_SA.NONE,     44, "Wood (thin)",          False ),
    ( COL_GROUP.GLASS,    COL_FLAG_SA.NONE,     45, "Glass",                False ),
    ( COL_GROUP.GLASS,    COL_FLAG_SA.NONE,     46, "Glass Window (large)", False ),
    ( COL_GROUP.GLASS,    COL_FLAG_SA.NONE,     47, "Glass Window (small)", False ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,     48, "Empty 1",              False ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,     49, "Empty 2",              False ),
    ( COL_GROUP.METAL,    COL_FLAG_SA.NONE,     50, "Garage Door",          False ),
    ( COL_GROUP.METAL,    COL_FLAG_SA.NONE,     51, "Thick Metal Plate",    False ),
    ( COL_GROUP.METAL,    COL_FLAG_SA.NONE,     52, "Scaffold Pole",        False ),
    ( COL_GROUP.METAL,    COL_FLAG_SA.NONE,     53, "Lamp Post",            False ),
    ( COL_GROUP.METAL,    COL_FLAG_SA.NONE,     54, "Metal Gate",           False ),
    ( COL_GROUP.METAL,    COL_FLAG_SA.NONE,     55, "Metal Chain fence",    False ),
    ( COL_GROUP.METAL,    COL_FLAG_SA.NONE,     56, "Girder",               False ),
    ( COL_GROUP.METAL,    COL_FLAG_SA.NONE,     57, "Fire Hydrant",         False ),
    ( COL_GROUP.METAL,    COL_FLAG_SA.NONE,     58, "Container",            False ),
    ( COL_GROUP.METAL,    COL_FLAG_SA.NONE,     59, "News Vendor",          False ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,     60, "Wheelbase",            False ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,     61, "Cardboard Box",        False ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,     62, "Ped",                  False ),
    ( COL_GROUP.METAL,    COL_FLAG_SA.NONE,     63, "Car (body)",           False ),
    ( COL_GROUP.METAL,    COL_FLAG_SA.NONE,     64, "Car (panel)",          False ),
    ( COL_GROUP.METAL,    COL_FLAG_SA.NONE,     65, "Car (moving)",         False ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,     66, "Transparent Cloth",    False ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,     67, "Rubber",               False ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,     68, "Plastic",              False ),
    ( COL_GROUP.ROCK,     COL_FLAG_SA.NONE,     69, "Transparent Stone",    False ),
    ( COL_GROUP.WOOD,     COL_FLAG_SA.NONE,     70, "Wood (bench)",         False ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,     71, "Carpet",               False ),
    ( COL_GROUP.WOOD,     COL_FLAG_SA.NONE,     72, "Floorboard",           False ),
    ( COL_GROUP.WOOD,     COL_FLAG_SA.NONE,     73, "Stairs (wood)",        False ),

    # Procedural Materials (74-157)
    ( COL_GROUP.SAND,     COL_FLAG_SA.NONE,     74, "Sand",                 True  ),
    ( COL_GROUP.SAND,     COL_FLAG_SA.NONE,     75, "Sand (dense)",         True  ),
    ( COL_GROUP.SAND,     COL_FLAG_SA.NONE,     76, "Sand (arid)",          True  ),
    ( COL_GROUP.SAND,     COL_FLAG_SA.NONE,     77, "Sand (compact)",       True  ),
    ( COL_GROUP.SAND,     COL_FLAG_SA.NONE,     78, "Sand (rocky)",         True  ),
    ( COL_GROUP.SAND,     COL_FLAG_SA.NONE,     79, "Sand (beach)",         True  ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,     80, "Grass (short)",        True  ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,     81, "Grass (meadow)",       True  ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,     82, "Grass (dry)",          True  ),
    ( COL_GROUP.DIRT,     COL_FLAG_SA.NONE,     83, "Woodland",             True  ),
    ( COL_GROUP.DIRT,     COL_FLAG_SA.NONE,     84, "Wood Dense",           True  ),
    ( COL_GROUP.GRAVEL,   COL_FLAG_SA.NONE,     85, "Roadside",             True  ),
    ( COL_GROUP.SAND,     COL_FLAG_SA.NONE,     86, "Roadside Desert",      True  ),
    ( COL_GROUP.DIRT,     COL_FLAG_SA.NONE,     87, "Flowerbed",            True  ),
    ( COL_GROUP.DIRT,     COL_FLAG_SA.NONE,     88, "Waste Ground",         True  ),
    ( COL_GROUP.CONCRETE, COL_FLAG_SA.NONE,     89, "Concrete",             True  ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,     90, "Office Desk",          True  ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,     91, "Shelf 711 1",          True  ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,     92, "Shelf 711 2",          True  ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,     93, "Shelf 711 3",          True  ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,     94, "Restuarant Table",     True  ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,     95, "Bar Table",            True  ),
    ( COL_GROUP.SAND,     COL_FLAG_SA.NONE,     96, "Underwater (lush)",    True  ),
    ( COL_GROUP.SAND,     COL_FLAG_SA.NONE,     97, "Underwater (barren)",  True  ),
    ( COL_GROUP.SAND,     COL_FLAG_SA.NONE,     98, "Underwater (coral)",   True  ),
    ( COL_GROUP.SAND,     COL_FLAG_SA.NONE,     99, "Underwater (deep)",    True  ),
    ( COL_GROUP.DIRT,     COL_FLAG_SA.NONE,    100, "Riverbed",             True  ),
    ( COL_GROUP.GRAVEL,   COL_FLAG_SA.NONE,    101, "Rubble",               True  ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,    102, "Bedroom Floor",        True  ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,    103, "Kitchen Floor",        True  ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,    104, "Livingroom Floor",     True  ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,    105, "Corridor Floor",       True  ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,    106, "711 Floor",            True  ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,    107, "Fast Food Floor",      True  ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,    108, "Skanky Floor",         True  ),
    ( COL_GROUP.ROCK,     COL_FLAG_SA.NONE,    109, "Mountain",             True  ),
    ( COL_GROUP.DIRT,     COL_FLAG_SA.NONE,    110, "Marsh",                True  ),
    ( COL_GROUP.BUSHES,   COL_FLAG_SA.NONE,    111, "Bushy",                True  ),
    ( COL_GROUP.BUSHES,   COL_FLAG_SA.NONE,    112, "Bushy (mix)",          True  ),
    ( COL_GROUP.BUSHES,   COL_FLAG_SA.NONE,    113, "Bushy (dry)",          True  ),
    ( COL_GROUP.BUSHES,   COL_FLAG_SA.NONE,    114, "Bushy (mid)",          True  ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,    115, "Grass (wee flowers)",  True  ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,    116, "Grass (dry, tall)",    True  ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,    117, "Grass (lush, tall)",   True  ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,    118, "Grass (green, mix)",   True  ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,    119, "Grass (brown, mix)",   True  ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,    120, "Grass (low)",          True  ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,    121, "Grass (rocky)",        True  ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,    122, "Grass (small trees)",  True  ),
    ( COL_GROUP.DIRT,     COL_FLAG_SA.NONE,    123, "Dirt (rocky)",         True  ),
    ( COL_GROUP.DIRT,     COL_FLAG_SA.NONE,    124, "Dirt (weeds)",         True  ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,    125, "Grass (weeds)",        True  ),
    ( COL_GROUP.DIRT,     COL_FLAG_SA.NONE,    126, "River Edge",           True  ),
    ( COL_GROUP.CONCRETE, COL_FLAG_SA.NONE,    127, "Poolside",             True  ),
    ( COL_GROUP.DIRT,     COL_FLAG_SA.NONE,    128, "Forest (stumps)",      True  ),
    ( COL_GROUP.DIRT,     COL_FLAG_SA.NONE,    129, "Forest (sticks)",      True  ),
    ( COL_GROUP.DIRT,     COL_FLAG_SA.NONE,    130, "Forest (leaves)",      True  ),
    ( COL_GROUP.SAND,     COL_FLAG_SA.NONE,    131, "Desert Rocks",         True  ),
    ( COL_GROUP.DIRT,     COL_FLAG_SA.NONE,    132, "Forest (dry)",         True  ),
    ( COL_GROUP.DIRT,     COL_FLAG_SA.NONE,    133, "Sparse Flowers",       True  ),
    ( COL_GROUP.GRAVEL,   COL_FLAG_SA.NONE,    134, "Building Site",        True  ),
    ( COL_GROUP.CONCRETE, COL_FLAG_SA.NONE,    135, "Docklands",            True  ),
    ( COL_GROUP.CONCRETE, COL_FLAG_SA.NONE,    136, "Industrial",           True  ),
    ( COL_GROUP.CONCRETE, COL_FLAG_SA.NONE,    137, "Industrial Jetty",     True  ),
    ( COL_GROUP.CONCRETE, COL_FLAG_SA.NONE,    138, "Concrete (litter)",    True  ),
    ( COL_GROUP.CONCRETE, COL_FLAG_SA.NONE,    139, "Alley Rubbish",        True  ),
    ( COL_GROUP.GRAVEL,   COL_FLAG_SA.NONE,    140, "Junkyard Piles",       True  ),
    ( COL_GROUP.DIRT,     COL_FLAG_SA.NONE,    141, "Junkyard Ground",      True  ),
    ( COL_GROUP.DIRT,     COL_FLAG_SA.NONE,    142, "Dump",                 True  ),
    ( COL_GROUP.SAND,     COL_FLAG_SA.NONE,    143, "Cactus Dense",         True  ),
    ( COL_GROUP.CONCRETE, COL_FLAG_SA.NONE,    144, "Airport Ground",       True  ),
    ( COL_GROUP.DIRT,     COL_FLAG_SA.NONE,    145, "Cornfield",            True  ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,    146, "Grass (light)",        True  ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,    147, "Grass (lighter)",      True  ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,    148, "Grass (lighter 2)",    True  ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,    149, "Grass (mid 1)",        True  ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,    150, "Grass (mid 2)",        True  ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,    151, "Grass (dark)",         True  ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,    152, "Grass (dark 2)",       True  ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,    153, "Grass (dirt mix)",     True  ),
    ( COL_GROUP.ROCK,     COL_FLAG_SA.NONE,    154, "Riverbed (stone)",     True  ),
    ( COL_GROUP.DIRT,     COL_FLAG_SA.NONE,    155, "Riverbed (shallow)",   True  ),
    ( COL_GROUP.DIRT,     COL_FLAG_SA.NONE,    156, "Riverbed (weeds)",     True  ),
    ( COL_GROUP.SAND,     COL_FLAG_SA.NONE,    157, "Seaweed",              True  ),

    # Normal Materials (158-178)
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,    158, "Door",                 False ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,    159, "Plastic Barrier",      False ),
    ( COL_GROUP.GRASS,    COL_FLAG_SA.NONE,    160, "Park Grass",           False ),
    ( COL_GROUP.ROCK,     COL_FLAG_SA.NONE,    161, "Stairs (stone)",       False ),
    ( COL_GROUP.METAL,    COL_FLAG_SA.NONE,    162, "Stairs (metal)",       False ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,    163, "Stairs (carpet)",      False ),
    ( COL_GROUP.METAL,    COL_FLAG_SA.NONE,    164, "Floor (metal)",        False ),
    ( COL_GROUP.CONCRETE, COL_FLAG_SA.NONE,    165, "Floor (concrete)",     False ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,    166, "Bin Bag",              False ),
    ( COL_GROUP.METAL,    COL_FLAG_SA.NONE,    167, "Thin Metal Sheet",     False ),
    ( COL_GROUP.METAL,    COL_FLAG_SA.NONE,    168, "Metal Barrel",         False ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,    169, "Plastic Cone",         False ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,    170, "Plastic Dumpster",     False ),
    ( COL_GROUP.METAL,    COL_FLAG_SA.NONE,    171, "Metal Dumpster",       False ),
    ( COL_GROUP.WOOD,     COL_FLAG_SA.NONE,    172, "Wood Picket Fence",    False ),
    ( COL_GROUP.WOOD,     COL_FLAG_SA.NONE,    173, "Wood Slatted Fence",   False ),
    ( COL_GROUP.WOOD,     COL_FLAG_SA.NONE,    174, "Wood Ranch Fence",     False ),
    ( COL_GROUP.GLASS,    COL_FLAG_SA.NONE,    175, "Unbreakable Glass",    False ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,    176, "Hay Bale",             False ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,    177, "Gore",                 False ),
    ( COL_GROUP.MISC,     COL_FLAG_SA.NONE,    178, "Rail Track",           False ),

    # Vehicle Presets
    ( COL_GROUP.VEHICLE,  COL_FLAG_SA.BODY,     63, "Body",                 False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_SA.BOOT,     63, "Boot",                 False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_SA.HOOD,     63, "Bonnet",               False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_SA.WIND_SH,  45, "Windshield",           False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_SA.BUMP_F,   63, "Bumper Front",         False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_SA.BUMP_R,   63, "Bumper Rear",          False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_SA.DOOR_FL,  63, "Door Front Left",      False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_SA.DOOR_FR,  63, "Door Front Right",     False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_SA.DOOR_RL,  63, "Door Rear Left",       False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_SA.DOOR_RR,  63, "Door Rear Right",      False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_SA.WING_FL,  63, "Wing Front Left",      False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_SA.WING_FR,  63, "Wing Front Right",     False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_SA.WING_RL,  63, "Wing Rear Left",       False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_SA.WING_RR,  63, "Wing Rear Right",      False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_SA.NONE,     64, "Flying Part",          False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_SA.NONE,     65, "Moving Part",          False ),
]


# --------------------------------------------------
# VICE CITY
# --------------------------------------------------

class COL_FLAG_VC(IntEnum):
    NONE    =  0

    BODY    =  0
    HOOD    =  1
    BOOT    =  2
    BUMP_F  =  3
    BUMP_R  =  4
    DOOR_FL =  5
    DOOR_FR =  6
    DOOR_RL =  7
    DOOR_RR =  8
    WING_FL =  9
    WING_FR = 10
    WING_RL = 11
    WING_RR = 12
    WIND_SH = 17

COL_PRESET_VC = [
    # group, flag, material, name, procedural

    # Normal Materials (0-34)
    ( COL_GROUP.ROAD,     COL_FLAG_VC.NONE,      0, "Default",              False ),
    ( COL_GROUP.ROAD,     COL_FLAG_VC.NONE,      1, "Street",               False ),
    ( COL_GROUP.GRASS,    COL_FLAG_VC.NONE,      2, "Grass",                False ),
    ( COL_GROUP.DIRT,     COL_FLAG_VC.NONE,      3, "Mud",                  False ),
    ( COL_GROUP.DIRT,     COL_FLAG_VC.NONE,      4, "Dirt",                 False ),
    ( COL_GROUP.CONCRETE, COL_FLAG_VC.NONE,      5, "Concrete",             False ),
    ( COL_GROUP.METAL,    COL_FLAG_VC.NONE,      6, "Aluminum",             False ),
    ( COL_GROUP.GLASS,    COL_FLAG_VC.NONE,      7, "Glass",                False ),
    ( COL_GROUP.METAL,    COL_FLAG_VC.NONE,      8, "Metal Pole",           False ),
    ( COL_GROUP.MISC,     COL_FLAG_VC.NONE,      9, "Door",                 False ),
    ( COL_GROUP.METAL,    COL_FLAG_VC.NONE,     10, "Metal Sheet",          False ),
    ( COL_GROUP.METAL,    COL_FLAG_VC.NONE,     11, "Metal",                False ),
    ( COL_GROUP.METAL,    COL_FLAG_VC.NONE,     12, "Small Metal Post",     False ),
    ( COL_GROUP.METAL,    COL_FLAG_VC.NONE,     13, "Large Metal Post",     False ),
    ( COL_GROUP.METAL,    COL_FLAG_VC.NONE,     14, "Medium Metal Post",    False ),
    ( COL_GROUP.METAL,    COL_FLAG_VC.NONE,     15, "Steel",                False ),
    ( COL_GROUP.METAL,    COL_FLAG_VC.NONE,     16, "Fence",                False ),
    ( COL_GROUP.MISC,     COL_FLAG_VC.NONE,     17, "Unknown",              False ),
    ( COL_GROUP.SAND,     COL_FLAG_VC.NONE,     18, "Sand",                 False ),
    ( COL_GROUP.WATER,    COL_FLAG_VC.NONE,     19, "Water",                False ),
    ( COL_GROUP.WOOD,     COL_FLAG_VC.NONE,     20, "Wooden Box",           False ),
    ( COL_GROUP.WOOD,     COL_FLAG_VC.NONE,     21, "Wooden Lathes",        False ),
    ( COL_GROUP.WOOD,     COL_FLAG_VC.NONE,     22, "Wood",                 False ),
    ( COL_GROUP.METAL,    COL_FLAG_VC.NONE,     23, "Metal Box 1",          False ),
    ( COL_GROUP.METAL,    COL_FLAG_VC.NONE,     24, "Metal Box 2",          False ),
    ( COL_GROUP.BUSHES,   COL_FLAG_VC.NONE,     25, "Hedge",                False ),
    ( COL_GROUP.ROCK,     COL_FLAG_VC.NONE,     26, "Rock",                 False ),
    ( COL_GROUP.METAL,    COL_FLAG_VC.NONE,     27, "Metal Container",      False ),
    ( COL_GROUP.METAL,    COL_FLAG_VC.NONE,     28, "Metal Barrel",         False ),
    ( COL_GROUP.MISC,     COL_FLAG_VC.NONE,     29, "Unknown",              False ),
    ( COL_GROUP.METAL,    COL_FLAG_VC.NONE,     30, "Metal Card Box",       False ),
    ( COL_GROUP.MISC,     COL_FLAG_VC.NONE,     31, "Unknown",              False ),
    ( COL_GROUP.METAL,    COL_FLAG_VC.NONE,     32, "Gate/Bars",            False ),
    ( COL_GROUP.SAND,     COL_FLAG_VC.NONE,     33, "Sand 2",               False ),
    ( COL_GROUP.GRASS,    COL_FLAG_VC.NONE,     34, "Grass 2",              False ),

    # Vehicle Presets
    ( COL_GROUP.VEHICLE,  COL_FLAG_VC.BODY,      6, "Body",                 False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_VC.BOOT,      6, "Boot",                 False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_VC.HOOD,      6, "Bonnet",               False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_VC.WIND_SH,   7, "Windshield",           False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_VC.BUMP_F,    6, "Bumper Front",         False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_VC.BUMP_R,    6, "Bumper Rear",          False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_VC.DOOR_FL,   6, "Door Front Left",      False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_VC.DOOR_FR,   6, "Door Front Right",     False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_VC.DOOR_RL,   6, "Door Rear Left",       False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_VC.DOOR_RR,   6, "Door Rear Right",      False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_VC.WING_FL,   6, "Wing Front Left",      False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_VC.WING_FR,   6, "Wing Front Right",     False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_VC.WING_RL,   6, "Wing Rear Left",       False ),
    ( COL_GROUP.VEHICLE,  COL_FLAG_VC.WING_RR,   6, "Wing Rear Right",      False ),
]


# --------------------------------------------------
# BACKWARDS COMPABILITY
# --------------------------------------------------

def _generate_sa_mats():
    result = {}
    for group_id, flag_id, mat_id, name, is_proc in COL_PRESET_SA:
        if group_id == COL_GROUP.VEHICLE:
            continue

        result[mat_id] = [group_id, name]

    return result

def _generate_vc_mats():
    result = {}
    for group_id, flag_id, mat_id, name, is_proc in COL_PRESET_VC:
        if group_id == COL_GROUP.VEHICLE:
            continue

        result[mat_id] = [group_id, name]

    return result

# Generate dictionaries
sa_mats = _generate_sa_mats()
vc_mats = _generate_vc_mats()

# Assign to new groups
groups = COL_PRESET_GROUP

# Fallback material
default = {
    "group": COL_GROUP.MISC,
    "material": 0
}

# --------------------------------------------------
# SAN ANDREAS
# --------------------------------------------------

COL_PRESET_SA = [
    # group, material, flag, name, procedural

    # Normal Materials (0-73)
    (  0,   0,  0, "Default",               False ),
    (  0,   1,  0, "Tarmac",                False ),
    (  0,   2,  0, "Tarmac (worn)",         False ),
    (  0,   3,  0, "Tarmac (very worn)",    False ),
    (  1,   4,  0, "Pavement",              False ),
    (  1,   5,  0, "Pavement (cracked)",    False ),
    (  2,   6,  0, "Gravel",                False ),
    (  1,   7,  0, "Concrete (cracked)",    False ),
    (  1,   8,  0, "Painted Ground",        False ),
    (  3,   9,  0, "Grass (short, lush)",   False ),
    (  3,  10,  0, "Grass (medium, lush)",  False ),
    (  3,  11,  0, "Grass (long, lush)",    False ),
    (  3,  12,  0, "Grass (short, dry)",    False ),
    (  3,  13,  0, "Grass (medium, dry)",   False ),
    (  3,  14,  0, "Grass (long, dry)",     False ),
    (  3,  15,  0, "Golf Grass (rough)",    False ),
    (  3,  16,  0, "Golf Grass (smooth)",   False ),
    (  3,  17,  0, "Steep Slidy Grass",     False ),
    (  9,  18,  0, "Steep Cliff",           False ),
    (  4,  19,  0, "Flower Bed",            False ),
    (  3,  20,  0, "Meadow",                False ),
    (  4,  21,  0, "Waste Ground",          False ),
    (  4,  22,  0, "Woodland Ground",       False ),
    ( 10,  23,  0, "Vegetation",            False ),
    (  4,  24,  0, "Mud (wet)",             False ),
    (  4,  25,  0, "Mud (dry)",             False ),
    (  4,  26,  0, "Dirt",                  False ),
    (  4,  27,  0, "Dirt Track",            False ),
    (  5,  28,  0, "Sand (deep)",           False ),
    (  5,  29,  0, "Sand (medium)",         False ),
    (  5,  30,  0, "Sand (compact)",        False ),
    (  5,  31,  0, "Sand (arid)",           False ),
    (  5,  32,  0, "Sand (more)",           False ),
    (  5,  33,  0, "Sand (beach)",          False ),
    (  1,  34,  0, "Concrete (beach)",      False ),
    (  9,  35,  0, "Rock (dry)",            False ),
    (  9,  36,  0, "Rock (wet)",            False ),
    (  9,  37,  0, "Rock (cliff)",          False ),
    ( 11,  38,  0, "Water (riverbed)",      False ),
    ( 11,  39,  0, "Water (shallow)",       False ),
    (  4,  40,  0, "Corn Field",            False ),
    ( 10,  41,  0, "Hedge",                 False ),
    (  7,  42,  0, "Wood (crates)",         False ),
    (  7,  43,  0, "Wood (solid)",          False ),
    (  7,  44,  0, "Wood (thin)",           False ),
    (  6,  45,  0, "Glass",                 False ),
    (  6,  46,  0, "Glass Window (large)",  False ),
    (  6,  47,  0, "Glass Window (small)",  False ),
    ( 12,  48,  0, "Empty 1",               False ),
    ( 12,  49,  0, "Empty 2",               False ),
    (  8,  50,  0, "Garage Door",           False ),
    (  8,  51,  0, "Thick Metal Plate",     False ),
    (  8,  52,  0, "Scaffold Pole",         False ),
    (  8,  53,  0, "Lamp Post",             False ),
    (  8,  54,  0, "Metal Gate",            False ),
    (  8,  55,  0, "Metal Chain fence",     False ),
    (  8,  56,  0, "Girder",                False ),
    (  8,  57,  0, "Fire Hydrant",          False ),
    (  8,  58,  0, "Container",             False ),
    (  8,  59,  0, "News Vendor",           False ),
    ( 12,  60,  0, "Wheelbase",             False ),
    ( 12,  61,  0, "Cardboard Box",         False ),
    ( 12,  62,  0, "Ped",                   False ),
    (  8,  63,  0, "Car (body)",            False ),
    (  8,  64,  0, "Car (panel)",           False ),
    (  8,  65,  0, "Car (moving)",          False ),
    ( 12,  66,  0, "Transparent Cloth",     False ),
    ( 12,  67,  0, "Rubber",                False ),
    ( 12,  68,  0, "Plastic",               False ),
    (  9,  69,  0, "Transparent Stone",     False ),
    (  7,  70,  0, "Wood (bench)",          False ),
    ( 12,  71,  0, "Carpet",                False ),
    (  7,  72,  0, "Floorboard",            False ),
    (  7,  73,  0, "Stairs (wood)",         False ),

    # Procedural Materials (74-157)
    (  5,  74,  0, "Sand",                  True  ),
    (  5,  75,  0, "Sand (dense)",          True  ),
    (  5,  76,  0, "Sand (arid)",           True  ),
    (  5,  77,  0, "Sand (compact)",        True  ),
    (  5,  78,  0, "Sand (rocky)",          True  ),
    (  5,  79,  0, "Sand (beach)",          True  ),
    (  3,  80,  0, "Grass (short)",         True  ),
    (  3,  81,  0, "Grass (meadow)",        True  ),
    (  3,  82,  0, "Grass (dry)",           True  ),
    (  4,  83,  0, "Woodland",              True  ),
    (  4,  84,  0, "Wood Dense",            True  ),
    (  2,  85,  0, "Roadside",              True  ),
    (  5,  86,  0, "Roadside Desert",       True  ),
    (  4,  87,  0, "Flowerbed",             True  ),
    (  4,  88,  0, "Waste Ground",          True  ),
    (  1,  89,  0, "Concrete",              True  ),
    ( 12,  90,  0, "Office Desk",           True  ),
    ( 12,  91,  0, "Shelf 711 1",           True  ),
    ( 12,  92,  0, "Shelf 711 2",           True  ),
    ( 12,  93,  0, "Shelf 711 3",           True  ),
    ( 12,  94,  0, "Restuarant Table",      True  ),
    ( 12,  95,  0, "Bar Table",             True  ),
    (  5,  96,  0, "Underwater (lush)",     True  ),
    (  5,  97,  0, "Underwater (barren)",   True  ),
    (  5,  98,  0, "Underwater (coral)",    True  ),
    (  5,  99,  0, "Underwater (deep)",     True  ),
    (  4, 100,  0, "Riverbed",              True  ),
    (  2, 101,  0, "Rubble",                True  ),
    ( 12, 102,  0, "Bedroom Floor",         True  ),
    ( 12, 103,  0, "Kitchen Floor",         True  ),
    ( 12, 104,  0, "Livingroom Floor",      True  ),
    ( 12, 105,  0, "Corridor Floor",        True  ),
    ( 12, 106,  0, "711 Floor",             True  ),
    ( 12, 107,  0, "Fast Food Floor",       True  ),
    ( 12, 108,  0, "Skanky Floor",          True  ),
    (  9, 109,  0, "Mountain",              True  ),
    (  4, 110,  0, "Marsh",                 True  ),
    ( 10, 111,  0, "Bushy",                 True  ),
    ( 10, 112,  0, "Bushy (mix)",           True  ),
    ( 10, 113,  0, "Bushy (dry)",           True  ),
    ( 10, 114,  0, "Bushy (mid)",           True  ),
    (  3, 115,  0, "Grass (wee flowers)",   True  ),
    (  3, 116,  0, "Grass (dry, tall)",     True  ),
    (  3, 117,  0, "Grass (lush, tall)",    True  ),
    (  3, 118,  0, "Grass (green, mix)",    True  ),
    (  3, 119,  0, "Grass (brown, mix)",    True  ),
    (  3, 120,  0, "Grass (low)",           True  ),
    (  3, 121,  0, "Grass (rocky)",         True  ),
    (  3, 122,  0, "Grass (small trees)",   True  ),
    (  4, 123,  0, "Dirt (rocky)",          True  ),
    (  4, 124,  0, "Dirt (weeds)",          True  ),
    (  3, 125,  0, "Grass (weeds)",         True  ),
    (  4, 126,  0, "River Edge",            True  ),
    (  1, 127,  0, "Poolside",              True  ),
    (  4, 128,  0, "Forest (stumps)",       True  ),
    (  4, 129,  0, "Forest (sticks)",       True  ),
    (  4, 130,  0, "Forest (leaves)",       True  ),
    (  5, 131,  0, "Desert Rocks",          True  ),
    (  4, 132,  0, "Forest (dry)",          True  ),
    (  4, 133,  0, "Sparse Flowers",        True  ),
    (  2, 134,  0, "Building Site",         True  ),
    (  1, 135,  0, "Docklands",             True  ),
    (  1, 136,  0, "Industrial",            True  ),
    (  1, 137,  0, "Industrial Jetty",      True  ),
    (  1, 138,  0, "Concrete (litter)",     True  ),
    (  1, 139,  0, "Alley Rubbish",         True  ),
    (  2, 140,  0, "Junkyard Piles",        True  ),
    (  4, 141,  0, "Junkyard Ground",       True  ),
    (  4, 142,  0, "Dump",                  True  ),
    (  5, 143,  0, "Cactus Dense",          True  ),
    (  1, 144,  0, "Airport Ground",        True  ),
    (  4, 145,  0, "Cornfield",             True  ),
    (  3, 146,  0, "Grass (light)",         True  ),
    (  3, 147,  0, "Grass (lighter)",       True  ),
    (  3, 148,  0, "Grass (lighter 2)",     True  ),
    (  3, 149,  0, "Grass (mid 1)",         True  ),
    (  3, 150,  0, "Grass (mid 2)",         True  ),
    (  3, 151,  0, "Grass (dark)",          True  ),
    (  3, 152,  0, "Grass (dark 2)",        True  ),
    (  3, 153,  0, "Grass (dirt mix)",      True  ),
    (  9, 154,  0, "Riverbed (stone)",      True  ),
    (  4, 155,  0, "Riverbed (shallow)",    True  ),
    (  4, 156,  0, "Riverbed (weeds)",      True  ),
    (  5, 157,  0, "Seaweed",               True  ),

    # Normal Materials (158-178)
    ( 12, 158,  0, "Door",                  False ),
    ( 12, 159,  0, "Plastic Barrier",       False ),
    (  3, 160,  0, "Park Grass",            False ),
    (  9, 161,  0, "Stairs (stone)",        False ),
    (  8, 162,  0, "Stairs (metal)",        False ),
    ( 12, 163,  0, "Stairs (carpet)",       False ),
    (  8, 164,  0, "Floor (metal)",         False ),
    (  1, 165,  0, "Floor (concrete)",      False ),
    ( 12, 166,  0, "Bin Bag",               False ),
    (  8, 167,  0, "Thin Metal Sheet",      False ),
    (  8, 168,  0, "Metal Barrel",          False ),
    ( 12, 169,  0, "Plastic Cone",          False ),
    ( 12, 170,  0, "Plastic Dumpster",      False ),
    (  8, 171,  0, "Metal Dumpster",        False ),
    (  7, 172,  0, "Wood Picket Fence",     False ),
    (  7, 173,  0, "Wood Slatted Fence",    False ),
    (  7, 174,  0, "Wood Ranch Fence",      False ),
    (  6, 175,  0, "Unbreakable Glass",     False ),
    ( 12, 176,  0, "Hay Bale",              False ),
    ( 12, 177,  0, "Gore",                  False ),
    ( 12, 178,  0, "Rail Track",            False ),

    # Vehicle Presets
    ( 13,  63,  0, "Body",                  False ),
    ( 13,  63,  2, "Boot",                  False ),
    ( 13,  63,  1, "Bonnet",                False ),
    ( 13,  45, 19, "Windshield",            False ),
    ( 13,  63,  3, "Bumper Front",          False ),
    ( 13,  63,  4, "Bumper Rear",           False ),
    ( 13,  63,  5, "Door Front Left",       False ),
    ( 13,  63,  6, "Door Front Right",      False ),
    ( 13,  63,  7, "Door Rear Left",        False ),
    ( 13,  63,  8, "Door Rear Right",       False ),
    ( 13,  63,  9, "Wing Front Left",       False ),
    ( 13,  63, 10, "Wing Front Right",      False ),
    ( 13,  63, 11, "Wing Rear Left",        False ),
    ( 13,  63, 12, "Wing Rear Right",       False ),
    ( 13,  64,  0, "Flying Part",           False ),
    ( 13,  65,  0, "Moving Part",           False ),
]


# --------------------------------------------------
# VICE CITY
# --------------------------------------------------

COL_PRESET_VC = [
    # group, material, flag, name, procedural

    # Normal Materials (0-34)
    (  0,   0,  0, "Default",               False ),
    (  0,   1,  0, "Street",                False ),
    (  3,   2,  0, "Grass",                 False ),
    (  4,   3,  0, "Mud",                   False ),
    (  4,   4,  0, "Dirt",                  False ),
    (  1,   5,  0, "Concrete",              False ),
    (  8,   6,  0, "Aluminum",              False ),
    (  6,   7,  0, "Glass",                 False ),
    (  8,   8,  0, "Metal Pole",            False ),
    ( 12,   9,  0, "Door",                  False ),
    (  8,  10,  0, "Metal Sheet",           False ),
    (  8,  11,  0, "Metal",                 False ),
    (  8,  12,  0, "Small Metal Post",      False ),
    (  8,  13,  0, "Large Metal Post",      False ),
    (  8,  14,  0, "Medium Metal Post",     False ),
    (  8,  15,  0, "Steel",                 False ),
    (  8,  16,  0, "Fence",                 False ),
    ( 12,  17,  0, "Unknown",               False ),
    (  5,  18,  0, "Sand",                  False ),
    ( 11,  19,  0, "Water",                 False ),
    (  7,  20,  0, "Wooden Box",            False ),
    (  7,  21,  0, "Wooden Lathes",         False ),
    (  7,  22,  0, "Wood",                  False ),
    (  8,  23,  0, "Metal Box 1",           False ),
    (  8,  24,  0, "Metal Box 2",           False ),
    ( 10,  25,  0, "Hedge",                 False ),
    (  9,  26,  0, "Rock",                  False ),
    (  8,  27,  0, "Metal Container",       False ),
    (  8,  28,  0, "Metal Barrel",          False ),
    ( 12,  29,  0, "Unknown",               False ),
    (  8,  30,  0, "Metal Card Box",        False ),
    ( 12,  31,  0, "Unknown",               False ),
    (  8,  32,  0, "Gate/Bars",             False ),
    (  5,  33,  0, "Sand 2",                False ),
    (  3,  34,  0, "Grass 2",               False ),

    # Vehicle Presets
    ( 13,   6,  0, "Body",                  False ),
    ( 13,   6,  2, "Boot",                  False ),
    ( 13,   6,  1, "Bonnet",                False ),
    ( 13,   7, 17, "Windshield",            False ),
    ( 13,   6,  3, "Bumper Front",          False ),
    ( 13,   6,  4, "Bumper Rear",           False ),
    ( 13,   6,  5, "Door Front Left",       False ),
    ( 13,   6,  6, "Door Front Right",      False ),
    ( 13,   6,  7, "Door Rear Left",        False ),
    ( 13,   6,  8, "Door Rear Right",       False ),
    ( 13,   6,  9, "Wing Front Left",       False ),
    ( 13,   6, 10, "Wing Front Right",      False ),
    ( 13,   6, 11, "Wing Rear Left",        False ),
    ( 13,   6, 12, "Wing Rear Right",       False ),
]


# --------------------------------------------------
# GROUPS
# --------------------------------------------------

COL_PRESET_GROUP = {
    0:  ["Road",     "303030"],
    1:  ["Concrete", "909090"],
    2:  ["Gravel",   "645E53"],
    3:  ["Grass",    "92C032"],
    4:  ["Dirt",     "775F40"],
    5:  ["Sand",     "E7E17E"],
    6:  ["Glass",    "A7E9FC"],
    7:  ["Wood",     "936944"],
    8:  ["Metal",    "BFC8D5"],
    9:  ["Rock",     "AFAAA0"],
    10: ["Bushes",   "2EA563"],
    11: ["Water",    "6493E1"],
    12: ["Misc",     "F1AB07"],
    13: ["Vehicle",  "FFD4FD"]
}


# --------------------------------------------------
# BACKWARDS COMPABILITY
# --------------------------------------------------

def _generate_sa_mats():
    result = {}
    for group_id, mat_id, flag_id, name, is_proc in COL_PRESET_SA:
        # Skip vehicle presets (group 13)
        if group_id == 13:
            continue

        result[mat_id] = [group_id, name]

    return result

def _generate_vc_mats():
    result = {}
    for group_id, mat_id, flag_id, name, is_proc in COL_PRESET_VC:
        # Skip vehicle presets (group 13)
        if group_id == 13:
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
    "group": 12,
    "material": 0
}

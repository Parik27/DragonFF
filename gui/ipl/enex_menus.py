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

import bpy

#######################################################
class ENEXObjectProps(bpy.types.PropertyGroup):

    exit_offset : bpy.props.FloatVectorProperty(
        name = "Exit Offset",
        description = "Exit location relative to the object's position",
        subtype = 'XYZ'
    )

    exit_angle : bpy.props.FloatProperty(
        name = "Exit Angle",
        description = "Exit angle along the Z axis",
        subtype = 'ANGLE'
    )

    interior : bpy.props.IntProperty(
        name = "Interior",
        description = "The target interior number",
        min = 0
    )

    interior_name : bpy.props.StringProperty(
        name = "Interior Name",
        description = "Interior name, used to find counterpart and to identify via mission script",
        maxlen = 7
    )

    sky : bpy.props.IntProperty(
        name = "Sky",
        description = "Sky color changer",
        min = 0,
        max = 30
    )

    peds : bpy.props.IntProperty(
        name = "Peds",
        description = "Number of peds to spawn in interior",
        min = 0
    )

    time_on : bpy.props.IntProperty(
        name = "Time On",
        description = "Enables the marker at this time",
        min = 0,
        max = 24,
        default = 0
    )

    time_off : bpy.props.IntProperty(
        name = "Time Off",
        description = "Disables the marker at this time",
        min = 0,
        max = 24,
        default = 24
    )

    flags : bpy.props.EnumProperty(
        name = "Flags",
        items = (
            ('1', 'Unknown interior',
            'Only used for interior markers',
            0, (1<<0)),

            ('2', 'Unknown pairing',
            'Used mostly for interior markers; also Big Ear & LS Skyscraper',
            0, (1<<1)),

            ('4', 'Create linked pair',
            'Pair with unflagged mate during new game start',
            0, (1<<2)),

            ('8', 'Reward interior',
            'Sets flag 0010 (Unknown pairing) on pair mate when used',
            0, (1<<3)),

            ('16', 'Used reward entrance',
            'Set by accessing reward interior',
            0, (1<<4)),

            ('32', 'Cars and aircraft',
            'Enable for cars and aircraft',
            0, (1<<5)),

            ('64', 'Bikes and motorcycles',
            'Enable for bikes and motorcycles',
            0, (1<<6)),

            ('128', 'Disable on foot',
            'No foot traffic. Use for cars and/or bikes only',
            0, (1<<7)),

            ('256', 'Accept NPC group',
            'Group members accepted at destination of pair (passengers stripped)',
            0, (1<<8)),

            ('512', 'Food date',
            'Set and cleared by food date (cut-scene related)',
            0, (1<<9)),

            ('1024', 'Unknown burglary',
            'Set on Bayside and Temporary Burglary doors',
            0, (1<<10)),

            ('2048', 'Disable exit',
            'Player can enter but cannot exit a two-way pair',
            0, (1<<11)),

            ('4096', 'Burglary access',
            'Enabled and disabled during Burglary',
            0, (1<<12)),

            ('8192', 'Entered without exit',
            'Set by Entrance, cleared by Exit; applies to one side of a two',
            0, (1<<13)),

            ('16384', 'Enable access',
            'Enabled by default; often cleared by scripts',
            0, (1<<14)),

            ('32768', 'Delete enex',
            'Enex is deleted when used',
            0, (1<<15)),
        ),
        options = {'ENUM_FLAG'}
    )

#######################################################
class ENEXMenus:

    #######################################################
    def draw_menu(layout, context):
        obj = context.object

        settings = obj.dff.enex

        box = layout.box()
        box.prop(settings, "exit_offset")
        box.prop(settings, "exit_angle")
        box.prop(settings, "interior")
        box.prop(settings, "interior_name")
        box.prop(settings, "sky")
        box.prop(settings, "peds")
        box.prop(settings, "time_on")
        box.prop(settings, "time_off")

        box = layout.box()
        box.label(text="Flags")
        box.prop(settings, "flags")

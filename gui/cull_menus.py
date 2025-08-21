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

from ..gtaLib.data.map_data import game_version

#######################################################
class CULLObjectProps(bpy.types.PropertyGroup):

    flags : bpy.props.EnumProperty(
        name = "Flags",
        items = (
            ('1', 'Cam Close In For Player',
             'Camera close in into player using closest third-person view camera mode,'
                'does not close in if in first person or cinematic mode, camera mode cannot be changed while in the zone',
             0, (1<<0)),

            ('2', 'Cam Stairs For Player',
             'Camera remotely placed outside the zone, no control of camera, camera mode cannot be changed while in the zone',
             0, (1<<1)),

            ('4', 'Cam 1st Person For Player',
             'Lowers the camera angle on boats',
             0, (1<<2)),

            ('8', 'No Rain',
             'Rain-free, police helicopter-free zone',
             0, (1<<3)),

            ('16', 'No Police',
             'They will only exit if you do something to them (like shoot it).'
                'Cops both on foot and in vehicles will not chase you but can shoot at you',
             0, (1<<4)),

            ('32', 'Flag 32',
             '',
             0, (1<<5)),

            ('64', 'Do Need To Load Collision',
             '',
             0, (1<<6)),

            ('128', 'Flag 128',
             '',
             0, (1<<7)),

            ('256', 'Police Abandon Cars',
             'Police will always exit their vehicles once they are spawned ONLY IF you have a wanted level'
                "If you don't, they'll drive normally",
             0, (1<<8)),

            ('512', 'In Room For Audio',
             '',
             0, (1<<9)),

            ('1024', 'Water Fudge',
             'Some visual ocean water effects are removed like the transparent waves and sparkles on the water',
             0, (1<<10)),

            ('2048', 'Flag 2048',
             '',
             0, (1<<11)),

            ('4096', 'Military Zone',
             '5-Star Military zone',
             0, (1<<12)),

            ('8192', 'Flag 8192',
             '',
             0, (1<<13)),

            ('16384', 'Extra Air Resistance',
             "Doesn't allow cars to reach top speed",
             0, (1<<14)),

            ('32768', 'Fewer Cars',
             "Spawn fewer cars in this area",
             0, (1<<15)),
        ),
        options = {'ENUM_FLAG'}
    )

    wanted_level_drop : bpy.props.IntProperty(
        name = "Wanted Level Drop"
    )

    mirror_enabled : bpy.props.BoolProperty(
        name = "Enable Mirror"
    )

    mirror_axis : bpy.props.EnumProperty(
        name = "Mirror Axis",
        description = "Mirror direction",
        items = (
            ('AXIS_X', 'X', ''),
            ('AXIS_Y', 'Y', ''),
            ('AXIS_Z', 'Z', ''),
            ('AXIS_NEGATIVE_X', '-X', ''),
            ('AXIS_NEGATIVE_Y', '-Y', ''),
            ('AXIS_NEGATIVE_Z', '-Z', ''),
        ),
        default = 'AXIS_Z'
    )

    mirror_coordinate : bpy.props.FloatProperty(
        name = "Mirror Coordinate",
        description = "Mirror plane coordinate in direction axis"
    )

#######################################################
class CULLMenus:

    #######################################################
    def draw_menu(layout, context):
        obj = context.object

        settings = obj.dff.cull
        game_id = context.scene.dff.game_version_dropdown

        layout.prop(context.scene.dff, "game_version_dropdown", text="Game")

        box = layout.box()

        if game_id in (game_version.III, game_version.VC):
            box.prop(settings, "wanted_level_drop")
        else:
            box.prop(settings, "mirror_enabled")
            if settings.mirror_enabled:
                box.prop(settings, "mirror_axis")
                box.prop(settings, "mirror_coordinate")

        box = layout.box()
        box.label(text="Flags")
        box.prop(settings, "flags")

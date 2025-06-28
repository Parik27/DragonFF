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

from ..ops.importer_common import game_version

#######################################################
class CULLObjectProps(bpy.types.PropertyGroup):

    flag_cam_close_in_for_player : bpy.props.BoolProperty(
        name = "Cam Close In For Player",
        description = "Camera close in into player using closest third-person view camera mode,"
            "does not close in if in first person or cinematic mode, camera mode cannot be changed while in the zone"
    )

    flag_cam_stairs_for_player : bpy.props.BoolProperty(
        name = "Cam Stairs For Player",
        description = "Camera remotely placed outside the zone, no control of camera, camera mode cannot be changed while in the zone"
    )

    flag_cam_1st_person_for_player : bpy.props.BoolProperty(
        name = "Cam 1st Person For Player",
        description = "Lowers the camera angle on boats"
    )

    flag_no_rain : bpy.props.BoolProperty(
        name = "No Rain",
        description = "Rain-free, police helicopter-free zone"
    )

    flag_no_police : bpy.props.BoolProperty(
        name = "No Police",
        description = "Police will not exit their vehicles voluntarily."
            "They will only exit if you do something to them (like shoot it)."
            "Cops both on foot and in vehicles will not chase you but can shoot at you"
    )

    flag_5 : bpy.props.BoolProperty(
        name = "Flag 32"
    )

    flag_do_need_to_load_collision : bpy.props.BoolProperty(
        name = "Do Need To Load Collision"
    )

    flag_7 : bpy.props.BoolProperty(
        name = "Flag 128"
    )

    flag_police_abandon_cars : bpy.props.BoolProperty(
        name = "Police Abandon Cars",
        description = "Police will always exit their vehicles once they are spawned ONLY IF you have a wanted level"
            "If you don't, they'll drive normally"
    )

    flag_in_room_for_audio : bpy.props.BoolProperty(
        name = "In Room For Audio"
    )

    flag_water_fudge : bpy.props.BoolProperty(
        name = "Water Fudge",
        description = "Some visual ocean water effects are removed like the transparent waves and sparkles on the water"
    )

    flag_military_zone : bpy.props.BoolProperty(
        name = "Military_Zone",
        description = "5-Star Military zone"
    )

    flag_extra_air_resistance : bpy.props.BoolProperty(
        name = "Extra Air Resistance",
        description = "Doesn't allow cars to reach top speed"
    )

    flag_fewer_cars : bpy.props.BoolProperty(
        name = "Fewer Cars",
        description = "Spawn fewer cars in this area"
    )

    wanted_level_drop : bpy.props.IntProperty(
        name = "Wanted Level Drop"
    )

#######################################################
class CULLMenus:

    #######################################################
    def draw_menu(layout, context):
        obj = context.object

        settings = obj.dff.cull
        game = context.scene.dff.game_version_dropdown

        layout.prop(context.scene.dff, "game_version_dropdown", text="Game")

        box = layout.box()

        if game in (game_version.III, game_version.VC):
            box.prop(settings, "wanted_level_drop")
        else:
            pass

        box = layout.box()
        box.label(text="Flags")
        box.prop(settings, "flag_cam_close_in_for_player")
        box.prop(settings, "flag_cam_stairs_for_player")
        box.prop(settings, "flag_cam_1st_person_for_player")
        box.prop(settings, "flag_no_rain")

        if game == game_version.III:
            box.prop(settings, "flag_no_police")
            box.prop(settings, "flag_5")
            box.prop(settings, "flag_do_need_to_load_collision")
            box.prop(settings, "flag_7")
            box.prop(settings, "flag_police_abandon_cars")
        elif game == game_version.VC:
            box.prop(settings, "flag_no_police")
            box.prop(settings, "flag_5")
            box.prop(settings, "flag_7")
            box.prop(settings, "flag_police_abandon_cars")
            box.prop(settings, "flag_in_room_for_audio")
            box.prop(settings, "flag_water_fudge")
        else:
            box.prop(settings, "flag_police_abandon_cars")
            box.prop(settings, "flag_in_room_for_audio")
            box.prop(settings, "flag_water_fudge")
            box.prop(settings, "flag_military_zone")
            box.prop(settings, "flag_extra_air_resistance")
            box.prop(settings, "flag_fewer_cars")

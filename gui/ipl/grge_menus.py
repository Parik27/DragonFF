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
class GRGEObjectProps(bpy.types.PropertyGroup):

    flags : bpy.props.EnumProperty(
        name = "Flags",
        items = (
            ('1', 'Door opens up and rotate', '', 0, (1<<0)),
            ('2', 'Door goes in', '', 0, (1<<1)),
            ('4', 'Camera follow players', '', 0, (1<<2)),
        ),
        options = {'ENUM_FLAG'}
    )

    grge_type : bpy.props.IntProperty(
        name = "Garage Type",
        description = "Garage type",
        min = 1
    )

    grge_name : bpy.props.StringProperty(
        name = "Garage Name",
        description = "A string which is used to manipulate the behaviour of garages through the main.scm"
    )

#######################################################
class GRGEMenus:

    #######################################################
    def draw_menu(layout, context):
        obj = context.object

        settings = obj.dff.grge

        box = layout.box()
        box.prop(settings, "grge_type")
        box.prop(settings, "grge_name")

        box = layout.box()
        box.label(text="Flags")
        box.prop(settings, "flags")

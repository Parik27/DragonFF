# GTA Blender Tools - Tools to edit basic GTA formats
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
import gui

from bpy.utils import register_class, unregister_class

# Class list to register
_classes = [
    gui.IMPORT_OT_dff
]
#######################################################
def register():

    # Register all the classes
    for cls in _classes:
        register_class(cls)

    bpy.types.INFO_MT_file_import.append(gui.import_dff_func)

#######################################################
def unregister():

    bpy.types.INFO_MT_file_import.remove(gui.import_dff_func)
    
    # Unregister all the classes
    for cls in _classes:
        unregister_class(cls)      

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
from ..gtaLib.data.col_materials import COL_PRESET_SA, COL_PRESET_VC, COL_PRESET_GROUP



#######################################################
def apply_collision_material(self, context):
    if self.col_mat_enum != "NONE":

        mat_id, flag_id = self.col_mat_enum.split('|')
        mat_id = int(mat_id)
        flag_id = int(flag_id)
    
        # Assign to material or object based on active context
        if context.object:
            obj = context.object
            mat = context.material
        
            # If it's a mesh
            if mat and obj.type == 'MESH':
                mat.dff.col_mat_index = mat_id
                mat.dff.col_flags = flag_id
        
            # If it's an empty
            elif obj.type == 'EMPTY' and obj.dff.type == 'COL':
                obj.dff.col_material = mat_id
                obj.dff.col_flags = flag_id


#######################################################
def get_col_mat_items(self, context):
    items = [("NONE", "Select a material below", "")]
    scn = context.scene
    mats = COL_PRESET_SA if scn.dff_col.col_game_vers == "SA" else COL_PRESET_VC
    
    for gid, mat_id, flag_id, name, is_proc in mats:
        if gid != int(scn.dff_col.col_mat_group):
            continue
        
        if scn.dff_col.col_game_vers == "VC" and scn.dff_col.col_mat_proc:
            continue
        
        if scn.dff_col.col_game_vers == "SA":
            if scn.dff_col.col_mat_norm and is_proc:
                continue
            if scn.dff_col.col_mat_proc and not is_proc:
                continue

        items.append((f"{mat_id}|{flag_id}", name, ""))

    return items


#######################################################
def update_type(self, context, changed):
    if changed == "normal" and self.col_mat_norm:
        self.col_mat_proc = False
    elif changed == "proc" and self.col_mat_proc:
        self.col_mat_norm = False

    if not self.col_mat_norm and not self.col_mat_proc:
        if changed == "normal":
            self.col_mat_norm = True
        else:
            self.col_mat_proc = True


#######################################################
def draw_col_preset_helper(layout, context):

    box = layout.box()
    box.label(text="Collision Presets")

    split = box.split(factor=0.4)
    split.label(text="Game")
    split.prop(context.scene.dff_col, "col_game_vers", text="")

    split = box.split(factor=0.4)
    split.label(text="Group")
    split.prop(context.scene.dff_col, "col_mat_group", text="")

    row = box.row(align=True)
    row.prop(context.scene.dff_col, "col_mat_norm", toggle=True)
    row.prop(context.scene.dff_col, "col_mat_proc", toggle=True)

    box.prop(context.object.dff.col_mat, "col_mat_enum", expand=True)


#######################################################
def reset_col_mat_enum(self, context):
    obj = context.object
    if obj and hasattr(obj.dff, "col_mat"):
        obj.dff.col_mat.col_mat_enum = "NONE"


#######################################################
class COLSceneProps(bpy.types.PropertyGroup):
    col_game_vers: bpy.props.EnumProperty(
        items=[("SA", "San Andreas", ""), ("VC", "Vice City", "")],
        default="SA",
        update=reset_col_mat_enum
    )
  
    col_mat_group: bpy.props.EnumProperty(
        items=[(str(k), v[0], "", v[1], k) for k, v in COL_PRESET_GROUP.items()],
        update=reset_col_mat_enum
    )
  
    col_mat_norm: bpy.props.BoolProperty(
        name="Normal",
        default=True,
        update=lambda self, context: (update_type(self, context, "normal"), reset_col_mat_enum(self, context))
    )
  
    col_mat_proc: bpy.props.BoolProperty(
        name="Procedural",
        default=False,
        update=lambda self, context: (update_type(self, context, "proc"), reset_col_mat_enum(self, context))
    )


########################################################
class COLMaterialEnumProps(bpy.types.PropertyGroup):  
    col_mat_enum: bpy.props.EnumProperty(  
        name="Material",  
        items=get_col_mat_items,  
        update=apply_collision_material  
    )
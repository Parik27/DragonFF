import bpy
from ..gtaLib.data.col_materials import COL_PRESET_SA, COL_PRESET_VC, COL_PRESET_GROUP

_ENUM_CACHE = {}

########################################################
def generate_col_mat_enums():
    global _ENUM_CACHE

    for game in ["SA", "VC"]:
        mats = COL_PRESET_SA if game == "SA" else COL_PRESET_VC

        for group_id in COL_PRESET_GROUP.keys():

            normal_items = [("NONE", "Select a material below", "")]
            proc_items = [("NONE", "Select a material below", "")]

            for gid, flag_id, mat_id, name, is_proc in mats:
                if gid != group_id:
                    continue

                item = (f"{flag_id}|{mat_id}", name, "")

                if game == "VC":
                    normal_items.append(item)
                else:
                    if is_proc:
                        proc_items.append(item)
                    else:
                        normal_items.append(item)

            _ENUM_CACHE[f"{game}_{group_id}_normal"] = normal_items
            _ENUM_CACHE[f"{game}_{group_id}_proc"] = proc_items

generate_col_mat_enums()


#######################################################
def get_col_mat_items_normal(self, context):
    scn = context.scene
    game = scn.dff_col.col_game_vers
    group = scn.dff_col.col_mat_group
    key = f"{game}_{group}_normal"
    return _ENUM_CACHE.get(key, [("NONE", "No materials", "")])

def get_col_mat_items_proc(self, context):
    scn = context.scene
    game = scn.dff_col.col_game_vers
    group = scn.dff_col.col_mat_group
    key = f"{game}_{group}_proc"
    return _ENUM_CACHE.get(key, [("NONE", "No materials", "")])


#######################################################
def apply_collision_material(self, context):
    if self.col_mat_enum_normal != "NONE":
        enum_value = self.col_mat_enum_normal
    elif self.col_mat_enum_proc != "NONE":
        enum_value = self.col_mat_enum_proc
    else:
        return

    flag_id, mat_id = enum_value.split('|')
    flag_id = int(flag_id)
    mat_id = int(mat_id)

    if context.object:
        obj = context.object
        mat = context.material

        if mat and obj.type == 'MESH':
            mat.dff.col_mat_index = mat_id
            mat.dff.col_flags = flag_id

        elif obj.type == 'EMPTY' and obj.dff.type == 'COL':
            obj.dff.col_material = mat_id
            obj.dff.col_flags = flag_id


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

    if context.scene.dff_col.col_mat_norm:
        box.prop(context.object.dff.col_mat, "col_mat_enum_normal", expand=True)
    else:
        box.prop(context.object.dff.col_mat, "col_mat_enum_proc", expand=True)


#######################################################
def reset_col_mat_enum(self, context):
    obj = context.object
    if obj and hasattr(obj.dff, "col_mat"):
        obj.dff.col_mat.col_mat_enum_normal = "NONE"
        obj.dff.col_mat.col_mat_enum_proc = "NONE"


########################################################
def update_col_mat_norm(self, context):
    update_type(self, context, "normal")
    reset_col_mat_enum(self, context)


#########################################################
def update_col_mat_proc(self, context):
    update_type(self, context, "proc")
    reset_col_mat_enum(self, context)


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
        update=update_col_mat_norm
    )

    col_mat_proc: bpy.props.BoolProperty(
        name="Procedural",
        default=False,
        update=update_col_mat_proc
    )


########################################################
class COLMaterialEnumProps(bpy.types.PropertyGroup):
    col_mat_enum_normal: bpy.props.EnumProperty(
        name="Material",
        items=get_col_mat_items_normal,
        update=apply_collision_material
    )

    col_mat_enum_proc: bpy.props.EnumProperty(
        name="Material",
        items=get_col_mat_items_proc,
        update=apply_collision_material
    )
# GTA DragonFF - Blender scripts to edit basic GTA formats
# Copyright (C) 2019  Parik

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License, either version 3
# of the License, or (at your option) any later version.

# Helper for games that split a character into several .dff files where each
# part carries its own (partial) skeleton.  Those parts import fine on their
# own but end up next to each other instead of forming one character, because
# nothing in the .dff tells Blender how the rigs relate to each other.

# For 轩辕剑外传：云之遥 (and the other 轩辕剑五 titles) the relation is:
#   * b* (body) and h* (hair) share one and the same skeleton -> already aligned
#   * f* (face/head) uses its own small rig whose root frame is called
#     "face-center".  In the body skeleton "face-center" is a child of the head
#     bone ("5400", i.e. Bip01's head) and sits exactly on it, so the face rig
#     simply has to be translated by
#           head_bone_world_position - face_center_world_position
# The same is true for the other NPC/character models of these games.

import bpy
import mathutils

# Bone names used as the attachment point on the main skeleton (first hit wins)
MAIN_ATTACH_BONES = (
    "face-center",
    "5400",
    "Bip01 Head",
    "Bip01 HeadNub",
    "Head",
    "head",
)

# Bone names that identify a part which carries its own rig
PART_ROOT_BONES = (
    "face-center",
)


#######################################################
def find_bone(armature, candidates):
    for name in candidates:
        if name in armature.data.bones:
            return name
    return None


#######################################################
def bone_world_location(armature, bone_name):
    """World space location of a bone, without requiring a mode change."""

    if not bone_name:
        return None

    pose_bone = armature.pose.bones.get(bone_name)
    if pose_bone is not None:
        return (armature.matrix_world @ pose_bone.matrix).translation.copy()

    bone = armature.data.bones.get(bone_name)
    if bone is not None:
        return (armature.matrix_world @ bone.matrix_local).translation.copy()

    return None


#######################################################
class OBJECT_OT_dff_assemble_parts(bpy.types.Operator):
    """Attach character parts that use their own rig to the main skeleton"""

    bl_idname      = "object.dff_assemble_parts"
    bl_label       = "Assemble Character Parts"
    bl_description = ("Move parts with their own rig (face/head) onto the head "
                      "bone of the biggest skeleton")
    bl_options     = {'REGISTER', 'UNDO'}

    use_selection: bpy.props.BoolProperty(
        name="Only Selected",
        description="Only consider the currently selected objects",
        default=True
    )

    #######################################################
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    #######################################################
    def execute(self, context):

        objects = (context.selected_objects if self.use_selection
                   else list(context.scene.objects))

        armatures = [obj for obj in objects if obj.type == 'ARMATURE']

        # Parts that are not armatures themselves but belong to one
        for obj in list(objects):
            if obj.type != 'ARMATURE' and obj.parent is not None \
                    and obj.parent.type == 'ARMATURE' \
                    and obj.parent not in armatures:
                armatures.append(obj.parent)

        if len(armatures) < 2:
            self.report({'WARNING'},
                        "Select (or import) at least two skeletons first")
            return {'CANCELLED'}

        main = max(armatures, key=lambda arm: len(arm.data.bones))
        attach_bone = find_bone(main, MAIN_ATTACH_BONES)

        if attach_bone is None:
            self.report({'WARNING'},
                        "No head bone found on '%s'" % main.name)
            return {'CANCELLED'}

        target = bone_world_location(main, attach_bone)
        if target is None:
            self.report({'WARNING'}, "Could not evaluate '%s'" % attach_bone)
            return {'CANCELLED'}

        moved = 0
        for arm in armatures:

            if arm is main:
                continue

            root_bone = find_bone(arm, PART_ROOT_BONES)
            if root_bone is None:
                continue

            current = bone_world_location(arm, root_bone)
            if current is None:
                continue

            delta = target - current
            if delta.length < 1e-6:
                continue

            arm.matrix_world = mathutils.Matrix.Translation(delta) @ arm.matrix_world
            moved += 1

            self.report({'INFO'},
                        "'%s' moved by (%.4f, %.4f, %.4f) onto '%s' of '%s'"
                        % (arm.name, delta.x, delta.y, delta.z,
                           attach_bone, main.name))

        if not moved:
            self.report({'INFO'}, "Nothing to assemble - parts already aligned")
            return {'CANCELLED'}

        return {'FINISHED'}

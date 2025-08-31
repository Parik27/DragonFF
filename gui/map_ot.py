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
import math
import os
import time

from bpy_extras.io_utils import ImportHelper, ExportHelper

from ..ops import map_importer, ide_exporter, ipl_exporter
from ..ops.ipl.cull_importer import cull_importer
from ..ops.ipl.grge_importer import grge_importer
from ..ops.ipl.enex_importer import enex_importer
from ..ops.importer_common import link_object
from ..gtaLib.data import map_data

#######################################################
class SCENE_OT_dff_import_map(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "scene.dragonff_map_import"
    bl_label = "Import map section"

    _timer = None
    _updating = False
    _progress_current = 0
    _progress_total = 0
    _importer = None

    _inst_index = 0
    _inst_loaded = False

    _col_index = 0
    _col_loaded = True

    _cull_loaded = True
    _grge_loaded = True
    _enex_loaded = True

    #######################################################
    def modal(self, context, event):

        if event.type in {'ESC'}:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER' and not self._updating:
            self._updating = True

            importer = self._importer

            # Import CULL if there are any left to load
            if not self._cull_loaded:

                for cull in importer.cull_instances:
                    importer.import_cull(context, cull)

                self._progress_current += 1
                self._cull_loaded = True

            # Import GRGE if there are any left to load
            elif not self._grge_loaded:

                for grge in importer.grge_instances:
                    importer.import_grge(context, grge)

                self._progress_current += 1
                self._grge_loaded = True

            # Import ENEX if there are any left to load
            elif not self._enex_loaded:

                for enex in importer.enex_instances:
                    importer.import_enex(context, enex)

                self._progress_current += 1
                self._enex_loaded = True

            # Import collision files if there are any left to load
            elif not self._col_loaded:
                num_objects_at_once = 5
                cols_num = len(importer.col_files)

                for _ in range(num_objects_at_once):
                    if self._col_index >= cols_num:
                        self._col_loaded = True
                        break

                    # Fetch next collision
                    col_file = importer.col_files[self._col_index]
                    self._col_index += 1

                    importer.import_collision(context, col_file)
                    self._progress_current += 1

            # Import objcets instances
            else:
                # As the number of objects increases, loading performance starts to get crushed by scene updates, so
                # we try to keep loading at least 5% of the total scene object count on each timer pulse.
                num_objects_at_once = max(10, int(0.05 * len(bpy.data.objects)))
                instances_num = len(importer.object_instances)

                for _ in range(num_objects_at_once):
                    if self._inst_index >= instances_num:
                        self._inst_loaded = True
                        break

                    # Fetch next instance
                    inst = importer.object_instances[self._inst_index]
                    self._inst_index += 1

                    try:
                        importer.import_object_instance(context, inst)
                    except:
                        print("Can`t import model... skipping")

                    self._progress_current += 1

            # Update cursor progress indicator if something needs to be loaded
            progress = (
                float(self._progress_current) / float(self._progress_total)
            ) if self._progress_total else 100

            context.window_manager.progress_update(progress)

            # Update dependency graph
            dg = context.evaluated_depsgraph_get()
            dg.update()

            self._updating = False

        if self._inst_loaded:
            self.cancel(context)
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    #######################################################
    def execute(self, context):

        settings = context.scene.dff
        self._importer = map_importer.load_map(settings)

        self._progress_current = 0
        self._progress_total = 0

        self._inst_index = 0
        self._inst_loaded = False
        self._progress_total += len(self._importer.object_instances)

        if self._importer.cull_instances:
            self._cull_loaded = False
            self._progress_total += 1
        else:
            self._cull_loaded = True

        if self._importer.grge_instances:
            self._grge_loaded = False
            self._progress_total += 1
        else:
            self._grge_loaded = True

        if self._importer.enex_instances:
            self._enex_loaded = False
            self._progress_total += 1
        else:
            self._enex_loaded = True

        if self._importer.col_files:
            self._col_index = 0
            self._col_loaded = False
            self._progress_total += len(self._importer.col_files)
        else:
            self._col_loaded = True

        wm = context.window_manager
        wm.progress_begin(0, 100.0)

         # Call the "modal" function every 0.1s
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    #######################################################
    def cancel(self, context):
        wm = context.window_manager
        wm.progress_end()
        wm.event_timer_remove(self._timer)

#######################################################
class SCENE_OT_ipl_select(bpy.types.Operator, ImportHelper):

    bl_idname = "scene.select_ipl"
    bl_label = "Select IPL File"

    filename_ext = ".ipl"

    filter_glob : bpy.props.StringProperty(
        default="*.ipl",
        options={'HIDDEN'})

    def invoke(self, context, event):
        self.filepath = context.scene.dff.game_root + "/data/maps/"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if os.path.splitext(self.filepath)[-1].lower() == self.filename_ext:
            filepath = os.path.normpath(self.filepath)
            # Try to find if the file is within the game directory structure
            sep_pos = filepath.upper().find(f"data{os.sep}maps")

            if sep_pos != -1:
                # File is within game directory, use relative path
                game_root = filepath[:sep_pos]
                context.scene.dff.game_root = game_root
                context.scene.dff.custom_ipl_path = os.path.relpath(filepath, game_root)
            else:
                # File is outside game directory, use absolute path
                # Don't change game_root, keep the existing one
                context.scene.dff.custom_ipl_path = filepath
        return {'FINISHED'}

#######################################################
class EXPORT_OT_ide(bpy.types.Operator, ExportHelper):
    """Export IDE file"""
    bl_idname           = "export_scene.dff_ide"
    bl_description      = "Export a GTA IDE File"
    bl_label            = "DragonFF IDE (.ide)"
    filename_ext        = ".ide"

    filepath            : bpy.props.StringProperty(name="File path",
                                              maxlen=1024,
                                              default="",
                                              subtype='FILE_PATH')

    filter_glob         : bpy.props.StringProperty(default="*.ide",
                                              options={'HIDDEN'})

    only_selected       : bpy.props.BoolProperty(
        name            = "Only Selected",
        description     = "Export only selected objects",
        default         = False
    )

    #######################################################
    def draw(self, context):
        settings = context.scene.dff

        layout = self.layout

        layout.prop(self, "only_selected")
        layout.prop(settings, "game_version_dropdown", text="Game")

    #######################################################
    def execute(self, context):
        settings = context.scene.dff
        game_id = settings.game_version_dropdown

        start = time.time()
        try:
            ide_exporter.export_ide(
                {
                    "file_name"     : self.filepath,
                    "only_selected" : self.only_selected,
                    "game_id"       : game_id,
                }
            )

            total_objs_num = len(ide_exporter.ide_exporter.objs_objects)
            total_tobj_num = len(ide_exporter.ide_exporter.tobj_objects)
            total_anim_num = len(ide_exporter.ide_exporter.anim_objects)

            if not (total_objs_num + total_tobj_num + total_anim_num):
                report = "No objects with IDE data found"
                self.report({"ERROR"}, report)
                return {'CANCELLED'}

            self.report(
                {"INFO"},
                f"Finished export {total_objs_num} objs, {total_tobj_num} tobj, {total_anim_num} anim "
                f"in {time.time() - start:.2f}s"
            )

        except Exception as e:
            self.report({"ERROR"}, str(e))
            return {'CANCELLED'}

        return {'FINISHED'}

#######################################################
class EXPORT_OT_ipl(bpy.types.Operator, ExportHelper):
    """Export IPL file"""
    bl_idname           = "export_scene.dff_ipl"
    bl_description      = "Export a GTA IPL File"
    bl_label            = "DragonFF IPL (.ipl)"
    filename_ext        = ".ipl"

    filepath            : bpy.props.StringProperty(name="File path",
                                              maxlen=1024,
                                              default="",
                                              subtype='FILE_PATH')

    filter_glob         : bpy.props.StringProperty(default="*.ipl",
                                              options={'HIDDEN'})

    only_selected       : bpy.props.BoolProperty(
        name            = "Only Selected",
        description     = "Export only selected objects",
        default         = False
    )

    export_inst         : bpy.props.BoolProperty(
        name            = "Export INST",
        description     = "Export INST entries",
        default         = True
    )

    export_cull         : bpy.props.BoolProperty(
        name            = "Export CULL",
        description     = "Export CULL entries",
        default         = False
    )

    export_grge         : bpy.props.BoolProperty(
        name            = "Export GRGE",
        description     = "Export GRGE entries",
        default         = False
    )

    export_enex         : bpy.props.BoolProperty(
        name            = "Export ENEX",
        description     = "Export ENEX entries",
        default         = False
    )

    #######################################################
    def draw(self, context):
        settings = context.scene.dff

        layout = self.layout

        layout.prop(self, "only_selected")
        layout.prop(settings, "game_version_dropdown", text="Game")

        box = layout.box()
        box.label(text="Export Entries")
        grid = box.grid_flow(columns=3, even_columns=True, even_rows=True)
        grid.prop(self, "export_inst", text="INST")
        grid.prop(self, "export_cull", text="CULL")

        if settings.game_version_dropdown == map_data.game_version.SA:
            grid.prop(self, "export_grge", text="GRGE")
            grid.prop(self, "export_enex", text="ENEX")

    #######################################################
    def execute(self, context):
        settings = context.scene.dff
        game_id = settings.game_version_dropdown

        export_options = {
            "file_name"     : self.filepath,
            "only_selected" : self.only_selected,
            "game_id"       : game_id,
            "export_inst"   : self.export_inst,
            "export_cull"   : self.export_cull,
        }

        if game_id == map_data.game_version.SA:
            export_options["export_grge"] = self.export_grge
            export_options["export_enex"] = self.export_enex

        start = time.time()
        try:
            ipl_exporter.export_ipl(export_options)

            total_objects_num = ipl_exporter.ipl_exporter.total_objects_num

            if not total_objects_num:
                report = "No objects with IPL data found"
                self.report({"ERROR"}, report)
                return {'CANCELLED'}

            self.report({"INFO"}, f"Finished export {total_objects_num} objects in {time.time() - start:.2f}s")

        except Exception as e:
            self.report({"ERROR"}, str(e))
            return {'CANCELLED'}

        return {'FINISHED'}

#######################################################
class OBJECT_OT_dff_add_cull(bpy.types.Operator):

    bl_idname = "object.dff_add_cull"
    bl_label = "Add CULL Zone"
    bl_description = "Add CULL zone to the scene"
    bl_options = {'REGISTER', 'UNDO'}

    location: bpy.props.FloatVectorProperty(
        name="Location",
        description="Location for the newly added object",
        subtype='XYZ',
        default=(0, 0, 0)
    )

    scale: bpy.props.FloatVectorProperty(
        name="Scale",
        description="Scale for the newly added object",
        subtype='XYZ',
        default=(1, 1, 1)
    )

    angle: bpy.props.FloatProperty(
        name="Angle",
        description="Angle along the Z axis",
        subtype='ANGLE',
        min=-math.pi * 2,
        max=math.pi * 2,
        step=100,
        default=0
    )

    #######################################################
    def invoke(self, context, event):
        self.location = context.scene.cursor.location
        return self.execute(context)

    #######################################################
    def execute(self, context):
        obj = cull_importer.create_cull_object(
            location=self.location,
            scale=self.scale,
            flags=0,
            angle=self.angle
        )
        link_object(obj, context.collection)

        context.view_layer.objects.active = obj
        for o in context.selected_objects:
            o.select_set(False)
        obj.select_set(True)

        return {'FINISHED'}

#######################################################
class OBJECT_OT_dff_add_grge(bpy.types.Operator):

    bl_idname = "object.dff_add_grge"
    bl_label = "Add GRGE Zone"
    bl_description = "Add GRGE zone to the scene"
    bl_options = {'REGISTER', 'UNDO'}

    location: bpy.props.FloatVectorProperty(
        name="Location",
        description="Location for the newly added object",
        subtype='XYZ',
        default=(0, 0, 0)
    )

    scale: bpy.props.FloatVectorProperty(
        name="Scale",
        description="Scale for the newly added object",
        subtype='XYZ',
        default=(1, 1, 1)
    )

    angle: bpy.props.FloatProperty(
        name="Angle",
        description="Angle along the Z axis",
        subtype='ANGLE',
        min=-math.pi * 2,
        max=math.pi * 2,
        step=100,
        default=0
    )

    #######################################################
    def invoke(self, context, event):
        self.location = context.scene.cursor.location
        return self.execute(context)

    #######################################################
    def execute(self, context):
        obj = grge_importer.create_grge_object(
            location=self.location,
            scale=self.scale,
            flags=0,
            angle=self.angle
        )
        obj.dff.grge.grge_type = 5
        link_object(obj, context.collection)

        context.view_layer.objects.active = obj
        for o in context.selected_objects:
            o.select_set(False)
        obj.select_set(True)

        return {'FINISHED'}

#######################################################
class OBJECT_OT_dff_add_enex(bpy.types.Operator):

    bl_idname = "object.dff_add_enex"
    bl_label = "Add ENEX Zone"
    bl_description = "Add ENEX zone to the scene"
    bl_options = {'REGISTER', 'UNDO'}

    location: bpy.props.FloatVectorProperty(
        name="Location",
        description="Location for the newly added object",
        subtype='XYZ',
        default=(0, 0, 0)
    )

    angle: bpy.props.FloatProperty(
        name="Angle",
        description="Angle along the Z axis",
        subtype='ANGLE',
        min=-math.pi * 2,
        max=math.pi * 2,
        step=100,
        default=0
    )

    #######################################################
    def invoke(self, context, event):
        self.location = context.scene.cursor.location
        return self.execute(context)

    #######################################################
    def execute(self, context):
        obj = enex_importer.create_enex_object(
            location=self.location,
            flags=0,
            angle=self.angle
        )
        obj.dff.enex.peds = 2
        link_object(obj, context.collection)

        context.view_layer.objects.active = obj
        for o in context.selected_objects:
            o.select_set(False)
        obj.select_set(True)

        return {'FINISHED'}

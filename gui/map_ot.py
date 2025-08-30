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

from bpy.props import StringProperty, CollectionProperty
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

        if self._importer.enex_instances:
            self._enex_loaded = False
            self._progress_total += 1
        else:
            self._enex_loaded = True

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
        layout = self.layout

        layout.prop(self, "only_selected")

    #######################################################
    def execute(self, context):
        start = time.time()
        try:
            ide_exporter.export_ide(
                {
                    "file_name"     : self.filepath,
                    "only_selected" : self.only_selected,
                }
            )

            total_objs_num = len(ide_exporter.ide_exporter.objs_objects)
            total_tobj_num = len(ide_exporter.ide_exporter.tobj_objects)

            if not (total_objs_num + total_tobj_num):
                report = "No objects with IDE data found"
                self.report({"ERROR"}, report)
                return {'CANCELLED'}

            self.report({"INFO"}, f"Finished export {total_objs_num} objs and {total_tobj_num} tobj in {time.time() - start:.2f}s")

        except Exception as e:
            self.report({"ERROR"}, str(e))

        return {'FINISHED'}

#######################################################
class EXPORT_OT_ipl(bpy.types.Operator, ExportHelper):
    """Export IPL file"""
    bl_idname           = "export_scene.dff_ipl"
    bl_description      = "Export a GTA IPL File"
    bl_label            = "DragonFF IPL (.ipl)"
    filename_ext        = ".ipl"

    stream_distance: bpy.props.FloatProperty(
        name="Stream Distance",
        default=300.0,
        description="Stream distance for dynamic objects"
    )
    draw_distance: bpy.props.FloatProperty(
        name="Draw Distance",
        default=300.0,
        description="Draw distance for objects"
    )
    x_offset: bpy.props.FloatProperty(
        name="X Offset",
        default=0.0,
        description="Offset for the x coordinate of the objects"
    )
    y_offset: bpy.props.FloatProperty(
        name="Y Offset",
        default=0.0,
        description="Offset for the y coordinate of the objects"
    )

    z_offset: bpy.props.FloatProperty(
        name="Z Offset",
        default=0.0,
        description="Offset for the z coordinate of the objects"
    )

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
        layout.prop(self, "x_offset")
        layout.prop(self, "y_offset")
        layout.prop(self, "z_offset")
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
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
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

#######################################################
class SCENE_OT_import_ide(bpy.types.Operator):
    """Import .IDE Files"""
    bl_idname = "scene.ide_import"
    bl_label = "Import IDE"
    bl_options = {'REGISTER', 'UNDO'}

    files: CollectionProperty(type=bpy.types.PropertyGroup)
    directory: StringProperty(subtype="DIR_PATH")

    filter_glob: StringProperty(default="*.ide", options={'HIDDEN'})

    IDE_TO_SAMP_DL_IDS = {i: 0 + i for i in range(50000)}

    #######################################################
    def assign_ide_map_properties(self, obj, ide_data):
        obj.dff_map.ide_object_id = ide_data.get("object_id", 0)
        obj.dff_map.ide_model_name = ide_data.get("model_name", "")
        obj.dff_map.ide_object_type = ide_data.get("object_type", "")
        obj.dff_map.ide_txd_name = ide_data.get("txd_name", "")
        obj.dff_map.ide_flags = ide_data.get("flags", 0)
        obj.dff_map.ide_draw_distances = ide_data.get("draw_distances", "")
        obj.dff_map.ide_draw_distance1 = ide_data.get("draw_distance1", 0.0)
        obj.dff_map.ide_draw_distance2 = ide_data.get("draw_distance2", 0.0)
    #######################################################
    def import_ide(self, filepaths, context):
        for filepath in filepaths:
            if not os.path.isfile(filepath):
                print(f"File not found: {filepath}")
                continue

            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
            except UnicodeDecodeError:
                print(f"UTF-8 decoding failed for {filepath}, attempting ASCII decoding.")
                try:
                    with open(filepath, 'r', encoding='ascii', errors='replace') as file:
                        lines = file.readlines()
                except UnicodeDecodeError:
                    print(f"Error decoding file: {filepath}")
                    continue

            obj_data = {}
            current = None  # objs / tobj / anim / None

            def try_float(s):
                try: return float(s)
                except: return None

            for raw in lines:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue

                low = line.lower()
                if low.startswith("objs"):
                    current = "objs";  continue
                if low.startswith("tobj"):
                    current = "tobj";  continue
                if low.startswith("anim"):
                    current = "anim";  continue
                if low.startswith("end"):
                    current = None;    continue
                if not current:
                    continue

                parts = [p.strip() for p in line.split(",") if p.strip() != ""]
                if len(parts) < 4:
                    print("Skipping short IDE line:", line)
                    continue

                try:
                    obj_id   = int(parts[0])
                except:
                    print("Bad id on line:", line);  continue
                model    = parts[1]
                txd_name = parts[2]

                rec = {
                    "section": current,
                    "object_id": obj_id,
                    "model_name": model,
                    "txd_name": txd_name,
                    "mesh_count": None,
                    "draw_distances": [],
                    "flags": 0,
                    "time_on": None,
                    "time_off": None,
                    "anim_name": None,
                }

                if current == "objs":
                    if len(parts) == 6:
                        rec["mesh_count"] = int(parts[3])
                        rec["draw_distances"] = [try_float(parts[4]) or 0.0]
                        rec["flags"] = int(parts[5])
                    elif len(parts) == 7:
                        rec["mesh_count"] = int(parts[3])
                        rec["draw_distances"] = [try_float(parts[4]) or 0.0,
                                                 try_float(parts[5]) or 0.0]
                        rec["flags"] = int(parts[6])
                    elif len(parts) == 8:
                        rec["mesh_count"] = int(parts[3])
                        rec["draw_distances"] = [try_float(parts[4]) or 0.0,
                                                 try_float(parts[5]) or 0.0,
                                                 try_float(parts[6]) or 0.0]
                        rec["flags"] = int(parts[7])
                    elif len(parts) == 5:
                        rec["mesh_count"] = None
                        rec["draw_distances"] = [try_float(parts[3]) or 0.0]
                        rec["flags"] = int(parts[4])
                    else:
                        print("Unknown OBJS line format:", line)
                        continue

                elif current == "tobj":
                    # SA VC: Id,Model,TXD,Draw,TimeOn,TimeOff,Flags
                    if len(parts) != 7:
                        print("Unknown TOBJ line format:", line)
                        continue
                    rec["mesh_count"] = None
                    rec["draw_distances"] = [try_float(parts[3]) or 0.0]
                    rec["time_on"]  = int(parts[4])
                    rec["time_off"] = int(parts[5])
                    rec["flags"]    = int(parts[6])

                elif current == "anim":
                    anim_name = parts[-1]
                    core = parts[:-1]
                    if len(core) == 6:
                        rec["mesh_count"] = int(core[3])
                        rec["draw_distances"] = [try_float(core[4]) or 0.0]
                        rec["flags"] = int(core[5])
                    elif len(core) == 7:
                        rec["mesh_count"] = int(core[3])
                        rec["draw_distances"] = [try_float(core[4]) or 0.0,
                                                 try_float(core[5]) or 0.0]
                        rec["flags"] = int(core[6])
                    elif len(core) == 8:
                        rec["mesh_count"] = int(core[3])
                        rec["draw_distances"] = [try_float(core[4]) or 0.0,
                                                 try_float(core[5]) or 0.0,
                                                 try_float(core[6]) or 0.0]
                        rec["flags"] = int(core[7])
                    elif len(core) == 5:
                        rec["mesh_count"] = None
                        rec["draw_distances"] = [try_float(core[3]) or 0.0]
                        rec["flags"] = int(core[4])
                    else:
                        print("Unknown ANIM line format:", line)
                        continue
                    rec["anim_name"] = anim_name

                obj_data[model] = rec

        for obj in context.scene.objects:
            base_name = obj.name.split('.')[0]
            data = obj_data.get(base_name)
            if not data or not hasattr(obj, "dff_map"):
                continue

            props = obj.dff_map

            # IDE section
            props.ide_section     = data["section"]
            props.ide_object_id   = data["object_id"]
            props.ide_model_name  = data["model_name"]
            props.ide_txd_name    = data["txd_name"]
            props.ide_flags       = data["flags"]

            # Mesh count + draw distances
            if data["mesh_count"] is not None:
                props.ide_meshes = int(data["mesh_count"])
            dds = data["draw_distances"]
            props.ide_draw1 = float(dds[0]) if len(dds) > 0 else 0.0
            props.ide_draw2 = float(dds[1]) if len(dds) > 1 else 0.0
            props.ide_draw3 = float(dds[2]) if len(dds) > 2 else 0.0

            if data["section"] == "tobj":
                props.ide_time_on  = int(data["time_on"] or 0)
                props.ide_time_off = int(data["time_off"] or 24)
            elif data["section"] == "anim":
                props.ide_anim = data["anim_name"] or ""

            props.object_id  = data["object_id"]
            props.model_name = data["model_name"]

            # Take Pawn Data from IDE unless already set
            if not props.pawn_model_name:
                props.pawn_model_name = data["model_name"]
            if not props.pawn_txd_name:
                props.pawn_txd_name   = data["txd_name"]

            print(f"Assigned IDE properties to {obj.name}")
    #######################################################
    def execute(self, context):
        filepaths = [os.path.join(self.directory, f.name) for f in self.files]
        self.import_ide(filepaths, context)
        return {'FINISHED'}
    #######################################################
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
#######################################################
class EXPORT_OT_ide(bpy.types.Operator, ExportHelper):
    bl_idname = "scene.ide_export"
    bl_label = "DragonFF IDE Export"
    bl_description = "Export a GTA IDE file (objs/tobj/anim)"
    filename_ext = ".ide"

    export_objs: bpy.props.BoolProperty(name="objs", default=True)
    export_tobj: bpy.props.BoolProperty(name="tobj", default=False)
    export_anim: bpy.props.BoolProperty(name="anim", default=False)
    only_selected: bpy.props.BoolProperty(name="Only Selected", default=False)

    filter_glob: bpy.props.StringProperty(default="*.ide", options={'HIDDEN'})

    #######################################################
    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.prop(self, "export_objs")
        col.prop(self, "export_tobj")
        col.prop(self, "export_anim")
        col.prop(self, "only_selected")
        layout.prop(context.scene.dff, "game_version_dropdown", text="Game")
    #######################################################
    def execute(self, context):
        try:
            map_exporter.export_ide({
                "file_name"    : self.filepath,
                "only_selected": self.only_selected,
                "game_id"      : context.scene.dff.game_version_dropdown,
                "export_objs"  : self.export_objs,
                "export_tobj"  : self.export_tobj,
                "export_anim"  : self.export_anim,
            })

            if not map_exporter.ide_exporter.total_definitions_num:
                self.report({"ERROR"}, "No objects with IDE data found")
                return {'CANCELLED'}

            return {'FINISHED'}

        except Exception as e:
            self.report({"ERROR"}, str(e))
            return {'CANCELLED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
#######################################################
class EXPORT_OT_pawn(bpy.types.Operator, ExportHelper):
    bl_idname = "scene.pwn_export"
    bl_label = "DragonFF Pawn Export"
    bl_description = "Export Pawn for current scene"
    filename_ext = ".pwn"

    only_selected: bpy.props.BoolProperty(
        name="Only Selected",
        default=False
    )
    stream_distance: bpy.props.FloatProperty(
        name="Stream Distance",
        default=300.0
    )
    draw_distance: bpy.props.FloatProperty(
        name="Draw Distance",
        default=300.0
    )
    x_offset: bpy.props.FloatProperty(
        name="X Offset",
        default=0.0
    )
    y_offset: bpy.props.FloatProperty(
        name="Y Offset",
        default=0.0
    )

    z_offset: bpy.props.FloatProperty(
        name="Z Offset",
        default=0.0,
        description="Offset for the z coordinate of the objects"
    )

    filter_glob : bpy.props.StringProperty(default="*.pwn;*.inc", options={'HIDDEN'})
    #######################################################
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "only_selected")
        layout.prop(self, "stream_distance")
        layout.prop(self, "draw_distance")
        layout.prop(self, "x_offset")
        layout.prop(self, "y_offset")
        layout.prop(self, "z_offset")
        layout.prop(context.scene.dff, "game_version_dropdown", text="Game")
    #######################################################
    def execute(self, context):
        try:
            map_exporter.export_pawn({
                "file_name"      : self.filepath,
                "only_selected"  : self.only_selected,
                "game_id"        : context.scene.dff.game_version_dropdown,
                "stream_distance": self.stream_distance,
                "draw_distance"  : self.draw_distance,
                "x_offset"       : self.x_offset,
                "y_offset"       : self.y_offset,
                "z_offset"       : self.z_offset,
            })

            if not map_exporter.pwn_exporter.total_objects_num:
                self.report({"ERROR"}, "No exportable meshes found")
                return {'CANCELLED'}
            return {'FINISHED'}

        except Exception as e:
            self.report({"ERROR"}, str(e))
            return {'CANCELLED'}
    #######################################################
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
#######################################################
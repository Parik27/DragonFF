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

import os
import bpy

from ..gtaLib.map import TextIPLData, MapDataUtility, SectionUtility
from ..gtaLib.data import map_data
from .cull_exporter import cull_exporter


#######################################################
def quat_xyzw(obj_or_empty):
    """Quaternion (x,y,z,w)."""
    q = getattr(obj_or_empty, "rotation_quaternion", None)
    if q is None:
        e = getattr(obj_or_empty, "rotation_euler", None)
        q = (e.to_quaternion() if e is not None else None)
    if q is None:
        return 0.0, 0.0, 0.0, 1.0
    q = q.normalized()
    return float(q.x), float(q.y), float(q.z), float(q.w)

#######################################################
def euler_xyz(obj_or_empty):
    """Euler XYZ in degrees."""
    e = getattr(obj_or_empty, "rotation_euler", None)
    if e is None:
        q = getattr(obj_or_empty, "rotation_quaternion", None)
        e = (q.to_euler('XYZ') if q is not None else None)
    if e is None:
        return 0.0, 0.0, 0.0
    rad2deg = 180.0 / 3.141592653589793
    return float(e.x*rad2deg), float(e.y*rad2deg), float(e.z*rad2deg)
#######################################################
class ipl_exporter:
    only_selected = False
    game_id = None
    export_inst = False
    export_cull = False
    export_grge = False 
    export_enex = False

    x_offset = 0.0
    y_offset = 0.0
    z_offset = 0.0

    inst_objects = []
    cull_objects = []
    grge_objects = []
    enex_objects = []
    total_objects_num = 0
    #######################################################
    def _q(obj, key, default):
        try:
            return obj.get(key, default)
        except Exception:
            return default
    #######################################################
    @staticmethod
    def _anchor_and_pos(obj):
        """Pick the transform carrier."""
        carrier = obj.parent if (obj.parent and obj.parent.type == 'EMPTY') else obj
        loc = carrier.location
        x = float(loc.x) + ipl_exporter.x_offset
        y = float(loc.y) + ipl_exporter.y_offset
        z = float(loc.z) + ipl_exporter.z_offset
        return carrier, x, y, z
    #######################################################
    @staticmethod
    def _resolve_meta(obj):
        """Read id/name/interior/lod."""
        dm = getattr(obj, "dff_map", None)

        # ID
        object_id = (
            int(getattr(dm, "object_id", 0)) if dm else
            int(obj.get("object_id", 0))
        )

        # Model name
        base_name = obj.name.split('.')[0]
        model_name = (
            getattr(dm, "model_name", None) or
            obj.get("model_name", None) or
            base_name
        )

        # Interior
        interior = (
            int(getattr(dm, "interior", 0)) if dm else
            int(obj.get("interior", 0))
        )

        # LOD index 
        if "LODIndex" in obj:
            lod_index = int(obj["LODIndex"])
        else:
            lod_index = int(getattr(dm, "lod", -1)) if dm else int(obj.get("lod", -1))

        return object_id, model_name, interior, lod_index
    #######################################################
    @staticmethod
    def collect_objects(context):
        self = ipl_exporter
        self.inst_objects = []
        self.cull_objects = []
        self.grge_objects = []
        self.enex_objects = [] 

        for obj in context.scene.objects:
            if self.only_selected and not obj.select_get():
                continue

            dff_tag  = getattr(obj, "dff", None)
            dff_type = getattr(dff_tag, "type", None)

            # INST entries
            if self.export_inst and obj.type == 'MESH' and dff_type == 'OBJ':
                if self._skip_lod_or_col(obj, context):
                    continue
                self.inst_objects.append(obj)
                continue

            # CULL entries
            if self.export_cull and obj.type == 'EMPTY' and dff_type == 'CULL':
                self.cull_objects.append(obj)
                continue

            # GRGE entries
            if self.export_grge and obj.type == 'MESH' and dff_type == 'GRGE':
                self.grge_objects.append(obj)
                continue

            # ENEX entries
            if self.export_enex and obj.type in {'MESH','EMPTY'} and dff_type == 'ENEX':
                self.enex_objects.append(obj)
                continue

            self.total_objects_num = len(self.inst_objects) + len(self.cull_objects) + len(self.grge_objects) + len(self.enex_objects)

    #######################################################
    @staticmethod
    def _skip_lod_or_col(obj, context):
        dff_scene = getattr(context.scene, "dff", None)
        if dff_scene and getattr(dff_scene, "skip_lod", False):
            if obj.name.startswith("LOD"):
                return True
        if ".ColMesh" in obj.name:
            return True
        return False

    #######################################################
    @staticmethod
    def format_inst_line(obj, context=None):
        #######################################################
        def round_float(v: float, places=10) -> str:
            s = f"{v:.{places}f}".rstrip("0").rstrip(".")
            return s if s else "0"
        #######################################################
        def round_quat(v: float) -> str:
            av = abs(v)
            if av != 0.0 and av < 1e-7:
                return f"{v:.10e}".replace("e-0", "e-").replace("e+0", "e+")
            places = 9 if av >= 0.9 else 11
            return round_float(v, places)
        #######################################################
        def format_inst_fields(v, places):
            s = f"{v:.{places}f}"
            if "." in s:
                s = s.rstrip("0").rstrip(".")
            if s in ("-0", "-0.0", "-0."):
                s = "0"
            return s
        #######################################################
        if context is not None and ipl_exporter._skip_lod_or_col(obj, context):
            return None

        carrier, x, y, z = ipl_exporter._anchor_and_pos(obj)
        object_id, model_name, interior, lod_index = ipl_exporter._resolve_meta(obj)

        gid = ipl_exporter.game_id

        # fields
        f6  = lambda v: format_inst_fields(v, 7)
        f7  = lambda v: format_inst_fields(v, 7)
        f10 = lambda v: format_inst_fields(v, 11)
        f11 = lambda v: format_inst_fields(v, 11)

        if gid == map_data.game_version.SA:
            qx, qy, qz, qw = quat_xyzw(carrier)

            qw_out = -qw

            return (
                f"{object_id}, {model_name}, {interior}, "
                f"{round_float(x,6)}, {round_float(y,6)}, {round_float(z,6)}, "
                f"{round_quat(qx)}, {round_quat(qy)}, "
                f"{round_quat(qz)}, {round_quat(qw_out)}, "
                f"{lod_index}  # {obj.name}"
            )

        elif gid == map_data.game_version.VC:
            sx, sy, sz = getattr(carrier, "scale", (1.0, 1.0, 1.0))
            qx, qy, qz, qw = quat_xyzw(carrier)
            if qw < 0.0:
                qx, qy, qz, qw = -qx, -qy, -qz, -qw

            return (
                f"{object_id}, {model_name}, {interior}, "
                f"{f7(x)}, {f7(y)}, {f7(z)}, "
                f"{f6(sx)}, {f6(sy)}, {f6(sz)}, "
                f"{f11(qx)}, {f11(qy)}, {f11(qz)}, {f11(qw)}"
            )

        elif gid == map_data.game_version.III:
            sx, sy, sz = getattr(carrier, "scale", (1.0, 1.0, 1.0))
            qx, qy, qz, qw = quat_xyzw(carrier)
            if qw < 0.0:
                qx, qy, qz, qw = -qx, -qy, -qz, -qw

            return (
                f"{object_id}, {model_name}, {interior}, "
                f"{f7(x)}, {f7(y)}, {f7(z)}, "
                f"{f6(sx)}, {f6(sy)}, {f6(sz)}, "
                f"{f10(qx)}, {f10(qy)}, {f10(qz)}, {f10(qw)}"
            )

        else:
            ex, ey, ez = euler_xyz(carrier)
            return (
                f"{object_id}, {model_name}, "
                f"{f6(x)}, {f6(y)}, {f6(z)}, "
                f"{f6(ex)}, {f6(ey)}, {f6(ez)}, "
                f"{lod_index}  # {obj.name}"
            )
    #######################################################
    @staticmethod
    def format_grge_line(obj):

        # based on GTAMods
        px = float(obj.get("grge_posX", obj.location.x))
        py = float(obj.get("grge_posY", obj.location.y))
        pz = float(obj.get("grge_posZ", obj.location.z))

        lx = float(obj.get("grge_lineX", 0.0))
        ly = float(obj.get("grge_lineY", 0.0))

        cx = float(obj.get("grge_cubeX", 0.0))
        cy = float(obj.get("grge_cubeY", 0.0))
        cz = float(obj.get("grge_cubeZ", 0.0))

        gtype = int(obj.get("grge_type", 5)) 
        flag  = int(obj.get("grge_flag", 0))

        name  = str(obj.get("grge_name", obj.name))

        return (f"{px:.5f}, {py:.5f}, {pz:.5f}, "
                f"{lx:.5f}, {ly:.5f}, "
                f"{cx:.5f}, {cy:.5f}, {cz:.5f}, "
                f"{flag}, {gtype}, {name}")

    #######################################################
    @staticmethod
    def format_enex_line(obj):
        ex = float(obj.get("enex_X1", obj.location.x))
        ey = float(obj.get("enex_Y1", obj.location.y))
        ez = float(obj.get("enex_Z1", obj.location.z))

        p0 = float(obj.get("enex_EnterAngle", 0.0))

        p1 = float(obj.get("enex_SizeX", 2.0))
        p2 = float(obj.get("enex_SizeY", 2.0))

        p3 = int(obj.get("enex_SizeZ", obj.get("enex_Flags", 8)))

        tx = float(obj.get("enex_X2", ex))
        ty = float(obj.get("enex_Y2", ey))
        tz = float(obj.get("enex_Z2", ez))

        ang = float(obj.get("enex_ExitAngle", 0.0))

        interior = int(obj.get("enex_TargetInterior", obj.get("enex_interior", 0)))
        mode     = int(obj.get("enex_mode", 4))

        name = obj.get("enex_Name", obj.name)
        if name.startswith("ENEX_"):
            name = name[5:]
        name = f"\"{name}\""

        t0 = int(obj.get("enex_Sky", 0))
        t1 = int(obj.get("enex_NumPedsToSpawn", 2))
        t2 = int(obj.get("enex_TimeOn", 0))
        t3 = int(obj.get("enex_TimeOff", 24))

        def f5(v): return f"{v:.5f}"
        def g(v):  return f"{v:.10g}"  

        return (
            f"{f5(ex)}, {f5(ey)}, {f5(ez)}, "
            f"{g(p0)}, {g(p1)}, {g(p2)}, {p3}, "
            f"{f5(tx)}, {f5(ty)}, {f5(tz)}, "
            f"{g(ang)}, {interior}, {mode}, {name}, {t0}, {t1}, {t2}, {t3}"
        )
    #######################################################
    def export_ipl(filename):
        self = ipl_exporter
        self.collect_objects(bpy.context)
        if not self.total_objects_num and not (self.export_grge and getattr(self, "grge_objects", None)):
            return

        # INST
        object_instances = []
        for obj in self.inst_objects:
            line = self.format_inst_line(obj, bpy.context)
            if line:
                object_instances.append(line)

        # CULL
        cull_instances = cull_exporter.export_objects(self.cull_objects, self.game_id)

        # GRGE 
        garage_instances = []
        if self.export_grge and self.grge_objects:
            for o in self.grge_objects:
                s = self.format_grge_line(o)
                if s:
                    garage_instances.append(s)

        # ENEX
        enex_instances = []
        if self.export_enex and self.enex_objects:
            for o in self.enex_objects:
                s = self.format_enex_line(o)
                if s:
                    enex_instances.append(s)

        # initialize
        ipl_data = TextIPLData(object_instances, cull_instances, garage_instances, enex_instances)
        MapDataUtility.write_ipl_data(filename, self.game_id, ipl_data)

#######################################################
def export_ipl(options):
    ipl_exporter.only_selected = bool(options.get('only_selected', False))
    ipl_exporter.game_id       = options.get('game_id', None)
    ipl_exporter.export_inst   = bool(options.get('export_inst', True))
    ipl_exporter.export_cull   = bool(options.get('export_cull', False))
    ipl_exporter.export_grge   = bool(options.get('export_grge', False))
    ipl_exporter.export_enex   = bool(options.get('export_enex', False))

    ipl_exporter.x_offset      = float(options.get('x_offset', 0.0))
    ipl_exporter.y_offset      = float(options.get('y_offset', 0.0))
    ipl_exporter.z_offset      = float(options.get('z_offset', 0.0))

    ipl_exporter.export_ipl(options['file_name'])
#######################################################
class ide_exporter:
    """Export an Item Definition file"""
    only_selected = False
    game_id = None
    export_objs = True
    export_tobj = False
    export_anim = False

    objs = []
    tobj = []
    anim = []
    total_definitions_num = 0

    #######################################################
    @staticmethod
    def get_prop(obj, name, cast=None, fallback=None):
        dff_map = getattr(obj, "dff_map", None)
        val = None
        if dff_map and hasattr(dff_map, name):
            val = getattr(dff_map, name)
        elif name in obj.keys():
            val = obj[name]
        if val is None:
            return fallback
        try:
            return cast(val) if cast else val
        except Exception:
            return fallback

    #######################################################
    @staticmethod
    def skip_lod(obj, context):
        dff_scene = getattr(context.scene, "dff", None)
        return bool(dff_scene and getattr(dff_scene, "skip_lod", False) and obj.name.startswith("LOD"))
    #######################################################
    @staticmethod
    def is_exportable(obj, context):
        if ide_exporter.only_selected and not obj.select_get():
            return False
        if obj.type != "MESH":  # skip empties, armatures, etc.
            return False
        if ".ColMesh" in obj.name:  # skip collisions
            return False
        if obj.name != obj.name.split('.')[0]:
            return False
        dff_tag = getattr(obj, "dff", None)
        if not (dff_tag and getattr(dff_tag, "type", None) == "OBJ"):
            return False
        if ide_exporter.skip_lod(obj, context):
            return False
        return True

    #######################################################
    @staticmethod
    def draw_distances(obj):
        s = ide_exporter.get_prop(obj, "ide_draw_distances", str)
        if s:
            vals = [v.strip() for v in s.split(",")]
            return [float(v) for v in vals if v]
        vals = []
        for k in ("ide_draw_distance", "ide_draw_distance1", "ide_draw_distance2", "ide_draw_distance3"):
            v = ide_exporter.get_prop(obj, k, float)
            if v is not None:
                vals.append(v)
        return vals or [100.0]
    #######################################################
    @staticmethod
    def count_obj_mesh_parts(root):
        count = 0
        stack = [root]
        seen = set()
        while stack:
            o = stack.pop()
            if o in seen:
                continue
            seen.add(o)
            if (
                o.type == "MESH"
                and getattr(getattr(o, "dff", None), "type", None) == "OBJ"
                and ".ColMesh" not in o.name
            ):
                count += 1
            stack.extend(list(o.children))
        return max(1, count)

    #######################################################
    @staticmethod
    def collect_objs(context):
        self = ide_exporter
        self.objs, self.tobj, self.anim = [], [], []

        for obj in context.scene.objects:
            if not self.is_exportable(obj, context):
                continue
            section = (self.get_prop(obj, "ide_section", str, "objs") or "objs").lower()
            if section == "objs" and self.export_objs:
                self.objs.append(obj)
            elif section == "tobj" and self.export_tobj:
                self.tobj.append(obj)
            elif section == "anim" and self.export_anim:
                self.anim.append(obj)

        self.total_definitions_num = len(self.objs) + len(self.tobj) + len(self.anim)

    #######################################################
    @staticmethod
    def fmt_objs(obj):
        model_id   = ide_exporter.get_prop(obj, "ide_object_id", int,
                    ide_exporter.get_prop(obj, "object_id",   int))
        model_name = ide_exporter.get_prop(obj, "ide_model_name", str,
                    ide_exporter.get_prop(obj, "model_name",   str, obj.name))
        txd_name   = ide_exporter.get_prop(obj, "ide_txd_name",   str, model_name)
        flags      = ide_exporter.get_prop(obj, "ide_flags",      int, 0)
        draws      = ide_exporter.draw_distances(obj)

        if model_id is None or not model_name or not txd_name or not draws:
            return None

        # Get type
        t = ide_exporter.get_prop(obj, "ide_type", int, 0)
        if t not in (1, 2, 3, 4):
            gid = str(ide_exporter.game_id or "").lower()
            t = 4 if ("san" in gid or "sa" == gid or " san " in gid) else 1

        mesh_count = ide_exporter.get_prop(obj, "ide_meshes", int, None)
        if t in (1, 2, 3):
            if mesh_count is None or mesh_count <= 0:
                mesh_count = t

        # from GTAMods
        if t == 4:
            d1 = float(draws[0])
            return f"{model_id}, {model_name}, {txd_name}, {d1:.0f}, {flags}"

        if t == 1:
            d1 = float(draws[0])
            return f"{model_id}, {model_name}, {txd_name}, {mesh_count}, {d1:.0f}, {flags}"

        if t == 2:
            d1 = float(draws[0]); d2 = float(draws[1] if len(draws) > 1 else d1)
            return f"{model_id}, {model_name}, {txd_name}, {mesh_count}, {d1:.0f}, {d2:.0f}, {flags}"

        # t == 3
        d1 = float(draws[0])
        d2 = float(draws[1] if len(draws) > 1 else d1)
        d3 = float(draws[2] if len(draws) > 2 else d1)
        return f"{model_id}, {model_name}, {txd_name}, {mesh_count}, {d1:.0f}, {d2:.0f}, {d3:.0f}, {flags}"
    #######################################################
    @staticmethod
    def fmt_tobj(obj):
        base = ide_exporter.fmt_objs(obj)
        if not base:
            return None
        on_  = ide_exporter.get_prop(obj, "ide_time_on", int)
        off_ = ide_exporter.get_prop(obj, "ide_time_off", int)
        if on_ is None or off_ is None:
            return None
        return f"{base}, {on_}, {off_}"
    #######################################################
    @staticmethod
    def fmt_anim(obj):
        base = ide_exporter.fmt_objs(obj)
        if not base:
            return None
        anim = ide_exporter.get_prop(obj, "ide_anim", str)
        if not anim:
            return None
        return f"{base}, {anim}"

    #######################################################
    @staticmethod
    def write_section(fh, name, objects, formatter):
        lines = []
        for o in objects:
            s = formatter(o)
            if s:
                lines.append(s)
        if lines:
            SectionUtility(name).write(fh, lines)
    #######################################################
    @staticmethod
    def export_ide(filename, context=None):
        self = ide_exporter
        context = context or bpy.context
        self.collect_objs(context)

        folder = os.path.dirname(filename)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)

        with open(filename, "w", encoding="ascii", errors="replace", newline="\n") as fh:
            fh.write("# IDE generated with DragonFF\n\n")
            self.write_section(fh, "objs", self.objs, self.fmt_objs)
            self.write_section(fh, "tobj", self.tobj, self.fmt_tobj)
            self.write_section(fh, "anim", self.anim, self.fmt_anim)
#######################################################
def export_ide(options):
    """IDE export functions"""
    ide_exporter.only_selected = bool(options.get('only_selected', False))
    ide_exporter.game_id       = options.get('game_id', None)
    ide_exporter.export_objs   = bool(options.get('export_objs', True))
    ide_exporter.export_tobj   = bool(options.get('export_tobj', False))
    ide_exporter.export_anim   = bool(options.get('export_anim', False))
    ide_exporter.export_ide(options['file_name'])
#######################################################
class pwn_exporter:
    """Export a Pawn script"""
    only_selected   = False
    game_id         = None
    stream_distance = 300.0
    draw_distance   = 300.0
    x_offset        = 0.0
    y_offset        = 0.0
    z_offset        = 0.0

    write_artconfig = True
    model_directory = ""
    base_id         = 19379
    id_start        = -1000
    id_min          = -40000

    inst_reps = []
    total_objects_num = 0

    #######################################################
    @staticmethod
    def _skip_lod(obj, context):
        dff = getattr(context.scene, "dff", None)
        if not dff:
            return False
        if not getattr(dff, "skip_lod", False):
            return False
        n = obj.name
        return n.startswith("LOD") or ".ColMesh" in n

    #######################################################
    @staticmethod
    def _is_obj_mesh(obj):
        if obj.type != "MESH":
            return False
        if ".ColMesh" in obj.name:
            return False
        dff_tag = getattr(obj, "dff", None)
        return bool(dff_tag and getattr(dff_tag, "type", None) == "OBJ")

    #######################################################
    @staticmethod
    def _root_anchor(obj):
        a = obj
        while a.parent and a.parent.type == "EMPTY":
            a = a.parent
        return a

    #######################################################
    @staticmethod
    def collect_instances(context):
        self = pwn_exporter
        self.inst_reps = []
        seen = set()
        for obj in context.scene.objects:
            if self.only_selected and not obj.select_get():
                continue
            if not self._is_obj_mesh(obj):
                continue
            if self._skip_lod(obj, context):
                continue
            root = self._root_anchor(obj)
            key = root.as_pointer()
            if key in seen:
                continue
            seen.add(key)
            self.inst_reps.append(obj)
        self.total_objects_num = len(self.inst_reps)

    #######################################################
    @staticmethod
    def _inst_transform(obj):
        parent = obj.parent
        if parent and parent.type == 'EMPTY':
            loc = parent.location
            rx, ry, rz = euler_xyz(parent)
        else:
            loc = obj.location
            rx, ry, rz = euler_xyz(obj)
        x = loc.x + pwn_exporter.x_offset
        y = loc.y + pwn_exporter.y_offset
        z = loc.z + pwn_exporter.z_offset
        return x, y, z, (rx, ry, rz)

    #######################################################
    @staticmethod
    def _model_meta(obj):
        dm = getattr(obj, "dff_map", None)

        model_id  = int(getattr(dm, "object_id", 0)) if dm else 0
        interior  = int(getattr(dm, "interior", -1)) if dm else -1

        base_name = obj.name.split('.')[0]

        modelname = (getattr(dm, "model_name", None) or base_name) if dm else base_name

        dff_name = (
            (getattr(dm, "pawn_model_name", None) or getattr(dm, "ide_model_name", None)) if dm else None
        ) or obj.get('DFF_Name', base_name)

        txd_name = (
            (getattr(dm, "pawn_txd_name", None) or getattr(dm, "ide_txd_name", None)) if dm else None
        ) or obj.get('TXD_Name', base_name)

        return model_id, interior, modelname, dff_name, txd_name
    #######################################################
    @staticmethod
    def export_pawn(filename):
        self = pwn_exporter
        ctx = bpy.context
        self.collect_instances(ctx)
        if not self.total_objects_num:
            return

        folder = os.path.dirname(filename)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        artconfig_path = os.path.join(folder, "artconfig.txt")

        next_id = self.id_start
        name_to_id = {}

        with open(filename, "w", encoding="ascii", errors="replace", newline="\n") as fpwn, \
             open(artconfig_path, "w", encoding="ascii", errors="replace", newline="\n") as facfg:

            fpwn.write("// Pawn generated with DragonFF\n")
            fpwn.write("// Objects: %d\n\n" % self.total_objects_num)
            if self.write_artconfig:
                facfg.write("// artconfig generated with DragonFF\n")

            for obj in self.inst_reps:
                base_name = obj.name.split('.')[0]
                if base_name not in name_to_id:
                    model_new_id = next_id
                    next_id -= 1
                    if next_id <= self.id_min:
                        next_id -= 1000
                    name_to_id[base_name] = model_new_id
                else:
                    model_new_id = name_to_id[base_name]

                x, y, z, (rx, ry, rz) = self._inst_transform(obj)
                _orig, interior, modelname, dff_name, txd_name = self._model_meta(obj)

                fpwn.write(
                    f"CreateDynamicObject({model_new_id}, {x:.3f}, {y:.3f}, {z:.3f}, "
                    f"{rx:.3f}, {ry:.3f}, {rz:.3f}, -1, {interior}, -1, "
                    f"{self.stream_distance:.3f}, {self.draw_distance:.3f}); // {modelname}\n"
                )

                if 'LODIndex' in obj:
                    lod_index = int(obj['LODIndex'])
                    fpwn.write(
                        f"CreateDynamicObject({lod_index}, {x:.3f}, {y:.3f}, {z:.3f}, "
                        f"{rx:.3f}, {ry:.3f}, {rz:.3f}, -1, {interior}, -1, "
                        f"{self.stream_distance:.3f}, {self.draw_distance:.3f}); // LOD for {modelname}\n"
                    )

                if self.write_artconfig:
                    prefix = self.model_directory.strip().replace("\\", "/")
                    if prefix and not prefix.endswith("/"):
                        prefix += "/"
                    facfg.write(
                        f"AddSimpleModel(-1, {self.base_id}, {model_new_id}, "
                        f"\"{prefix}{dff_name}.dff\", \"{prefix}{txd_name}.txd\"); // {modelname}\n"
                    )

#######################################################
def export_pawn(options):
    """Pawn export functions"""
    pwn_exporter.only_selected   = bool(options.get('only_selected', False))
    pwn_exporter.game_id         = options.get('game_id', None)
    pwn_exporter.stream_distance = float(options.get('stream_distance', 300.0))
    pwn_exporter.draw_distance   = float(options.get('draw_distance', 300.0))
    pwn_exporter.x_offset        = float(options.get('x_offset', 0.0))
    pwn_exporter.y_offset        = float(options.get('y_offset', 0.0))
    pwn_exporter.z_offset        = float(options.get('z_offset', 0.0))

    pwn_exporter.write_artconfig = bool(options.get('write_artconfig', True))
    pwn_exporter.model_directory = str(options.get('model_directory', "") or "")
    pwn_exporter.base_id         = int(options.get('base_id', 19379))
    pwn_exporter.id_start        = int(options.get('id_start', -1000))
    pwn_exporter.id_min          = int(options.get('id_min', -40000))

    pwn_exporter.export_pawn(options['file_name'])
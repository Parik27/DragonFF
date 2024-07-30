import bpy
from bpy_extras.io_utils import ExportHelper
from ..ops import col_exporter
import bmesh
from mathutils import Vector

#######################################################
class EXPORT_OT_col(bpy.types.Operator, ExportHelper):
    
    bl_idname      = "export_col.scene"
    bl_description = "Export a GTA III/VC/SA Collision File"
    bl_label       = "DragonFF Collision (.col)"
    filename_ext   = ".col"

    filepath       : bpy.props.StringProperty(name="File path",
                                              maxlen=1024,
                                              default="",
                                              subtype='FILE_PATH')
    
    filter_glob    : bpy.props.StringProperty(default="*.col",
                                              options={'HIDDEN'})
    
    directory      : bpy.props.StringProperty(maxlen=1024,
                                              default="",
                                              subtype='FILE_PATH')

    only_selected   :  bpy.props.BoolProperty(
        name        = "Only Selected",
        default     = False
    )
    
    export_version  : bpy.props.EnumProperty(
        items =
        (
            ('1', "GTA 3/VC (COLL)", "Grand Theft Auto 3 and Vice City (PC) - Version 1"),
            ('3', "GTA SA PC/Xbox (COL3)", "Grand Theft Auto SA (PC/Xbox) - Version 3"),
            ('2', "GTA SA PS2 (COL2)", "Grand Theft Auto SA (PS2) - Version 2")
        ),
        name = "Version Export"
    )

    use_active_collection : bpy.props.BoolProperty(
        name = "Only the objects from the active collection",
        default = False
    )

    #######################################################
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "export_version")
        layout.prop(self, "only_selected")
        return None

    #######################################################
    def execute(self, context):
        
        col_exporter.export_col(
            {
                "file_name"      : self.filepath,
                "version"        : int(self.export_version),
                "collection"     : context.collection if self.use_active_collection else None,
                "memory"         : False,
                "mass_export"    : True,
                "only_selected"  : self.only_selected
            }
        )

        # Save settings of the export in scene custom properties for later
        context.scene['dragonff_imported_version_col'] = self.export_version
            
        return {'FINISHED'}

    #######################################################
    def invoke(self, context, event):
        if 'dragonff_imported_version_col' in context.scene:
            self.export_version = context.scene['dragonff_imported_version_col']

        if not self.filepath:
            if context.blend_data.filepath:
                self.filepath = context.blend_data.filepath
            else:
                self.filepath = "untitled"

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

#######################################################
class OBJECT_OT_facegoups_col(bpy.types.Operator):
    bl_idname      = "generate_facegroups.col"
    bl_description = "Generate Face Groups for GTA III/VC/SA Collision File"
    bl_label       = "Generate Face Groups"

    def execute(self, context):
        obj = context.active_object
        if not (obj and obj.type == 'MESH' and obj.dff.type == 'COL'):
            return {'CANCELLED'}

        avoid_smalls = context.scene.dff.face_group_avoid_smalls
        min_size = max(5, context.scene.dff.face_group_min)
        max_size = max(min_size, context.scene.dff.face_group_max)
        mesh = obj.data

        # Set min/max to object bound_box with a small margin
        mn = Vector(obj.bound_box[0]) - Vector((1, 1, 1))
        mx = Vector(obj.bound_box[6]) + Vector((1, 1, 1))
        big_groups = []
        lil_groups = []
        big_groups.append({'min': mn, 'max': mx, 'indices': [f.index for f in mesh.polygons]})
        while len(big_groups):
            # Group is done if under max_size
            grp = big_groups.pop()
            if len(grp['indices']) <= max_size:
                lil_groups.append(grp)
                continue

            # Otherwise, split the bounds in half along the longest axis and create 2 sub-groups
            mn = grp['min'].copy()
            mx = grp['max'].copy()
            dims = mx-mn
            axis = list(dims).index(max(dims, key=abs))
            cen = 0.5 * (mn + mx)
            mn1 = mn.copy()
            mx1 = mx.copy()
            mx1[axis] = cen[axis]
            mn2 = mn.copy()
            mn2[axis] = cen[axis]
            mx2 = mx.copy()

            # Stuff the faces into their corresponding sub-group bounds
            inds1 = []
            inds2 = []
            for idx in grp['indices']:
                face = mesh.polygons[idx]
                c = face.center
                if mn1.x < c.x < mx1.x and mn1.y < c.y < mx1.y and mn1.z < c.z < mx1.z:
                    inds1.append(idx)
                else:
                    inds2.append(idx)

            # Avoid making overly small face groups by combining them with their neighbor
            if avoid_smalls and len(grp['indices']) < max_size + min_size and (len(inds1) < min_size or len(inds2) < min_size):
                lil_groups.append(grp)
            else:
                if len(inds1) > 0:
                    big_groups.append({'min': mn1, 'max': mx1, 'indices': inds1})
                if len(inds2) > 0:
                    big_groups.append({'min': mn2, 'max': mx2, 'indices': inds2})

        # No reason to generate face groups if there's only 1 group
        if len(lil_groups) > 1:
            # Create a face groups attribute for the mesh if there isn't one already
            if not mesh.attributes.get("face group"):
                mesh.attributes.new(name="face group", type="INT", domain="FACE")

            # Sort the face list by face group index
            bm = bmesh.new()
            bm.from_mesh(mesh)
            bm.faces.ensure_lookup_table()
            layer = bm.faces.layers.int.get("face group")
            min_size = max_size = len(lil_groups[0]['indices'])
            avg_size = 0
            for fg, grp in enumerate(lil_groups):
                grp_size = len(grp['indices'])
                min_size = min(min_size, grp_size)
                max_size = max(max_size, grp_size)
                avg_size += grp_size
                for idx in grp['indices']:
                    bm.faces[idx][layer] = fg
            avg_size /= float(len(lil_groups))
            print("Generated %i face groups with minimum size of %i, a maximum size of %i and an average size of %f "
                  "faces." % (len(lil_groups), min_size, max_size, avg_size))
            bm.faces.sort(key=lambda f: f[layer])

            bm.to_mesh(mesh)

        # Delete face groups if they exist now but the generation found them unnecessary
        elif mesh.attributes.get("face group"):
            mesh.attributes.remove(mesh.attributes.get("face group"))
            print("No face groups were generated with the current settings.")

        # Make an undo and force a redraw of the viewport
        bpy.ops.ed.undo_push()
        for area in bpy.context.window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        return {'FINISHED'}

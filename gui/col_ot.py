import bpy
import gpu
import random
from bpy_extras.io_utils import ExportHelper
from gpu_extras.batch import batch_for_shader
from ..ops import col_exporter
from ..ops.importer_common import create_bmesh_for_mesh, redraw_viewport
import bmesh
from mathutils import Vector

if bpy.app.version < (3, 4, 0):
    import bgl

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
                                              subtype='DIR_PATH')

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

    apply_transformations : bpy.props.BoolProperty(
        name = "Apply Transformations",
        default = True
    )

    use_active_collection : bpy.props.BoolProperty(
        name = "Only the objects from the active collection",
        default = False
    )

    #######################################################
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "export_version")
        layout.prop(self, "apply_transformations")
        if not self.use_active_collection:
            layout.prop(self, "only_selected")
        return None

    #######################################################
    def execute(self, context):
        
        col_exporter.export_col(
            {
                "file_name"             : self.filepath,
                "version"               : int(self.export_version),
                "collection"            : context.collection if self.use_active_collection else None,
                "apply_transformations" : self.apply_transformations,
                "only_selected"         : self.only_selected
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

    #######################################################
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH' and obj.dff.type == 'COL')

    #######################################################
    def execute(self, context):
        avoid_smalls = context.scene.dff.face_group_avoid_smalls
        min_size = max(5, context.scene.dff.face_group_min)
        max_size = max(min_size, context.scene.dff.face_group_max)

        obj = context.active_object
        mesh = obj.data
        bm = create_bmesh_for_mesh(mesh, obj.mode)

        # Triangulate mesh
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bm.faces.ensure_lookup_table()

        # Set min/max to object bound_box with a small margin
        mn = Vector(obj.bound_box[0]) - Vector((1, 1, 1))
        mx = Vector(obj.bound_box[6]) + Vector((1, 1, 1))
        big_groups = []
        lil_groups = []
        big_groups.append({'min': mn, 'max': mx, 'indices': [f.index for f in bm.faces]})
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
                face = bm.faces[idx]
                c = face.calc_center_median()
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
            layer = bm.faces.layers.int.get("face group") or bm.faces.layers.int.new("face group")

            # Sort the face list by face group index
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

            # Apply
            bm.to_mesh(mesh)

        # Delete face groups if they exist now but the generation found them unnecessary
        elif mesh.attributes.get("face group"):
            mesh.attributes.remove(mesh.attributes.get("face group"))
            print("No face groups were generated with the current settings.")

        bm.free()

        # Make an undo and force a redraw of the viewport
        bpy.ops.ed.undo_push()
        redraw_viewport()

        return {'FINISHED'}

#######################################################
class COLLECTION_OT_dff_generate_bounds(bpy.types.Operator):

    bl_idname           = "collection.dff_generate_bounds"
    bl_description      = "Generate bounds for active collection"
    bl_label            = "Generate Bounds"

    #######################################################
    @classmethod
    def poll(cls, context):
        col = context.collection
        return (col and not col.dff.auto_bounds)

    #######################################################
    def execute(self, context):
        col = context.collection

        bounds_objects = [obj for obj in col.objects if obj.dff.type == 'COL']
        bounds = col_exporter.calculate_bounds(bounds_objects)
        col.dff.bounds_max, col.dff.bounds_min = bounds

        if context.scene.dff.draw_bounds:
            redraw_viewport()

        return {'FINISHED'}

#######################################################
class AddCollisionHelper:
    bl_options = {'REGISTER', 'UNDO'}

    location: bpy.props.FloatVectorProperty(
        name="Location",
        description="Location for the newly added object",
        subtype='XYZ',
        default=(0, 0, 0)
    )

    radius: bpy.props.FloatProperty(
        name="Radius",
        description="Radius",
        default=1,
        min=0.001
    )

    #######################################################
    def invoke(self, context, event):
        self.location = context.scene.cursor.location
        return self.execute(context)

#######################################################
class OBJECT_OT_dff_add_collision_box(bpy.types.Operator, AddCollisionHelper):

    bl_idname = "object.dff_add_collision_box"
    bl_label = "Add Collision Box"
    bl_description = "Add collision box to the scene"

    #######################################################
    def execute(self, context):
        ret = bpy.ops.object.empty_add(type='CUBE', radius=self.radius, location=self.location)
        if ret != {'FINISHED'}:
            return ret

        obj = context.object

        obj.name = "ColBox"
        obj.dff.type = 'COL'

        obj.lock_rotation[0] = True
        obj.lock_rotation[1] = True
        obj.lock_rotation[2] = True
        obj.lock_rotation_w = True

        return {'FINISHED'}

#######################################################
class OBJECT_OT_dff_add_collision_sphere(bpy.types.Operator, AddCollisionHelper):

    bl_idname = "object.dff_add_collision_sphere"
    bl_label = "Add Collision Sphere"
    bl_description = "Add collision sphere to the scene"

    #######################################################
    def execute(self, context):
        ret = bpy.ops.object.empty_add(type='SPHERE', radius=self.radius, location=self.location)
        if ret != {'FINISHED'}:
            return ret

        obj = context.object

        obj.name = "ColSphere"
        obj.dff.type = 'COL'

        obj.lock_rotation[0] = True
        obj.lock_rotation[1] = True
        obj.lock_rotation[2] = True
        obj.lock_rotation_w = True

        return {'FINISHED'}

#######################################################
class FaceGroupsDrawer:

    _draw_3d_handler = None
    _cached_batch = None  
    _cached_mesh_id = None  
    _cached_attr_hash = None

    #######################################################
    def get_draw_enabled(self):
        return FaceGroupsDrawer._draw_3d_handler is not None

    #######################################################
    def set_draw_enabled(self, value):
        FaceGroupsDrawer.enable_draw() if value else FaceGroupsDrawer.disable_draw()

    #######################################################
    @staticmethod
    def draw_callback():
        FaceGroupsDrawer.draw()

    #######################################################
    @staticmethod
    def enable_draw():
        if not FaceGroupsDrawer._draw_3d_handler:
            callback = FaceGroupsDrawer.draw_callback
            FaceGroupsDrawer._draw_3d_handler = bpy.types.SpaceView3D.draw_handler_add(callback, (), 'WINDOW', 'POST_VIEW')
            redraw_viewport()

    #######################################################
    @staticmethod
    def disable_draw():
        if FaceGroupsDrawer._draw_3d_handler:
            bpy.types.SpaceView3D.draw_handler_remove(FaceGroupsDrawer._draw_3d_handler, 'WINDOW')
            FaceGroupsDrawer._draw_3d_handler = None
            redraw_viewport()

    #######################################################
    @staticmethod  
    def draw():  
        o = bpy.context.active_object  
        if not (o and o.select_get() and o.type == 'MESH' and o.data.attributes.get('face group')):  
            # Clear cache when not drawing  
            FaceGroupsDrawer._cached_batch = None  
            FaceGroupsDrawer._cached_mesh_id = None  
            FaceGroupsDrawer._cached_attr_hash = None  
            return  
        
        mesh = o.data  
        attr = mesh.attributes['face group'].data  
        if len(attr) == 0:  
            return  
        
        # Check if we can use cached batch  
        current_mesh_id = id(mesh)  
        current_attr_hash = hash(tuple(f.value for f in attr))  
        
        if (FaceGroupsDrawer._cached_batch and   
            FaceGroupsDrawer._cached_mesh_id == current_mesh_id and  
            FaceGroupsDrawer._cached_attr_hash == current_attr_hash):  
            
            # Use cached batch  
            if bpy.app.version < (4, 0, 0):  
                shader = gpu.shader.from_builtin("3D_FLAT_COLOR")  
            else:  
                shader = gpu.shader.from_builtin("FLAT_COLOR")  
            
            # Set up depth test and draw  
            if bpy.app.version < (3, 4, 0):  
                bgl.glEnable(bgl.GL_DEPTH_TEST)  
                bgl.glDepthFunc(bgl.GL_LEQUAL)  
            else:  
                gpu.state.depth_test_set('LESS_EQUAL')  
                gpu.state.depth_mask_set(True)  
            
            gpu.matrix.push()  
            gpu.matrix.multiply_matrix(o.matrix_local)  
            FaceGroupsDrawer._cached_batch.draw(shader)  
            gpu.matrix.pop()  
            
            if bpy.app.version < (3, 4, 0):  
                bgl.glDisable(bgl.GL_DEPTH_TEST)  
            else:  
                gpu.state.depth_mask_set(False)  
            return  
        
        # Rebuild cache
        mesh.calc_loop_triangles()  
        size = 3 * len(mesh.loop_triangles)  
        vertices = [[0.0,0.0,0.0]] * size  
        vertex_colors = [(0.0,0.0,0.0,0.0)] * size  
        indices = [(i, i+1, i+2) for i in range(0, size, 3)]  
        
        random.seed(10)  
        color = (0.0, 0.0, 0.0, 0.0)  
        grp = -1  
        idx = 0  
        for i, face in enumerate(mesh.loop_triangles):  
            vertices[idx  ] = mesh.vertices[face.vertices[0]].co  
            vertices[idx+1] = mesh.vertices[face.vertices[1]].co  
            vertices[idx+2] = mesh.vertices[face.vertices[2]].co  
            if grp != attr[i].value:  
                color = random.uniform(0.2, 1.0), random.uniform(0.2, 1.0), random.uniform(0.2, 1.0), 1.0  
                grp = attr[i].value  
            vertex_colors[idx  ] = color  
            vertex_colors[idx+1] = color  
            vertex_colors[idx+2] = color  
            idx += 3  
        
        if bpy.app.version < (4, 0, 0):  
            shader = gpu.shader.from_builtin("3D_FLAT_COLOR")  
        else:  
            shader = gpu.shader.from_builtin("FLAT_COLOR")  
        
        # Cache the batch  
        FaceGroupsDrawer._cached_batch = batch_for_shader(  
            shader, 'TRIS',  
            {"pos": vertices, "color": vertex_colors},  
            indices=indices,  
        )  
        FaceGroupsDrawer._cached_mesh_id = current_mesh_id  
        FaceGroupsDrawer._cached_attr_hash = current_attr_hash  
        
        # Draw
        if bpy.app.version < (3, 4, 0):  
            bgl.glEnable(bgl.GL_DEPTH_TEST)  
            bgl.glDepthFunc(bgl.GL_LEQUAL)  
        else:  
            gpu.state.depth_test_set('LESS_EQUAL')  
            gpu.state.depth_mask_set(True)  
        
        gpu.matrix.push()  
        gpu.matrix.multiply_matrix(o.matrix_local)  
        FaceGroupsDrawer._cached_batch.draw(shader)  
        gpu.matrix.pop()  
        
        if bpy.app.version < (3, 4, 0):  
            bgl.glDisable(bgl.GL_DEPTH_TEST)  
        else:  
            gpu.state.depth_mask_set(False)

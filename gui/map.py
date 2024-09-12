import bpy
import gpu
import numpy as np
import random
from gpu_extras.batch import batch_for_shader
from ..data import map_data
from ..ops.importer_common import game_version

#######################################################
class DFFFrameProps(bpy.types.PropertyGroup):
    obj  : bpy.props.PointerProperty(type=bpy.types.Object)
    icon : bpy.props.StringProperty()

#######################################################
class DFFAtomicProps(bpy.types.PropertyGroup):
    obj       : bpy.props.PointerProperty(type=bpy.types.Object)
    frame_obj : bpy.props.PointerProperty(type=bpy.types.Object)

#######################################################
class DFFSceneProps(bpy.types.PropertyGroup):

    #######################################################
    def update_map_sections(self, context):
        return map_data.data[self.game_version_dropdown]['IPL_paths']

    #######################################################
    def frames_active_changed(self, context):
        scene_dff = context.scene.dff

        frames_num = len(scene_dff.frames)
        if not frames_num:
            return

        if scene_dff.frames_active >= frames_num:
            scene_dff.frames_active = frames_num - 1
            return

        frame_object = scene_dff.frames[scene_dff.frames_active].obj

        for a in scene_dff.frames: a.obj.select_set(False)
        frame_object.select_set(True)
        context.view_layer.objects.active = frame_object

    #######################################################
    def atomics_active_changed(self, context):
        scene_dff = context.scene.dff

        atomics_num = len(scene_dff.atomics)
        if not atomics_num:
            return

        if scene_dff.atomics_active >= atomics_num:
            scene_dff.atomics_active = atomics_num - 1
            return

        atomic_object = scene_dff.atomics[scene_dff.atomics_active].obj

        for a in scene_dff.atomics: a.obj.select_set(False)
        atomic_object.select_set(True)
        context.view_layer.objects.active = atomic_object

    game_version_dropdown : bpy.props.EnumProperty(
        name = 'Game',
        items = (
            (game_version.III, 'GTA III', 'GTA III map segments'),
            (game_version.VC, 'GTA VC', 'GTA VC map segments'),
            (game_version.SA, 'GTA SA', 'GTA SA map segments'),
            (game_version.LCS, 'GTA LCS', 'GTA LCS map segments'),
            (game_version.VCS, 'GTA VCS', 'GTA VCS map segments'),
        )
    )

    map_sections : bpy.props.EnumProperty(
        name = 'Map segment',
        items = update_map_sections
    )

    skip_lod: bpy.props.BoolProperty(
        name        = "Skip LOD Objects",
        default     = False
    )

    load_txd: bpy.props.BoolProperty(
        name        = "Load TXD files",
        default     = False
    )

    read_mat_split  :  bpy.props.BoolProperty(
        name        = "Read Material Split",
        description = "Whether to read material split for loading triangles",
        default     = False
    )

    load_collisions: bpy.props.BoolProperty(
        name        = "Load Map Collisions",
        default     = False
    )

    game_root : bpy.props.StringProperty(
        name = 'Game root',
        default = 'C:/Program Files (x86)/Steam/steamapps/common/',
        description = "Folder with the game's executable",
        subtype = 'DIR_PATH'
    )

    dff_folder : bpy.props.StringProperty(
        name = 'Dff folder',
        default = 'C:/Users/blaha/Documents/GitHub/DragonFF/tests/dff',
        description = "Define a folder where all of the dff models are stored.",
        subtype = 'DIR_PATH'
    )

    # txd_folder = bpy.props.StringProperty \
    #     (
    #     name = 'Txd folder',
    #     default = 'C:/Users/blaha/Documents/GitHub/DragonFF/tests/txd',
    #     description = "Define a folder where all of the txd models are stored.",
    #     subtype = 'DIR_PATH'
    #     )

    draw_facegroups : bpy.props.BoolProperty(
        name="Draw Face Groups",
        description="Display the Face Groups of the active object (if they exist) in the viewport",
        default=False
    )

    face_group_min : bpy.props.IntProperty(
        name = 'Face Group Minimum Size',
        description="Don't generate groups below this size",
        default = 20,
        min = 5,
        max = 200
    )

    face_group_max : bpy.props.IntProperty(
        name = 'Face Group Maximum Size',
        description="Don't generate groups above this size (minimum size overrides this if larger)",
        default = 50,
        min = 5,
        max = 200
    )

    face_group_avoid_smalls : bpy.props.BoolProperty(
        name = "Avoid overly small groups",
        description="Combine really small groups with their neighbor to avoid pointless isolated groups",
        default = True
    )

    frames : bpy.props.CollectionProperty(
        type    = DFFFrameProps,
        options = {'SKIP_SAVE','HIDDEN'}
    )

    frames_active : bpy.props.IntProperty(
        name    = "Active frame",
        default = 0,
        min     = 0,
        update  = frames_active_changed
    )

    atomics : bpy.props.CollectionProperty(
        type    = DFFAtomicProps,
        options = {'SKIP_SAVE','HIDDEN'}
    )

    atomics_active : bpy.props.IntProperty(
        name    = "Active atomic",
        default = 0,
        min     = 0,
        update  = atomics_active_changed
    )

    real_time_update : bpy.props.BoolProperty(
        name        = "Real Time Update",
        description = "Update the list of objects in real time",
        default     = True
    )

    filter_collection : bpy.props.BoolProperty(
        name        = "Filter Collection",
        description = "Filter frames and atomics by active collection",
        default     = True
    )

    def draw_fg():
        if not bpy.context.scene.dff.draw_facegroups:
            return
        o = bpy.context.active_object
        if o and o.select_get() and o.type == 'MESH' and o.data.attributes.get('face group'):
            mesh = bpy.context.active_object.data
            attr = mesh.attributes['face group'].data
            if len(attr) == 0:
                return
            mesh.calc_loop_triangles()

            # As the face groups are stored as face attributes, we'll generate unique vertices across the whole overlay
            # because the colors of different faces can't be shared across vertices
            size = 3 * len(mesh.loop_triangles)
            vertices = np.empty((size, 3), 'f')
            vertex_colors = np.empty((size, 4), 'f')
            indices = np.arange(0, size, dtype='i')

            # Each face group gets a random color, but set an explicit seed so the resulting color array remains
            # deterministic across redraws
            random.seed(10)
            color = []
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

            shader = gpu.shader.from_builtin('FLAT_COLOR')
            batch = batch_for_shader(
                shader, 'TRIS',
                {"pos": vertices, "color": vertex_colors},
                indices=indices,
            )

            # Draw the overlay over the existing collision object faces. There will be z-fighting as the object
            # location falls further from the origin, which it especially does for map objects. Unfortunate, but
            # probably fine for a simple visualization of the face groups.
            gpu.state.depth_test_set('LESS_EQUAL')
            gpu.state.depth_mask_set(True)
            gpu.matrix.push()
            gpu.matrix.multiply_matrix(bpy.context.active_object.matrix_local)
            batch.draw(shader)
            gpu.matrix.pop()
            gpu.state.depth_mask_set(False)

    #######################################################
    def register():
        bpy.types.Scene.dff = bpy.props.PointerProperty(type=DFFSceneProps)

#######################################################
class MapImportPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "DragonFF - Map Import"
    bl_idname = "SCENE_PT_layout"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    #######################################################
    def draw(self, context):
        layout = self.layout
        settings = context.scene.dff

        flow = layout.grid_flow(row_major=True,
                                columns=0,
                                even_columns=True,
                                even_rows=False,
                                align=True)

        col = flow.column()
        col.prop(settings, "game_version_dropdown", text="Game")
        col.prop(settings, "map_sections", text="Map segment")
        col.separator()
        col.prop(settings, "skip_lod", text="Skip LOD objects")
        col.prop(settings, "load_txd", text="Load TXD files")
        col.prop(settings, "read_mat_split", text="Read Material Split")
        col.prop(settings, "load_collisions", text="Load Map Collisions")

        layout.separator()

        layout.prop(settings, 'game_root')
        layout.prop(settings, 'dff_folder')

        row = layout.row()
        row.operator("scene.dragonff_map_import")

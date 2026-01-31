import bpy
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import IntProperty, EnumProperty, FloatProperty

class UVAnimatorProperties(PropertyGroup):
    columns: IntProperty(name="Columns", default=4, min=1, max=100)
    rows: IntProperty(name="Rows", default=4, min=1, max=100)
    horizontal_order: EnumProperty(
        name="Horizontal",
        items=[
            ('LEFT_TO_RIGHT', "L -> R", "Left to Right"),
            ('RIGHT_TO_LEFT', "R -> L", "Right to Left"),
        ],
        default='LEFT_TO_RIGHT'
    )
    vertical_order: EnumProperty(
        name="Vertical",
        items=[
            ('TOP_TO_BOTTOM', "T -> B", "Top to Bottom"),
            ('BOTTOM_TO_TOP', "B -> T", "Bottom to Top"),
        ],
        default='TOP_TO_BOTTOM'
    )
    fps: FloatProperty(name="FPS", default=24.0, min=1.0, max=120.0)

class UV_OT_AnimateSpriteSheet(Operator):
    bl_idname = "uv.animate_sprite_sheet"
    bl_label = "Generate keyframes"
    bl_description = "Generate keyframes for sprite sheet"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.area.type == 'NODE_EDITOR' and
                context.space_data.tree_type == 'ShaderNodeTree' and
                context.active_object and
                context.active_object.active_material and
                context.active_object.active_material.use_nodes)

    def execute(self, context):
        props = context.scene.dff_uv_animator_props
        mat = context.active_object.active_material
        nodes = mat.node_tree.nodes

        if not (context.active_node and context.active_node.type == 'MAPPING'):
            self.report({'INFO'}, "No Mapping node selected")
            return {'CANCELLED'}

        mapping = context.active_node

        scale_x = 1.0 / props.columns
        scale_y = 1.0 / props.rows

        mapping.inputs['Scale'].default_value[0] = scale_x
        mapping.inputs['Scale'].default_value[1] = scale_y

        total_sprites = props.columns * props.rows
        frame_positions = []

        for row in range(props.rows):
            for col in range(props.columns):
                actual_col = col if props.horizontal_order == 'LEFT_TO_RIGHT' else (props.columns - 1 - col)
                actual_row = row if props.vertical_order == 'TOP_TO_BOTTOM' else (props.rows - 1 - row)
                x_offset = actual_col * scale_x
                y_offset = (props.rows - 1 - actual_row) * scale_y if props.vertical_order == 'TOP_TO_BOTTOM' else actual_row * scale_y
                frame_positions.append((x_offset, y_offset))

        start_frame = context.scene.frame_start

        if mat.node_tree.animation_data and mat.node_tree.animation_data.action:
            action = mat.node_tree.animation_data.action
            fcurves_to_remove = []
            for fcurve in action.fcurves:
                if f'nodes["{mapping.name}"]' in fcurve.data_path:
                    fcurves_to_remove.append(fcurve)
            for fcurve in fcurves_to_remove:
                action.fcurves.remove(fcurve)

        for i, (x, y) in enumerate(frame_positions):
            frame = start_frame + i
            mapping.inputs['Location'].default_value[0] = x
            mapping.inputs['Location'].default_value[1] = y
            mapping.inputs['Location'].keyframe_insert("default_value", index=0, frame=frame)
            mapping.inputs['Location'].keyframe_insert("default_value", index=1, frame=frame)
            mapping.inputs['Scale'].keyframe_insert("default_value", index=0, frame=frame)
            mapping.inputs['Scale'].keyframe_insert("default_value", index=1, frame=frame)

        if mat.node_tree.animation_data and mat.node_tree.animation_data.action:
            for fcurve in mat.node_tree.animation_data.action.fcurves:
                if f'nodes["{mapping.name}"]' in fcurve.data_path:
                    for kf in fcurve.keyframe_points:
                        kf.interpolation = 'CONSTANT'

        context.scene.render.fps = int(props.fps)
        context.scene.frame_end = start_frame + total_sprites - 1

        self.report({'INFO'}, f"Created {len(frame_positions)} keyframes from frame {start_frame} to {start_frame + total_sprites - 1}")
        return {'FINISHED'}

class NODE_PT_UVAnimator(Panel):
    bl_label = "DragonFF - UV Animator"
    bl_idname = "NODE_PT_uv_animator"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    @classmethod
    def poll(cls, context):
        return (context.area.type == 'NODE_EDITOR' and
                context.space_data.tree_type == 'ShaderNodeTree')

    def draw_labelled_prop(self, row, obj, props, label):
        split = row.split(factor=0.4)
        split.label(text=label)
        if len(props) > 1:
            prop_row = split.row(align=True)
            for prop in props:
                prop_row.prop(obj, prop, text="")
        else:
            split.prop(obj, props[0], text="")

    def draw(self, context):
        layout = self.layout
        props = context.scene.dff_uv_animator_props

        if not context.active_object or not context.active_object.active_material:
            layout.label(text="No active material", icon='ERROR')
            return

        box = layout.box()
        has_mapping = context.active_node and context.active_node.type == 'MAPPING'
        icon = 'CHECKMARK' if has_mapping else 'X'
        text = "Mapping Node Selected" if has_mapping else "No Mapping Node Selected"
        box.label(text=text, icon=icon)

        self.draw_labelled_prop(box.row(), props, ["columns", "rows"], "Size")
        self.draw_labelled_prop(box.row(), props, ["horizontal_order", "vertical_order"], "Order")
        self.draw_labelled_prop(box.row(), props, ["fps"], "Framerate")

        box.separator()
        box.operator("uv.animate_sprite_sheet", icon='ACTION')

classes = (
    UVAnimatorProperties,
    UV_OT_AnimateSpriteSheet,
    NODE_PT_UVAnimator,
)

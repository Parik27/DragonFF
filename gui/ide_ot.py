import bpy
from bpy_extras.io_utils import ExportHelper
from ..ops import ide_exporter
from ..ops.importer_common import game_version


class EXPORT_OT_ide(bpy.types.Operator, ExportHelper):
    """Export IDE file"""
    bl_idname = "export_ide.scene"
    bl_description = "Export a GTA IDE File"
    bl_label = "DragonFF IDE (.ide)"
    filename_ext = ".ide"
    
    filepath: bpy.props.StringProperty(
        name="File path",
        maxlen=1024,
        default="",
        subtype='FILE_PATH'
    )
    
    filter_glob: bpy.props.StringProperty(
        default="*.ide",
        options={'HIDDEN'}
    )
    
    only_selected: bpy.props.BoolProperty(
        name="Only Selected",
        description="Export only selected objects",
        default=False
    )
    
    game_version_dropdown: bpy.props.EnumProperty(
        name='Game Version',
        items=(
            (game_version.III, 'GTA III', 'Export for GTA III'),
            (game_version.VC, 'GTA VC', 'Export for GTA Vice City'),
            (game_version.SA, 'GTA SA', 'Export for GTA San Andreas'),
        ),
        default=game_version.SA
    )
    
    def execute(self, context):
        result, message = ide_exporter.export_ide(
            self.filepath,
            self.game_version_dropdown,
            self.only_selected
        )
        
        if result == {'FINISHED'}:
            self.report({'INFO'}, message)
        else:
            self.report({'ERROR'}, message)
            
        return result
    
    def invoke(self, context, event):
        # Try to get game version from scene settings
        if hasattr(context.scene, 'dff'):
            self.game_version_dropdown = context.scene.dff.game_version_dropdown
            
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

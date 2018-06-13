import bpy
from . import handheld_operators
from . import handheld_data


class HanhdheldPanel(bpy.types.Panel):
    bl_idname = "hanhdheld_panel"
    bl_label = "Hanhdheld Animate"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "Animation"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        settings = context.scene.handheld_data
        col.prop(settings, "port")
        col.prop(settings, "host")

        col.operator("handheld.animate", text=handheld_operators.HandheldAnimate.status, icon="URL")  # WORLD

        col.prop(settings, "scale")
        layout.prop(settings, "selected_object")

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    StringProperty,
)

from . import export


class USDExporter(bpy.types.Operator):
    """
    Export to USD file
    """
    bl_idname = "export.usdz"
    bl_label = "Export USDZ"

    filepath = StringProperty(subtype='FILE_PATH')

    only_selected = BoolProperty(name="Only selected", default=False,
                                 description="What object will be exported? Only selected / all objects")

    apply_modifiers = BoolProperty(name="Apply modifiers", default=True,
                                   description="Shall be modifiers applied during export?")

    verbose = BoolProperty(name="Verbose", default=False,
                           description="Run the exporter in debug mode.  Check the console for output")

    def execute(self, context):
        filePath = bpy.path.ensure_ext(self.filepath, ".usd")
        config = {
            'only_selected': self.only_selected,
            'apply_modifiers': self.apply_modifiers,
            'verbose': self.verbose
        }

        export.exportUSD(context, filePath, config)
        return {'FINISHED'}

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = bpy.path.ensure_ext(bpy.data.filepath, ".usd")
        WindowManager = context.window_manager
        WindowManager.fileselect_add(self)
        return {'RUNNING_MODAL'}

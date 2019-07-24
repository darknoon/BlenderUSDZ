# License GPLv3

bl_info = {
    "name": "Export Pixar USD Format (.usd .usd, .usd, .usd)",
    "author": "Andrew Pouliot",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "File > Export > USD (.usd)",
    "description": "Exports USD file format, or .usd",
    "wiki_url": None,
    "category": "Import-Export",
}

# Allow reloading the module with command -> Reload Scripts
# python modules don't re-import without reload()
if "export" in locals():
    from importlib import reload
    # Operator calls into export module
    reload(export)
    reload(operator)
    del reload

import bpy
from . import operator
from . import export


def menu_func(self, context):
    self.layout.operator(operator.USDExporter.bl_idname,
                         text="Universal Scene Description (.usd)")


def register():
    bpy.types.TOPBAR_MT_file_export.append(menu_func)
    bpy.utils.register_class(operator.USDExporter)


def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func)
    bpy.utils.unregister_class(operator.USDExporter)


# This allows you to run the script directly from blenders text editor
# to test the addon without having to install it.
if __name__ == "__main__":
    register()

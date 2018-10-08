# License GPLv3

bl_info = {
    "name": "Export Pixar USDZ Format (.usd, .usda, .usdc, .usdz)",
    "author": "Andrew Pouliot",
    "version": (0, 0, 1),
    "blender": (2, 79, 0),
    "location": "File > Export > USDZ (.usdz)",
    "description": "Exports USDZ file format, or .usd",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
    "Scripts/Import-Export/USDZ_Exporter",
    "category": "Import-Export",
}

if "export" in locals():
    from importlib import reload
    # Operator calls into export, so do in this order
    reload(export)
    reload(operator)
    del reload

import bpy
from . import operator
from . import export


def menu_func(self, context):
    self.layout.operator(operator.USDExporter.bl_idname,
                         text="UNIVERSAL SCENE DESCRIPTION <> (.usd)")


def register():
    bpy.types.INFO_MT_file_export.append(menu_func)
    bpy.utils.register_class(operator.USDExporter)


def unregister():
    bpy.types.INFO_MT_file_export.remove(menu_func)
    bpy.utils.unregister_class(operator.USDExporter)


# This allows you to run the script directly from blenders text editor
# to test the addon without having to install it.
if __name__ == "__main__":
    register()

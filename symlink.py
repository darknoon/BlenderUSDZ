import os


def symlink_relative(src, dst):
    src = os.path.expanduser(src)
    src = os.path.abspath(src)
    dst = os.path.expanduser(dst)
    dst = os.path.abspath(dst)
    parent = os.path.dirname(dst)
    if not os.path.exists(parent):
        os.makedirs(parent)
    os.symlink(src, dst)


# symlink_relative('./io_export_usd',
#                  '~/Library/Application Support/Blender/2.79/scripts/addons/io_export_usd')

symlink_relative('./io_export_usd',
                 '~/Library/Application Support/Blender/2.80/scripts/addons/io_export_usd')

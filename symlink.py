import os


def symlink_relative(src, dst):
    src = os.path.expanduser(src)
    src = os.path.abspath(src)
    dst = os.path.expanduser(dst)
    dst = os.path.abspath(dst)
    os.symlink(src, dst)


symlink_relative('./io_export_usd',
                 '~/Library/Application Support/Blender/2.79/scripts/addons/io_export_usd')

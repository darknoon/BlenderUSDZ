from distutils.dir_util import copy_tree
from shutil import rmtree
from os.path import expanduser


def replace_tree(source, dest):
    source = expanduser(source)
    dest = expanduser(dest)
    rmtree(dest)
    copy_tree(source, dest)


replace_tree('./io_export_usd',
             '~/Library/Application Support/Blender/2.79/scripts/addons/io_export_usd')


# License GPLv3

import os
import mathutils
import json
import sys
from math import pi
import bpy

DEBUG = os.environ.get('BLENDER_DEBUG', False)

TIMEOUT = 5.0

# TODO: I think we need to convert from blender's Z-up coordinates to Y-up coordinates


def object_get_rotation(o):
    return {
        "eulerAngles": tuple(a * (180.0 / pi) for a in o.rotation_euler),
        "eulerOrder": o.rotation_euler.order,
    }


def exportMesh(o, settings):
    print("Exporting mesh: {}".format(o))

    apply_modifiers = settings["apply_modifiers"]

    if apply_modifiers:
        # Apply modifiers
        # This technique is from the GLTF2 exporter in Blender 2.80
        # See also: https://docs.blender.org/api/current/bpy.types.Depsgraph.html#dependency-graph-simple-exporter
        depsgraph = bpy.context.evaluated_depsgraph_get()
        object_with_modifiers = o.evaluated_get(depsgraph)
        mesh = object_with_modifiers.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    else:
        object_with_modifiers = o
        mesh = object_with_modifiers.to_mesh(preserve_all_data_layers=True)

    # Is this correct?
    edges = mesh.edges
    positions = [v.co for v in mesh.vertices]
    normals = [v.normal for v in mesh.vertices]
    loops = mesh.loops

    # Check for subdivision modifier
    # TODO: apply all modifiers EXCEPT this one by default since USD supports subdivision
    # There should be an option to subdivide the meshes as well...
    subsurf_mod = next((
        m for m in o.modifiers if m.type == 'SUBSURF'), None)

    # Export everything as JSON for now to input into other process w/ Python 2
    json_data = {
        "name": o.name,
        "type": "mesh",
        "location": tuple(o.location),
        "rotation": object_get_rotation(o),
        "scale": tuple(o.scale),
        "positions": [[p.x, p.y, p.z] for p in positions],
        "normals": [[n.x, n.y, n.z] for n in normals],
        "creases": [[e.vertices[0], e.vertices[1]] for e in edges if e.crease > 0.0],
        "creaseSharpnesess": [e.crease for e in edges if e.crease > 0.0],
        "polygons": [[loops[li].vertex_index for li in poly.loop_indices] for poly in mesh.polygons],
        "hasSubdivision": subsurf_mod is not None,
    }

    object_with_modifiers.to_mesh_clear()

    return json_data


def exportCamera(o, settings):
    print("Exporting camera: {}".format(o))
    data = o.data

    projection = {
        "PERSP": "perspective",
        "ORTHO": "orthographic",
        "PANO": None,
    }

    # Stereo cameras are not supported

    # Is this focal length mm?
    if data.lens_unit == "MILLIMETERS":
        focal_length = data.lens
    elif data.lens_unit == "FOV":
        pass
        # TODO: Convert FOV to lens mm
        # TODO: do we need to consider data.sensor_fit in this?

        # Grab location & rotation of object?

        # Export everything as JSON for now to input into other process w/ Python 2
    json_data = {
        "name": o.name,
        "type": "camera",
        "location": tuple(o.location),
        "rotation": object_get_rotation(o),
        "scale": tuple(o.scale),
        "projection": projection[data.type],
        "lens": {
            "focalLength": focal_length,
            # "fov": fov,
        }
    }
    return json_data


EXPORTERS = {
    'MESH': exportMesh,
    'CURVE': None,
    'EMPTY': None,
    'TEXT': None,
    'CAMERA': exportCamera,
    'LIGHT': None,
}


def write_json(name, obj):
    import json
    with open(name + '.json', "w", encoding="utf8") as f:
        json.dump(obj, f, allow_nan=False)

def run_python2_subprocess(input_bytes, filePath, timeout=TIMEOUT):
    import subprocess
    python2_path = '/usr/bin/python2.7'
    dirname = os.path.dirname(__file__)
    script_path = os.path.join(dirname, 'usd_python2/usdWriter.py')
    library_python_path = os.path.join(dirname, 'usd_python2/USD/lib/python/')
    library_path = os.path.join(dirname, 'usd_python2/USD/lib/')
    # We need to make sure Python can find our USD sdk binaries
    print("Adjusting $PYTHONPATH and $PATH for spawned executable...")
    env = {
        "PYTHONPATH": "$PYTHONPATH:" + library_python_path,
        "PATH": "$PATH:" + library_path,
    }
    return subprocess.run(
        [python2_path, script_path, filePath],
        input=input_bytes,
        timeout=timeout,
        env=env)


def write_usd(objects, filePath):
    strs = [json.dumps(o) for o in objects]
    input_bytes = '\n'.join(strs).encode('utf-8')
    result = run_python2_subprocess(input_bytes, filePath)
    print("Output was: {}".format(result.stdout))


def exportUSD(context, filePath, settings):
    """
    Main entry point into export
    """
    print("----------\nExporting to " + filePath)

    if settings['verbose']:
        print("Starting export...")

    scene = context.scene

    if settings['only_selected'] is True:
        objects = (ob for ob in scene.objects if ob.visible_get() and ob.select_get())
    else:
        objects = (ob for ob in scene.objects if ob.visible_get())

    mw = None

    output = []

    try:
        for o in objects:
            addToOutput(context, o, mw, output, settings)
        print("Ready to write.")

    except Exception:
        import traceback
        print('Nothing exported.')
        print(traceback.format_exc())
        return

    # TODO: check DEBUG flag for this
    write_json(filePath, output)

    write_usd(output, filePath)

    print("Finished")


def addToOutput(ctx, o, mw, output, settings):
    """
    Export one item from export list.
    mw - modelview
    """
    if settings['verbose']:
        print('Exporting {}'.format(o))

    e = EXPORTERS[o.type]

    if e is not None:
        result = e(o, settings)
        if result is not None:
            output.append(result)
    else:
        return None

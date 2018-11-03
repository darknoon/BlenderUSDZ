
# License GPLv3

import os
import mathutils
import json
import sys


DEBUG = os.environ.get('BLENDER_DEBUG', False)


def exportMesh(o, settings):
    print("Exporting mesh: {}".format(o))
    data = o.data
    edges = data.edges
    positions = [v.co for v in data.vertices]
    normals = [v.normal for v in data.vertices]

    loops = data.loops

    # TODO: Check for subdivision modifier
    subsurf_mod = next((
        m for m in o.modifiers if m.type == 'SUBSURF'), None)

    # Export everything as JSON for now to input into other process w/ Python 2
    json_data = {
        "name": o.name,
        "location": tuple(o.location),
        "positions": [[p.x, p.y, p.z] for p in positions],
        "normals": [[n.x, n.y, n.z] for n in normals],
        "creases": [[e.vertices[0], e.vertices[1]] for e in edges if e.crease > 0.0],
        "creaseSharpnesess": [e.crease for e in edges if e.crease > 0.0],
        "polygons": [[loops[li].vertex_index for li in poly.loop_indices] for poly in data.polygons],
        "hasSubdivision": subsurf_mod is not None,
    }
    return json_data


EXPORTERS = {
    'MESH': exportMesh,
    'CURVE': None,
    'EMPTY': None,
    'TEXT': None,
    'CAMERA': None,
    'LAMP': None,
}


def write_json(name, obj):
    import json
    with open(name + '.json', "w", encoding="utf8") as f:
        json.dump(obj, f, allow_nan=False)


def write_usd(objects, filePath):
    import subprocess
    python2_path = '/usr/bin/python2.7'
    dirname = os.path.dirname(__file__)
    script_path = os.path.join(dirname, 'usd_python2/usdWriter.py')
    library_path = os.path.join(dirname, 'usd_python2/USD/')
    # We need to make sure Python can find our
    env = {
        "PYTHONPATH": "$PYTHONPATH:" + library_path,
        "PATH": "$PATH:" + library_path,
    }
    strs = [json.dumps(o) for o in objects]
    input_bytes = '\n'.join(strs).encode('utf-8')
    result = subprocess.run(
        [python2_path, script_path, filePath],
        input=input_bytes,
        timeout=5.0,
        env=env)
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
        objects = (ob for ob in scene.objects if ob.is_visible(
            scene) and ob.select)
    else:
        objects = (ob for ob in scene.objects if ob.is_visible(
            scene))

    mw = None

    output = []

    try:
        for o in objects:
            addToOutput(context, o, mw, output, settings)
        print("Ready to write.")

    except Exception as e:
        print('Nothing exported. Error: {} {}'.format(type(e), str(e)))

    # DEBUG
    write_json(filePath, output)

    # TODO: subprocess!
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

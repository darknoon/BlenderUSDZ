
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


def exportPrincipledBSDFShader(shader, settings):
    def get_in(id):
        return next(s for s in shader.inputs if s.identifier == id)

    color_in = get_in("Base Color")
    metal_in = get_in("Metallic")
    rough_in = get_in("Roughness")

    def remove_prefix(path):
        if path.startswith("//"):
            return path[2:]
        else:
            return path

    # Find what is plugged into this connection
    def find_connected_texture(shader_input):
        if len(shader_input.links) is 1:
            connected = shader_input.links[0].from_socket.node
            if type(connected) is bpy.types.ShaderNodeTexImage:
                image = connected.image
                if image.source == "FILE":
                    image_path = image.filepath
                    if image_path is not "":
                        return remove_prefix(image_path)
        return None
    
    def add_texture(d, shader_input):
        texture_path = find_connected_texture(shader_input)
        if texture_path is not None:
            d["texture"] = {"filename": texture_path}
        return d

    diffuse_color = add_texture({"default": tuple(color_in.default_value[0:3])}, color_in)
    # TODO: there is another setting, Transmission that should be considered
    # TODO: look for opacity texture!
    opacity = {"default": color_in.default_value[3]}
    metallic = add_texture({"default": metal_in.default_value}, metal_in)
    roughness = add_texture({"default": rough_in.default_value}, rough_in)
    return {
        "type": "principled",
        "diffuseColor": diffuse_color,
        "metallic": metallic,
        "roughness": roughness,
        "opacity": opacity,
    }


def exportMaterial(m, settings):
    # If there is a principled node hooked up, maybe we're in luck?

    node_tree = m.node_tree
    if node_tree:
        # Export nodes.
        # Find the material connected to the output
        output_node = next(
            (n for n in node_tree.nodes if n.type == "OUTPUT_MATERIAL"))
        if output_node is None:
            print("Couldn't find output for material: ", m)
            return None

        output_node_input = output_node.inputs[0]
        if len(output_node_input.links) is 1:
            shader = output_node_input.links[0].from_socket.node
            print("Found shader to export: ", shader, shader.type)
            shader = exportPrincipledBSDFShader(shader, settings)
        else:
            print("Couldn't find shader connected for material: ", m)
            return None
        # Look for the shader hooked up to this node

    else:
        # Export basic blender colors directly (not common in 2.80 anymore)
        shader = {
            "type": "basic",
            "diffuseColor": {"default": tuple(m.diffuse_color)},
        }
        pass

    print("Asked to export: {}".format(m))
    return {
        "name": m.name,
        "type": "material",
        "shader": shader,
    }


# This corresponds to blender's Mesh object type
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

    edges = mesh.edges
    positions = [v.co for v in mesh.vertices]
    normals = [v.normal for v in mesh.vertices]
    loops = mesh.loops
    # Check whether there are texture coordinates to export
    # TODO: support multiple texture coordinates
    # in the future, this should look at what texture coordinate is connected to the relevant texture nodes, etc
    texture_coordinates = None
    # If we have an active UV layer
    if mesh.uv_layers.active:
        # : MeshUVLoopLayer
        uv_layer = mesh.uv_layers.active
        # list of uv data for each polygon
        polygon_uv_data = [[tuple(uv_layer.data[li].uv) for li in poly.loop_indices] for poly in mesh.polygons]
        texture_coordinates = {"st": polygon_uv_data}

    # Check for subdivision modifier
    # TODO: apply all modifiers EXCEPT this one by default since USD supports subdivision
    # There should be an option to subdivide the meshes as well...
    subsurf_mod = next((
        m for m in o.modifiers if m.type == 'SUBSURF'), None)

    # Ok, where are the submeshes?
    # How does USD handle submeshes / material bindings?
    # def Material "MyMaterial"
    # {
    #   token outputs:surface.connect = </Materials/MyMaterial/pbrMat1.outputs:surface>
    #   def Shader "pbrMat1" {
    #       ...
    #   }
    # }
    #
    material_slots = o.material_slots.items()
    material_name = None
    if len(material_slots) > 0:
        print("slot 0: ", material_slots[0])
        (key, material) = material_slots[0]
        material_name = material.material.name

    json_data = {
        "name": o.name,
        "type": "mesh",
        "location": tuple(o.location),
        "rotation": object_get_rotation(o),
        "scale": tuple(o.scale),
        "material": material_name,
        "positions": [[p.x, p.y, p.z] for p in positions],
        "normals": [[n.x, n.y, n.z] for n in normals],
        "textureCoordinates": texture_coordinates,
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

    # TODO: only export referenced materials
    materials = bpy.data.materials

    output = []

    # Export everything as JSON for now to input into other process w/ Python 2
    try:
        for m in materials:
            writeMaterial(context, m, output, settings)
        for o in objects:
            writeObject(context, o, output, settings)
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


def writeMaterial(ctx, m, output, settings):
    """
    Export one Material from the blender data
    """
    result = exportMaterial(m, settings)
    if result is not None:
        output.append(result)


def writeObject(ctx, o, output, settings):
    """
    Export one Object from a scene
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

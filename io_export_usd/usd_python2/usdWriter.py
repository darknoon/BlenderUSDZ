# This file is NOT licensed under the GPL because it does not interact with the Blender python API.
# Use of this file may be goverened under terms of the USD binaries or other restrictions.

import json
import sys

if sys.version_info.major >= 3:
    print('You need to run this with Python 2.7!')
    exit(1)

from pprint import pprint

try:
    from pxr import UsdGeom, Usd
except:
    print("Make sure you have the USD files in your path!")

filePath = sys.argv[1]

print("Will be writing filePath: " + filePath)


def flatten(p):
    return [v for p in p for v in p]


def usd_mesh_from_json(data):
    positions = [tuple(p) for p in data["positions"]]
    normals = [tuple(n) for n in data["normals"]]
    creases = flatten([[int(idx) for idx in c] for c in data["creases"]])
    crease_sharpnesess = [d * 10 for d in data["creaseSharpnesess"]]
    crease_lengths = [len(c) for c in data["creases"]]
    polygons = data["polygons"]
    face_vertex_counts = [len(v) for v in polygons]
    face_vertex_indices = [
        vertex_id for polygon in polygons for vertex_id in polygon]

    # create mesh
    mesh = UsdGeom.Mesh.Define(stage, '/' + data["name"])

    # Encode transformation
    mesh.AddTranslateOp().Set(tuple(data["location"]))
    mesh.AddRotateXYZOp().Set((0, 0, 0))
    mesh.AddScaleOp().Set((1, 1, 1))

    mesh.CreatePointsAttr(positions)
    # TODO: we should export the BB after subdivision, right?
    # set (static) bounding box for framing and frustum culling
    mesh.CreateExtentAttr(UsdGeom.PointBased(
        mesh).ComputeExtent(mesh.GetPointsAttr().Get()))
    mesh.CreateNormalsAttr(normals)
    # mesh.SetNormalsInterpolation(UsdGeom.Tokens.faceVarying) # normals are stored per-face

    if data["hasSubdivision"]:
        # Technically redundant, since this is the default
        mesh.CreateSubdivisionSchemeAttr().Set(UsdGeom.Tokens.catmullClark)
        mesh.CreateCreaseIndicesAttr(creases, True)
        mesh.CreateCreaseLengthsAttr(crease_lengths, True)
        mesh.CreateCreaseSharpnessesAttr(crease_sharpnesess, True)
    else:
        mesh.CreateSubdivisionSchemeAttr().Set(UsdGeom.Tokens.none)

    # per-face vertex count: cube consists of 6 faces with 4 vertices each
    mesh.CreateFaceVertexCountsAttr(face_vertex_counts)
    mesh.CreateFaceVertexIndicesAttr(
        face_vertex_indices)  # per-face vertex indices


stage = Usd.Stage.CreateNew(filePath)

for line in sys.stdin:
    # print("Got a payload!: {}".format(line))
    payload = json.loads(line)
    usd_mesh_from_json(payload)

print("USD data:")
print(stage.GetRootLayer().ExportToString())

# Save it
stage.Save()

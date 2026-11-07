"""End-to-end check for issue #397 on a real DFF file.

Imports a real DFF, swaps the first material's texture for an image Blender
names "vivian_face_d.png.002" (the same file loaded three times), exports,
then parses the exported file and checks the texture names written to it.

Run headless with the add-on from this checkout (not the installed one):
    blender --background --factory-startup --python tests/blender/test_texture_name_export.py -- <input.dff>
Exit code 0 = pass, 1 = fail.
"""

import os
import sys
import tempfile

import bpy

REPO_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(REPO_DIR))
addon = __import__(os.path.basename(REPO_DIR))
addon.register()
dff = sys.modules[addon.__name__ + ".gtaLib.dff"]

SWAPPED_NAME = "vivian_face_d"


def texture_names(path):
    model = dff.dff()
    model.clumps = []
    model.load_file(path)
    return [[tex.name for mat in geo.materials for tex in mat.textures] for clump in model.clumps for geo in clump.geometry_list]


def make_duplicate_image(work_dir):
    png = os.path.join(work_dir, SWAPPED_NAME + ".png")
    img = bpy.data.images.new(SWAPPED_NAME, 4, 4)
    img.filepath_raw = png
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    for _ in range(3):
        img = bpy.data.images.load(png, check_existing=False)
    return img


def main():
    src = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
    work_dir = tempfile.mkdtemp(prefix="dragonff_test_")
    out = os.path.join(work_dir, "out.dff")

    before = texture_names(src)
    print("input textures:", before)

    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj)
    bpy.ops.import_scene.dff(filepath=src, directory=os.path.dirname(src), files=[{"name": os.path.basename(src)}], load_images=False)

    # Images aren't loaded (no TXD needed), but the exporter only writes a
    # texture when a node has an image: give each node one named after it
    for mat in bpy.data.materials:
        for node in mat.node_tree.nodes if mat.node_tree else []:
            if node.type == "TEX_IMAGE" and node.image is None and node.label:
                node.image = bpy.data.images.get(node.label) or bpy.data.images.new(node.label, 4, 4)

    image = make_duplicate_image(work_dir)
    print("swapped image name:", image.name)

    # First textured material gets the duplicated image
    swapped_from = None
    for mat in bpy.data.materials:
        if not mat.node_tree:
            continue
        node = next((n for n in mat.node_tree.nodes if n.type == "TEX_IMAGE"), None)
        if node is not None:
            swapped_from = node.label
            node.image = image
            break
    if swapped_from is None:
        print("FAIL: input has no textured material")
        return 1
    print("replaced texture:", swapped_from)

    bpy.ops.export_dff.scene(filepath=out, directory=work_dir, only_selected=False, export_version="0x36003")
    if not os.path.isfile(out):
        print("FAIL: export produced no file")
        return 1

    after = texture_names(out)
    print("output textures:", after)

    flat_before = [n for geo in before for n in geo]
    flat_after = [n for geo in after for n in geo]
    expected = sorted(SWAPPED_NAME if n == swapped_from else n for n in flat_before)

    ok = True
    if SWAPPED_NAME not in flat_after:
        print(f"FAIL: '{SWAPPED_NAME}' not in output (bad names: {sorted(set(flat_after) - set(flat_before))})")
        ok = False
    if sorted(set(flat_after)) != sorted(set(expected)):
        print(f"FAIL: texture name set changed\n  expected {sorted(set(expected))}\n  got      {sorted(set(flat_after))}")
        ok = False
    print("PASS" if ok else "FAILED")
    return 0 if ok else 1


sys.exit(main())

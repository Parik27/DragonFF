"""Tests for exported texture names (issue #397).

Run from the repository root, no Blender needed:
    python -m unittest discover -s tests -v
"""

import importlib.util
import pathlib
import unittest

# Load the module by path: the add-on package imports bpy, this module does not.
MODULE_PATH = pathlib.Path(__file__).resolve().parent.parent / "ops" / "exporter_common.py"
spec = importlib.util.spec_from_file_location("exporter_common", MODULE_PATH)
exporter_common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter_common)

texture_name_from_image_name = exporter_common.texture_name_from_image_name


class TextureNameFromImageName(unittest.TestCase):

    def check(self, image_name, expected):
        self.assertEqual(texture_name_from_image_name(image_name), expected)

    def test_extension_and_duplicate_suffix(self):
        # The exact case reported in #397
        self.check("vivian_face_d.png.002", "vivian_face_d")

    def test_extension_only(self):
        self.check("vivian_face_d.png", "vivian_face_d")

    def test_duplicate_suffix_only(self):
        self.check("vivian_face_d.002", "vivian_face_d")

    def test_plain_name(self):
        self.check("vivian_face_d", "vivian_face_d")

    def test_other_extensions(self):
        self.check("road.tga.001", "road")
        self.check("road.dds", "road")

    def test_txd_import_name(self):
        self.check("vehicle.txd/carplate/0", "carplate")

    def test_txd_import_name_with_duplicate_suffix(self):
        self.check("vehicle.txd/carplate/0.001", "carplate")


if __name__ == "__main__":
    unittest.main()

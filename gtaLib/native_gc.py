# GTA DragonFF - Blender scripts to edit basic GTA formats
# Copyright (C) 2019  Parik

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from struct import unpack_from, calcsize

from .dff import RGBA, Sections, TexCoords, Triangle, Vector

# geometry flags
rpGEOMETRYTRISTRIP              = 0x00000001
rpGEOMETRYPOSITIONS             = 0x00000002
rpGEOMETRYTEXTURED              = 0x00000004
rpGEOMETRYPRELIT                = 0x00000008
rpGEOMETRYNORMALS               = 0x00000010
rpGEOMETRYLIGHT                 = 0x00000020
rpGEOMETRYMODULATEMATERIALCOLOR = 0x00000040
rpGEOMETRYTEXTURED2             = 0x00000080
rpGEOMETRYNATIVE                = 0x01000000

# section types
GC_SECTIONTYPE_VERTEX              = 0x09
GC_SECTIONTYPE_NORMAL              = 0x0a
GC_SECTIONTYPE_COLOR               = 0x0b
GC_SECTIONTYPE_TEXCOORD            = 0x0d
GC_SECTIONTYPE_TEXCOORD2           = 0x0e

#######################################################
class NativeGSSkin:

    #######################################################
    @staticmethod
    def unpack(skin, data, geometry):

        skin.num_bones, _num_used_bones, skin.max_weights_per_vertex = unpack_from("<3Bx", data)

        skin.bones_used = []
        for pos in range(4, _num_used_bones + 4):
            skin.bones_used.append(unpack_from("<B", data, pos)[0])

        pos = _num_used_bones + 4
        vertices_count = len(geometry.vertices)

        if _num_used_bones > 1:
            # Read vertex bone indices
            skin.vertex_bone_indices = []
            for _ in range(vertices_count):
                _data = unpack_from("<%dB" % (skin.max_weights_per_vertex), data, pos)
                _extra = [0] * (4 - skin.max_weights_per_vertex)
                skin.vertex_bone_indices.append(list(_data) + _extra)
                pos += skin.max_weights_per_vertex

            # Read vertex bone weights
            skin.vertex_bone_weights = []
            for _ in range(vertices_count):
                _data = unpack_from("<%dB" % (skin.max_weights_per_vertex), data, pos)
                _extra = [0] * (4 - skin.max_weights_per_vertex)
                skin.vertex_bone_weights.append([w / 128 for w in _data] + _extra)
                pos += skin.max_weights_per_vertex
        else:
            skin.vertex_bone_indices = list((skin.bones_used[0], 0, 0, 0) for _ in range(vertices_count))
            skin.vertex_bone_weights = list((1, 0, 0, 0) for _ in range(vertices_count))

        unpack_format = ">16f"

        # Read bone matrices
        skin.bone_matrices = []
        for _ in range(skin.num_bones):

            _data = list(unpack_from(unpack_format, data, pos))
            _data[ 3] = 0.0
            _data[ 7] = 0.0
            _data[11] = 0.0
            _data[15] = 1.0

            skin.bone_matrices.append(
                [_data[0:4], _data[4:8], _data[8:12],
                _data[12:16]]
            )

            pos += calcsize(unpack_format)

#######################################################
class NativeGCGeometry:
    __slots__ = [
        "section_headers",
        "triangle_section_headers",
        "normals",
        "prelit_colors",
        "tex_coords",
        "tex_coords2",
        "_pos",
        "_header_size",
        "_data_size"
    ]

    #######################################################
    def __init__(self):
        self.section_headers = []
        self.triangle_section_headers = []
        self.normals = []
        self.prelit_colors = []
        self.tex_coords = []
        self.tex_coords2 = []
        self._pos = 0
        self._header_size = 0
        self._data_size = 0

    #######################################################
    @staticmethod
    def unpack(geometry, data):
        self = NativeGCGeometry()

        self._header_size, self._data_size = unpack_from("<II", data, self._read(8))

        data_pos = self._pos + self._header_size

        # Read Header
        unk1, mesh_index, unk2, sections_num = unpack_from(">HHII", data, self._read(12))

        for _ in range(sections_num):
            section_offset, section_type, entry_size, byte_type, pad = unpack_from(">IBBBB", data, self._read(8))
            self.section_headers.append(NativeGCSectionHeader(section_offset, section_type, entry_size, byte_type))

        for _ in range(len(geometry.materials)):
            section_offset, section_size = unpack_from(">II", data, self._read(8))
            self.triangle_section_headers.append(NativeGCTriangleSectionHeader(section_offset, section_size))

        # Read Data
        self._read_sections(geometry, data, data_pos)

        try:
            self._read_triangles(geometry, data, data_pos, False)
        except BaseException:
            self._read_triangles(geometry, data, data_pos, True)

    #######################################################
    def _read(self, size):
        current_pos = self._pos
        self._pos += size

        return current_pos

    #######################################################
    def _read_sections(self, geometry, data, data_pos):
        geometry.vertices = []

        last_section_index = len(self.section_headers) - 1

        for s, hdr in enumerate(self.section_headers):
            if s == last_section_index:
                next_section_offset = self._data_size
            else:
                next_section_offset = self.section_headers[s + 1].section_offset
            entries_num = (next_section_offset - hdr.section_offset) // hdr.entry_size

            self._pos = data_pos + hdr.section_offset
            if hdr.section_type == GC_SECTIONTYPE_VERTEX:
                for _ in range(geometry._num_vertices):
                    vertex = Vector._make(unpack_from(">3f", data, self._read(hdr.entry_size)))
                    geometry.vertices.append(vertex)
                    geometry.has_vertices = 1

            elif hdr.section_type == GC_SECTIONTYPE_NORMAL:
                for _ in range(entries_num):
                    normal = Vector._make(unpack_from(">3f", data, self._read(hdr.entry_size)))
                    self.normals.append(normal)
                    geometry.has_normals = 1

            elif hdr.section_type == GC_SECTIONTYPE_COLOR:
                for _ in range(entries_num):
                    prelit_color = Sections.read(RGBA, data, self._read(hdr.entry_size))
                    self.prelit_colors.append(prelit_color)

            elif hdr.section_type == GC_SECTIONTYPE_TEXCOORD:
                for _ in range(entries_num):
                    tex_coords = TexCoords._make(unpack_from(">2f", data, self._read(hdr.entry_size)))
                    self.tex_coords.append(tex_coords)

            elif hdr.section_type == GC_SECTIONTYPE_TEXCOORD2:
                for _ in range(entries_num):
                    tex_coords2 = TexCoords._make(unpack_from(">2f", data, self._read(hdr.entry_size)))
                    self.tex_coords2.append(tex_coords2)

            else:
                raise Exception("Unknown GC section")

    #######################################################
    def _read_triangles(self, geometry, data, data_pos, skip_byte):
        geometry.normals = []
        geometry.prelit_colors = []
        geometry.triangles = []
        geometry.uv_layers = []

        if self.tex_coords:
            geometry.uv_layers.append([])

        if self.tex_coords2:
            geometry.uv_layers.append([])

        for mat, hdr in enumerate(self.triangle_section_headers):
            self._pos = data_pos + hdr.section_offset
            end_pos = self._pos + hdr.section_size

            while self._pos < end_pos:
                b1 = unpack_from(">B", data, self._read(1))[0]
                if b1 == 0:
                    continue

                if b1 != 0x98:
                    raise Exception("Unexpected value")

                unk, entries_num = unpack_from(">BB", data, self._read(2))

                tri_vertices = []
                tri_normals = []
                tri_prelit_colors = []
                tri_tex_coords = []
                tri_tex_coords2 = []

                for _ in range(entries_num):
                    if skip_byte:
                        self._pos += 1

                    for sec_hdr in self.section_headers:
                        if sec_hdr.byte_type == 0x02:
                            val = unpack_from(">B", data, self._read(1))[0]
                        elif sec_hdr.byte_type == 0x03:
                            val = unpack_from(">H", data, self._read(2))[0]
                        else:
                            raise Exception("Unexpected value")

                        if sec_hdr.section_type == GC_SECTIONTYPE_VERTEX:
                            tri_vertices.append(val)
                        elif sec_hdr.section_type == GC_SECTIONTYPE_NORMAL:
                            tri_normals.append(val)
                        elif sec_hdr.section_type == GC_SECTIONTYPE_COLOR:
                            tri_prelit_colors.append(val)
                        elif sec_hdr.section_type == GC_SECTIONTYPE_TEXCOORD:
                            tri_tex_coords.append(val)
                        elif sec_hdr.section_type == GC_SECTIONTYPE_TEXCOORD2:
                            tri_tex_coords2.append(val)

                for i in range(len(tri_vertices) - 2):
                    if i % 2 == 0:
                        idx1 = i + 1
                        idx2 = i + 0
                    else:
                        idx1 = i + 0
                        idx2 = i + 1
                    idx3 = i + 2

                    vertex1, vertex2, vertex3 = tri_vertices[idx1], tri_vertices[idx2], tri_vertices[idx3]
                    if vertex1 == vertex2 or vertex1 == vertex3 or vertex2 == vertex3:
                        continue

                    geometry.triangles.append(Triangle(vertex1, vertex2, mat, vertex3))

                    if tri_normals:
                        geometry.normals.append(self.normals[tri_normals[idx2]])
                        geometry.normals.append(self.normals[tri_normals[idx1]])
                        geometry.normals.append(self.normals[tri_normals[idx3]])

                    if tri_prelit_colors:
                        geometry.prelit_colors.append(self.prelit_colors[tri_prelit_colors[idx2]])
                        geometry.prelit_colors.append(self.prelit_colors[tri_prelit_colors[idx1]])
                        geometry.prelit_colors.append(self.prelit_colors[tri_prelit_colors[idx3]])

                    if tri_tex_coords:
                        geometry.uv_layers[0].append(self.tex_coords[tri_tex_coords[idx2]])
                        geometry.uv_layers[0].append(self.tex_coords[tri_tex_coords[idx1]])
                        geometry.uv_layers[0].append(self.tex_coords[tri_tex_coords[idx3]])

                    if tri_tex_coords2:
                        geometry.uv_layers[1].append(self.tex_coords2[tri_tex_coords2[idx2]])
                        geometry.uv_layers[1].append(self.tex_coords2[tri_tex_coords2[idx1]])
                        geometry.uv_layers[1].append(self.tex_coords2[tri_tex_coords2[idx3]])

#######################################################
class NativeGCSectionHeader:
    __slots__ = [
        "section_offset",
        "section_type",
        "entry_size",
        "byte_type"
    ]

    #######################################################
    def __init__(self, section_offset, section_type, entry_size, byte_type):
        self.section_offset = section_offset
        self.section_type = section_type
        self.entry_size = entry_size
        self.byte_type = byte_type

#######################################################
class NativeGCTriangleSectionHeader:
    __slots__ = [
        "section_offset",
        "section_size"
    ]

    #######################################################
    def __init__(self, section_offset, section_size):
        self.section_offset = section_offset
        self.section_size = section_size

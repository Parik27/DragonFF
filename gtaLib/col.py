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

from struct import unpack_from, calcsize, pack
from struct import error as StructError
from collections import namedtuple
from .dff import strlen

class ColModel:
    def __init__(self):

        # initialise
        self.version       = None
        self.model_name    = None
        self.model_id      = 0
        self.bounds        = None
        self.spheres       = []
        self.boxes         = []
        self.mesh_verts    = []
        self.mesh_faces    = []
        self.face_groups   = []
        self.lines         = []
        self.flags         = 0
        self.shadow_verts  = []
        self.shadow_faces  = []
        self.col_mesh      = None

#######################################################
TBounds    = None
TSurface   = None
TSphere    = None
TBox       = None
TFaceGroup = None
TVertex    = None
TFace      = None
TVector    = namedtuple("TVector", "x y z")
        
#######################################################
class Sections:

    version = 1

    #######################################################
    def init_sections(version):

        global TSurface, TVertex, TBox, TBounds, TSphere, TFace, TFaceGroup
        
        TSurface = namedtuple("TSurface" , "material flags brightness light")
        TVertex  = namedtuple("TVertex"  , "x y z")
        TBox     = namedtuple("TBox"     , "min max surface")

        if version == 1:
            
            TBounds = namedtuple("TBounds", "radius center min max")
            TSphere = namedtuple("TSphere", "radius center surface")
            TFace   = namedtuple("TFace"  , "a b c surface")

        else:

            TFaceGroup = namedtuple("TFaceGroup" , "min max start end")
            TFace      = namedtuple("TFace"      , "a b c material light")
            TBounds    = namedtuple("TBounds"    , "min max center radius")
            TSphere    = namedtuple("TSphere"    , "center radius surface")

        Sections.version = version

        Sections.__formats = {
            # V = Vector, S = Surface
            TBounds    : [  "fVVV" , "VVVf"  ],
            TSurface   : [  "BBBB" , "BBBB"  ],
            TSphere    : [  "fVS"  , "VfS"   ],
            TBox       : [  "VVS"  , "VVS"   ],
            TFaceGroup : [  "VVHH" , "VVHH"  ],
            TVertex    : [  "fff"  , "hhh"   ],
            TFace      : [  "IIIS" , "HHHBB" ]
        }

    #######################################################
    def compress_vertices(vertices):
        compressed_vertices = []
        for vertex in vertices:
            compressed_vertices.append(TVertex._make(int(i*128) for i in vertex))

        return compressed_vertices
            
    #######################################################
    def __read_format(format, data, offset):

        output = []

        for char in format:
            # Custom format: Vector
            if char == 'V':
                output.append(unpack_from("<fff", data, offset))
                offset += 12

            # Custom format: Surface
            elif char == 'S':
                output.append(
                    Sections.read_section(TSurface, data, offset)
                )
                offset += Sections.size(TSurface)

            else:
                output.append(unpack_from(char, data, offset)[0])
                offset += calcsize(char)
                
        return output

    #######################################################
    def __write_format(format, data):

        _data = b''
        
        for index, char in enumerate(format):
            # Custom format: Vector
            if char == 'V':
                _data += pack("<fff", *data[index])

            # Custom format: Surface
            elif char == 'S':
                _data += Sections.write_section(TSurface, data[index])

            else:
                _data += pack(char, data[index])
            
        return _data

    #######################################################
    def write_section(type, data):

        version = 0 if Sections.version == 1 else 1

        return Sections.__write_format(
            Sections.__formats[type][version], data
        )
    
    #######################################################
    def read_section(type, data, offset):

        version = 0 if Sections.version == 1 else 1
        
        return type._make(Sections.__read_format(
            Sections.__formats[type][version], data, offset)
        )

    #######################################################
    def size(type):

        version = 0 if Sections.version == 1 else 1

        format = Sections.__formats[type][version]

        # Convert vectors and surface to their properties
        format = format.replace("V", "fff")
        format = format.replace("S", "BBBB")

        return calcsize(format)
        
#######################################################
class coll:

    __slots__ = [
        "models",
        "_data",
        "_pos"
    ]

    #######################################################
    def __read_struct(self, format):

        unpacked = unpack_from(format, self._data, self._pos)
        self._pos += calcsize(format)

        return unpacked

    #######################################################
    def __incr(self, incr):
        pos = self._pos
        self._pos += incr
        return pos

    #######################################################
    def __read_block(self, block_type, count=-1):
        block_size = Sections.size(block_type)
        object_array = []

        if count == -1:
            count = unpack_from("<I", self._data, self.__incr(4))[0]

        for i in range(count):
            object_array.append(
                Sections.read_section(
                    block_type,
                    self._data,
                    self.__incr(block_size)
                )
            )
            
        return object_array
    
    #######################################################
    def __read_legacy_col(self, model):

        # Spheres
        model.spheres += self.__read_block(TSphere)
        self.__incr(4) # number of unk. data (from GTAModding)

        model.boxes      += self.__read_block(TBox)
        model.mesh_verts += self.__read_block(TVertex)
        model.mesh_faces += self.__read_block(TFace)

    #######################################################
    def __read_new_col(self, model, pos):
        sphere_count, box_count, face_count, line_count, flags, \
            spheres_offset, box_offset, lines_offset, verts_offset, \
            faces_offset, triangles_offset = \
            unpack_from("<HHHBxIIIIIII", self._data, self.__incr(36))

        model.flags = flags
        
        if model.version >= 3:
            shadow_mesh_face_count, shadow_verts_offset, shadow_faces_offset = \
                unpack_from("<III", self._data, self.__incr(12))

        if model.version == 4:
            self.__incr(4)

        # Spheres
        self._pos = pos + spheres_offset + 4
        model.spheres += self.__read_block(TSphere, sphere_count)

        # Boxes
        self._pos = pos + box_offset + 4
        model.boxes += self.__read_block(TBox, box_count)
        
        # Face Groups
        if flags & 8:
            self._pos = pos + faces_offset
            facegroup_count = unpack_from("<L", self._data, self._pos)
            self._pos = pos + faces_offset - (28 * facegroup_count[0])
            model.face_groups += self.__read_block(TFaceGroup, facegroup_count[0])

        # Faces
        self._pos = pos + faces_offset + 4
        model.mesh_faces += self.__read_block(TFace, face_count)
        
        verts_count = 0
        # Calculate Verts count
        for i in model.mesh_faces:
            verts_count = max(verts_count, i.a + 1, i.b + 1, i.c + 1)
            
        # Vertices        
        self._pos = pos + verts_offset + 4
        model.mesh_verts += self.__read_block(TVertex, verts_count)
        
        # Calculate the actual vertices
        for i, vertex in enumerate(model.mesh_verts):
            model.mesh_verts[i] = (
                vertex.x / 128,
                vertex.y / 128,
                vertex.z / 128
            )

        # Read shadow mesh
        if model.version >= 3 and flags & 16:

            # Vertices
            self._pos = pos + shadow_verts_offset + 4
            verts_count = (shadow_faces_offset - shadow_verts_offset) // 6
            model.shadow_verts += self.__read_block(TVertex, verts_count)

            for i, vertex in enumerate(model.shadow_verts):
                model.shadow_verts[i] = (
                    vertex.x / 128,
                    vertex.y / 128,
                    vertex.z / 128
                )
            
            # Faces
            self._pos = pos + shadow_faces_offset + 4
            model.shadow_faces += self.__read_block(TFace, shadow_mesh_face_count)
        
    #######################################################
    def __read_col(self):
        model = ColModel()
        pos = self._pos
        header_format = namedtuple("header_format",
                                   [
                                       "magic_number",
                                       "file_size",
                                       "model_name",
                                       "model_id"
                                   ]
        )

        try:
            if self._data[:3] == b"COL":
                header = header_format._make(self.__read_struct("4sI22sH"))
            else:
                # Headless COL (DFF embedded PS2 version)
                header = header_format._make((b"COLL", len(self._data) - 8, b"col", 0))
        except StructError:
            raise RuntimeError("Unexpected EOF")

        magic_number = header.magic_number.decode("ascii")

        model.model_name = header.model_name[:strlen(header.model_name)].decode(
            "ascii"
        )
        model.model_id = header.model_id

        version_headers = {
            "COLL": 1,
            "COL2": 2,
            "COL3": 3,
            "COL4": 4 # what version is this?
        }
        
        try:
            model.version = version_headers[magic_number]
        except KeyError:
            raise RuntimeError("Invalid COL header")

        Sections.init_sections(model.version)
        
        # Read TBounds
        model.bounds = Sections.read_section(
            TBounds,
            self._data,
            self._pos
        )
        self._pos += Sections.size(TBounds)

        if model.version == 1:
            self.__read_legacy_col(model)
        else:
            self.__read_new_col(model, pos)

        self._pos = pos + header.file_size + 8 # set to next model
        return model
            
    #######################################################
    def load_memory(self, memory):
        self._data = memory
        self._pos = 0

        while self._pos < len(self._data):
            try:
                self.models.append(self.__read_col())
            except RuntimeError:
                return
    
    #######################################################
    def load_file(self, filename):

        with open(filename, mode='rb') as file:
            content = file.read()
            self.load_memory(content)

    #######################################################
    def __write_block(self, block_type, blocks, write_count = True):

        data = b''
        
        if write_count:
            data += pack("<I", len(blocks))

        for block in blocks:
            data += Sections.write_section(block_type, block)

        return data
            
    #######################################################
    def __write_col_legacy(self, model):
        data = b''

        data += self.__write_block(TSphere, model.spheres)
        data += pack('<I', 0)
        data += self.__write_block(TBox, model.boxes)
        data += self.__write_block(TVertex, model.mesh_verts)
        data += self.__write_block(TFace, model.mesh_faces)

        return data

    #######################################################
    def __write_col_new(self, model):
        data = b''

        flags = 0
        flags |= 2 if model.spheres or model.boxes or model.mesh_faces else 0
        flags |= 8 if model.face_groups else 0
        flags |= 16 if model.shadow_faces and model.version >= 3 else 0
        
        header_len = 104
        header_len += 12 if model.version >= 3 else 0
        header_len += 4 if model.version >= 4 else 0

        offsets = []
        
        # Spheres
        offsets.append(len(data) + header_len)
        data += self.__write_block(TSphere, model.spheres, False)

        # Boxes
        offsets.append(len(data) + header_len)
        data += self.__write_block(TBox, model.boxes, False)

        offsets.append(0) # TODO: Cones
        
        # Vertices
        offsets.append(len(data) + header_len)
        data += self.__write_block(TVertex,
                                   Sections.compress_vertices(model.mesh_verts),
                                   False)
        
        # Face Groups
        if flags & 8:
            data += self.__write_block(TFaceGroup, model.face_groups, False)
            data += pack("<L", len(model.face_groups))

        # Faces
        offsets.append(len(data) + header_len)
        data += self.__write_block(TFace, model.mesh_faces, False)

        offsets.append(0) # Triangle Planes (what are these?)
        
        # Shadow Mesh

        if model.version >= 3:

            # Shadow Vertices
            offsets.append(len(data) + header_len)
            data += self.__write_block(TVertex,
                                       Sections.compress_vertices(
                                           model.shadow_verts),
                                       False)
            
            # Shadow Vertices
            offsets.append(len(data) + header_len)
            data += self.__write_block(TFace,
                                       model.shadow_faces,
                                       False)

        # Write Header
        header_data = pack("<HHHBxIIIIIII",
                            len(model.spheres),
                            len(model.boxes),
                            len(model.mesh_faces),
                            len(model.lines),
                            flags,
                            *offsets[:6])

        # Shadow Mesh (only after version 3)
        if model.version >= 3:
            header_data += pack("<III", len(model.shadow_faces), *offsets[6:])

        return header_data + data
    
    #######################################################
    def __write_col(self, model):

        Sections.init_sections(model.version)
        
        if model.version == 1:
            data = self.__write_col_legacy(model)
        else:
            data = self.__write_col_new(model)
            
        data = Sections.write_section(TBounds, model.bounds) + data

        header_size = 24
        header = [
            ("COL" + ('L' if model.version == 1 else str(model.version))).encode(
                "ascii"
            ),
            len(data) + header_size,
            model.model_name.encode("ascii"),
            model.model_id
        ]

        return pack("4sI22sH", *header) + data
            
    #######################################################
    def write_memory(self):

        data = b''
        
        for model in self.models:
            data += self.__write_col(model)

        return data
            
    #######################################################
    def write_file(self, filename):

        with open(filename, mode='wb') as file:
            content = self.write_memory()
            file.write(content)
            
    #######################################################
    def __init__(self, model = None):
        self.models = [ColModel()] * 0
        self._data = ""
        self._pos = 0

        if model is not None:
            self.models.append(model)

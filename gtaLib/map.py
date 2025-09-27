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

from collections import defaultdict
from io import StringIO, BytesIO
import struct

from .map_formats import (
    MAP_SECTION_TYPES, MapTextSectionFormat, MapBinarySectionFormat, MapCarsSection, MapInstSection
)

#######################################################
# Map files are ide/ipl type files
class MapFileText:
    def __init__(self):
        self.entries = []

    def load_file (self, filename):
        with open(filename, 'r') as f:
            self.load_file_stream(f)

    def load_memory (self, data):
        f = StringIO(data)
        self.load_file_stream(f)

    def load_file_stream (self, f):
        current_section = None
        for line in f:
            line = line.strip()

            if line.startswith("#") or not line:
                continue

            if line == "end":
                current_section = None

            elif current_section is None:
                current_section = line

            else:
                for map_section_type in MAP_SECTION_TYPES:
                    data = map_section_type.read (MapTextSectionFormat, "SA", (current_section, line))
                    if data:
                        self.entries.append (data)
                        break

    def write_file (self, filename):
        with open(filename, 'w') as f:
            f.write(self.write_memory ())

    def write_memory (self):
        f = StringIO()

        sections = defaultdict(list)

        for output_format, entry in self.entries:
            section, line = entry.write (output_format)
            sections[section].append (line)

        for section, lines in sections.items():
            f.write(section + "\n")
            for line in lines:
                f.write(line + "\n")
            f.write("end\n")
        return f.getvalue()

#######################################################
class MapFileBinary:
    def __init__(self):
        self.entries = []

    def load_file (self, filename):
        with open(filename, 'rb') as f:
            self.load_file_stream(f)

    def load_memory (self, data):
        f = BytesIO(data)
        self.load_file_stream(f)

    def load_file_stream (self, f):
        header = f.read(76)
        num_instances, num_cars, instances_offset, cars_offset = struct.unpack("<4xI12xI4xI4x24xI12x", header)

        f.seek(instances_offset)
        for _ in range(num_instances):
            self.entries.append(MapInstSection.read (MapBinarySectionFormat, "SA", f))

        f.seek(cars_offset)
        for _ in range(num_cars):
            self.entries.append(MapCarsSection.read (MapBinarySectionFormat, "SA", f))

    def write_memory (self):
        f = BytesIO()

        instances = []
        cars = []
        for entry in self.entries:
            if isinstance(entry[1], MapCarsSection):
                cars.append(entry)
            elif isinstance(entry[1], MapInstSection):
                instances.append(entry)

        inst_data = b"".join(entry[1].write(entry[0]) for entry in instances)
        cars_data = b"".join(entry[1].write(entry[0]) for entry in cars)

        num_instances = len(instances)
        num_cars = len(cars)
        instances_offset = 76
        cars_offset = instances_offset + len(inst_data)

        # Write header
        f.write(struct.pack("<4sI12xI4xI4x24xI12x",
            b"bnry",
            num_instances,
            instances_offset,
            num_cars,
            cars_offset
        ))

        # Write sections
        f.write(inst_data)
        f.write(cars_data)

        return f.getvalue()

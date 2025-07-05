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

import os

from dataclasses import dataclass
from struct import unpack, unpack_from

#######################################################
@dataclass
class DirectoryEntry:
    offset: int
    size: int
    name: str

    #######################################################
    @classmethod
    def read_from_memory(cls, data, offset=0):
        offset, size, name = unpack_from("II24s", data, offset)
        name = name.split(b'\0', 1)[0].decode('utf-8')
        return cls(offset, size, name)

#######################################################
class img:

    #######################################################
    def load_dir_memory(self, data):
        data_len = len(data)
        for pos in range(0, data_len, 32):
            entry = DirectoryEntry.read_from_memory(data, pos)
            self.directory_entries.append(entry)

    #######################################################
    def clear(self):
        self.directory_entries:list[DirectoryEntry] = []
        self.entry_idx = 0

    #######################################################
    @classmethod
    def open(cls, filename):
        file = open(filename, mode='rb')
        self = cls(file)

        magic, entries_num = unpack("4sI", file.read(8))

        if magic == b"VER2":
            dir_data = file.read(entries_num * 32)
            self.load_dir_memory(dir_data)

        else:
            dir_filename = os.path.splitext(filename)[0] + '.dir'
            with open(dir_filename, mode='rb') as dir_file:
                dir_data = dir_file.read()
                self.load_dir_memory(dir_data)

        file.seek(0, os.SEEK_SET)

        return self

    #######################################################
    def close(self):
        if self._file and not self._file.closed:
            self._file.close()

    #######################################################
    def read_entry(self, entry_idx=None):
        if entry_idx is None:
            entry_idx = self.entry_idx

        if 0 <= entry_idx < len(self.directory_entries):
            entry = self.directory_entries[entry_idx]
            self._file.seek(entry.offset * 2048, os.SEEK_SET)
            return entry.name, self._file.read(entry.size * 2048)

        return "", b""

    #######################################################
    def find_entry_idx(self, name):
        return next(
            (idx for idx, entry in enumerate(self.directory_entries) if entry.name == name),
            -1
        )

    #######################################################
    def __init__(self, file):
        self._file = file
        self.clear()

    #######################################################
    def __enter__(self):
        return self

    #######################################################
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    #######################################################
    def __del__(self):
        self.close()

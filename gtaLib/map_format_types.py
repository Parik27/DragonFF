import struct
from collections import defaultdict
from dataclasses import fields
from typing import get_args

class MapSectionFormat:
    def can_parse (self, data):
        return True

    def read (self, data_class, data):
        return None

    def write (self, data_class):
        return None

    def supports_field (self, field_name):
        return True

#######################################################
class MapTextSectionFormat(MapSectionFormat):
    def __init__ (self, section, fields_order):
        self.section = section
        self.fields_order = fields_order

    def can_parse (self, data : tuple[str, str]):
        section = data[0]
        line = data[1]

        return section == self.section and len(self.fields_order) == len(line.split(","))

    def supports_field(self, field_name):
        return field_name in self.fields_order

    def __get_fields_target_indices (self) -> dict[str, list[int]]:
        fields = defaultdict(list)
        for idx, field in enumerate(self.fields_order):
            fields[field].append(idx)
        return fields

    def read (self, data_class, data):
        _ = data[0]
        line = data[1]
        line = line.replace(",", " ")
        line = line.split()

        fields_target_indices = self.__get_fields_target_indices ()
        cls_kwargs = {}

        for field in fields(data_class):
            if field.name not in fields_target_indices:
                continue

            target_indices = fields_target_indices[field.name]
            if len(target_indices) == 1:
                cls_kwargs[field.name] = field.type(line[target_indices[0]])
            else:
                cls_kwargs[field.name] = field.type(
                    x(line[idx]) for idx, x in zip(target_indices, field.type.__args__)
                )

        return data_class(**cls_kwargs)

    def write (self, data_class):
        fields_target_indices = self.__get_fields_target_indices ()
        data = [""] * len(self.fields_order)

        for field in fields(data_class):
            if field.name not in fields_target_indices:
                continue

            target_indices = fields_target_indices[field.name]
            value = getattr(data_class, field.name)
            if len(target_indices) == 1:
                data[target_indices[0]] = str(value)

            else:
                for idx, v in zip(target_indices, value):
                    data[idx] = str(v)

        return (self.section, ", ".join(data))

class MapPlaceholderTextSectionFormat (MapTextSectionFormat):
    def __init__ (self):
        pass

    def can_parse (self, data):
        return True

    def read (self, data_class, data):
        return data_class(text_section=data[0], text_data=data[1])

    def write (self, data_class):
        return (data_class.text_section, data_class.text_data)

    def supports_field(self, field_name):
        return True

#######################################################
class MapBinarySectionFormat(MapSectionFormat):
    def __init__ (self, struct_format, fields_order):
        self.struct_format = struct_format
        self.fields_order = fields_order

    def supports_field(self, field_name):
        return field_name in self.fields_order

    def read (self, data_class, file_stream):
        cls_kwargs = {}

        size = struct.calcsize (self.struct_format)

        data = file_stream.read (size)
        data = struct.unpack (self.struct_format, data)

        current_idx = 0
        for field in self.fields_order:
            field_metadata = data_class.__dataclass_fields__[field]
            if len(get_args(field_metadata.type)) > 1:
                cls_kwargs[field] = field_metadata.type(data[current_idx:current_idx + len(get_args(field_metadata.type))])
                current_idx += len(get_args(field_metadata.type))
            else:
                cls_kwargs[field] = field_metadata.type(data[current_idx])
                current_idx += 1

        return data_class(**cls_kwargs)

    def write (self, data_class):
        data = []

        for field in self.fields_order:
            value = getattr(data_class, field)
            if isinstance(value, (list, tuple)):
                data.extend(value)
            else:
                data.append(value)

        return struct.pack (self.struct_format, *data)


#######################################################
def add_format (format_name, games, format_obj):
    def _add_format(cls):
        if not hasattr(cls, "formats"):
            cls.formats = []

        cls.formats.append((format_name, games, format_obj))
        return cls
    return _add_format

#######################################################
class MapSection:
    @classmethod
    def get_name (cls):
        return cls.__name__

    @classmethod
    def get_format_by_name (cls, target_format_name) -> MapSectionFormat | None:
        for format_name, format_games, format_obj in cls.formats:
            if format_name == target_format_name:
                return format_obj
        return None

    @classmethod
    def read (cls, format_type, game, data):
        for format_name, format_games, format_obj in cls.formats:
            if game in format_games and isinstance(format_obj, format_type) and format_obj.can_parse (data):
                section_obj = format_obj.read (cls, data)
                return (format_name, section_obj)
        return None

    def write (self, target_format_name, **kwargs):
        for format_name, _, format_obj in self.formats:
            if format_name == target_format_name:
                return format_obj.write (self)
        return None

    # Returns a format that can be used to export to a given game
    # target_format is used to choose between the multiple formats
    # a game might have.
    @classmethod
    def choose_best_format_for_game (cls, target_exporter, target_game, target_format_name):

        target_format_obj : MapSectionFormat | None = None

        # check if current format is fine for this game
        for format_name, format_games, format_obj in cls.formats:
            if format_name == target_format_name:
                target_format_obj = format_obj

            if (
                    isinstance(format_obj, target_exporter)
                    and format_name == target_format_name
                    and target_game in format_games
            ):
                return format_name

        # current format is not fine for the game, find a different one
        # based on the common supported fields and the overall fields.
        supported_fields_by_target_format = []
        for field in fields (cls):
            if target_format_obj is None or target_format_obj.supports_field (field.name):
                supported_fields_by_target_format.append (field.name)

        final_format = None
        final_format_heuristic = 0
        for format_name, format_games, format_obj in cls.formats:
            if target_game not in format_games or not isinstance(format_obj, target_exporter):
                continue

            supported_target_fields = 0
            for field in supported_fields_by_target_format:
                if format_obj.supports_field (field):
                    supported_target_fields += 1

            if supported_target_fields > final_format_heuristic:
                final_format = format_name
                final_format_heuristic = supported_target_fields

        return final_format


    def get_location (self):
        return getattr (self, "location", (0.0, 0.0, 0.0))

    def get_rotation (self):
        return getattr (self, "rotation", (0.0, 0.0, 0.0, 1.0))

    def get_scale (self):
        return getattr (self, "scale", (1.0, 1.0, 1.0))

    def set_location (self, location):
        if hasattr (self, "location"):
            self.location = location

    def set_rotation (self, rotation):
        if hasattr (self, "rotation"):
            self.rotation = rotation

    def set_scale (self, scale):
        if hasattr (self, "scale"):
            self.scale = scale

    def get_linked_entries (self) -> list[str]:
        return []

    def get_collection_name (self) -> str | None:
        return None

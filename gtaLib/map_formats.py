from .map_format_types import MapPlaceholderTextSectionFormat, MapTextSectionFormat, MapBinarySectionFormat, MapSection, add_format
from dataclasses import dataclass, KW_ONLY

#######################################################
# Defines simple objects. They can be placed into the world through the inst section of the item placement files.
@dataclass
@add_format("IDE - Timed - SA - Type 4", ["SA"], MapTextSectionFormat("tobj", ['ide_id', 'model_name', 'txd_name', 'draw_distance', 'flags', 'time_on', 'time_off']))
@add_format("IDE - Timed - Type 3", ["III", "VC", "SA"], MapTextSectionFormat("objs", ['ide_id', 'model_name', 'txd_name', 'mesh_count', 'draw_distance', 'flags', 'time_on', 'time_off']))
@add_format("IDE - Timed - Type 2", ["III", "VC", "SA"], MapTextSectionFormat("objs", ['ide_id', 'model_name', 'txd_name', 'mesh_count', 'draw_distance', 'draw_distance_2', 'flags', 'time_on', 'time_off']))
@add_format("IDE - Timed - Type 1", ["III", "VC", "SA"], MapTextSectionFormat("objs", ['ide_id', 'model_name', 'txd_name', 'mesh_count', 'draw_distance', 'draw_distance_2', 'draw_distance_3', 'flags', 'time_on', 'time_off']))
@add_format("IDE - Type 3", ["III", "VC", "SA"], MapTextSectionFormat("objs", ['ide_id', 'model_name', 'txd_name', 'mesh_count', 'draw_distance', 'flags']))
@add_format("IDE - Type 2", ["III", "VC", "SA"], MapTextSectionFormat("objs", ['ide_id', 'model_name', 'txd_name', 'mesh_count', 'draw_distance', 'draw_distance_2', 'flags']))
@add_format("IDE - Type 1", ["III", "VC", "SA"], MapTextSectionFormat("objs", ['ide_id', 'model_name', 'txd_name', 'mesh_count', 'draw_distance', 'draw_distance_2', 'draw_distance_3', 'flags']))
@add_format("IDE - SA - Type 4", ["SA"], MapTextSectionFormat("objs", ['ide_id', 'model_name', 'txd_name', 'draw_distance', 'flags']))
class MapObjDefSection (MapSection):
    ide_id : int
    model_name : str
    txd_name : str
    mesh_count : int = 1
    draw_distance : float = 255.0
    draw_distance_2 : float = 255.0
    draw_distance_3 : float = 255.0
    flags : int = 0
    time_on : int = 0
    time_off : int = 0

    def get_collection_name (self):
        return f"ide_{self.ide_id}"

    def get_linked_entries (self):
        return [f"{self.model_name}.dff"]

#######################################################
@dataclass
@add_format("IPL - III", ["III"], MapTextSectionFormat("inst", ['ide', 'model_name', 'interior', 'location', 'location', 'location', 'rotation', 'rotation', 'rotation', 'rotation', 'lod']))
@add_format("IPL - VC", ["VC"], MapTextSectionFormat("inst", ['ide', 'model_name', 'interior', 'location', 'location', 'location', 'scale', 'scale', 'scale', 'rotation', 'rotation', 'rotation', 'rotation']))
@add_format("IPL - SA", ["SA"], MapTextSectionFormat("inst", ['ide', 'model_name', 'interior', 'location', 'location', 'location', 'rotation', 'rotation', 'rotation', 'rotation', 'lod']))
@add_format("Binary", ["SA"], MapBinarySectionFormat ("<fffffffiii", ['location', 'rotation', 'ide', 'interior', 'lod']))
class MapInstSection(MapSection):
    ide : int
    location : tuple[float, float, float]
    rotation : tuple[float, float, float, float]
    scale : tuple[float, float, float] = (1.0, 1.0, 1.0)

    _ : KW_ONLY
    model_name : str = "dummy"
    interior : int = -1
    lod : int = 0

    def get_linked_entries (self):
        return [f"ide_{self.ide}"]

#######################################################
@dataclass
@add_format("Binary", ["SA"], MapBinarySectionFormat ("<ffffIIIIIIII", ["location", "angle", "car_id", "prim", "sec", "flags", "alarm", "door_lock", "min_delay", "max_delay"]))
class MapCarsSection(MapSection):
    location : tuple[float, float, float]
    angle : float
    car_id : int
    prim : int
    sec : int
    flags : int
    alarm : int
    door_lock : int
    min_delay : int
    max_delay : int

#######################################################
@dataclass(kw_only=True)
@add_format("IPL/IDE", ["III", "VC", "SA"], MapPlaceholderTextSectionFormat ())
class MapPlaceholderSection(MapSection):
    text_section : str = ""
    text_data : str = ""


MAP_SECTION_TYPES = [
    MapObjDefSection,
    MapInstSection,
    MapCarsSection,
    MapPlaceholderSection
]

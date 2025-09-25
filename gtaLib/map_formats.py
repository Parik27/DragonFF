from .map_format_types import MapPlaceholderTextSectionFormat, MapTextSectionFormat, MapBinarySectionFormat, MapSection, add_format
from dataclasses import dataclass, KW_ONLY

#######################################################
@dataclass
@add_format("IPL - III", "III", MapTextSectionFormat("inst", ['ide', 'model_name', 'interior', 'location', 'location', 'location', 'rotation', 'rotation', 'rotation', 'rotation', 'lod']))
@add_format("IPL - VC", "VC", MapTextSectionFormat("inst", ['ide', 'model_name', 'interior', 'location', 'location', 'location', 'scale', 'scale', 'scale', 'rotation', 'rotation', 'rotation', 'rotation']))
@add_format("IPL - SA", "SA", MapTextSectionFormat("inst", ['ide', 'model_name', 'interior', 'location', 'location', 'location', 'rotation', 'rotation', 'rotation', 'rotation', 'lod']))
@add_format("Binary", "SA", MapBinarySectionFormat ("<fffffffiii", ['location', 'rotation', 'ide', 'interior', 'lod']))
class MapInstSection(MapSection):
    ide : int
    location : tuple[float, float, float]
    rotation : tuple[float, float, float, float]
    scale : tuple[float, float, float] = (1.0, 1.0, 1.0)

    _ : KW_ONLY
    model_name : str = "dummy"
    interior : int = -1
    lod : int = 0

#######################################################
@dataclass
@add_format("Binary", "SA", MapBinarySectionFormat ("<ffffIIIIIIII", ["location", "angle", "car_id", "prim", "sec", "flags", "alarm", "door_lock", "min_delay", "max_delay"]))
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
@add_format("IPL/IDE", "SA", MapPlaceholderTextSectionFormat ())
class MapPlaceholderSection(MapSection):
    text_section : str = ""
    text_data : str = ""


MAP_SECTION_TYPES = [
    MapInstSection,
    MapCarsSection,
    MapPlaceholderSection
]

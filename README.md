# DragonFF 🐉

DragonFF is a Blender Addon for import and export of GTA files. 

At the moment, only Renderware files are supported. Support for formats other than .dff is planned. 

## Supported Features

The following is a list of supported features by the addon

#### File Types

- [X] Model files
- [ ] Texture Files
- [X] Collision files (including the ones packed in dff)
  - [X] Import
  - [X] Export *(Partial)*
- [ ] Map files (.ipl, .ide)
  - [X] Import *(Partial, experimental)*
  - [ ] Export
- [ ] Animation files

#### Model Features

- [X] Skinned mesh support
- [X] Multiple UV Maps
- [X] Mass export
- [X] Material Effects
  - [X] Environment/Normal Maps
  - [ ] Dual Textures
  - [X] UV Animation
- [X] Rockstar Specular and Reflection Extensions
- [ ] 2D Effects

## Installation

1. [Download](https://github.com/Parik27/DragonFF/archive/refs/heads/master.zip) the addon zip file from the latest master branch
2. Import the downloaded .zip file by selecting it from *(User) Preferences/Addons/Install from File*
3. Set the addon "GTA DragonFF" to enabled
4. Import dff from Import tab or an IPL/IFP from the panel in *Scene Settings*

## Python Module

The python scripts have been designed with reusability in mind. As of now, the dff module is standalone, and can be used with any other Python instance without the need for Blender API.

#### Standalone Modules

* [X] - DFF - `dff.py`
* [ ] - TXD - `txd.py`
* [X] - COL - `col.py`
* [X] - IPL/IDE - `map.py` (partial, experimental)
* [ ] - IFP - `ifp.py`

#### Contributors

The following have contributed significantly to the project:

* [swift502](https://github.com/swift502) - For the map importer.
* [Psycrow101](https://github.com/Psycrow101) - For delta morphs importer.


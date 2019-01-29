# DragonFF 🐉

DragonFF is a Blender Addon for import and export of GTA files. 

At the moment, only Renderware files are supported. Support for formats other than .dff is planned. 

## Supported Features

The following is a list of supported features by the addon

#### File Types

- [X] Model files
- [ ] Texture Files
- [ ] Collision files (including the ones packed in dff)
- [ ] Map files (.ipl, .ide)
- [ ] Animation files

#### Model Features

- [X] Skinned mesh support
- [X] Multiple UV Maps
- [X] Mass export
- [ ] Material Effects
  - [ ] Environment/Normal Maps
  - [ ] UV Animation
- [ ] 2D Effects

## Installation

1. Get a release from the *Releases* for a stable release, or the bleeding-edge script by cloning the repository
2. Import the downloaded .zip file by selecting it from *(User) Preferences/Addons/Install from File*
3. Set the addon "GTA DragonFF" to enabled
4. Import dff from Import tab or an IPL/IFP from the panel in *Scene Settings*

## Python Module

The python scripts have been designed with reusability in mind. As of now, the dff module is standalone, and can be used with any other Python instance without the need for Blender API.

#### Standalone Modules

* [X] - DFF - `dff.py`
* [ ] - TXD - `txd.py`
* [ ] - COL - `col.py`
* [ ] - IPL/IDE - `map.py`
* [ ] - IFP - `ifp.py`

# DragonFF 🐉

[![Discord](https://img.shields.io/discord/1286221154612281405.svg?label=&logo=discord&logoColor=ffffff&color=7389D8&labelColor=6A7EC2)](https://discord.gg/QxpkwNqeTr)

DragonFF is a Blender Addon for import and export of GTA files. 

At the moment, only Renderware files are supported. Support for formats other than .dff is planned. 

## Supported Features

The following is a list of supported features by the addon

#### File Types

- [X] Model files
- [X] Texture Files
  - [X] Import
  - [X] Export *(partial, experimental)*
- [X] Collision files (including the ones packed in dff)
  - [X] Import
  - [X] Export
- [ ] Map files (.ipl, .ide)
  - [X] Import *(partial, experimental)*
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
- [X] 2D Effects

## Installation

There are two ways to install DragonFF.

### From Blender Extentensions

In Blender 4.2 and above, you can install DragonFF directly from within Blender.

![image](https://github.com/user-attachments/assets/02868d1c-273b-47a2-927d-083aa5d45605)

1. Go to Blender Preferences.
2. In the Get Extensions Tab, search for DragonFF
3. Click Install

## Manually

In older versions of Blender or to get the newest changes (that may be unstable), use the following instructions to install Blender from GitHub.

1. [Download](https://github.com/Parik27/DragonFF/archive/refs/heads/master.zip) the addon zip file from the latest master branch
2. Import the downloaded .zip file by selecting it from *(User) Preferences/Addons/Install from File*
3. Set the addon "GTA DragonFF" to enabled
4. Import dff from Import tab or an IPL/IFP from the panel in *Scene Settings*

## Python Module

The python scripts have been designed with reusability in mind. As of now, the dff module is standalone, and can be used with any other Python instance without the need for Blender API.

#### Standalone Modules

* [X] - DFF - `dff.py`
* [X] - TXD - `txd.py`
* [X] - COL - `col.py`
* [X] - IPL/IDE - `map.py` *(partial, experimental)*
* [ ] - IFP - `ifp.py`

#### Contributors

The following have contributed significantly to the project:

* [swift502](https://github.com/swift502) - For the map importer.
* [Psycrow101](https://github.com/Psycrow101) - For delta morphs importer.


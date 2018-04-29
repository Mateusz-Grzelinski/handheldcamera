'''
Copyright (C) 2018 Mateusz Grzeliński
czubaka111@gmail.com

Created by Mateusz Grzeliński

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

bl_info = {
    "name": "Handheld Camera",
    "description": "Use accelerometer and gyroscope data to handheld animate any object in your scene",
    "author": "Mateusz Grzeliński",
    "version": (0, 0, 1),
    "blender": (2, 79, 0),
    "location": "View3D > Tool Shelf > Animation",
    "warning": "This addon is stable, still in development.",
    "wiki_url": "",
    "category": "Animation" }


import bpy


# load and reload submodules
##################################

import importlib
from . import developer_utils
importlib.reload(developer_utils)
modules = developer_utils.setup_addon_modules(__path__, __name__, "bpy" in locals())



# register
##################################

import traceback
from .handheld_data import HandheldData

def register():
    try: 
        bpy.utils.register_module(__name__)
        bpy.types.Scene.handheld_data = bpy.props.PointerProperty(type=HandheldData)
    except: traceback.print_exc()

    print("Registered {} with {} modules".format(bl_info["name"], len(modules)))

def unregister():
    try: 
        del bpy.types.Scene.handheld_data
        bpy.utils.unregister_module(__name__)
    except: traceback.print_exc()

    print("Unregistered {}".format(bl_info["name"]))

#!/usr/bin/env bash

# connnect to debugger automatically
blender --python-expr "import bpy; bpy.ops.debug.connect_debugger_pycharm()"
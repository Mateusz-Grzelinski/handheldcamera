#!/usr/bin/env bash

# run blender and connnect to pycharm debugger automatically
# see: https://code.blender.org/2015/10/debugging-python-code-with-pycharm/
blender --python-expr "import bpy; bpy.ops.debug.connect_debugger_pycharm()"

import bpy


def objects_in_scene(scene, context):
    """ List all objects in scene with some icons"""
    result = []
    objs = []
    for i, obj in enumerate(context.scene.objects):
        item = (obj.name, obj.name, "", i)
        if obj.type == 'CAMERA':
            item = (obj.name, obj.name, "", 'CAMERA_DATA', i)
        if obj.type == 'LAMP':
            item = (obj.name, obj.name, "", 'LAMP_SUN', i)
        if obj.type == 'MESH':
            item = (obj.name, obj.name, "", 'MESH_CUBE', i)
        result.append(item)
    return result


class HandheldData(bpy.types.PropertyGroup):
    """Strones data, that will be accesed by user (or must be globally accesible).
    Only blender properties 
    """

    host = bpy.props.StringProperty(
        name="Host",
        default="localhost",
        description="Host to connect to for example: localhost, 192.168.0.10")

    port = bpy.props.IntProperty(
        name="Port number",
        description="Port number for the connection",
        default=5000,
        min=1025, max=65535)

    connection_button_label = bpy.props.StringProperty(
        name="connection_button_label",
        default="Connect",
        description="")

    scale = bpy.props.FloatProperty(
        name="Scale",
        description="Scale of location",
        default=1, min=0)

    selected_object = bpy.props.EnumProperty(
        name="Object",
        description="Select object that will be animated",
        items=objects_in_scene)

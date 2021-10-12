import bpy
import bpy_extras
import mathutils
import numpy as np
import pathlib
import os
import sys


class mplInstall(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "mpl.install"
    bl_label = "Install matplotlib"
    bl_description = 'Install matplotlib into blenders python enviornment'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        fdir = self.properties.filepath
        scene = context.scene
        #sys.executable
        #choose mpl install and move? or do something? open terminal?
        #maybe run pip from the site-packages?

        return{'FINISHED'}


class mplPanel(bpy.types.Panel):
    bl_label = 'Matplotlib Tools'
    bl_idname = 'VIEW_3D_PT_mplPanel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'mpl'

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        mpl_data = scene.mpl_data

        row = layout.row()
        row.operator("mpl.install", text='Install matplotlib')

        keys = [
            'animate', 
            'start_date', 
            'end_date', 
            'start_frame', 
            'end_frame',
        ]

        layout.label(text="Matplotlib settings")
        setting_rows = []
        for key in keys:
            setting_rows.append(layout.row())
            setting_rows[-1].prop(mpl_data, key)
        
        setting_rows[2].enabled = mpl_data.animate
        setting_rows[3].enabled = mpl_data.animate
        setting_rows[4].enabled = mpl_data.animate


class mplExternal:
    def __init__(self):
        self.datas = None


class mplData(bpy.types.PropertyGroup):
    animate: bpy.props.BoolProperty(name='Animate', default = False)
    start_date: bpy.props.FloatProperty(name='Start date [MJD]', soft_min = 0, default = 59366.5)
    end_date: bpy.props.FloatProperty(name='End date [MJD]', soft_min = 0, default = 59367.5)
    start_frame: bpy.props.IntProperty(name='Start frame', soft_min = 1, default = 1)
    end_frame: bpy.props.IntProperty(name='End frame', soft_min = 1, default = 240)


classes = [
    mplPanel,
    mplData,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.mpl_data = bpy.props.PointerProperty(type=mplData)
    bpy.types.Scene.mpl_external = mplExternal()

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.mpl_data
    del bpy.types.Scene.mpl_external



if __name__ == "__main__":
    register()

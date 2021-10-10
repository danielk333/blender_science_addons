import bpy
import bpy_extras
import numpy as np
import pathlib
import os

'''
https://blender.stackexchange.com/questions/3219/how-to-show-to-the-user-a-progression-in-a-script
https://docs.blender.org/api/blender_python_api_current/bpy.types.Operator.html#modal-execution

https://www.youtube.com/watch?v=4TcY8UE2IrQ&ab_channel=Rogue_Knight3d
https://www.youtube.com/watch?v=V4HNIbDn4K4&ab_channel=CGGeek
https://www.youtube.com/watch?v=h_xAWf13ziI&ab_channel=StargazeImagery

bpy.utils.user_resource('SCRIPTS', "addons")
'''

LOCAL_PATH = pathlib.Path(os.getcwd())

class radEarth(bpy.types.Operator):
    bl_idname = 'radar.earth'
    bl_label = 'Make Earth'
    bl_description = 'Make selected object Earth'
    bl_options = {'REGISTER', 'UNDO'}
 
 
    def execute(self, context):
        
        obj = context.object
        scene = context.scene
        
        if 'this-is-earth' not in obj:

            bpy.ops.object.subdivision_set(level=2, relative=False)
            bpy.ops.object.shade_smooth()

            mat = bpy.data.materials.new('Earth')
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            nodes.clear()
            
            links = mat.node_tree.links
            
            node_bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
            node_out = nodes.new(type="ShaderNodeOutputMaterial")
            node_mix_earth = nodes.new(type="ShaderNodeMixShader")
            links.new(node_bsdf.outputs[0], node_mix_earth.inputs[1])
            links.new(node_mix_earth.outputs[0], node_out.inputs[0])
            
            node_tex = nodes.new(type="ShaderNodeTexImage")
            node_tex_bump = nodes.new(type="ShaderNodeTexImage")
            node_bump = nodes.new(type="ShaderNodeBump")        
            nmap = nodes.new(type="ShaderNodeMapping")
            ncoord = nodes.new(type="ShaderNodeTexCoord")
            
            node_tex_light = nodes.new(type="ShaderNodeTexImage")
            nmap_light = nodes.new(type="ShaderNodeMapping")
            ncoord_light = nodes.new(type="ShaderNodeTexCoord")
            node_emis_light = nodes.new(type="ShaderNodeEmission")
            node_math_light = nodes.new(type="ShaderNodeMath")

            node_emis_light.inputs[0].default_value = (1, 0.977526, 0.535937, 1)
            node_math_light.operation = 'MULTIPLY'
            node_math_light.inputs[1].default_value = 0.5

            node_bump.inputs[0].default_value = 0.1
            
            alb_pth = pathlib.Path(scene.rad_data_folder) / 'earth' / 'Albedo.jpg'
            node_tex.image = bpy.data.images.load(str(alb_pth), check_existing=False)
            
            bump_pth = pathlib.Path(scene.rad_data_folder) / 'earth' / 'Bump.jpg'
            node_tex_bump.image = bpy.data.images.load(str(bump_pth), check_existing=False)
            node_tex_bump.image.colorspace_settings.name = 'Non-Color'
            
            light_pth = pathlib.Path(scene.rad_data_folder) / 'earth' / 'night_lights_modified.png'
            node_tex_light.image = bpy.data.images.load(str(light_pth), check_existing=False)
            
            links.new(ncoord_light.outputs[2], nmap_light.inputs[0])
            links.new(nmap_light.outputs[0], node_tex_light.inputs[0])
            links.new(node_tex_light.outputs[0], node_math_light.inputs[0])
            links.new(node_math_light.outputs[0], node_emis_light.inputs[1])
            links.new(node_emis_light.outputs[0], node_mix_earth.inputs[2])
            
            links.new(ncoord.outputs[2], nmap.inputs[0])
            links.new(nmap.outputs[0], node_tex.inputs[0])
            links.new(node_tex_bump.outputs[0], node_bump.inputs[2])
            links.new(node_bump.outputs[0], node_bsdf.inputs[20])
            links.new(node_tex.outputs[0], node_bsdf.inputs[0])
            
            obj.data.materials.append(mat)
            obj['this-is-earth'] = True

        if obj.name + '-atmos' in scene.objects:
            atmos_obj = scene.objects[obj.name + '-atmos']
        else:
            bpy.ops.mesh.primitive_uv_sphere_add(
                scale=obj.scale*1.007,
                location=obj.location,
            )
            atmos_obj = bpy.context.active_object
            
        if 'this-is-earth' not in atmos_obj:
            bpy.ops.object.shade_smooth()
            bpy.ops.object.subdivision_set(level=2, relative=False)
            atmos_obj.name = obj.name + '-atmos'
            
            mat_atmos = bpy.data.materials.new('Earth-atmos')
            mat_atmos.use_nodes = True
            nodes_atmos = mat_atmos.node_tree.nodes
            nodes_atmos.clear()
            
            links_atmos = mat_atmos.node_tree.links
            
            node_bsdf_atmos = nodes_atmos.new(type="ShaderNodeBsdfPrincipled")
            node_mix_atmos = nodes_atmos.new(type="ShaderNodeMixShader")
            node_out_atmos = nodes_atmos.new(type="ShaderNodeOutputMaterial")
            links_atmos.new(node_bsdf_atmos.outputs[0], node_mix_atmos.inputs[2])
            links_atmos.new(node_mix_atmos.outputs[0], node_out_atmos.inputs[0])
            
            node_tr_bsdf = nodes_atmos.new(type="ShaderNodeBsdfTransparent")
            links_atmos.new(node_tr_bsdf.outputs[0], node_mix_atmos.inputs[1])
            node_lr_weight = nodes_atmos.new(type="ShaderNodeLayerWeight")
            links_atmos.new(node_lr_weight.outputs[1], node_mix_atmos.inputs[0])
            
            node_lr_weight.inputs[0].default_value = 0.1
            
            node_bsdf_atmos.inputs[0].default_value = (0.0645064, 0.303284, 0.8, 1)

            atmos_obj.data.materials.append(mat_atmos)
            atmos_obj['this-is-earth-atmosphere'] = True

        return {'FINISHED'}


class radSetup(bpy.types.Operator):
    bl_idname = "radar.setup"
    bl_label = "Set engine and background"
    bl_description = 'Set engine and background'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bg_node = bpy.data.worlds["World"].node_tree.nodes["Background"]
        bg_node.inputs[0].default_value = (0, 0, 0, 1)
        
        # (make sure we use the EEVEE render engine + enable bloom effect)
        scene = bpy.context.scene
        scene.render.engine = "BLENDER_CYCLES"
        scene.cycles.device = 'GPU'

        st_path = pathlib.Path(scene.rad_data_folder) / 'stars' / '8k_stars_milky_way.png'
        
        bg_node


class radSelect(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "radar.select"
    bl_label = "Load resources"
    bl_description = 'Load resources folder'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        fdir = self.properties.filepath
        scene = context.scene
        
        scene.rad_data_folder = fdir
        

class radClear(bpy.types.Operator):
    bl_idname = 'radar.clear'
    bl_label = 'Clear scene'
    bl_description = 'Clear scene'
    bl_options = {'REGISTER', 'UNDO'}
 
 
    def execute(self, context):
        for obj in bpy.data.objects:
            bpy.data.objects.remove(obj)
        
        return {'FINISHED'}

class radarPanel(bpy.types.Panel):
    bl_label = 'Radar Tools'
    bl_idname = 'VIEW_3D_PT_radarPanel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'radar'

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        row = layout.row()
        row.operator("radar.select", text="Select resource folder")
        row = layout.row()
        row.operator("radar.setup", text="Setup scene")
        row = layout.row()
        row.operator("radar.clear", text='Clear all objects')
        row = layout.row()
        row.operator("mesh.primitive_uv_sphere_add", text='Add sphere')
        row = layout.row()
        row.operator("radar.earth", text="Convert to Earth")

        layout.label(text="Radar data:")
        row = layout.row()
        row.scale_y = 2.0
        sub = row.row()
        

classes = [
    radarPanel,
    radClear,
    radEarth,
    radSelect,
    radSetup,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.rad_data_folder = bpy.props.StringProperty()

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.rad_data_folder


if __name__ == "__main__":
    register()

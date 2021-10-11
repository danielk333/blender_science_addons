import bpy
import bpy_extras
import mathutils
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
            
            mat = bpy.data.materials.get('Earth')
            if mat is None:
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
            node_math_off_light = nodes.new(type="ShaderNodeMath")
            node_math_off_light.name = 'sun_input_multiply'

            node_emis_light.inputs[0].default_value = (1, 0.977526, 0.535937, 1)
            node_math_light.operation = 'MULTIPLY'
            node_math_off_light.operation = 'MULTIPLY'
            node_math_off_light.inputs[0].default_value = 1
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
            links.new(node_math_light.outputs[0], node_math_off_light.inputs[1])
            links.new(node_math_off_light.outputs[0], node_emis_light.inputs[1])
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
            
        if 'this-is-earth-atmosphere' not in atmos_obj:
            bpy.ops.object.shade_smooth()
            bpy.ops.object.subdivision_set(level=2, relative=False)
            atmos_obj.name = obj.name + '-atmos'
            
            mat_atmos = bpy.data.materials.get('Earth-atmos')
            if mat_atmos is None:
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



class radSun(bpy.types.Operator):
    bl_idname = "radar.sun"
    bl_label = "Add Sun"
    bl_description = 'Add the Sun with a diurnal cycle'
    bl_options = {'REGISTER', 'UNDO'}


    def get_sun_equatorial(self, jd):
        n = jd - 2451545.0
        L = 280.460 + 0.9856474*n
        g = np.radians(357.528 + 0.9856003*n)
        lam = np.radians(L + 1.915*np.sin(g) + 0.02*np.sin(2*g))
        eps = np.radians(23.439 - 0.0000004*n)
        ra = np.arctan2(np.cos(eps)*np.sin(lam), np.cos(lam))
        dec = np.arcsin(np.sin(eps)*np.sin(lam))
        return ra, dec
        

    def execute(self, context):
        scene = context.scene
        sun_prop = scene.rad_sun_properties
        
        obj = None
        for obj_ in scene.objects:
            if 'this-is-earth' in obj_:
                obj = obj_
                break
        assert obj is not None, 'There is no Earth'
        
        sun = None
        for obj_ in scene.objects:
            if 'this-is-sun' in obj_:
                sun = obj_
                break
        if sun is None:        
            bpy.ops.object.light_add(
                type='SUN', 
                radius=1, 
                align='WORLD', 
                location=(0, 0, 0), 
                scale=(1, 1, 1),
            )
            sun = bpy.context.active_object
            sun['this-is-sun'] = True
            
        sun.animation_data_clear()

        mat = bpy.data.materials.get('Earth')
        node = None
        nd_rot = None
        if mat is not None:
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            for nd in nodes:
                if nd.name == 'sun_input_multiply':
                    node = nd
                    break
            if node is not None:
                for nd in nodes:
                    if nd.name == 'lights_rotator':
                        nd_rot = nd
                        break
                if nd_rot is None:
                    nd_grad = nodes.new(type="ShaderNodeTexGradient")
                    nd_ramp = nodes.new(type="ShaderNodeValToRGB")
                    nd_tex = nodes.new(type="ShaderNodeTexCoord")
                    nd_rot = nodes.new(type="ShaderNodeMapping")
                    
                    nd_ramp.color_ramp.elements[0].position = (0.0)
                    nd_ramp.color_ramp.elements[0].color = (0.0735011, 0.0735011, 0.0735011, 1)
                    nd_ramp.color_ramp.elements[1].position = (1)
                    nd_ramp.color_ramp.elements[1].color = (1, 1, 1, 1)

                    nd_grad.gradient_type = 'LINEAR'
                    nd_rot.name = 'lights_rotator'

                    links.new(nd_tex.outputs[3], nd_rot.inputs[0])
                    links.new(nd_rot.outputs[0], nd_grad.inputs[0])
                    links.new(nd_grad.outputs[0], nd_ramp.inputs[0])
                    links.new(nd_ramp.outputs[0], node.inputs[0])
                else:
                    if sun_prop.animate and \
                        mat.node_tree.animation_data is not None and \
                        mat.node_tree.animation_data.action is not None:
                        frame_range = mat.node_tree.animation_data.action.frame_range
                        for frame in range(int(frame_range.x), int(frame_range.y) + 1):
                            nd_rot.inputs[2].keyframe_delete(data_path='default_value', frame=frame)
        
        #'XYZ', 'QUATERNION'
        obj.rotation_mode = 'XYZ'
        sun.rotation_mode = 'XYZ'
        obj.animation_data_clear()
        
        jd = sun_prop.start_date + 2400000.5
        
        if sun_prop.animate:
            frames = sun_prop.end_frame - sun_prop.start_frame
            d_jd = (sun_prop.end_date - sun_prop.start_date)/float(frames)
            frame_range = range(sun_prop.start_frame, sun_prop.end_frame)
        else:
            frame_range = [1]
    
        for frame in frame_range:
            ra, dec = self.get_sun_equatorial(jd)
            tod = np.mod(jd - 0.5,1)*np.pi*2
            
            print(f'ra={np.degrees(ra)}, dec={np.degrees(dec)}, tod={np.degrees(tod)}')
            
            rot_z = mathutils.Matrix.Rotation(ra, 4, 'Z')
            rot_z_tex = mathutils.Matrix.Rotation(ra + np.pi/2, 4, 'Z')
            rot_z_tod = mathutils.Matrix.Rotation(tod, 4, 'Z')
            rot_x_down = mathutils.Matrix.Rotation(np.pi/2 - dec, 4, 'X')
            rot_x_up = mathutils.Matrix.Rotation(dec, 4, 'X')
            
            light_rot = rot_z_tex @ rot_x_down @ rot_z_tod
            sun_rot = rot_z @ rot_x_down
            obj_rot = rot_z_tod.inverted()
            
            #to_quaternion
            #to_euler('XYZ')
            sun.rotation_euler = sun_rot.to_euler('XYZ')
            obj.rotation_euler = rot_z_tod.to_euler('XYZ')
            if sun_prop.animate:
                sun.keyframe_insert(data_path = 'rotation_euler', frame=frame)
                obj.keyframe_insert(data_path = 'rotation_euler', frame=frame)
            
            if nd_rot is not None:
                nd_rot.inputs[2].default_value = light_rot.to_euler('XYZ')
                if sun_prop.animate:
                    nd_rot.inputs[2].keyframe_insert(data_path='default_value', frame=frame)
            
            if sun_prop.animate:
                jd += d_jd

            
        return {'FINISHED'}


class radSetup(bpy.types.Operator):
    bl_idname = "radar.setup"
    bl_label = "Set engine and background"
    bl_description = 'Set engine and background'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        nodes = bpy.data.worlds["World"].node_tree.nodes
        nodes.clear()
        links = bpy.data.worlds["World"].node_tree.links
        
        scene = bpy.context.scene
        scene.render.engine = "CYCLES"
        scene.cycles.device = 'GPU'

        st_path = pathlib.Path(scene.rad_data_folder) / 'stars' / '8k_stars_milky_way.jpg'
        
        node_output = nodes.new(type="ShaderNodeOutputWorld")
        node_mix = nodes.new(type="ShaderNodeMixShader")
        node_bg_img = nodes.new(type="ShaderNodeTexEnvironment")
        node_bg_color = nodes.new(type="ShaderNodeBackground")

        node_mix.inputs[0].default_value = 0.2
        node_bg_color.inputs[0].default_value = (0, 0, 0, 1)
        node_bg_img.image = bpy.data.images.load(str(st_path), check_existing=False)
        
        links.new(node_bg_color.outputs[0], node_mix.inputs[1])
        links.new(node_bg_img.outputs[0], node_mix.inputs[2])
        links.new(node_mix.outputs[0], node_output.inputs[0])
        
        return {'FINISHED'}



class radSelect(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "radar.select"
    bl_label = "Load resources"
    bl_description = 'Load resources folder'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        fdir = self.properties.filepath
        scene = context.scene
        
        scene.rad_data_folder = fdir
        
        return {'FINISHED'}



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
        sun_prop = scene.rad_sun_properties
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

        keys = [
            'animate', 
            'start_date', 
            'end_date', 
            'start_frame', 
            'end_frame',
        ]

        layout.label(text="Sun settings:")
        setting_rows = []
        for key in keys:
            setting_rows.append(layout.row())
            setting_rows[-1].prop(sun_prop, key)
        
        setting_rows[2].enabled = sun_prop.animate
        setting_rows[3].enabled = sun_prop.animate
        setting_rows[4].enabled = sun_prop.animate

        row = layout.row()
        row.operator("radar.sun", text="Set Sun")

        layout.label(text="Radar data:")
        row = layout.row()
        row.scale_y = 2.0
        sub = row.row()
        

class radSunProperties(bpy.types.PropertyGroup):
    animate: bpy.props.BoolProperty(name='Animate', default = False)
    start_date: bpy.props.FloatProperty(name='Start date [MJD]', soft_min = 0, default = 59366.5)
    end_date: bpy.props.FloatProperty(name='End date [MJD]', soft_min = 0, default = 59367.5)
    start_frame: bpy.props.IntProperty(name='Start frame', soft_min = 1, default = 1)
    end_frame: bpy.props.IntProperty(name='End frame', soft_min = 1, default = 240)


classes = [
    radarPanel,
    radClear,
    radEarth,
    radSelect,
    radSetup,
    radSun,
    radSunProperties,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.rad_sun_properties = bpy.props.PointerProperty(type=radSunProperties)
    bpy.types.Scene.rad_data_folder = bpy.props.StringProperty()

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.rad_data_folder


if __name__ == "__main__":
    register()

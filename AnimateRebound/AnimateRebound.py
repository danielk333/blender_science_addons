import bpy
import bpy_extras
import numpy as np
import time


'''

REFACTOR PLAN:
    load data with button, then set settings, have operators for building the scene step by step
    add sun
    add planets
    add test particles
    modal opeartors with calls to adding one particles, allows progressbars
    

'''
def create_emission_shader(color, strength, mat_name):
    '''From: https://demando.se/blogg/post/dev-generating-a-procedural-solar-system-with-blenders-python-api/
    '''
    # create a new material resource (with its
    # associated shader)
    mat = bpy.data.materials.new(mat_name)
    # enable the node-graph edition mode
    mat.use_nodes = True
    
    # clear all starter nodes
    nodes = mat.node_tree.nodes
    nodes.clear()

    # add the Emission node
    node_emission = nodes.new(type="ShaderNodeEmission")
    # (input[0] is the color)
    node_emission.inputs[0].default_value = color
    # (input[1] is the strength)
    node_emission.inputs[1].default_value = strength
    
    # add the Output node
    node_output = nodes.new(type="ShaderNodeOutputMaterial")
    
    # link the two nodes
    links = mat.node_tree.links
    link = links.new(node_emission.outputs[0], node_output.inputs[0])

    # return the material reference
    return mat


def setup_scene(END_FRAME):
    # set a black background
    bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)
    
    # (make sure we use the EEVEE render engine + enable bloom effect)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.use_bloom = True
    
    # (set the animation start/end/current frames)
    scene.frame_start = 1
    scene.frame_end = END_FRAME
    scene.frame_current = 1
    # get the current 3D view (among all visible windows
    # in the workspace)
    area = None
    for a in bpy.data.window_managers[0].windows[0].screen.areas:
        if a.type == "VIEW_3D":
            area = a
            break
    space = area.spaces[0] if area else bpy.context.space_data
    # apply a "rendered" shading mode + hide all
    # additional markers, grids, cursors...
    space.shading.type = 'RENDERED'
    
    bpy.ops.object.camera_add(
        enter_editmode=False, 
        align='VIEW', 
        location=(0, 0, 0), 
        rotation=(0.801518, 0.0107709, 2.23358), 
        scale=(1, 1, 1),
    )
    bpy.ops.view3d.camera_to_view()



class rebData:
    def __init__(self):
        self.data = None
        self.reb_particles = None


class rebAnimationProperties(bpy.types.PropertyGroup):
    star_index: bpy.props.IntProperty(name='Star index', soft_min = 0)
    star_radius: bpy.props.FloatProperty(name='Star radius', soft_min = 0)
    particle_radius: bpy.props.FloatProperty(name='Particle radius', soft_min = 0)
    frame_rate: bpy.props.IntProperty(name='Frame-rate', soft_min = 1)
    

class rebSelect(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "reb.select"
    bl_label = "Load archive file"
    bl_description = 'Load archive file and add objects'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        fdir = self.properties.filepath
        scene = context.scene
        anim = scene.reb_anim
        
        #bpy.ops.reb.progress('INVOKE_DEFAULT')
        
        data = np.load(fdir)
        pos0 = data['0']
        
        scene.reb_data.data = data
        scene.reb_data.reb_particles = pos0.shape[1]

        #set scene
        setup_scene(anim.frame_rate*len(data))
        
        steps_total = pos0.shape[1]*len(data)
        steps = 0
        
        #add objects and animate
        for pi in range(pos0.shape[1]):
            bpy.ops.mesh.primitive_uv_sphere_add(
                radius=1,
                location=pos0[:,pi],
            )
            obj = bpy.context.active_object
            bpy.ops.object.shade_smooth()
            obj.name = f'particle-{pi}'
            obj.keyframe_insert(data_path = 'location', frame=1)
            
            scene.reb_progress_label = f'Adding keyframes object-{pi}'
            time.sleep(3)
        
            for step in range(1, len(data)):
                pos = data[f'{step}']
                obj.location = pos[:,pi]
                obj.keyframe_insert(data_path = 'location', frame=(step+1)*anim.frame_rate)
                
                steps += 1
                scene.reb_progress = 100*steps/steps_total
                context.area.tag_redraw()

            if pi == anim.star_index:
                obj.scale = [anim.star_radius]*3
                obj.data.materials.append(
                    create_emission_shader(
                        (1, 0.66, 0.08, 1),
                        10,
                        f'particleMat-{pi}',
                    )
                )
            else:
                obj.scale = [anim.particle_radius]*3
                obj.data.materials.append(
                    create_emission_shader(
                        (0.7, 0.7, 1, 1),
                        2,
                        f'particleMat-{pi}',
                    )
                )
        scene.reb_progress_label = 'Done'

        return{'FINISHED'}


class rebClear(bpy.types.Operator):
    bl_idname = 'reb.clear'
    bl_label = 'Clear scene'
    bl_description = 'Clear scene'
    bl_options = {'REGISTER', 'UNDO'}
 
 
    def execute(self, context):
        for obj in bpy.data.objects:
            bpy.data.objects.remove(obj)
        
        return {'FINISHED'}

'''
class rebProgress(bpy.types.Operator):
    bl_idname = "reb.progress"
    bl_label = "Progress-bar"

    def execute(self, context):
        context.object.location.x = self.value / 100.0
        return {'FINISHED'}

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            self.value = event.mouse_x
            
            
            self.execute(context)
            
            
            return {'FINISHED'}
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.init_loc_x = context.object.location.x
        self.value = event.mouse_x
        self.execute(context)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
'''

class rebPanel(bpy.types.Panel):
    """Creates a Panel in the 3d view to configure the Rebound animation"""
    bl_label = 'REBOUND Tools'
    bl_idname = 'VIEW_3D_PT_REBPanel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'REBOUND'

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        anim = scene.reb_anim

        layout.label(text="Animation settings:")
        layout.prop(anim, 'star_index')
        layout.prop(anim, 'star_radius')
        layout.prop(anim, 'particle_radius')
        layout.prop(anim, 'frame_rate')
        
        progress_bar = layout.row()
        progress_bar.prop(scene,"reb_progress")
        progress_lbl = layout.row()
        progress_lbl.active = False
        progress_lbl.label(text=scene.reb_progress_label)

        layout.label(text="REBOUND data:")
        row = layout.row()
        row.scale_y = 2.0
        sub = row.row()
        sub.operator("reb.clear", text="Clear scene")
        sub.operator("reb.select", text="Load archive")
        

classes = [
    rebSelect,
    rebClear,
    rebPanel,
    #rebProgress,
    rebAnimationProperties,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.reb_anim = bpy.props.PointerProperty(type=rebAnimationProperties)
    bpy.types.Scene.reb_progress = bpy.props.FloatProperty(
        name="Progress", 
        subtype="PERCENTAGE",
        soft_min=0, 
        soft_max=100, 
        precision=0,
    )
    bpy.types.Scene.reb_progress_label = bpy.props.StringProperty()
    bpy.types.Scene.reb_data = rebData()


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.reb_data
    del bpy.types.Scene.reb_anim


if __name__ == "__main__":
    register()

import bpy
import bpy_extras
import numpy as np

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
        
        scene.eevee.use_bloom = True
        
        data = np.load(fdir)
        pos0 = data['0']
        
        scene.reb_data.data = data
        scene.reb_data.reb_particles = pos0.shape[1]

        #set scene        
        for pi in range(pos0.shape[1]):
            bpy.ops.mesh.primitive_uv_sphere_add(
                radius=1,
                location=pos0[:,pi],
            )
            obj = bpy.context.active_object
            bpy.ops.object.shade_smooth()
            obj.name = f'particle-{pi}'
            obj.keyframe_insert(data_path = 'location', frame=1)
        
            for step in range(1, len(data)):
                pos = data[f'{step}']
                obj.location = pos[:,pi]
                obj.keyframe_insert(data_path = 'location', frame=(step+1)*anim.frame_rate)

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
    rebAnimationProperties,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.reb_anim = bpy.props.PointerProperty(type=rebAnimationProperties)
    bpy.types.Scene.reb_data = rebData()


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.reb_data
    del bpy.types.Scene.reb_anim


if __name__ == "__main__":
    register()

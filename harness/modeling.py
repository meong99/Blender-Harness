"""Small reusable Blender helpers for agent-authored builders; units are metres."""
import bpy
def material(name,color,roughness=.45):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=roughness
 return m
def attach(ob,name,asset,mat=None):
 ob.name=name
 for col in list(ob.users_collection):col.objects.unlink(ob)
 asset.objects.link(ob)
 if mat:ob.data.materials.append(mat)
 return ob

def rounded_box(name,location,dimensions,asset,mat,radius=.004):
 bpy.ops.mesh.primitive_cube_add(size=1,location=location);ob=attach(bpy.context.object,name,asset,mat);ob.dimensions=dimensions
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 bevel=ob.modifiers.new('Soft edges','BEVEL');bevel.width=radius;bevel.segments=3
 return ob

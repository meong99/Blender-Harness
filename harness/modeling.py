"""Small reusable Blender helpers for agent-authored builders; units are metres."""
import bpy,json
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

def fuse_voxel(objects,voxel_size,output_name=None,smooth_iterations=3,smooth_factor=.2):
 """Explicit early-blockout union. Caller must permit ALL affected objects.

 Rebuilds topology; UVs/custom data are not guaranteed. Not an automatic cleanup.
 Keep one existing output name so the edit preservation contract remains stable.
 """
 if not objects or voxel_size<=0:raise ValueError('Mesh objects and positive voxel size required')
 if output_name and output_name not in [o.name for o in objects]:raise ValueError('Output name must belong to an existing target')
 if any(o.type!='MESH' for o in objects):raise ValueError('Mesh targets only')
 plan_text=bpy.data.texts.get('H_quality_plan')
 if plan_text:
  names={o.name for o in objects}
  for group in json.loads(plan_text.as_string()).get('separate',[]):
   if len(names.intersection(group['objects']))>1:raise ValueError('Fusion would violate separate group: '+group['name'])
 bpy.ops.object.select_all(action='DESELECT')
 for ob in objects:ob.select_set(True)
 active=next((o for o in objects if o.name==output_name),objects[0]);bpy.context.view_layer.objects.active=active
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 # Convert evaluated modifiers explicitly before remeshing.
 bpy.ops.object.convert(target='MESH')
 if len(objects)>1:bpy.ops.object.join()
 active=bpy.context.object;active.data.remesh_voxel_size=voxel_size;active.data.use_remesh_preserve_volume=True
 result=bpy.ops.object.voxel_remesh()
 if 'FINISHED' not in result:raise RuntimeError('Voxel remesh did not finish')
 if smooth_iterations:
  mod=active.modifiers.new('Local union smoothing','SMOOTH');mod.factor=smooth_factor;mod.iterations=smooth_iterations
  bpy.ops.object.modifier_apply(modifier=mod.name)
 for face in active.data.polygons:face.use_smooth=True
 return active
def rounded_box(name,location,dimensions,asset,mat,radius=.004):
 bpy.ops.mesh.primitive_cube_add(size=1,location=location);ob=attach(bpy.context.object,name,asset,mat);ob.dimensions=dimensions
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 bevel=ob.modifiers.new('Soft edges','BEVEL');bevel.width=radius;bevel.segments=3
 return ob

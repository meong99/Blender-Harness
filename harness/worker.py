"""Blender-only worker. All runs use a separate factory-startup process."""
import bpy,bmesh,sys,json,hashlib,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'vendor/blenderwright'))
sys.path.insert(0,str(ROOT/'harness'))
from addon import dispatcher,handlers
handlers.register()
job=json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text(encoding='utf-8'))
run=Path(job['run']);records=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,value):Path(p).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
def call(name,params):
 result=dispatcher.dispatch(name,params)
 records.append({'command':name,'params':{k:hashlib.sha256(v.encode()).hexdigest() if k=='code' else v for k,v in params.items()},'status':result['status']})
 dump(run/'logs'/f'{job["id"]}_commands.json',records)
 if result['status']!='ok':raise RuntimeError(str(result))
 if name=='execute_code' and result.get('result',{}).get('success') is False:raise RuntimeError(str(result))
 return result['result']
def objects():return list(bpy.data.collections['ASSET'].all_objects)
def bounds():
 verts=[];tris=0;deps=bpy.context.evaluated_depsgraph_get()
 for ob in objects():
  if ob.type not in ['MESH','CURVE']:continue
  ev=ob.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();tris+=len(me.loop_triangles)
  for v in me.vertices:
   p=ob.matrix_world@v.co
   if not all(math.isfinite(x) for x in p):raise ValueError('Non-finite geometry: '+ob.name)
   verts.append(p)
  ev.to_mesh_clear()
 if not verts:raise ValueError('No asset geometry')
 lo=Vector(tuple(min(v[i] for v in verts) for i in range(3)));hi=Vector(tuple(max(v[i] for v in verts) for i in range(3)))
 return lo,hi,tris
def fingerprint(ob):
 data={'matrix':[list(r) for r in ob.matrix_world],'type':ob.type,'hide':ob.hide_render}
 if ob.type=='MESH':
  data['verts']=[list(v.co) for v in ob.data.vertices];data['faces']=[list(p.vertices) for p in ob.data.polygons]
  data['face_settings']=[(p.material_index,p.use_smooth) for p in ob.data.polygons]
  data['edges']=[list(e.vertices) for e in ob.data.edges]
  data['uv']={layer.name:[list(v.uv) for v in layer.data] for layer in ob.data.uv_layers}
 if ob.type=='CAMERA':data['camera']=[ob.data.type,ob.data.lens,ob.data.ortho_scale,ob.data.clip_start,ob.data.clip_end]
 if ob.type=='LIGHT':data['light']=[ob.data.type,ob.data.energy,list(ob.data.color),getattr(ob.data,'size',None)]
 data['materials']=[]
 for slot in ob.material_slots:
  m=slot.material
  if not m:continue
  values={'name':m.name,'diffuse':list(m.diffuse_color),'nodes':[]}
  if m.use_nodes:
   for node in m.node_tree.nodes:
    inputs=[]
    for socket in node.inputs:
     if not hasattr(socket,'default_value'):continue
     v=socket.default_value
     if isinstance(v,(str,float,int,bool)):inputs.append((socket.name,v))
     else:
      try:inputs.append((socket.name,list(v)))
      except TypeError:pass
    values['nodes'].append((node.name,node.bl_idname,inputs))
   values['links']=[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links]
  data['materials'].append(values)
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
 if ob.type in ['MESH','CURVE']:
  me=ev.to_mesh();data['evaluated_verts']=[list(v.co) for v in me.vertices];data['evaluated_faces']=[list(p.vertices) for p in me.polygons];ev.to_mesh_clear()
 return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
def studio():
 lo,hi,_=bounds();center=(lo+hi)/2;size=max(hi-lo);radius=max(size,.01)
 col=bpy.data.collections.new('STUDIO');bpy.context.scene.collection.children.link(col)
 def move(ob):
  for c in list(ob.users_collection):c.objects.unlink(ob)
  col.objects.link(ob)
 def aim(ob):ob.rotation_euler=(center-ob.location).to_track_quat('-Z','Y').to_euler()
 for name,direction in {'hero':(1.5,-3.4,1.2),'front':(0,-4,.30),'side':(4,0,.30),'back':(.2,4,.45)}.items():
  d=bpy.data.cameras.new('H_'+name);ob=bpy.data.objects.new(d.name,d);col.objects.link(ob);ob.location=center+Vector(direction)*radius;aim(ob);d.type='ORTHO';d.ortho_scale=radius*1.40;d.clip_start=max(radius/1000,.0001)
 for name,direction,power,color in [('key',(-2,-3,3),350,(1,.87,.8)),('fill',(2,-2,1),175,(.79,.88,1)),('rim',(1,2,3),450,(1,.9,.77))]:
  d=bpy.data.lights.new('H_'+name,'AREA');ob=bpy.data.objects.new(d.name,d);col.objects.link(ob);ob.location=center+Vector(direction)*radius;aim(ob);d.energy=power*radius*radius;d.shape='DISK';d.size=radius*1.5;d.color=color
 bpy.ops.mesh.primitive_plane_add(size=radius*200,location=(center.x,center.y,lo.z-.00001));floor=bpy.context.object;floor.name='H_ground';move(floor)
 mat=bpy.data.materials.new('H_graphite');mat.diffuse_color=(.105,.12,.135,1);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=mat.diffuse_color;bs.inputs['Roughness'].default_value=.8;floor.data.materials.append(mat)
 scene=bpy.context.scene;scene.camera=bpy.data.objects['H_hero'];scene.world.use_nodes=True;bg=scene.world.node_tree.nodes.get('Background');bg.inputs[0].default_value=(.24,.27,.32,1);bg.inputs[1].default_value=.3;scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-.45;scene.unit_settings.system='METRIC'
def main():
 if job.get('base'):
  source=run/job['base']
  if job['phase']!='verify' and sha(source)!=job['base_hash']:raise ValueError('Base checkpoint changed')
  bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
 if job['phase']=='verify':
  lo,hi,tris=bounds();refs=[im for im in bpy.data.images if im.name.startswith('H_ref_')]
  result={'status':'succeeded','dirty_after_reopen':bpy.data.is_dirty,'dimensions_m':list(hi-lo),'triangles':tris,'references_packed':len(refs)==len(job['references']) and all(im.packed_file for im in refs),'source_packed':any(t.name.startswith('H_source_') for t in bpy.data.texts),'blender_version':bpy.app.version_string}
  if result['dirty_after_reopen'] or not result['references_packed'] or not result['source_packed']:raise ValueError('Saved content verification failed')
  if job.get('quality_plan'):
   from quality import inspect
   text=bpy.data.texts.get('H_quality_plan')
   if not text or json.loads(text.as_string())!=job['quality_plan']:raise ValueError('Saved quality plan missing or changed')
   result['surface_checks']=inspect(job['quality_plan'])
  dump(run/job['receipt'],result);return
 if job['phase']=='body':
  if job.get('base'):raise ValueError('Fresh body stage must not use a base')
  bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
  for c in list(bpy.data.collections):bpy.data.collections.remove(c)
  asset=bpy.data.collections.new('ASSET');bpy.context.scene.collection.children.link(asset)
 if 'ASSET' not in bpy.data.collections:raise ValueError('Missing ASSET collection')
 before={o.name:fingerprint(o) for o in objects()} if job['phase'] in ['detail','edit'] else {}
 outside={o.name:fingerprint(o) for o in bpy.data.objects if o not in objects()} if before else {}
 if job['phase']=='edit' and any(t not in before for t in job['targets']):raise ValueError('Unknown edit target')
 if job.get('source'):
  function={'body':'build_body','detail':'add_details','edit':'edit'}[job['phase']]
  code=f"import runpy, bpy\nns=runpy.run_path({str(run/job['source'])!r})\nns[{function!r}]({{'asset':bpy.data.collections['ASSET'],'dimensions':{job['dimensions_m']!r}}})\n"
  call('execute_code',{'code':code});bpy.context.view_layer.update()
  bpy.data.texts.new('H_source_'+job['id']).write((run/job['source']).read_text(encoding='utf-8'))
 preservation=None
 if before:
  after={o.name:fingerprint(o) for o in objects()};changed=[n for n in set(before)|set(after) if before.get(n)!=after.get(n)]
  unexpected=[n for n in changed if (n in before if job['phase']=='detail' else n not in job['targets'])]
  outside_after={o.name:fingerprint(o) for o in bpy.data.objects if o not in objects()}
  unexpected+=['outside ASSET: '+n for n in set(outside)|set(outside_after) if outside.get(n)!=outside_after.get(n)]
  preservation={'changed':sorted(changed),'unchanged':len(set(before)&set(after))-len([n for n in changed if n in before and n in after]),'unexpected':unexpected}
  if unexpected:raise ValueError('Non-target objects changed: '+str(unexpected))
 if job['phase']=='body':studio()
 if job.get('quality_plan') and 'H_quality_plan' not in bpy.data.texts:bpy.data.texts.new('H_quality_plan').write(json.dumps(job['quality_plan'],ensure_ascii=False))
 for i,ref in enumerate(job['references']):
  name=f'H_ref_{i:02d}'
  if name not in bpy.data.images:
   im=bpy.data.images.load(str(run/ref['path']),check_existing=False);im.name=name;im.pack();im.use_fake_user=True
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.use_denoising=True
 settings=job['defaults']['final' if job['phase']=='final' else 'draft']
 scene.render.resolution_x,scene.render.resolution_y=settings['resolution'];scene.render.resolution_percentage=100;scene.cycles.samples=settings['samples'];scene.render.image_settings.file_format='PNG'
 previews=[];clay=bpy.data.materials.get('H_clay') or bpy.data.materials.new('H_clay');clay.use_nodes=True;clay.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.38,.38,.38,1);clay.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.78
 for view in job['views']:
  scene.camera=bpy.data.objects['H_'+view.replace('_clay','')]
  bpy.context.view_layer.material_override=clay if view.endswith('_clay') or job['phase']=='body' else None
  preview=f'renders/{job["id"]}_{view}.png';call('render_image',{'filepath':str(run/preview)});previews.append(preview)
 surface_quality=None
 if job.get('quality_plan'):
  from quality import evidence
  surface_quality,focused=evidence(job['quality_plan'],run,job,call,clay);previews+=focused
 bpy.context.view_layer.material_override=None;scene.camera=bpy.data.objects['H_hero'];lo,hi,tris=bounds()
 quality={}
 if job['phase']=='final':
  for ob in objects():
   if ob.type=='MESH':quality[ob.name]=call('analyze_mesh_quality',{'object_name':ob.name})
 output=run/job['blend']
 if output.exists():raise FileExistsError(output)
 call('save_file',{'filepath':str(output)})
 result={'status':'succeeded','blend':job['blend'],'blend_sha256':sha(output),'base_hash':job.get('base_hash'),'preview_paths':previews,'dimensions_m':list(hi-lo),'triangles':tris,'preservation':preservation,'mesh_diagnostics':quality,'blender_version':bpy.app.version_string,'transport':'official blenderwright handlers via isolated CLI','automatic_repairs':0}
 result['surface_reference_quality']=surface_quality
 dump(run/job['receipt'],result)
try:main()
except Exception as e:
 dump(run/job['receipt'],{'status':'failed','error':str(e)});raise

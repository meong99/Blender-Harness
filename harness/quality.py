"""Blender evaluated-topology checks and fixed-camera evidence; no automatic visual judge."""
import bpy,bmesh,math,json
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

def mesh_info(ob):
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 try:
  parents=list(range(len(me.vertices)))
  def root(i):
   while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
   return i
  for edge in me.edges:
   a,b=edge.vertices;parents[root(a)]=root(b)
  bm=bmesh.new();bm.from_mesh(me)
  stats={'components':len({root(i) for i in range(len(parents))}),'vertices':len(me.vertices),'boundary_edges':sum(e.is_boundary for e in bm.edges),'non_manifold_edges':sum(not e.is_manifold for e in bm.edges)};bm.free()
  verts=[ob.matrix_world@v.co for v in me.vertices]
  if not verts:raise ValueError('Empty mesh '+ob.name)
  stats['min']=[min(v[i] for v in verts) for i in range(3)];stats['max']=[max(v[i] for v in verts) for i in range(3)]
  return stats
 finally:ev.to_mesh_clear()

def inspect(plan):
 asset={o.name:o for o in bpy.data.collections['ASSET'].all_objects}
 groups=[]
 for group in plan['continuous']:
  missing=[n for n in group['objects'] if n not in asset or asset[n].type!='MESH']
  stats={n:mesh_info(asset[n]) for n in group['objects'] if n not in missing}
  components=sum(s['components'] for s in stats.values());non_manifold=sum(s['non_manifold_edges'] for s in stats.values())
  passed=not missing and components==1 and (not group['closed'] or non_manifold==0)
  groups.append({'name':group['name'],'passed':passed,'missing':missing,'components':components,'non_manifold_edges':non_manifold,'objects':stats})
 separate=[{'name':g['name'],'passed':all(n in asset for n in g['objects']),'objects':g['objects']} for g in plan['separate']]
 return {'continuous':groups,'separate':separate,'passed':all(g['passed'] for g in groups+separate),'limits':'Connectivity is evaluated index topology, not proof of tangent continuity, no self-intersection, or reference fidelity. Intentional UV splits may need a different declared contract.'}

def evidence(plan,run,job,render,clay):
 scene=bpy.context.scene;result=inspect(plan);result['views']=[];previews=[]
 old=(scene.camera,scene.render.resolution_x,scene.render.resolution_y,scene.cycles.samples,bpy.context.view_layer.material_override)
 resolution=job['defaults'].get('quality',{}).get('resolution',[640,640]);scene.render.resolution_x,scene.render.resolution_y=resolution
 scene.cycles.samples=job['defaults'].get('quality',{}).get('samples',16)
 try:
  for view in plan['views']:
   name='H_quality_'+view['name'];ob=bpy.data.objects.get(name)
   if ob is None:
    data=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,data);bpy.data.collections['STUDIO'].objects.link(ob)
   ob.location=view['location'];ob.rotation_euler=(Vector(view['target'])-ob.location).to_track_quat('-Z','Y').to_euler();ob.data.type=view['type']
   if ob.data.type=='ORTHO':ob.data.ortho_scale=view['ortho_scale']
   else:ob.data.lens=view['lens']
   ob.data.clip_start=.0001;scene.camera=ob;bpy.context.view_layer.update();bpy.context.view_layer.material_override=clay
   cached=job.get('base_quality_evidence') if job['phase']=='final' else None
   if cached:
    prior=next(row for row in cached['views'] if row['name']==view['name'])
    if prior['camera']!=view or not (run/prior['preview']).is_file():raise ValueError('Cached quality evidence mismatch')
    path=prior['preview']
   else:
    path=f'renders/{job["id"]}_quality_{view["name"]}.png';render('render_image',{'filepath':str(run/path)})
   previews.append(path)
   landmarks=[]
   for mark in view.get('landmarks',[]):
    target=bpy.data.objects.get(mark['object'])
    if not target or target.name not in bpy.data.collections['ASSET'].all_objects or target.type!='MESH':
     landmarks.append({'name':mark['name'],'passed':False,'error':'Missing mesh'});continue
    stats=mesh_info(target);point=Vector([a+(b-a)*t for a,b,t in zip(stats['min'],stats['max'],mark['anchor'])]);uv=world_to_camera_view(scene,ob,point);actual=[uv.x,1-uv.y]
    error=math.hypot((actual[0]-mark['uv'][0])*resolution[0],(actual[1]-mark['uv'][1])*resolution[1])
    landmarks.append({'name':mark['name'],'actual_uv':actual,'target_uv':mark['uv'],'error_px':error,'tolerance_px':mark['tolerance_px'],'passed':uv.z>0 and error<=mark['tolerance_px']})
   row={'name':view['name'],'role':view['role'],'preview':path,'landmarks':landmarks,'passed':all(m['passed'] for m in landmarks),'camera':view}
   if cached:row['reused_reviewed_base']=job['base_hash']
   result['views'].append(row);result['passed']=result['passed'] and row['passed']
 finally:
  scene.camera,scene.render.resolution_x,scene.render.resolution_y,scene.cycles.samples,bpy.context.view_layer.material_override=old
 result['visual_review_required']=True
 out=run/'logs'/f'{job["id"]}_quality.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 result['evidence_json']=str(out.relative_to(run));return result,previews

"""Portable, stdlib-only validation of agent-authored surface/reference intent."""
import math,re

def validate(plan,reference_count):
 if plan.get('schema_version')!=1:raise ValueError('quality plan schema_version must be 1')
 if not isinstance(plan.get('intent'),str) or not plan['intent'].strip():raise ValueError('Explain continuous and intentionally separate surfaces in intent')
 for field in ['continuous','separate','views']:
  if not isinstance(plan.get(field),list):raise ValueError('quality plan needs '+field+' list')
 names=[]
 def vec(v,size):
  if not isinstance(v,list) or len(v)!=size or not all(isinstance(x,(int,float)) and math.isfinite(x) for x in v):raise ValueError('Invalid finite vector')
 for group in plan['continuous']+plan['separate']:
  obs=group.get('objects')
  if not isinstance(obs,list) or not obs or not all(isinstance(n,str) and n for n in obs) or len(set(obs))!=len(obs):raise ValueError('Group requires unique object names')
  if not group.get('name'):raise ValueError('Group needs name')
 for group in plan['continuous']:
  if not isinstance(group.get('closed'),bool):raise ValueError('Specify closed explicitly for continuous group')
 if len(plan['views'])>3:raise ValueError('At most three focused quality views')
 if plan['continuous'] and not any(v.get('role')=='joint' for v in plan['views']):raise ValueError('Continuous surfaces need a joint close-up')
 for view in plan['views']:
  n=view.get('name','')
  if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,35}',n) or n in names:raise ValueError('Unique safe view name required')
  names.append(n)
  if view.get('role') not in ['reference','joint']:raise ValueError('View role must be reference or joint')
  vec(view.get('location'),3);vec(view.get('target'),3)
  if view['location']==view['target']:raise ValueError('Camera must be away from target')
  if view.get('type') not in ['ORTHO','PERSP']:raise ValueError('Explicit camera type required')
  key='ortho_scale' if view['type']=='ORTHO' else 'lens'
  if not isinstance(view.get(key),(int,float)) or not math.isfinite(view[key]) or view[key]<=0:raise ValueError('Positive camera scale/lens required')
  if view.get('role')=='reference':
   idx=view.get('reference_index')
   if not isinstance(idx,int) or not 0<=idx<reference_count:raise ValueError('Reference view needs a copied reference image index')
   if not view.get('provenance'):raise ValueError('Explain reference camera/landmark provenance')
   if not view.get('landmarks'):raise ValueError('Reference view needs measurable landmarks')
  for mark in view.get('landmarks',[]):
   if not mark.get('name') or not mark.get('object'):raise ValueError('Landmark needs name and object')
   vec(mark.get('anchor'),3);vec(mark.get('uv'),2)
   if not all(0<=x<=1 for x in mark['anchor']+mark['uv']):raise ValueError('anchor/uv must be normalized 0..1')
   if not isinstance(mark.get('tolerance_px'),(int,float)) or not math.isfinite(mark['tolerance_px']) or mark['tolerance_px']<=0:raise ValueError('Positive pixel tolerance required')
 if reference_count and not any(v.get('role')=='reference' for v in plan['views']):raise ValueError('Supplied references need at least one calibrated comparison view')
 return plan

def require_pass(rev,decision):
 if decision=='pass' and (rev.get('surface_reference_quality') or {}).get('passed') is False:
  raise ValueError('Measured quality checks failed; repair or explicitly review partial/revise')

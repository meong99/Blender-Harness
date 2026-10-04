"""Portable, agent-guided Blender workflow. Standard library only; no model API call."""
import argparse, datetime as dt, hashlib, json, os, re, shutil, subprocess, sys, time, uuid, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'harness'))
from quality_plan import validate as validate_quality_plan, require_pass
def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,value):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(p)
def runtime():
 override=os.environ.get('BLENDER_BIN')
 if override:
  if not Path(override).is_file():raise ValueError('BLENDER_BIN does not point to a file')
  return str(Path(override).resolve())
 found=shutil.which('blender')
 if found:return found
 paths=list(Path('C:/Program Files/Blender Foundation').glob('Blender */blender.exe'))
 paths+=list(Path('/Applications').glob('Blender*.app/Contents/MacOS/Blender'))
 if paths:return str(sorted(paths,key=lambda p:tuple(map(int,re.findall(r'\d+',str(p)))))[-1])
 raise RuntimeError('Install Blender or set BLENDER_BIN; no global installation is performed.')
def snapshot(session):
 if not session:return {'status':'unavailable','tokens':None}
 result={'status':'unavailable','tokens':None,'source':str(Path(session).resolve())}
 try:
  for line in Path(session).open(encoding='utf-8'):
   try:e=json.loads(line)
   except json.JSONDecodeError:continue
   p=e.get('payload',{})
   if e.get('type')=='turn_context':result['model']=p.get('model')
   if p.get('type')=='token_count' and p.get('info',{}):
    tokens=p['info'].get('total_token_usage')
    if tokens:result.update(status='observed',tokens=tokens,through=e.get('timestamp'))
 except OSError as e:result['reason']=str(e)
 return result
def run_path(name):
 p=(ROOT/'runs'/name).resolve()
 if p.parent!=(ROOT/'runs').resolve():raise ValueError('Run must be a direct child of runs/')
 return p
def report(run,m):
 m['updated']=now()
 stop=dt.datetime.fromisoformat(m['completed']) if m.get('completed') else dt.datetime.now(dt.timezone.utc)
 m['wall_seconds']=(stop-dt.datetime.fromisoformat(m['created'])).total_seconds()
 end=m.get('usage_end',{}) if m.get('usage_frozen') else snapshot(m.get('session_log'));start=m['usage_start'];m['usage_end']=end
 if m.get('completed'):m['usage_frozen']=True
 if start.get('tokens') and end.get('tokens'):
  delta={k:v-start['tokens'].get(k,0) for k,v in end['tokens'].items()}
  m['token_usage']=delta if all(v>=0 for v in delta.values()) else None
 else:m['token_usage']=None
 m['token_scope']='shared session interval from run creation through last flushed event; may include other work; cached/reasoning counts are subsets; not billing'
 m['target_exceeded']=m['wall_seconds']>m['defaults']['target_minutes']*60
 write(run/'manifest.json',m)
 lines=[f'# {m["name"]}',f'\n요청: {m["request"]}',f'\n상태: {m["status"]} / 품질: {m.get("quality","not_reviewed")}',f'\n경과 시간: {m["wall_seconds"]:.1f}초. 기본 목표 {m["defaults"]["target_minutes"]}분은 소프트 목표.',f'\n토큰: {json.dumps(m["token_usage"],ensure_ascii=False) if m["token_usage"] is not None else "미계측"}. 공유 세션 구간값이며 캐시 입력을 중복 합산하지 않는다.', '\n| 단계 | 명령 경과 시간 | 상태 |','| --- | ---: | --- |']
 for rev in m['revisions']:
  lines.append(f'| {rev["id"]} | {rev.get("seconds",0):.2f}초 | {rev["status"]} |')
  if 'verification_seconds' in rev:lines.append(f'| {rev["id"]} 재열기 | {rev["verification_seconds"]:.2f}초 | {rev.get("verification",{}).get("status","failed")} |')
 for rev in m['revisions']:
  lines.append('\n## '+rev['id'])
  if rev.get('preview_paths'):
   for image in rev['preview_paths']:lines.append(f'\n![{rev["id"]} {Path(image).stem}]({(run/image).as_posix()})')
  if rev.get('review'):lines.append('\n검수: '+rev['review']['notes'])
  if rev.get('surface_reference_quality'):
   q=rev['surface_reference_quality'];lines.append(f'\n연결·시안 수치 검사: {q["passed"]} · [확대/기준점 비교]({q["report"]})')
 (run/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 (ROOT/'runs'/'CURRENT.md').write_text(f'# 최근 제작\n\n[{m["name"]}]({run.name}/report.md) · {m["status"]}\n\n원본: [{run.name}/manifest.json]({run.name}/manifest.json)\n',encoding='utf-8')
def launch(run,m,job):
 job_path=run/'logs'/f'{job["id"]}_job.json';write(job_path,job)
 log=run/'logs'/f'{job["id"]}.log';started=time.perf_counter()
 command=[runtime(),'--background','--factory-startup','--python-exit-code','1','--python',str(ROOT/'harness/worker.py'),'--',str(job_path)]
 entry={'id':job['id'],'phase':job['phase'],'status':'running','started':now(),'source_sha256':sha(run/job['source']) if job.get('source') else None}
 entry['implementation_sha256']={p.name:sha(p) for p in (ROOT/'harness').glob('*.py')}
 entry['content_stage']=job.get('content_stage',job['phase'])
 m['revisions'].append(entry);m['status']='running';report(run,m)
 try:
  with log.open('w',encoding='utf-8') as f:
   result=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,timeout=m['defaults']['process_timeout_seconds'],env=dict(os.environ,PYTHONIOENCODING='utf-8'))
  if result.returncode:raise RuntimeError(f'Blender exit {result.returncode}; see {log}')
  receipt=read(run/job['receipt'])
  if receipt.get('status')!='succeeded':raise RuntimeError('Worker did not report success')
  entry.update(receipt);entry['status']='awaiting_review'
 except Exception as e:
  entry.update(status='failed',error=str(e));m['status']='failed';raise
 finally:
  entry['seconds']=time.perf_counter()-started;entry['ended']=now();report(run,m)
 return entry
def selected(m,rid):
 return next(r for r in m['revisions'] if r['id']==rid)
def content_stage(run,m,rev):
 if rev.get('content_stage'):return rev['content_stage']
 if rev['phase'] not in ['edit','final']:return rev['phase']
 job=read(run/'logs'/f'{rev["id"]}_job.json')
 parent=next(r for r in m['revisions'] if r.get('blend')==job['base'])
 return content_stage(run,m,parent)
def require_review(run,rev):
 if rev.get('review',{}).get('decision') not in ['pass','partial']:raise ValueError('Agent must view previews and record review before continuing')
 if sha(run/rev['blend'])!=rev['review']['blend_sha256']:raise ValueError('Reviewed checkpoint changed; review again')
 for p,h in rev['review']['preview_hashes'].items():
  if sha(run/p)!=h:raise ValueError('Reviewed preview changed; review again')
 for p,h in rev['review'].get('evidence_hashes',{}).items():
  if sha(run/p)!=h:raise ValueError('Reviewed quality evidence changed; review again')
def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='cmd',required=True)
 sub.add_parser('doctor')
 new=sub.add_parser('new');new.add_argument('--name',required=True);new.add_argument('--request',required=True);new.add_argument('--reference',action='append',default=[]);new.add_argument('--session-log');new.add_argument('--dimensions',nargs=3,type=float);new.add_argument('--target-minutes',type=float)
 new.add_argument('--quality-plan')
 stage=sub.add_parser('stage');stage.add_argument('--run',required=True);stage.add_argument('--phase',choices=['body','detail','edit'],required=True);stage.add_argument('--source',required=True);stage.add_argument('--base');stage.add_argument('--targets',nargs='+');stage.add_argument('--views',nargs='+',choices=['hero','front','side','back'])
 review=sub.add_parser('review');review.add_argument('--run',required=True);review.add_argument('--revision',required=True);review.add_argument('--decision',choices=['pass','partial','revise'],required=True);review.add_argument('--notes',required=True);review.add_argument('--reviewer',default='agent')
 review.add_argument('--surface-notes');review.add_argument('--reference-notes')
 final=sub.add_parser('finalize');final.add_argument('--run',required=True);final.add_argument('--base',required=True)
 status=sub.add_parser('status');status.add_argument('--run',required=True)
 pack=sub.add_parser('bundle');pack.add_argument('--out',required=True)
 for command in ['install','update','check-update']:
  installer=sub.add_parser(command);installer.add_argument('--project');installer.add_argument('--package');installer.add_argument('--repo');installer.add_argument('--dry-run',action='store_true')
 a=p.parse_args()
 if a.cmd in ['install','update','check-update']:
  from distribution import source_payload, read_package, install
  from github_updates import repository_name, latest, download, version_key
  project=a.project or (str(ROOT.parent) if (ROOT/'.install.json').is_file() else None)
  if not project:raise ValueError('--project must name an existing destination project')
  state_path=Path(project)/'.blender-harness/.install.json';state=read(state_path) if state_path.is_file() else {}
  repo=a.repo or state.get('repository')
  if repo:repository_name(repo)
  if a.package and a.repo:raise ValueError('Use either a local --package or a remote --repo')
  if a.cmd=='check-update':
   if not repo:raise ValueError('No update repository configured; provide --repo owner/repo')
   release=latest(repo);release['installed_version']=state.get('version');release['update_available']=not state or version_key(release['version'])>version_key(state['version'])
   print(json.dumps(release,ensure_ascii=False,indent=2));return
  if a.package:files=read_package(a.package)
  elif repo:files=download(latest(repo))
  elif a.cmd=='install':files=source_payload(ROOT)
  else:raise ValueError('No update repository configured; provide --repo owner/repo or --package NEW.zip')
  print(json.dumps(install(project,files,update=a.cmd=='update',dry_run=a.dry_run,repository=repo),ensure_ascii=False,indent=2));return
 if a.cmd=='doctor':
  print(json.dumps({'blender':runtime(),'addon_present':(ROOT/'vendor/blenderwright/addon/dispatcher.py').is_file(),'defaults':read(ROOT/'harness/defaults.json'),'mode':'agent-guided official handlers via isolated CLI; not autonomous NLP or MCP transport'},ensure_ascii=False));return
 if a.cmd=='bundle':
  from distribution import bundle
  print(bundle(ROOT,a.out));return
 if a.cmd=='new':
  settings=read(ROOT/'harness/defaults.json')
  if settings.get('quality_plan_required') and not a.quality_plan:raise ValueError('Agent must prepare --quality-plan; user does not need to write it')
  plan=validate_quality_plan(read(a.quality_plan),len(a.reference)) if a.quality_plan else None
  for path in a.reference:
   if not Path(path).is_file():raise FileNotFoundError(path)
  if a.target_minutes is not None:
   if a.target_minutes<=0:raise ValueError('Target must be positive')
   settings['target_minutes']=a.target_minutes
  if a.dimensions and any(x<=0 for x in a.dimensions):raise ValueError('Dimensions must be positive metres')
  rid=dt.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+re.sub(r'[^a-zA-Z0-9_-]','-',a.name)[:35]+'-'+uuid.uuid4().hex[:6]
  run=run_path(rid);run.mkdir(parents=True)
  for folder in ['input','sources','native','renders','logs']: (run/folder).mkdir()
  refs=[]
  for i,path in enumerate(a.reference):
   src=Path(path).resolve()
   if not src.is_file():raise FileNotFoundError(src)
   dest=run/'input'/f'ref_{i:02d}{src.suffix.lower()}';shutil.copy2(src,dest);refs.append({'path':str(dest.relative_to(run)),'sha256':sha(dest)})
  session=a.session_log or os.environ.get('HARNESS_SESSION_LOG')
  m={'schema_version':1,'name':a.name,'request':a.request,'created':now(),'status':'initialized','quality':'not_reviewed','defaults':settings,'dimensions_m':a.dimensions,'references':refs,'revisions':[],'session_log':str(Path(session).resolve()) if session else None,'usage_start':snapshot(session)}
  if plan is not None:
   write(run/'input/quality-plan.json',plan);m['quality_plan']={'path':'input/quality-plan.json','sha256':sha(run/'input/quality-plan.json')}
  report(run,m);print(rid);return
 run=run_path(a.run);m=read(run/'manifest.json')
 plan=None
 if m.get('quality_plan'):
  qp=m['quality_plan']
  if sha(run/qp['path'])!=qp['sha256']:raise ValueError('Quality plan changed; start a new run instead of moving the acceptance criteria')
  plan=validate_quality_plan(read(run/qp['path']),len(m['references']))
 if a.cmd=='status':report(run,m);print(json.dumps({'run':a.run,'status':m['status'],'revisions':[{k:r.get(k) for k in ['id','phase','status','seconds']} for r in m['revisions']],'tokens':m['token_usage']},ensure_ascii=False));return
 if m['status']=='completed' and a.cmd in ['stage','review']:raise ValueError('Completed run is immutable; start a new run for further work')
 if a.cmd=='review':
  rev=selected(m,a.revision)
  if rev['status']=='failed':raise ValueError('Cannot accept a failed execution')
  if not rev.get('preview_paths'):raise ValueError('No rendered evidence')
  require_pass(rev,a.decision)
  if plan is not None and (not a.surface_notes or not a.reference_notes):raise ValueError('Record --surface-notes and --reference-notes after inspecting evidence; explain N/A when appropriate')
  rev['review']={'decision':a.decision,'notes':a.notes,'reviewer':a.reviewer,'timestamp':now(),'blend_sha256':sha(run/rev['blend']),'preview_hashes':{im:sha(run/im) for im in rev['preview_paths']}}
  if plan is not None:
   q=rev['surface_reference_quality'];rev['review'].update(surface_notes=a.surface_notes,reference_notes=a.reference_notes,evidence_hashes={p:sha(run/p) for p in [q['report'],q['evidence_json']]})
  rev['status']='reviewed' if a.decision!='revise' else 'needs_revision'
  m['status']='completed' if rev['phase']=='final' and a.decision!='revise' else 'needs_revision' if a.decision=='revise' else 'ready'
  if m['status']=='completed':m['quality']='passed' if a.decision=='pass' else 'partial';m['delivered_blend']=rev['blend'];m['completed']=now()
  report(run,m);print(m['status']);return
 base=None
 if getattr(a,'base',None):
  base=selected(m,a.base);require_review(run,base)
 if a.cmd=='finalize':
  if base['phase'] not in ['detail','edit']:raise ValueError('Finalize a reviewed detail/edit checkpoint')
  existing=next((r for r in m['revisions'] if r['phase']=='final' and r.get('base_hash')==sha(run/base['blend']) and r['status']!='failed'),None)
  if existing:
   if sha(run/existing['blend'])!=existing.get('blend_sha256'):raise ValueError('Final artifact changed; recover or make a new revision')
   print(json.dumps({'reused':existing['id'],'reason':'same reviewed checkpoint; no repeated final render/reopen'}));return
  phase='final';source=None;views=m['defaults']['final_views']
 else:
  phase=a.phase
  if phase in ['detail','edit'] and base is None:raise ValueError('detail/edit requires --base with recorded visual review')
  if phase=='detail' and content_stage(run,m,base)!='body':raise ValueError('detail must start from a reviewed body or its local repair')
  if phase=='edit' and not a.targets:raise ValueError('edit needs exact --targets to enforce non-target preservation')
  source=Path(a.source).resolve();views=a.views or m['defaults']['body_views' if phase=='body' else 'detail_views']
  if len(views)>3:raise ValueError('At most 3 draft views; final renders are separate')
 revision=f'{len(m["revisions"])+1:03d}_{phase}'
 source_rel=None
 if source:
  dest=run/'sources'/f'{revision}.py';shutil.copy2(source,dest);source_rel=str(dest.relative_to(run))
 job={'id':revision,'phase':phase,'run':str(run),'source':source_rel,'base':base['blend'] if base else None,'base_hash':sha(run/base['blend']) if base else None,'targets':getattr(a,'targets',None),'views':views,'defaults':m['defaults'],'dimensions_m':m['dimensions_m'],'references':m['references'],'blend':f'native/{revision}.blend','receipt':f'logs/{revision}_receipt.json'}
 job['quality_plan']=plan
 job['content_stage']=content_stage(run,m,base) if phase in ['edit','final'] else phase
 if phase=='final':job['base_quality_evidence']=base.get('surface_reference_quality')
 rev=launch(run,m,job)
 if phase=='final':
  check=dict(job,id=revision+'_verify',phase='verify',base=rev['blend'],receipt=f'logs/{revision}_verify.json')
  path=run/'logs'/f'{check["id"]}_job.json';write(path,check);started=time.perf_counter()
  try:
   with (run/'logs'/f'{check["id"]}.log').open('w',encoding='utf-8') as log:
    result=subprocess.run([runtime(),'--background','--factory-startup','--python-exit-code','1','--python',str(ROOT/'harness/worker.py'),'--',str(path)],stdout=log,stderr=subprocess.STDOUT,timeout=60)
   verification=read(run/check['receipt']) if (run/check['receipt']).exists() else {}
   if result.returncode or verification.get('status')!='succeeded':raise RuntimeError('Saved-file verification failed; see logs')
   rev['verification']=verification
  except Exception as e:rev['status']='failed';m['status']='failed';rev['error']=str(e);raise
  finally:rev['verification_seconds']=time.perf_counter()-started;report(run,m)
 m['status']='awaiting_review';report(run,m);print(json.dumps({'revision':rev['id'],'blend':rev.get('blend'),'previews':rev.get('preview_paths'),'status':m['status']},ensure_ascii=False))
if __name__=='__main__':
 try:main()
 except Exception as e:print(f'{type(e).__name__}: {e}',file=sys.stderr);sys.exit(1)

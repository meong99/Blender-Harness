"""Run with background Blender to verify JSON-only quality evidence and review."""
from pathlib import Path
import sys
import json
import uuid
from unittest.mock import patch
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'harness'))
import quality
import cli

root = ROOT / 'work' / ('json-review-check-' + uuid.uuid4().hex[:8])
run = root / 'runs' / 'test'
(run / 'logs').mkdir(parents=True)
(run / 'renders').mkdir()
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
asset = bpy.data.collections.new('ASSET')
bpy.context.scene.collection.children.link(asset)
studio = bpy.data.collections.new('STUDIO')
bpy.context.scene.collection.children.link(studio)
bpy.ops.mesh.primitive_cube_add()
cube = bpy.context.object
cube.name = 'Cube'
for collection in list(cube.users_collection):
    collection.objects.unlink(cube)
asset.objects.link(cube)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_percentage = 100
view = dict(name='front', role='joint', location=[0,-5,0], target=[0,0,0], type='ORTHO', ortho_scale=3)
plan = dict(continuous=[dict(name='body',objects=['Cube'],closed=True)], separate=[], views=[view])
job = dict(id='001_body', phase='body', defaults={'quality':{'resolution':[32,32],'samples':1}})
def render(command, arguments):
    scene.render.filepath = arguments['filepath']
    bpy.ops.render.render(write_still=True)
result, previews = quality.evidence(plan,run,job,render,None)
assert result['passed'] and previews and (run/previews[0]).is_file()
assert 'report' not in result and not list(run.rglob('*.html'))
assert json.loads((run/result['evidence_json']).read_text())['passed']
bpy.ops.wm.save_as_mainfile(filepath=str(run/'asset.blend'))
rev = dict(id='001_body',phase='body',status='awaiting_review',blend='asset.blend',preview_paths=previews,surface_reference_quality=result)
m = dict(name='test',request='JSON-only review',status='ready',defaults={},revisions=[rev])
with patch.object(cli,'ROOT',root):
    cli.report(run,m)
    with patch.object(sys,'argv',['cli','review','--run','test','--revision','001_body','--decision','pass','--notes','review fixture']):
        cli.main()
    report = (run/'report.md').read_text(encoding='utf-8')
    assert result['evidence_json'] in report and '.html' not in report
    checked = cli.read(run/'manifest.json')['revisions'][0]
    # Exercise the JSON hash protection used by quality-plan reviews.
    checked['review']['evidence_hashes']={result['evidence_json']:cli.sha(run/result['evidence_json'])}
    cli.require_review(run,checked)
    with (run/result['evidence_json']).open('a') as f:
        f.write(' ')
    try:
        cli.require_review(run,checked)
    except ValueError:
        pass
    else:
        raise AssertionError('Changed JSON evidence was accepted')
print('PASS: real Blender render, JSON output, report and review without HTML, changed JSON rejected.')

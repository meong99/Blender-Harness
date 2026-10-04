import importlib.util,json,unittest,uuid
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('harness_cli',Path(__file__).resolve().parents[1]/'harness/cli.py')
cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)

@contextmanager
def fixture_directory():
 # Keep small test evidence locally; Windows sandbox disallows tempfile's private ACL.
 path=Path(__file__).resolve().parents[1]/'runs'/('_unit-'+uuid.uuid4().hex[:8])
 path.mkdir(parents=True)
 yield path

class HarnessTests(unittest.TestCase):
 def test_run_cannot_escape(self):
  for name in ['../escape','nested/child',str(Path.cwd().parent)]:
   with self.assertRaises(ValueError):cli.run_path(name)

 def test_missing_usage_is_unknown(self):
  self.assertIsNone(cli.snapshot(None)['tokens'])

 def test_repaired_body_can_continue_to_detail(self):
  with fixture_directory() as root:
   (root/'logs').mkdir()
   body={'id':'001_body','phase':'body','blend':'native/001_body.blend'}
   edit={'id':'002_edit','phase':'edit','blend':'native/002_edit.blend'}
   cli.write(root/'logs/002_edit_job.json',{'base':body['blend']})
   self.assertEqual(cli.content_stage(root,{'revisions':[body,edit]},edit),'body')

 def test_usage_and_completed_time_freeze(self):
  with fixture_directory() as tmp:
   root=Path(tmp);run=root/'runs/test';run.mkdir(parents=True)
   m={'name':'test','request':'test','created':'2026-10-03T01:00:00+00:00','completed':'2026-10-03T01:01:00+00:00','status':'completed','defaults':{'target_minutes':15},'usage_start':{'tokens':{'total_tokens':100,'cached_input_tokens':50}},'revisions':[]}
   with patch.object(cli,'ROOT',root),patch.object(cli,'snapshot',return_value={'tokens':{'total_tokens':150,'cached_input_tokens':80}}):cli.report(run,m)
   self.assertEqual(m['wall_seconds'],60)
   self.assertEqual(m['token_usage'],{'total_tokens':50,'cached_input_tokens':30})
   with patch.object(cli,'ROOT',root),patch.object(cli,'snapshot',side_effect=AssertionError('must not read again')):cli.report(run,m)
   self.assertEqual(m['wall_seconds'],60)

 def test_review_rejects_changed_evidence(self):
  with fixture_directory() as tmp:
   run=Path(tmp);(run/'a.blend').write_bytes(b'blend');(run/'a.png').write_bytes(b'preview')
   rev={'blend':'a.blend','review':{'decision':'pass','blend_sha256':cli.sha(run/'a.blend'),'preview_hashes':{'a.png':cli.sha(run/'a.png')}}}
   cli.require_review(run,rev)
   (run/'a.png').write_bytes(b'changed')
   with self.assertRaises(ValueError):cli.require_review(run,rev)
   rev['review']['preview_hashes']['a.png']=cli.sha(run/'a.png');(run/'a.blend').write_bytes(b'changed')
   with self.assertRaises(ValueError):cli.require_review(run,rev)

if __name__=='__main__':unittest.main()

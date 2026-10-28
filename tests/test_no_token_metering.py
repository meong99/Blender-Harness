import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import uuid
import unittest
from unittest.mock import patch

HARNESS = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('harness_cli', HARNESS/'harness/cli.py')
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)

class WorkflowWithoutMetering(unittest.TestCase):
    def test_create_status_and_legacy_report(self):
        work = HARNESS/'work'
        work.mkdir(exist_ok=True)
        folder = work / ('metering-test-' + uuid.uuid4().hex[:8])
        folder.mkdir()
        with contextlib.nullcontext(folder):
            root = Path(folder)
            (root/'harness').mkdir()
            defaults = {'quality_plan_required':False,'visual_gate_required':False}
            (root/'harness/defaults.json').write_text(json.dumps(defaults))
            with patch.object(cli,'ROOT',root), patch.dict(os.environ,{'HARNESS_SESSION_LOG':str(root/'missing-session.jsonl')}):
                output=io.StringIO()
                with contextlib.redirect_stdout(output), patch.object(sys,'argv',['cli','new','--name','test','--request','test']):
                    cli.main()
                rid=output.getvalue().strip()
                run=root/'runs'/rid
                manifest=cli.read(run/'manifest.json')
                for key in ('session_log','usage_start','usage_end','token_usage','token_scope'):
                    self.assertNotIn(key,manifest)
                output=io.StringIO()
                with contextlib.redirect_stdout(output), patch.object(sys,'argv',['cli','status','--run',rid]):
                    cli.main()
                self.assertEqual(json.loads(output.getvalue())['status'],'initialized')
                self.assertNotIn('tokens',json.loads(output.getvalue()))
                self.assertNotIn('토큰',(run/'report.md').read_text(encoding='utf-8'))
                manifest.update(created='2026-10-01T00:00:00+00:00',completed='2026-10-01T00:01:00+00:00',status='completed',session_log=str(root/'missing.jsonl'),usage_start={'tokens':{'total_tokens':100}},token_usage={'total_tokens':50})
                cli.report(run,manifest)
                saved=cli.read(run/'manifest.json')
                self.assertNotIn('wall_seconds',saved)
                self.assertEqual(saved['token_usage'],{'total_tokens':50})  # Historical values remain untouched.
                self.assertNotIn('토큰',(run/'report.md').read_text(encoding='utf-8'))

if __name__=='__main__':
    unittest.main()

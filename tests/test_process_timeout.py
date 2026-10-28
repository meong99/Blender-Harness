import importlib.util
from pathlib import Path
import subprocess
import unittest
import uuid
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('harness_cli', ROOT/'harness/cli.py')
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)

class ProcessTimeout(unittest.TestCase):
    def test_timeout_is_per_process_and_other_run_can_continue(self):
        root = ROOT/'work'/('timeout-test-'+uuid.uuid4().hex[:8])
        (root/'harness').mkdir(parents=True)
        runs=[]
        for name in ['slow','next']:
            run=root/'runs'/name
            (run/'logs').mkdir(parents=True)
            m=dict(name=name,request='test',status='initialized',defaults={'process_timeout_seconds':300},revisions=[])
            job=dict(id='001_body',phase='body',source=None,receipt='logs/receipt.json')
            runs.append((run,m,job))
        def execute(command,**kwargs):
            self.assertEqual(kwargs['timeout'],300)
            job=cli.read(command[-1])
            if 'slow' in str(command[-1]):
                raise subprocess.TimeoutExpired(command,300)
            cli.write(runs[1][0]/job['receipt'],{'status':'succeeded'})
            return subprocess.CompletedProcess(command,0)
        with patch.object(cli,'ROOT',root),patch.object(cli,'runtime',return_value='blender'),patch.object(cli.subprocess,'run',side_effect=execute) as runner:
            with self.assertRaises(subprocess.TimeoutExpired):
                cli.launch(*runs[0])
            self.assertEqual(runs[0][1]['status'],'failed')
            entry=cli.launch(*runs[1])
            self.assertEqual(entry['status'],'awaiting_review')
            self.assertEqual(runner.call_count,2)
            for run,m,job in runs:
                self.assertNotIn('wall_seconds',m)
                self.assertNotIn('seconds',m['revisions'][0])
                self.assertNotIn('경과 시간',(run/'report.md').read_text(encoding='utf-8'))

if __name__=='__main__':unittest.main()

import io
import json
import sys
import unittest
import uuid
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'harness'))
import distribution as d
import github_updates as g


class DistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files=d.source_payload(ROOT)
        cls.version=d.validate_payload(cls.files)
        major,minor,patch_number=d.version_key(cls.version)
        cls.next_version=f'{major}.{minor}.{patch_number+1}'

    def setUp(self):
        self.project=ROOT/'runs'/('_installer-'+uuid.uuid4().hex[:10])
        self.project.mkdir(parents=True)
        self.agents=b'\xef\xbb\xbf# Existing project\r\n\r\nKeep Unity settings and asset paths.\r\n'
        (self.project/'AGENTS.md').write_bytes(self.agents)

    def newer(self):
        files=dict(self.files)
        defaults=json.loads(files['harness/defaults.json'])
        defaults['version']=self.next_version
        files['harness/defaults.json']=d.json_bytes(defaults)
        files['START.md']+=b'\nNew release documentation.\n'
        return files

    def installed(self):
        return d.install(self.project,self.files,repository='meong99/Blender-Harness')

    def test_install_preserves_project_bytes_and_scopes_files(self):
        result=self.installed()
        self.assertTrue((self.project/'AGENTS.md').read_bytes().startswith(self.agents))
        self.assertFalse((self.project/'harness.ps1').exists())
        self.assertTrue((self.project/'.blender-harness/harness.ps1').exists())
        backup=Path(result['backup'])/'files/AGENTS.md'
        self.assertEqual(backup.read_bytes(),self.agents)

    def test_update_preserves_external_rules_runs_and_local_only_edits(self):
        self.installed()
        agents=self.project/'AGENTS.md'
        agents.write_bytes(agents.read_bytes()+b'\r\nMy extra rule.\r\n')
        before=agents.read_bytes()
        local=self.project/'.blender-harness/templates/example_asset.py'
        local.write_bytes(local.read_bytes()+b'\n# Local customization\n')
        result_file=self.project/'.blender-harness/runs/finished/model.blend'
        result_file.parent.mkdir(parents=True)
        result_file.write_bytes(b'keep existing model')
        result=d.install(self.project,self.newer(),update=True)
        self.assertEqual(agents.read_bytes(),before)
        self.assertEqual(result_file.read_bytes(),b'keep existing model')
        self.assertIn('templates/example_asset.py',result['retained_local_files'])
        self.assertIn(b'Local customization',local.read_bytes())
        self.assertEqual(json.loads((self.project/'.blender-harness/.install.json').read_bytes())['repository'],'meong99/Blender-Harness')

    def test_same_file_conflict_has_no_partial_updates(self):
        self.installed()
        changed=self.project/'.blender-harness/START.md'
        changed.write_bytes(b'Local start instructions')
        before=(self.project/'.blender-harness/harness/defaults.json').read_bytes()
        with self.assertRaisesRegex(ValueError,'conflicts'):
            d.install(self.project,self.newer(),update=True)
        self.assertEqual(changed.read_bytes(),b'Local start instructions')
        self.assertEqual((self.project/'.blender-harness/harness/defaults.json').read_bytes(),before)

    def test_managed_block_conflict(self):
        self.installed()
        path=self.project/'AGENTS.md'
        path.write_bytes(path.read_bytes().replace(b'## Blender',b'## Modified Blender'))
        with self.assertRaisesRegex(ValueError,'managed block'):
            d.install(self.project,self.newer(),update=True)

    def test_preview_does_not_write(self):
        d.install(self.project,self.files,dry_run=True)
        self.assertEqual((self.project/'AGENTS.md').read_bytes(),self.agents)
        self.assertFalse((self.project/'.blender-harness').exists())

    def test_repeated_update_is_noop(self):
        self.installed()
        result=d.install(self.project,self.files,update=True)
        self.assertEqual(result['changed'],[])
        self.assertIsNone(result['backup'])
        self.assertEqual((self.project/'AGENTS.md').read_bytes().count(d.BEGIN),1)

    def test_unmanaged_folder_and_malformed_markers(self):
        target=self.project/'.blender-harness'
        target.mkdir();(target/'mine.txt').write_text('mine')
        with self.assertRaisesRegex(ValueError,'not managed'):
            self.installed()
        for content in [d.BEGIN,d.END,d.BEGIN+d.END+d.BEGIN+d.END,d.END+d.BEGIN]:
            with self.assertRaises(ValueError):d.merge_agents(content,None)

    def test_active_run_blocks_update(self):
        self.installed()
        manifest=self.project/'.blender-harness/runs/active/manifest.json'
        manifest.parent.mkdir(parents=True);manifest.write_text('{"status":"awaiting_review"}')
        with self.assertRaisesRegex(ValueError,'active run'):
            d.install(self.project,self.newer(),update=True)

    def test_downgrade_and_repository_switch_refused(self):
        self.installed()
        files=dict(self.files);defaults=json.loads(files['harness/defaults.json']);defaults['version']='1.1.0'
        files['harness/defaults.json']=d.json_bytes(defaults)
        with self.assertRaisesRegex(ValueError,'Downgrade'):d.install(self.project,files,update=True)
        with self.assertRaisesRegex(ValueError,'pinned'):d.install(self.project,self.newer(),update=True,repository='other/repo')

    def test_write_failure_restores_previous_bytes(self):
        self.installed()
        original=d.atomic_write
        calls=0
        def fail_once(path,content):
            nonlocal calls
            calls+=1
            if calls==2:raise OSError('simulated disk error')
            return original(path,content)
        with patch.object(d,'atomic_write',side_effect=fail_once):
            with self.assertRaises(OSError):d.install(self.project,self.newer(),update=True)
        for name,data in self.files.items():
            self.assertEqual((self.project/'.blender-harness'/name).read_bytes(),data)
        self.assertFalse((self.project/'.blender-harness/.install.lock').exists())

    def test_bundle_roundtrip_excludes_user_data(self):
        destination=self.project/'release.zip'
        d.bundle(ROOT,destination)
        self.assertEqual(d.read_package(destination),self.files)
        with zipfile.ZipFile(destination) as z:
            self.assertFalse(any(n.startswith(('runs/','dist/','.github/')) for n in z.namelist()))

    def test_malicious_archive_paths_and_tampering(self):
        for name in ['../AGENTS.md','harness/../../AGENTS.md','C:/bad.py','harness\\bad.py']:
            stream=io.BytesIO()
            with zipfile.ZipFile(stream,'w') as z:z.writestr(name,b'bad')
            stream.seek(0)
            with self.assertRaises(ValueError):d.read_package(stream)
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as z:
            for name,data in self.files.items():z.writestr(name,data)
            z.writestr('PACKAGE.json',d.json_bytes({'format':1,'version':'1.2.0','files':{}}))
        stream.seek(0)
        with self.assertRaisesRegex(ValueError,'hash'):d.read_package(stream)

    def test_remote_release_download_verifies_hash_and_version(self):
        destination=self.project/'release.zip';d.bundle(ROOT,destination);binary=destination.read_bytes()
        release={'tag_name':'v'+self.version,'draft':False,'prerelease':False,'assets':[{'name':f'blenderwright-harness-v{self.version}.zip','id':123,'digest':'sha256:'+d.digest(binary)}]}
        with patch.object(g,'fetch',side_effect=[d.json_bytes(release),binary]):
            metadata=g.latest('meong99/Blender-Harness')
            self.assertEqual(g.download(metadata),self.files)
        with patch.object(g,'fetch',return_value=b'corrupt'):
            with self.assertRaisesRegex(ValueError,'SHA256'):g.download(metadata)

    def test_remote_invalid_repository_and_digest(self):
        for repository in ['../secret','https://evil.example/repo','owner/..']:
            with self.assertRaises(ValueError):g.repository_name(repository)
        release={'tag_name':'v1.2.0','assets':[{'name':'blenderwright-harness-v1.2.0.zip','id':123}]}
        with patch.object(g,'fetch',return_value=d.json_bytes(release)):
            with self.assertRaisesRegex(ValueError,'digest'):g.latest('owner/repo')

    def test_auth_not_forwarded_to_asset_cdn(self):
        request=g.urllib.request.Request('https://api.github.com/test',headers={'Authorization':'Bearer test-placeholder'})
        redirected=g.GitHubRedirect().redirect_request(request,None,302,'redirect',{},'https://release-assets.githubusercontent.com/file')
        self.assertIsNone(redirected.get_header('Authorization'))
        with self.assertRaises(ValueError):
            g.GitHubRedirect().redirect_request(request,None,302,'redirect',{},'https://unrelated.example/file')


if __name__=='__main__':unittest.main()

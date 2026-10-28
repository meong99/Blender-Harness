import copy
import json
import sys
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
import cli
from visual_gate import evaluate, require_final, validate_requirements


class VisualGateTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]/'runs'/('_visual-'+uuid.uuid4().hex[:8])
        self.root.mkdir(parents=True)
        self.plan = {'views': [{'name': 'front', 'location': [0,-1,0], 'target': [0,0,0]}, {'name': 'side', 'location': [1,0,0], 'target': [0,0,0]}], 'visual_requirements': [{'id': 'junction', 'expected': 'Filled reference junction, no notch', 'views': ['front','side'], 'reference_indices': []}]}
        self.manifest = {'defaults': {'visual_gate_required': True}, 'references': [], 'revisions': []}
        self.rev, self.payload = self.revision('001_edit')

    def revision(self, name):
        paths = [name+'_front.png', name+'_side.png', name+'_hero.png']
        for path in paths:
            (self.root/path).write_bytes(path.encode())
        (self.root/(name+'.blend')).write_bytes(name.encode())
        rev = {'id': name, 'phase': 'edit', 'blend': name+'.blend', 'preview_paths': paths, 'review': {'decision': 'pass'}, 'surface_reference_quality': {'passed': True, 'views': [{'name': 'front', 'preview': paths[0]}, {'name': 'side', 'preview': paths[1]}]}}
        self.manifest['revisions'].append(rev)
        payload = {'schema_version': 1, 'revision': name, 'inspected_images': paths.copy(), 'requirements': [{'id': 'junction', 'status': 'pass', 'observed': 'Both silhouettes have filled junctions', 'evidence': paths[:2]}], 'defects': []}
        return rev, payload

    def evaluate(self, payload=None, decision='pass', rev=None):
        return evaluate(self.root, self.manifest, rev or self.rev, self.plan, payload or self.payload, decision)

    def record_failure(self):
        self.payload['requirements'][0]['status'] = 'fail'
        self.payload['defects'] = [{'id': 'notch', 'requirement_id': 'junction', 'status': 'open', 'description': 'Visible notch unlike reference', 'evidence': self.rev['preview_paths'][:2]}]
        result = self.evaluate(decision='partial')
        self.manifest.update(visual_requirements=result['requirements'], visual_defects=result['defects'], visual_latest_revision=self.rev['id'])
        return result

    def test_plan_requires_concrete_multiview_requirements(self):
        validate_requirements(self.plan, 0)
        for mutation in ['missing', 'single', 'same_camera', 'no_reference']:
            p = copy.deepcopy(self.plan)
            if mutation == 'missing':p.pop('visual_requirements')
            if mutation == 'single':p['visual_requirements'][0]['views'] = ['front']
            if mutation == 'same_camera':p['views'][1]['location'] = p['views'][0]['location']
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate_requirements(p, 1 if mutation == 'no_reference' else 0)

    def test_rejects_missing_feature_or_view_or_old_evidence(self):
        self.evaluate()
        for mutation in ['missing_feature', 'missing_view', 'old_path', 'not_inspected', 'waived']:
            p = copy.deepcopy(self.payload)
            if mutation == 'missing_feature':p['requirements'] = []
            if mutation == 'missing_view':p['requirements'][0]['evidence'] = p['requirements'][0]['evidence'][:1]
            if mutation == 'old_path':p['requirements'][0]['evidence'][0] = '../old.png'
            if mutation == 'not_inspected':p['inspected_images'].pop()
            if mutation == 'waived':p['requirements'][0]['status'] = 'waived'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):self.evaluate(p)

    def test_numeric_success_does_not_override_visual_failure(self):
        self.payload['requirements'][0]['status'] = 'fail'
        with self.assertRaises(ValueError):self.evaluate()
        self.evaluate(decision='partial')

    def test_partial_cannot_finalize_even_legacy(self):
        self.rev['review']['decision'] = 'partial'
        for defaults in [{}, {'visual_gate_required': True}]:
            with self.assertRaises(ValueError):require_final({'defaults': defaults}, self.rev)

    def test_open_defect_cannot_be_omitted_or_bypassed_with_old_base(self):
        self.record_failure()
        rev, p = self.revision('002_edit')
        p['requirements'][0]['status'] = 'fail'
        with self.assertRaises(ValueError):self.evaluate(p, 'partial', rev)
        with self.assertRaises(ValueError):require_final(self.manifest, self.rev)

    def test_cannot_relabel_same_checkpoint_as_pass(self):
        self.record_failure()
        self.payload['requirements'][0]['status'] = 'pass'
        with self.assertRaises(ValueError):self.evaluate()

    def repaired_payload(self):
        self.record_failure()
        rev, p = self.revision('002_edit')
        repair = {'action': 'Rebuilt missing volume and compared both views', 'before_images': self.rev['preview_paths'][:2]}
        p['requirements'][0]['repair'] = repair
        p['defects'] = [{'id': 'notch', 'requirement_id': 'junction', 'status': 'resolved', 'description': 'Junction now filled', 'evidence': rev['preview_paths'][:2], 'repair': repair}]
        return rev, p

    def test_repair_requires_before_after_and_accepts_new_review(self):
        rev, p = self.repaired_payload()
        bad = copy.deepcopy(p);bad['defects'][0]['repair']['before_images'] = []
        with self.assertRaises(ValueError):self.evaluate(bad, rev=rev)
        result = self.evaluate(p, rev=rev)
        self.manifest.update(visual_requirements=result['requirements'], visual_defects=result['defects'], visual_latest_revision=rev['id'])
        require_final(self.manifest, rev)
        with self.assertRaises(ValueError):require_final(self.manifest, self.rev)
        with self.assertRaises(ValueError):self.evaluate()

    def test_changed_before_evidence_is_rejected(self):
        rev, p = self.repaired_payload()
        (self.root/self.rev['preview_paths'][0]).write_bytes(b'changed')
        with self.assertRaises(ValueError):self.evaluate(p, rev=rev)

    def test_changed_reference_is_rejected(self):
        (self.root/'ref.png').write_bytes(b'changed')
        self.manifest['references'] = [{'path':'ref.png','sha256':'not-current'}]
        self.plan['visual_requirements'][0]['reference_indices'] = [0]
        with self.assertRaises(ValueError):self.evaluate()

    def test_cli_final_partial_never_completes(self):
        # Exercise real CLI persistence, not only the helper decision function.
        self.manifest.update(name='fixture', request='fixture', status='awaiting_review', defaults={})
        self.rev.update(phase='final', status='awaiting_review')
        self.rev['surface_reference_quality']['evidence_json'] = 'fixture-quality.json'
        self.manifest.pop('visual_latest_revision', None)
        cli.write(self.root/'manifest.json', self.manifest)
        with patch.object(cli, 'run_path', return_value=self.root), patch.object(cli, 'ROOT', self.root.parent.parent), patch.object(sys, 'argv', ['cli','review','--run','fixture','--revision',self.rev['id'],'--decision','partial','--notes','Visible flaw remains']):
            cli.main()
        result = cli.read(self.root/'manifest.json')
        self.assertEqual(result['status'], 'needs_revision')
        self.assertNotIn('completed', result)
        self.assertNotIn('delivered_blend', result)

    def test_cli_partial_blocks_before_launch(self):
        self.rev['review']['decision'] = 'partial'
        self.manifest['status'] = 'ready'
        cli.write(self.root/'manifest.json', self.manifest)
        with patch.object(cli, 'run_path', return_value=self.root), patch.object(cli, 'require_review'), patch.object(cli, 'launch') as launch, patch.object(sys, 'argv', ['cli','finalize','--run','fixture','--base',self.rev['id']]):
            with self.assertRaisesRegex(ValueError, 'partial'):cli.main()
            launch.assert_not_called()

    def test_completed_final_is_reused_without_rendering(self):
        final, payload = self.revision('002_final')
        final.update(phase='final', status='reviewed', base_hash=cli.sha(self.root/self.rev['blend']), blend_sha256=cli.sha(self.root/final['blend']))
        self.manifest.update(status='completed', visual_latest_revision=final['id'], visual_requirements={'junction':{'status':'pass'}}, visual_defects={})
        cli.write(self.root/'manifest.json', self.manifest)
        with patch.object(cli, 'run_path', return_value=self.root), patch.object(cli, 'require_review'), patch.object(cli, 'launch') as launch, patch.object(sys, 'argv', ['cli','finalize','--run','fixture','--base',self.rev['id']]):
            cli.main()
            launch.assert_not_called()


if __name__ == '__main__':unittest.main()

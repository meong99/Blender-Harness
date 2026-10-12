"""Evidence-backed visual review bookkeeping, not an image-understanding engine."""
import hashlib
import re


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Visual review needs '+label)


def validate_requirements(plan, reference_count):
    requirements = plan.get('visual_requirements')
    if not isinstance(requirements, list) or not requirements:
        raise ValueError('Prepare visual_requirements before modeling')
    views = {v['name']: v for v in plan['views']}
    ids = set()
    for item in requirements:
        key = item.get('id', '')
        if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}', key) or key in ids:
            raise ValueError('Unique visual requirement id required')
        ids.add(key)
        text(item.get('expected'), 'reference shape/acceptance description')
        names = item.get('views')
        if not isinstance(names, list) or len(names) < 2 or len(set(names)) != len(names) or any(n not in views for n in names):
            raise ValueError('Each required feature needs at least two named quality views')
        cameras = {(tuple(views[n]['location']), tuple(views[n]['target'])) for n in names}
        if len(cameras) < 2:
            raise ValueError('Required views must use distinct camera positions/targets')
        refs = item.get('reference_indices', [])
        if not isinstance(refs, list) or any(type(i) is not int or not 0 <= i < reference_count for i in refs):
            raise ValueError('Invalid visual requirement reference indices')
        if reference_count and not refs:
            raise ValueError('Each feature must identify its source reference images')
    return requirements


def evaluate(run, manifest, revision, plan, payload, decision):
    """Pure validation: no manifest mutation until every check succeeds."""
    requirements = validate_requirements(plan, len(manifest['references']))
    if payload.get('schema_version') != 1 or payload.get('revision') != revision['id']:
        raise ValueError('Visual review must identify the current revision and schema 1')
    previews = revision['preview_paths']
    inspected = payload.get('inspected_images')
    if not isinstance(inspected, list) or len(inspected) != len(previews) or set(inspected) != set(previews):
        raise ValueError('Inspect and list every current preview, including color/clay and focused views')
    latest = manifest.get('visual_latest_revision')
    order = {r['id']: i for i, r in enumerate(manifest['revisions'])}
    if latest and order[revision['id']] < order[latest]:
        raise ValueError('Cannot roll visual review state back to an older revision')
    for ref in manifest['references']:
        if digest(run/ref['path']) != ref['sha256']:
            raise ValueError('Reference image changed after acceptance criteria were fixed')
    hashes = {p: digest(run/p) for p in previews}
    blend_hash = digest(run/revision['blend'])
    quality_views = {v['name']: v['preview'] for v in revision['surface_reference_quality']['views']}

    def evidence(row, required=()):
        paths = row.get('evidence')
        if not isinstance(paths, list) or not paths or len(set(paths)) != len(paths) or any(p not in hashes for p in paths):
            raise ValueError('Evidence must use current rendered preview paths')
        if not set(required).issubset(paths):
            raise ValueError('Feature evidence must cover all its required camera views')
        return {p: hashes[p] for p in paths}

    def repaired(row, previous):
        if blend_hash == previous['blend_sha256'] or order[revision['id']] <= order[previous['revision']]:
            raise ValueError('A failed feature needs a newer changed checkpoint, not a rewritten review')
        repair = row.get('repair', {})
        text(repair.get('action'), 'concrete repair action')
        if set(repair.get('before_images', [])) != set(previous['evidence_hashes']):
            raise ValueError('Resolution must link all before images of the recorded defect')
        for p, h in previous['evidence_hashes'].items():
            if digest(run/p) != h:
                raise ValueError('Before-repair evidence changed')

    rows = payload.get('requirements', [])
    if not isinstance(rows, list) or len(rows) != len(requirements) or {r.get('id') for r in rows} != {r['id'] for r in requirements}:
        raise ValueError('Review every fixed requirement exactly once; none may be omitted or waived')
    states = {}
    for item in requirements:
        row = next(r for r in rows if r['id'] == item['id'])
        if row.get('status') not in ['pass', 'fail', 'uncertain']:
            raise ValueError('Required feature status must be pass/fail/uncertain')
        text(row.get('observed'), 'observed shape compared with the reference')
        ev = evidence(row, [quality_views[n] for n in item['views']])
        previous = manifest.get('visual_requirements', {}).get(item['id'])
        if row['status'] == 'pass' and previous and previous['status'] != 'pass':
            repaired(row, previous)
        states[item['id']] = dict(row, evidence_hashes=ev, revision=revision['id'], blend_sha256=blend_hash)

    defects = dict(manifest.get('visual_defects', {}))
    found = payload.get('defects')
    if not isinstance(found, list):
        raise ValueError('List additional visible defects explicitly, or use [] after inspection')
    seen = set()
    for row in found:
        key = row.get('id', '')
        if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}', key) or key in seen:
            raise ValueError('Unique defect id required')
        seen.add(key)
        if row.get('requirement_id') not in states or row.get('status') not in ['open', 'resolved']:
            raise ValueError('Defect needs a requirement and open/resolved status')
        text(row.get('description'), 'visible defect description')
        ev = evidence(row)
        previous = defects.get(key)
        if row['status'] == 'resolved':
            if not previous:
                raise ValueError('Cannot resolve an unrecorded defect')
            if previous['status'] == 'open':
                repaired(row, previous)
        defects[key] = dict(row, evidence_hashes=ev, revision=revision['id'], blend_sha256=blend_hash)
    if any(v['status'] == 'open' and k not in seen for k, v in defects.items()):
        raise ValueError('An open defect cannot disappear from the next review, even on another base')
    if decision == 'pass' and (any(v['status'] != 'pass' for v in states.values()) or any(v['status'] == 'open' for v in defects.values())):
        raise ValueError('Visible failures/uncertainty/open defects block pass regardless of numeric checks')
    return {'requirements': states, 'defects': defects, 'inspected_hashes': hashes}


def require_final(manifest, base):
    if base.get('review', {}).get('decision') != 'pass':
        raise ValueError('partial is a repair checkpoint, never a finalization approval')
    if manifest['defaults'].get('visual_gate_required'):
        if manifest.get('visual_latest_revision') != base['id']:
            raise ValueError('Finalize the latest visual review; an older pass cannot bypass later findings')
        states = manifest.get('visual_requirements', {})
        if not states or any(v['status'] != 'pass' for v in states.values()) or any(v['status'] == 'open' for v in manifest.get('visual_defects', {}).values()):
            raise ValueError('Resolve all required features and visible defects before finalization')

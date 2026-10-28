"""Local, manifest-checked installation. Never execute code from an incoming ZIP."""
import datetime as dt
import hashlib
import json
import re
import stat
import uuid
import zipfile
from pathlib import Path, PurePosixPath

BEGIN = b'<!-- blender-modeling-harness:begin -->'
END = b'<!-- blender-modeling-harness:end -->'
DIRECTORY = '.blender-harness'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8')


def allowed(name):
    p = PurePosixPath(name)
    if '\\' in name or ':' in name or p.is_absolute() or '..' in p.parts or str(p) != name:
        return False
    if any(part.endswith(('.', ' ')) for part in p.parts):
        return False
    if name in ['AGENTS.md', 'START.md', 'harness.ps1', 'vendor/blenderwright/LICENSE.md']:
        return True
    if len(p.parts) == 2 and p.parts[0] in ['harness', 'templates']:
        return p.suffix in ['.py', '.md', '.json']
    return name.startswith('vendor/blenderwright/addon/') and p.suffix == '.py' and '__pycache__' not in p.parts


def version_key(version):
    if not isinstance(version, str) or not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('Release version must be X.Y.Z')
    return tuple(map(int, version.split('.')))


def validate_payload(files):
    required = ['AGENTS.md', 'START.md', 'harness.ps1', 'harness/cli.py',
                'harness/distribution.py', 'harness/worker.py', 'harness/defaults.json',
                'harness/WORKFLOW.md', 'vendor/blenderwright/LICENSE.md',
                'vendor/blenderwright/addon/dispatcher.py']
    if not all(name in files for name in required):
        raise ValueError('Incomplete release package')
    if not all(allowed(name) for name in files) or len({n.casefold() for n in files}) != len(files):
        raise ValueError('Unsafe or duplicate package paths')
    version = json.loads(files['harness/defaults.json'].decode('utf-8-sig'))['version']
    version_key(version)
    return version


def source_payload(root):
    paths = [root/'AGENTS.md', root/'START.md', root/'harness.ps1', root/'vendor/blenderwright/LICENSE.md']
    for folder in ['harness', 'templates']:
        paths.extend(p for p in (root/folder).iterdir() if p.is_file() and allowed(p.relative_to(root).as_posix()))
    paths.extend((root/'vendor/blenderwright/addon').rglob('*.py'))
    files = {p.relative_to(root).as_posix(): p.read_bytes() for p in paths if '__pycache__' not in p.parts}
    validate_payload(files)
    return files


def bundle(root, destination):
    files = source_payload(root)
    manifest = {'format': 1, 'version': validate_payload(files),
                'files': {name: digest(data) for name, data in sorted(files.items())}}
    destination = Path(destination).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.with_suffix('.manifest.json').exists():
        raise FileExistsError(destination)
    with zipfile.ZipFile(destination, 'x', zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            archive.writestr(name, data)
        archive.writestr('PACKAGE.json', json_bytes(manifest))
    destination.with_suffix('.manifest.json').write_bytes(json_bytes({
        **manifest, 'sha256': digest(destination.read_bytes()),
        'requires': ['Blender installed', 'coding agent'],
        'excludes': ['models', 'references', 'session logs', 'credentials', 'other candidate runtimes']}))
    return str(destination)


def read_package(path):
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        names = [p.filename for p in entries]
        if 'PACKAGE.json' not in names:
            raise ValueError('Missing PACKAGE.json; use a v1.2 or later release ZIP')
        if len(names) != len(set(n.casefold() for n in names)):
            raise ValueError('Duplicate ZIP entries')
        if sum(p.file_size for p in entries) > 64*1024*1024:
            raise ValueError('Package exceeds 64 MiB')
        for entry in entries:
            if (entry.filename != 'PACKAGE.json' and not allowed(entry.filename)) or stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError('Unsafe ZIP entry: '+entry.filename)
        manifest = json.loads(archive.read('PACKAGE.json'))
        files = {n: archive.read(n) for n in names if n != 'PACKAGE.json'}
    if manifest.get('format') != 1 or manifest.get('files') != {n: digest(b) for n, b in files.items()}:
        raise ValueError('Package hash manifest mismatch')
    if manifest.get('version') != validate_payload(files):
        raise ValueError('Package version mismatch')
    return files


def safe_path(project, relative):
    path = project/relative
    if path.resolve() != project and project not in path.resolve().parents:
        raise ValueError('Path escapes project: '+str(path))
    for part in [path, *path.parents]:
        if part == project:
            break
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise ValueError('Linked paths are not managed: '+str(part))
        if part != path and part.exists() and not part.is_dir():
            raise ValueError('Parent is not a directory: '+str(part))
    return path


def agent_block(newline=b'\n'):
    text = '''<!-- blender-modeling-harness:begin -->
## Blender 모델링 하네스 (관리 구역)

- Blender 모델 제작·수정 요청에만 적용한다. 사용자의 명시 지시와 이 프로젝트의 기존 규칙·해당 경로의 규칙을 우선한다. 해소되지 않는 중요 충돌만 질문한다.
- 시작 시 `.blender-harness/harness/WORKFLOW.md`와 `.blender-harness/harness/defaults.json`을 읽는다. 하네스 문서의 상대 경로는 `.blender-harness/` 기준이다.
- 실행: 프로젝트 루트에서 `.\\.blender-harness\\harness.ps1` 또는 `python3 .blender-harness/harness/cli.py`. 결과는 `.blender-harness/runs/`에 기록한다.
- 대상·참고 이미지·달라지는 조건만 받아 제작한다. 모델 오브젝트 수와 실제 메시 연결 여부를 구분하고, 지정된 분리 조건을 지킨다.
- 이 관리 구역은 설치기가 갱신한다. 프로젝트별 추가 규칙은 구역 밖에 쓴다. 기존 문서를 통째로 대체하지 않는다.
- 하네스는 사용자와 함께 수정하며, 보고 없이 임의로 수정하지 않는다.
<!-- blender-modeling-harness:end -->'''
    return text.encode('utf-8').replace(b'\n', newline)


def merge_agents(current, previous_hash):
    # Preserve every byte outside the managed block, including BOM and line endings.
    current.decode('utf-8-sig')  # Refuse UTF-16/unknown encodings before writing.
    newline = b'\r\n' if b'\r\n' in current else b'\n'
    block = agent_block(newline)
    if current.count(BEGIN) != current.count(END) or current.count(BEGIN) > 1:
        raise ValueError('Malformed or duplicate AGENTS.md managed markers')
    if BEGIN in current:
        start, end = current.index(BEGIN), current.index(END)+len(END)
        if end < start or not previous_hash or digest(current[start:end]) != previous_hash:
            raise ValueError('AGENTS.md managed block was modified; preserve it and resolve manually')
        return current[:start]+block+current[end:], digest(block)
    if previous_hash:
        raise ValueError('AGENTS.md managed block was removed; resolve manually')
    separator = newline*2 if current else b''
    return current+separator+block+newline, digest(block)


def install(project, files, *, update=False, dry_run=False, repository=None):
    project = Path(project).resolve(strict=True)
    if not project.is_dir():
        raise ValueError('Project must be an existing directory')
    version = validate_payload(files)
    target = safe_path(project, DIRECTORY)
    state_path = safe_path(project, DIRECTORY+'/.install.json')
    agents_path = safe_path(project, 'AGENTS.md')
    previous = json.loads(state_path.read_bytes()) if state_path.is_file() else None
    if update and not previous:
        raise ValueError('No managed installation; use install for first setup')
    if not update and previous:
        raise ValueError('Already installed; use update --package NEW.zip')
    if previous and repository and previous.get('repository') and repository.casefold() != previous['repository'].casefold():
        raise ValueError('Changing the pinned update repository is refused')
    if not previous and target.exists() and any(target.iterdir()):
        raise ValueError('Existing .blender-harness is not managed; it will not be overwritten')
    old_files = previous['files'] if previous else {}
    if any(not allowed(n) for n in old_files):
        raise ValueError('Unsafe paths in installation state')
    if previous and version_key(version) < version_key(previous['version']):
        raise ValueError('Downgrade refused')
    for manifest in (target/'runs').glob('*/manifest.json'):
        if json.loads(manifest.read_bytes()).get('status') not in ['completed', 'failed']:
            raise ValueError('Finish the active run before updating: '+str(manifest.parent))
    current_agents = agents_path.read_bytes() if agents_path.exists() else b''
    merged_agents, block_hash = merge_agents(current_agents, previous.get('agents_block_sha256') if previous else None)
    changes, snapshots, conflicts, retained = {}, {}, [], []
    for name in sorted(set(old_files)|set(files)):
        relative = DIRECTORY+'/'+name
        path = safe_path(project, relative)
        current = path.read_bytes() if path.exists() else None
        incoming = files.get(name)
        baseline = old_files.get(name)
        current_hash = digest(current) if current is not None else None
        incoming_hash = digest(incoming) if incoming is not None else None
        if current == incoming:
            continue
        if current_hash == baseline:
            changes[relative], snapshots[relative] = incoming, current
        elif incoming_hash == baseline:
            retained.append(name)  # Local-only change, upstream did not change this file.
        else:
            conflicts.append(name)
    if conflicts:
        raise ValueError('Update conflicts; no files changed: '+', '.join(conflicts))
    if merged_agents != current_agents:
        changes['AGENTS.md'], snapshots['AGENTS.md'] = merged_agents, current_agents if agents_path.exists() else None
    state = {'format': 1, 'version': version, 'files': {n: digest(b) for n, b in files.items()},
             'agents_block_sha256': block_hash, 'repository': repository or (previous.get('repository') if previous else None)}
    state_data = json_bytes(state)
    old_state = state_path.read_bytes() if state_path.exists() else None
    if state_data != old_state:
        changes[DIRECTORY+'/.install.json'], snapshots[DIRECTORY+'/.install.json'] = state_data, old_state
    result = {'status': 'dry_run' if dry_run else 'updated' if update else 'installed',
              'project': str(project), 'version': version, 'changed': list(changes),
              'retained_local_files': retained, 'backup': None}
    if dry_run or not changes:
        return result
    target.mkdir(exist_ok=True)
    lock = safe_path(project, DIRECTORY+'/.install.lock')
    # Exclusive lock and recheck protect concurrent installer calls; not a general filesystem sandbox.
    with lock.open('x') as handle:
        handle.write(version)
    backup_rel = DIRECTORY+'/.backups/'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    try:
        for relative, before in snapshots.items():
            path = safe_path(project, relative)
            if (path.read_bytes() if path.exists() else None) != before:
                raise ValueError('File changed during preflight: '+relative)
        backup = safe_path(project, backup_rel)
        backup.mkdir(parents=True)
        journal = {'version': version, 'before': {n: digest(b) if b is not None else None for n, b in snapshots.items()}}
        for relative, before in snapshots.items():
            if before is not None:
                saved = safe_path(project, backup_rel+'/files/'+relative)
                saved.parent.mkdir(parents=True, exist_ok=True)
                saved.write_bytes(before)
        (backup/'journal.json').write_bytes(json_bytes(journal))
        written = []
        try:
            for relative, content in changes.items():
                path = safe_path(project, relative)
                path.parent.mkdir(parents=True, exist_ok=True)
                written.append(relative)
                if content is None:
                    path.unlink()
                else:
                    atomic_write(path, content)
        except Exception:
            for relative in reversed(written):
                path = safe_path(project, relative)
                if snapshots[relative] is None:
                    path.unlink(missing_ok=True)
                else:
                    atomic_write(path, snapshots[relative])
            raise
        result['backup'] = str(backup)
    finally:
        lock.unlink(missing_ok=True)
    return result


def atomic_write(path, content):
    temporary = path.with_name(path.name+'.install-'+uuid.uuid4().hex+'.tmp')
    try:
        with temporary.open('xb') as handle:
            handle.write(content)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)

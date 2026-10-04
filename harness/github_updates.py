"""Fetch stable GitHub Releases; apply through the same conservative local installer."""
import io
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from distribution import digest, read_package, validate_payload, version_key


def repository_name(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+', value):
        raise ValueError('Repository must be owner/repo on github.com')
    if value.split('/')[1] in ['.', '..']:
        raise ValueError('Invalid repository name')
    return value


class GitHubRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlparse(newurl)
        host = parsed.hostname or ''
        if parsed.scheme != 'https' or not (host in ['api.github.com', 'github.com'] or host.endswith('.githubusercontent.com')):
            raise ValueError('Unexpected GitHub download redirect')
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected and host != 'api.github.com':
            redirected.remove_header('Authorization')
        return redirected


def fetch(url, binary=False):
    headers = {'User-Agent': 'blender-modeling-harness',
               'Accept': 'application/octet-stream' if binary else 'application/vnd.github+json'}
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = 'Bearer '+token
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.build_opener(GitHubRedirect()).open(request, timeout=30) as response:
            data = response.read((64*1024*1024 if binary else 2*1024*1024)+1)
    except urllib.error.HTTPError as error:
        raise ValueError(f'GitHub HTTP {error.code}; check repository/release access. Private repositories require GH_TOKEN or GITHUB_TOKEN.') from None
    if len(data) > (64*1024*1024 if binary else 2*1024*1024):
        raise ValueError('GitHub response exceeds size limit')
    return data


def latest(repository):
    repository = repository_name(repository)
    release = json.loads(fetch(f'https://api.github.com/repos/{repository}/releases/latest'))
    tag = release.get('tag_name', '')
    version = tag[1:] if tag.startswith('v') else tag
    version_key(version)
    if release.get('draft') or release.get('prerelease'):
        raise ValueError('Only stable published releases are supported')
    asset_name = f'blenderwright-harness-v{version}.zip'
    assets = [a for a in release.get('assets', []) if a.get('name') == asset_name]
    if len(assets) != 1:
        raise ValueError('Release is missing '+asset_name)
    asset = assets[0]
    if not isinstance(asset.get('id'), int) or not re.fullmatch(r'sha256:[0-9a-f]{64}', asset.get('digest') or ''):
        raise ValueError('Release asset has no valid SHA256 digest')
    return {'repository': repository, 'version': version, 'tag': tag, 'asset': asset_name,
            'asset_id': asset['id'], 'sha256': asset['digest'][7:],
            'release_url': f'https://github.com/{repository}/releases/tag/{urllib.parse.quote(tag, safe="")}' }


def download(release):
    repository = repository_name(release['repository'])
    data = fetch(f'https://api.github.com/repos/{repository}/releases/assets/{release["asset_id"]}', binary=True)
    if digest(data) != release['sha256']:
        raise ValueError('Downloaded release SHA256 mismatch; nothing installed')
    files = read_package(io.BytesIO(data))
    if validate_payload(files) != release['version']:
        raise ValueError('Release tag and package version disagree')
    return files

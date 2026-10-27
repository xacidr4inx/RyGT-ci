"""Trusted GitHub workflow control: resolve GitLab development and publish CI packages."""
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.request

API = 'https://gitlab.com/api/v4/projects/rygt-team%2FRyGT'


def version(commit):
    if not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('Invalid source commit')
    return 'development-' + commit


def resolve():
    with urllib.request.urlopen(API + '/repository/branches/development', timeout=60) as response:
        commit = json.load(response)['commit']['id']
    package_version = version(commit)
    url = API + '/packages/generic/rygt-ci/' + package_version + '/CI-BUILD.json'
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            previous = json.load(response)
        if previous.get('commit') != commit:
            raise RuntimeError('Existing package marker has unexpected commit')
        needed = 'false'
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        needed = 'true'
    if os.environ.get('FORCE_BUILD') == 'true':
        needed = 'true'
    with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as output:
        output.write(f'commit={commit}\nversion={package_version}\nneeded={needed}\n')
    print(f'GitLab development: {commit}; build needed: {needed}')


def publish():
    commit = os.environ['SOURCE_SHA']
    package_version = version(commit)
    folder = Path('source/dist')
    archive = folder / f'RyGT-development-{commit[:8]}.zip'
    checksum = archive.with_suffix('.zip.sha256')
    digest, name = checksum.read_text().strip().split('  ', 1)
    with archive.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if name != archive.name or actual != digest:
        raise RuntimeError('Final package checksum mismatch')
    run = f'https://github.com/{os.environ["GITHUB_REPOSITORY"]}/actions/runs/{os.environ["GITHUB_RUN_ID"]}'
    marker = folder / 'CI-BUILD.json'
    marker.write_text(json.dumps({'type': 'CI build', 'branch': 'development', 'commit': commit,
                                 'build_url': run, 'filename': archive.name, 'sha256': digest}, indent=2) + '\n')
    token = os.environ['GITLAB_PACKAGE_TOKEN']
    # Marker is uploaded last: scheduled checks only skip fully published packages.
    for file in (archive, checksum, marker):
        url = API + '/packages/generic/rygt-ci/' + package_version + '/' + file.name
        with file.open('rb') as stream:
            request = urllib.request.Request(url, data=stream, method='PUT', headers={
                'DEPLOY-TOKEN': token, 'Content-Length': str(file.stat().st_size),
                'Content-Type': 'application/octet-stream'})
            with urllib.request.urlopen(request, timeout=600) as response:
                if response.status != 201:
                    raise RuntimeError('Package upload did not return Created')
        # Verify server content before publishing the completion marker.
        with urllib.request.urlopen(url, timeout=600) as response:
            remote_digest = hashlib.file_digest(response, 'sha256').hexdigest()
        with file.open('rb') as stream:
            local_digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if remote_digest != local_digest:
            raise RuntimeError('Uploaded package checksum mismatch')
        print('Published and verified:', url)
    with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as output:
        output.write(f'CI build `{commit}`\n\n[ZIP]({API}/packages/generic/rygt-ci/{package_version}/{archive.name})'
                     f' | [SHA-256]({API}/packages/generic/rygt-ci/{package_version}/{checksum.name})\n')


if __name__ == '__main__':
    import sys
    {'resolve': resolve, 'publish': publish}[sys.argv[1]]()

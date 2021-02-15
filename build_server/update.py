import json
import random
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Union

import jwt
import requests
from github import Github

from build_server.consts import (FAKE_HASH, FIREFOX_JSON_PATH, GITHUB_TOKEN,
                                 HASH_RE, LIBUSB_JSON_PATH, NVIM_JSON_PATH,
                                 PKGS_DIR, MOZILLA_ADDONS_USER, MOZILLA_ADDONS_SECRET)
from build_server.git import commit_changes


def get_working_commit(repo_name: str, current_sha: str):
    github = Github(GITHUB_TOKEN)
    repo = github.get_repo(repo_name)
    commits = repo.get_commits(sha='master')
    for commit in commits[:20]:
        if commit.sha == current_sha:
            break
        if commit.get_combined_status().state == 'success':
            return commit.sha
    return None


def update_package(repo: str, src_file: Path, pkg_name: str):
    with src_file.open('r') as pkg_file:
        current_commit = json.load(pkg_file)['rev']

    latest_commit = get_working_commit(repo, current_commit)
    if latest_commit is None:
        return

    with src_file.open('w') as pkg_file:
        json.dump({'rev': latest_commit, 'sha256': FAKE_HASH}, pkg_file)

    build = subprocess.run(
        ['nix', 'build', '--no-link', f'{PKGS_DIR}#{pkg_name}'],
        capture_output=True,
        # this fill fail because the given hash is fake
        check=False
    )
    match = HASH_RE.search(build.stderr.decode('utf-8'))
    sha256 = match.group(1)

    with src_file.open('w') as pkg_file:
        json.dump({'rev': latest_commit, 'sha256': sha256}, pkg_file)

    print(f'updated {pkg_name} to {latest_commit}')
    try:
        subprocess.run(
            ['nix', 'build', '--no-link', f'{PKGS_DIR}#{pkg_name}'], check=True
        )
        commit_changes(src_file.name, PKGS_DIR)
    except subprocess.CalledProcessError:
        print(f'{pkg_name} failed to build')


def update_nvim():
    update_package('neovim/neovim', NVIM_JSON_PATH, 'neovim-unwrapped')


def update_libusb():
    update_package('libusb/libusb', LIBUSB_JSON_PATH, 'libusb-patched')


def jwt_nonce() -> str:
    # i hate that this works
    return ''.join([str(random.randint(0, 9)) for _ in range(30)])


def generate_jwt() -> bytes:
    now = datetime.utcnow()
    exp = now + timedelta(seconds=60)
    return jwt.encode({
        'iss': MOZILLA_ADDONS_USER,
        'jti': jwt_nonce(),
        'iat': int(now.timestamp()),
        'exp': int(exp.timestamp())
    }, MOZILLA_ADDONS_SECRET, algorithm='HS256')


def amo_api_request(path: str):
    jwt_token = generate_jwt()
    headers = {
        'Authorization': f'JWT {jwt_token}'
    }
    res = requests.get(
        f'https://addons.mozilla.org/api/v5/{path}', headers=headers
    )
    return json.loads(res.text)


def get_latest_version(guid: str) -> Union[Dict[str, Any], None]:
    data = amo_api_request(f'addons/addon/{guid}')
    for file in data['current_version']['files']:
        if file['platform'] == 'all' or file['platform'] == 'linux':
            return file
    return None


def update_firefox_extensions():
    with FIREFOX_JSON_PATH.open('r') as firefox_src_file:
        firefox_src = json.load(firefox_src_file)

    ext_updated = False
    for ext in firefox_src:
        latest_version = get_latest_version(ext['guid'])
        assert latest_version is not None, 'failed to get latest version'

        if latest_version['hash'] == ext['last_hash']:
            continue

        prefetch = subprocess.run(
            ['nix-prefetch-url', latest_version['url']],
            capture_output=True,
            check=True
        )
        ext['sha256'] = prefetch.stdout.decode('utf-8').strip()
        ext['url'] = latest_version['url']
        ext['last_hash'] = latest_version['hash']
        name = ext['name']
        ext_updated = True
        print(f'updated extension {name}')

    if not ext_updated:
        return

    with FIREFOX_JSON_PATH.open('w') as firefox_src_file:
        json.dump(firefox_src, firefox_src_file)

    try:
        subprocess.run(
            [
                'nix',
                'build',
                '--no-link',
                f'{PKGS_DIR}#firefox-with-extensions'
            ],
            check=True
        )
        commit_changes(FIREFOX_JSON_PATH.name, PKGS_DIR)
    except subprocess.CalledProcessError:
        print('firefox failed to build')

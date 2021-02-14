import jwt
import os
import random
import requests
import json
import subprocess
from github import Github
from datetime import datetime, timedelta
from build_server.consts import *
from build_server.git import commit_changes, push_changes

def get_working_commit(repo_name, current_sha):
    g = Github(os.getenv('GITHUB_TOKEN'))
    repo = g.get_repo(repo_name)
    commits = repo.get_commits(sha='master')
    for commit in commits[:20]:
        if commit.sha == current_sha:
            return None
        elif commit.get_combined_status().state == 'success':
            return commit.sha
    return None

def update_package(repo, src_file, pkg_name):
    with src_file.open('r') as pkg_file:
        current_commit = json.load(pkg_file)['rev']

    latest_commit = get_working_commit(repo, current_commit)
    if latest_commit == None:
        return

    with src_file.open('w') as pkg_file:
        json.dump({ 'rev': latest_commit, 'sha256': FAKE_HASH }, pkg_file)

    build = subprocess.run(['nix', 'build', '--no-link', f'{PKGS_DIR}#{pkg_name}'], capture_output=True)
    match = HASH_RE.search(build.stderr.decode('utf-8'))
    sha256 = match.group(1)

    with src_file.open('w') as pkg_file:
        json.dump({ 'rev': latest_commit, 'sha256': sha256 }, pkg_file)

    print(f'updated {pkg_name} to {commit}')
    try:
        subprocess.run(['nix', 'build', '--no-link', f'{PKGS_DIR}#{pkg_name}'], check=True)
        commit_changes(src_file.name, PKGS_DIR)
    except subprocess.CalledProcessError:
        print(f'{pkg_name} failed to build')

def update_nvim():
    update_package('neovim/neovim', NVIM_JSON_PATH, 'neovim-unwrapped')

def update_libusb():
    update_package('libusb/libusb', LIBUSB_JSON_PATH, 'libusb-patched')

def jwt_nonce():
    # i hate that this works
    return ''.join([str(random.randint(0, 9)) for _ in range(30)])

def generate_jwt():
    now = datetime.utcnow()
    exp = now + timedelta(seconds=60)
    return jwt.encode({
        'iss': os.getenv('MOZILLA_ADDONS_USER'),
        'jti': jwt_nonce(),
        'iat': int(now.timestamp()),
        'exp': int(exp.timestamp())
    }, os.getenv('MOZILLA_ADDONS_SECRET'), algorithm='HS256')

def amo_api_request(path):
    jwt_token = generate_jwt()
    headers = {
        'Authorization': f'JWT {jwt_token}'
    }
    res = requests.get(f'https://addons.mozilla.org/api/v5/{path}', headers=headers)
    return json.loads(res.text)

def get_latest_version(guid):
    data = amo_api_request(f'addons/addon/{guid}')
    for file in data['current_version']['files']:
        if file['platform'] == 'all' or file['platform'] == 'linux':
            return file


def update_firefox_extensions():
    with FIREFOX_JSON_PATH.open('r') as firefox_src_file:
        firefox_src = json.load(firefox_src_file)

    ext_updated = False
    for ext in firefox_src:
        latest_version = get_latest_version(ext['guid'])

        if latest_version['hash'] == ext['last_hash']:
            continue

        prefetch = subprocess.run(['nix-prefetch-url', latest_version['url']], capture_output=True)
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
        subprocess.run(['nix', 'build', '--no-link', f'{PKGS_DIR}#firefox-with-extensions'], check=True)
        commit_changes(FIREFOX_JSON_PATH.name, PKGS_DIR)
        push_changes(PKGS_DIR)
    except subprocess.CalledProcessError:
        print(f'firefox failed to build')

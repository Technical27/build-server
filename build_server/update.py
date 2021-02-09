import jwt
import os
import random
import requests
import json
import subprocess
from datetime import datetime, timedelta
from build_server.consts import *
from build_server.git import commit_changes, push_changes

def jwt_nonce():
    random_string = ''

    for _ in range(20):
        random_string += chr(random.randint(0, 127))

    return random_string

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

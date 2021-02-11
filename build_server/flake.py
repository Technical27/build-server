import json
import subprocess
from build_server.consts import *

class FlakeUnsupported(Exception):
    pass

def update_flake(dir):
    with dir.joinpath('flake.lock').open('r') as lock_file:
        flake_json = json.load(lock_file)

    if flake_json['version'] > 7:
        raise FlakeUnsupported

    # 99% sure that it will be 'root', but we can never be sure
    root = flake_json['root'];
    root_node = flake_json['nodes'][root]
    root_inputs = root_node['inputs']

    g = Github(os.getenv('GITHUB_TOKEN'))

    for name, node in root_inputs:
        node = flake_json['nodes'][node]
        orig_repo = node['original']
        owner = orig_repo['owner']
        repo_name = orig_repo['repo']
        repo_combined = f'{owner}/{repo_name}'
        repo = g.get_repo(repo_combined)
        latest_commit = repo.get_commits()[0]
        if latest_commit != node['locked']['rev']:
            print(f'updating input {name}')
            subprocess.run(['nix', 'flake', 'update', '--update-input', name], check=True)

    commit_changes('flake.lock', dir)

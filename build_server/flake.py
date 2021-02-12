import json
import subprocess
from github import Github
from build_server.consts import *
from build_server.git import commit_changes

class FlakeUnsupported(Exception):
    pass

def update_flake(dir):
    with dir.joinpath('flake.lock').open('r') as lock_file:
        flake_json = json.load(lock_file)

    if flake_json['version'] != 7:
        raise FlakeUnsupported

    # 99% sure that it will be 'root', but we can never be sure
    root = flake_json['root'];
    root_node = flake_json['nodes'][root]
    root_inputs = root_node['inputs']

    g = Github(os.getenv('GITHUB_TOKEN'))

    for name, node in root_inputs.items():
        if node == root:
            continue

        node = flake_json['nodes'][node]
        orig_repo = node['original']
        owner = orig_repo['owner']
        repo_name = orig_repo['repo']
        repo_combined = f'{owner}/{repo_name}'

        repo = g.get_repo(repo_combined)

        if 'ref' in orig_repo:
            branch = orig_repo['ref']
        else:
            branch = repo.default_branch

        latest_commit = repo.get_branch(branch).commit
        if latest_commit != node['locked']['rev']:
            print(f'updating input {name}')
            subprocess.run(['nix', 'flake', 'update', '--update-input', name, dir], check=True)

    commit_changes('flake.lock', dir)

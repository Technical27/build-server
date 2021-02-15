from pathlib import Path

from pygit2 import (GIT_MERGE_ANALYSIS_FASTFORWARD, GIT_MERGE_ANALYSIS_NORMAL,
                    GIT_MERGE_ANALYSIS_UP_TO_DATE, GIT_STATUS_WT_MODIFIED,
                    GIT_STATUS_WT_NEW, Commit, RemoteCallbacks, Repository,
                    UserPass)

from build_server.consts import GITHUB_TOKEN, SIGNATURE


def pull_repo(repo_path: Path):
    """Update a repository at repo_path by pulling from the remote named origin."""
    repo = Repository(repo_path)
    remote = repo.remotes['origin']
    remote.fetch()
    master_id = repo.lookup_reference('refs/remotes/origin/master').target
    merge_result, _ = repo.merge_analysis(master_id)

    if merge_result & GIT_MERGE_ANALYSIS_UP_TO_DATE:
        return

    if merge_result & GIT_MERGE_ANALYSIS_FASTFORWARD:
        repo.checkout_tree(repo.get(master_id))
        master_ref = repo.lookup_reference('refs/heads/master')
        master_ref.set_target(master_id)
        repo.head.set_target(master_id)
    elif merge_result & GIT_MERGE_ANALYSIS_NORMAL:
        repo.merge(master_id)
        assert repo.index.conflicts is None, \
            'Merge conflicts, please manually fix'
        tree = repo.index.write_tree()
        repo.create_commit(
            'refs/heads/master',
            SIGNATURE,
            SIGNATURE,
            '[build-server]: Merge',
            tree,
            [repo.head.target, master_id]
        )
        repo.state_cleanup()


def commit_changes(file: str, repo_path: Path):
    """Commit changes on file to the repository at repo_path."""
    repo = Repository(repo_path)

    for path, flags in repo.status().items():
        if path == file and (flags != GIT_STATUS_WT_MODIFIED or flags != GIT_STATUS_WT_NEW):
            return

    print(f'commiting {file}')
    repo.index.add(file)
    repo.index.write()

    tree = repo.index.write_tree()
    old_head = repo.head.peel(Commit).id
    repo.create_commit(
        'refs/heads/master',
        SIGNATURE, SIGNATURE,
        f'[build-server]: update {file}',
        tree,
        [old_head]
    )


def push_changes(repo_path: Path):
    """Push the repository at repo_path to the remote named origin."""
    repo = Repository(repo_path)
    remote = repo.remotes['origin']
    creds = UserPass('Technical27', GITHUB_TOKEN)
    callback = RemoteCallbacks(credentials=creds)
    remote.connect(callbacks=callback)
    remote.push(['refs/heads/master:refs/heads/master'], callbacks=callback)

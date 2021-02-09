import os
from pygit2 import Repository, Signature, Commit, UserPass, RemoteCallbacks, GIT_MERGE_ANALYSIS_UP_TO_DATE, GIT_MERGE_ANALYSIS_FASTFORWARD, GIT_MERGE_ANALYSIS_NORMAL

def pull_repo(dir):
    repo = Repository(dir)
    remote = repo.remotes['origin']
    remote.fetch()
    master_id = repo.lookup_reference('refs/remotes/origin/master').target
    merge_result, _ = repo.merge_analysis(master_id)

    if merge_result & GIT_MERGE_ANALYSIS_UP_TO_DATE:
        return
    elif merge_result & GIT_MERGE_ANALYSIS_FASTFORWARD:
        repo.checkout_tree(repo.get(master_id))
        master_ref = repo.lookup_reference('refs/heads/master')
        master_ref.set_target(master_id)
        repo.head.set_target(master_id)
    elif merge_result & GIT_MERGE_ANALYSIS_NORMAL:
        repo.merge(remote_master_id)
        assert repo.index.conflicts is None, 'Merge conflicts, please manually fix'
        author = Signature('Aamaruvi Yogamani', '38222826+Technical27@users.noreply.github.com')
        tree = repo.index.write_tree()
        commit = repo.create_commit('refs/heads/master', author, author, '[build-server]: Merge', tree, [repo.head.target, remote_master_id])
        repo.state_cleanup()

def commit_changes(file, dir):
    repo = Repository(dir)
    repo.index.add(file)
    repo.index.write()
    tree = repo.index.write_tree()
    author = Signature('Aamaruvi Yogamani', '38222826+Technical27@users.noreply.github.com')
    old_head = repo.head.peel(Commit).id
    repo.create_commit('refs/heads/master', author, author, f'[build-server]: update {file}', tree, [old_head])

def push_changes(dir):
    repo = Repository(dir)
    remote = repo.remotes['origin']
    creds = UserPass('Technical27', os.getenv('GITHUB_TOKEN'))
    callback = RemoteCallbacks(credentials=creds)
    remote.connect(callbacks=callback)
    remote.push(['refs/heads/master:refs/heads/master'], callbacks=callback)
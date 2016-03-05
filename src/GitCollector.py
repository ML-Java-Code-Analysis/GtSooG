from git import Repo

def collectData(repository_path, branch='master'):
    repo = Repo(repository_path)
    last_commit = None
    for commit in reversed(list(repo.iter_commits(branch))):

        print("-"*20)
        commit_id = commit.hexsha
        print(commit_id)
        print(commit.message)
        print(commit.committer)

        # Ignore merges
        if len(commit.parents) > 1:
            continue

        if last_commit:
            print("CHANGES: ")
            print("Current commit: " + commit.message.rstrip('\n'))
            print("Last commit:    " + last_commit.message.rstrip('\n'))
            diff = commit.diff(last_commit)
            for item in diff:
                if item.b_blob:
                    filepath = item.b_blob.path
                if item.a_blob:
                    filepath = item.a_blob.path

                msg = filepath + ", "
                msg += "" if item.a_blob is None else "a"
                msg += "" if item.b_blob is None else "b"
                msg += "" if not item.renamed else ", " + str(item.rename_from) + " -> " + str(item.rename_to)
                print(msg)
        last_commit = commit


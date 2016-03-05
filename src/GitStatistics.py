from git import Repo
import time

def stats(repository_path, branch='master'):
    repo = Repo(repository_path)
    commits = list(repo.iter_commits(branch))
    commits.reverse()

    first_commit = commits[0]
    last_commit = commits[-1]
    time_first_commit = first_commit.committed_date
    time_last_commit = last_commit.committed_date
    commit_count = len(commits)

    commits_per_second = commit_count/(time_last_commit-time_first_commit)
    commits_per_day = commits_per_second*3600*24

    print("First commit: " + time.asctime(time.gmtime(time_first_commit)))

    previous_year = time.gmtime(time_first_commit).tm_year
    commits_per_year = 0
    changed_files_count = 0

    last_commit = None

    for commit in commits:
        if len(commit.parents) > 1:
            continue

        commit_year = time.gmtime(commit.committed_date).tm_year
        commits_per_year+=1
        if ( commit_year > previous_year ) or ( commit == last_commit ):
            print("Year: " + str(previous_year) + " Commits: " + str(commits_per_year) + " File changes: " + str(changed_files_count) + " File changes per commit: " + str(changed_files_count/commits_per_year))

            commits_per_year = 0
            changed_files=0

            first_commit = commit
            previous_year=commit_year
            commit_year+=1

        changed_files = []
        if last_commit:
            diff = commit.diff(last_commit)
            for item in diff:
                if item.a_blob is not None and item.a_blob.path not in changed_files:
                    changed_files.append(item.a_blob.path)
                if item.b_blob is not None and item.b_blob.path not in changed_files:
                    changed_files.append(item.b_blob.path)

        last_commit = commit
        changed_files_count+=len(changed_files)
        #print(changed_files_count)


    print("Last commit: " + time.asctime(time.gmtime(time_last_commit)))
from git import Repo
from gtsoog import Log
import time

class RepositoryMiner(object):

    def __init__(self, repository_url, branch='master'):
        self.repository = Repo(repository_url)
        self.branch = branch

        self.iterate_commits()

    def iterate_commits(self):
        commits = self.get_commits()
        previous_commit = None

        for commit in commits:
            manipulated_files = self.get_changed_files(commit, previous_commit)
            Log.log(str(manipulated_files),Log.LEVEL_DEBUG)
            previous_commit = commit


    def get_commits(self):
        """
        Get all commits of a repository exclude all merges
        Returns: commits in reversed order --> first commit is first element in list
        """
        commits = list(filter(lambda commit: len(commit.parents) <= 1, self.repository.iter_commits(self.branch)))
        commits.reverse()
        return commits

    def get_changed_files(self, commit, previous_commit):
        assert commit is not None

        added_files = []
        deleted_files = []
        changed_files = []

        diff = commit.diff(previous_commit)
        for item in diff:
            if item.a_blob is None:
                added_files.append(item.b_blob.path)
            elif item.b_blob is None:
                deleted_files.append(item.a_blob.path)
            else:
                changed_files.append(item.a_blob)

        return added_files,deleted_files,changed_files

    def stats(repository_path, branch='master'):
        print("mine mine\n")
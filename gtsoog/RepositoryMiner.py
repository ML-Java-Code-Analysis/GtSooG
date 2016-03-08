from git import Repo
import time


class RepositoryMiner(object):

    def __init__(self, repository_url, branch='master'):
        self.repository = Repo(repository_url)
        self.branch = branch

    def get_commits(self):
        """
        Get all commits of a repository exclude all merges
        Returns: commits in reversed order --> first commit is first element in list
        """
        commits = list(filter(lambda comit: len(commit.parents) <= 1, self.repository.iter_commits(self.branch)))
        return commits.reverse()

    def get_changed_files(self, previous_commit, commit):
        assert commit is not None and previous_commit is not None

        added_files = []
        deleted_files = []
        changed_files = []

        diff = commit.diff(previous_commit)
        for item in diff:




    def stats(repository_path, branch='master'):
        print("mine mine\n")
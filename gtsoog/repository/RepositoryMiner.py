import os
import threading

from git import Repo

from model import DB
from model.objects.IssueTracking import IssueTracking
from model.objects.Repository import Repository
from utils import Log


class RepositoryMiner(object):
    def __init__(self, repository_url, name=None, branch='master'):
        self.db_session = DB.create_session()
        self.repository = Repo(repository_url)
        self.branch = branch

        self.NUMBER_OF_THREADS = 15
        self.interesting_file_extensions = [".md", ".py", ".java"]

        if name is None:
            name = os.path.split(repository_url)[1]
        self.repository_orm = Repository(
            name=name,
            url=repository_url
        )
        self.issue_tracking_orm = IssueTracking(
            repository_id=self.repository_orm.id,
            type='JIRA',
            url='www.penisland.net'
        )
        self.db_session.add(self.repository_orm)
        self.db_session.add(self.issue_tracking_orm)
        self.db_session.commit()

        commits = self.get_commits()
        self.iterate_commits(commits)

    def iterate_commits(self, commits):
        """

        Args:
            commits:
        """

        previous_commit = None

        threads = []
        commit_counter = 0

        for commit in commits:
            commit_counter += 1
            if commit_counter % 1000 == 0:
                Log.log("Commit counter: " + str(commit_counter), Log.LEVEL_DEBUG)

            if commit.parents:
                previous_commit = commit.parents[0]

            if len(commit.parents) <= 1:
                if threading.active_count() < self.NUMBER_OF_THREADS:
                    t = threading.Thread(target=self.process_commit, args=(commit, previous_commit,))
                    threads.append(t)
                    t.start()
                else:
                    self.process_commit(commit, previous_commit)

    def process_commit(self, commit, previous_commit):
        """

        Args:
            commit:
            previous_commit:

        Returns:

        """
        manipulated_files = self.get_changed_files(commit, previous_commit)

        added_files = manipulated_files[0]
        deleted_files = manipulated_files[1]
        changed_files = manipulated_files[2]
        files_diff = manipulated_files[3]

        Log.log("------------", Log.LEVEL_DEBUG)
        Log.log("Commit: " + commit.message, Log.LEVEL_DEBUG)
        Log.log("Added: " + str([file.path for file in added_files]), Log.LEVEL_DEBUG)
        Log.log("Deleted: " + str([file.path for file in deleted_files]), Log.LEVEL_DEBUG)
        Log.log("Changed: " + str([file.path for file in changed_files]), Log.LEVEL_DEBUG)

        Log.log("Diff: " + str(files_diff), Log.LEVEL_DEBUG)
        # for file in files_diff:
        #     # Log.log("Changed: " + str(file),Log.LEVEL_DEBUG)
        #     filename = re.search(r"\/.*\\n", str(file))
        #     print(str(filename.group(0)))

        return

    def get_commits(self):
        """
        Get all commits of a repository
        Returns: commits in reversed order --> first commit is first element in list
        """
        commits = list(self.repository.iter_commits(self.branch))
        commits.reverse()
        return commits

    def get_changed_files(self, commit, previous_commit):

        """

        Args:
            commit:
            previous_commit:

        Returns: tuple of lists of added_files, deleted_files, changed_files, differences in string format

        """
        assert commit is not None

        added_files = []
        deleted_files = []
        changed_files = []
        files_diff = []

        """ do the diff for previous_commit
            otherwise diff shows added code as deleted code
        """
        if previous_commit:
            diff_with_patch = previous_commit.diff(commit, create_patch=True)
            diff = previous_commit.diff(commit)
        else:
            diff_with_patch = commit.diff(None, create_patch=True)
            diff = commit.diff(None)

        for item in diff:
            if item.a_blob is None:
                added_files.append(item.b_blob)
            if item.b_blob is None:
                deleted_files.append(item.a_blob)
            if (item.a_blob is not None) and (item.b_blob is not None) and (not item.renamed):
                changed_files.append(item.a_blob)

        for item in diff_with_patch:
            files_diff.append(item.diff)

            # for diff_added in diff_with_patch.iter_change_type('A'):
            # print(diff_added)
            # for diff_changed in diff_with_patch.iter_change_type('M'):
            # print(diff_changed)

        """ handle first commit"""
        if previous_commit is None:
            added_files = deleted_files
            deleted_files = []

        return added_files, deleted_files, changed_files, files_diff
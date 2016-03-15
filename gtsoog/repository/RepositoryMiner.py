import os
import threading
import datetime

from git import Repo

from model import DB
from model.objects.IssueTracking import IssueTracking
from model.objects.Repository import Repository
from model.objects.Commit import Commit
from utils import Log


class RepositoryMiner(object):
    def __init__(self, repository_url, name=None, branch='master'):
        """ Initialize the Repository Miner

        Args:
            repository_url: The url to the repository
            name: Optional. The unique name of this repository. Defaults to the last part of the path.
            branch: Optional. The branch to mine. Defaults to the master branch.
        """
        # TODO wäre repository_url nicht der Filepfad?
        self.repository = Repo(repository_url)
        self.branch = branch

        # TODO das sollte parametrisierbar sein
        self.interesting_file_extensions = [".md", ".py", ".java"]
        self.NUMBER_OF_THREADS = 5
        self.NUMBER_OF_DBSESSIONS = 0 #self.NUMBER_OF_THREADS

        self.init_db_sessions()

        self.existing_commit_ids = set()
        self.__create_new_repository(name, repository_url)

        commits = self.get_commits()
        self.iterate_commits(commits)

        self.close_all_db_sessions()

    def init_db_sessions(self):
        self.db_session = DB.create_session()
        self.thread_db_sessions = {}
        for i in range(self.NUMBER_OF_DBSESSIONS):
            self.thread_db_sessions[i] = (False, DB.create_session())

    def close_all_db_sessions(self):
        self.db_session.close()
        for i in self.thread_db_sessions.keys():
            self.thread_db_sessions[i][1].close()

    def __create_new_repository(self, name, repository_url):
        # Try to retrieve the repository record, if not found a new one is created.
        if name is None:
            name = os.path.split(repository_url)[1]

        self.repository_orm = self.db_session.query(Repository).filter(Repository.name == name).one_or_none()
        if not self.repository_orm:
            # create new repository
            self.repository_orm = Repository(
                name=name,
                url=repository_url
            )
            # TODO: get issue tracking via params
            self.issue_tracking_orm = IssueTracking(
                repository_id=self.repository_orm.id,
                type='JIRA',
                url='www.penisland.net'
            )
            self.db_session.add(self.repository_orm)
            self.db_session.add(self.issue_tracking_orm)
            self.db_session.commit()
        else:
            # read existing commit ids into memory
            self.__read_existings_commit_ids(self.repository_orm.id)

    def __read_existings_commit_ids(self, repository_id):
        self.existing_commit_ids = set([t[0] for t in self.db_session.query(Commit.id).all()])

    def commit_exists(self, commit_id):
        return commit_id in self.existing_commit_ids

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

            if len(commit.parents) <= 1 or self.commit_exists(str(commit)):
                if threading.active_count() < self.NUMBER_OF_THREADS:
                    session = self.__get_db_session()
                    t = threading.Thread(target=self.__process_commit, args=(commit, previous_commit))
                    threads.append(t)
                    t.start()
                else:
                    self.__process_commit(commit, previous_commit, db_session=self.db_session)

    def __get_db_session(self):
        for i in range(self.NUMBER_OF_DBSESSIONS):
            session_tuple = self.thread_db_sessions[i]
            if not session_tuple[0]:
                return session_tuple[1]


    def __process_commit(self, commit, previous_commit, db_session = None):
        """

        Args:
            commit:
            previous_commit:

        Returns:

        """
        if not db_session:
            db_session = DB.create_session()
        manipulated_files = self.get_changed_files(commit, previous_commit)

        added_files = manipulated_files[0]
        deleted_files = manipulated_files[1]
        changed_files = manipulated_files[2]
        files_diff = manipulated_files[3]

        commit_time = datetime.datetime.utcfromtimestamp(commit.committed_date)

        Log.log("------------", Log.LEVEL_DEBUG)
        Log.log("Commit: " + commit.message + "with ID: " + str(commit) + "Commit date: " + str(commit_time), Log.LEVEL_DEBUG)
        Log.log("Added: " + str([file.path for file in added_files]), Log.LEVEL_DEBUG)
        Log.log("Deleted: " + str([file.path for file in deleted_files]), Log.LEVEL_DEBUG)
        Log.log("Changed: " + str([file.path for file in changed_files]), Log.LEVEL_DEBUG)

        Log.log("Diff: " + str(files_diff), Log.LEVEL_DEBUG)
        # for file in files_diff:
        #     # Log.log("Changed: " + str(file),Log.LEVEL_DEBUG)
        #     filename = re.search(r"\/.*\\n", str(file))
        #     print(str(filename.group(0)))

        self.__create_new_commit(db_session, str(commit),commit.message,commit_time)

        db_session.close()

    def __create_new_commit(self, db_session, id, message, timestamp):
        # Try to retrieve the commit record, if not found a new one is created.
        # TODO: Now that existing commits are skipped anyway, this query could be removed for performance
        self.commit_orm = db_session.query(Commit).filter(Commit.id == id).one_or_none()
        if not self.commit_orm:
            self.commit_orm = Commit(
                id=id,
                message=message,
                timestamp=timestamp
            )
            db_session.add(self.commit_orm)
            db_session.commit()

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

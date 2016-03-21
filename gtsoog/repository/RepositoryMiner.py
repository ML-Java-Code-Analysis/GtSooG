import os
import threading
import datetime

from git import Repo

from model import DB
from model.objects.IssueTracking import IssueTracking
from model.objects.Repository import Repository
from model.objects.Commit import Commit
from model.objects.File import File
from model.objects.Version import Version
from utils import Log
from sqlalchemy import desc


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
        self.PROGRAMMING_LANGUAGES = [("README", "md"), ("Python", "py"), ("Java", "java")]
        self.NUMBER_OF_THREADS = 0
        self.NUMBER_OF_DBSESSIONS = 0

        self.db_session = None
        self.init_db_sessions()
        self.thread_db_sessions = {}

        self.existing_commit_ids = set()
        self.repository_id = self.__create_new_repository(name, repository_url)

        commits = self.get_commits()
        self.iterate_commits(commits)

        self.close_all_db_sessions()

    def init_db_sessions(self):
        self.db_session = DB.create_session()
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
            self.db_session.add(self.repository_orm)
            self.db_session.flush()
            self.db_session.commit()

            self.db_session.add(self.issue_tracking_orm)
            self.db_session.commit()
        else:
            # read existing commit ids into memory
            self.__read_existings_commit_ids(self.repository_orm.id)

        return self.repository_orm.id

    def __read_existings_commit_ids(self, repository_id):
        self.existing_commit_ids = set(
            [t[0] for t in self.db_session.query(Commit.id).filter(Commit.repository_id == repository_id).all()])

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

    def __process_commit(self, commit, previous_commit, db_session=None):
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
        renamed_files = manipulated_files[3]
        files_diff = manipulated_files[4]
        if (not added_files) and (not deleted_files) and (not changed_files) and (not renamed_files) and (
                not renamed_files):
            return

        commit_time = datetime.datetime.utcfromtimestamp(commit.committed_date)
        commit_id = str(commit)
        commit_files_size = {}

        self.__create_new_commit(db_session, commit_id, self.repository_id, commit.message, commit_time)

        # Log.log("------------", Log.LEVEL_DEBUG)
        # Log.log("Commit: " + commit.message + "with ID: " + str(commit) + "Commit date: " + str(commit_time), Log.LEVEL_DEBUG)
        # Log.log("Added: " + str([file.path for file in added_files]), Log.LEVEL_DEBUG)
        # Log.log("Deleted: " + str([file.path for file in deleted_files]), Log.LEVEL_DEBUG)
        # Log.log("Changed: " + str([file.path for file in changed_files]), Log.LEVEL_DEBUG)
        # Log.log("Diff: " + str(files_diff), Log.LEVEL_DEBUG)

        if added_files:
            for file in added_files:
                commit_files_size[file.path] = file.size
                programming_language = self.__get_programming_langunage(file.path)
                self.__create_new_file(db_session, str(file.path), commit_time, self.repository_id, programming_language)

        if deleted_files:
            for file in deleted_files:
                commit_files_size[file.path] = file.size

        if changed_files:
            for file in changed_files:
                commit_files_size[file.path] = file.size

        # for renamed files just create a new one
        # TODO handle file history
        if renamed_files:
            for file in renamed_files:
                old_file = file[0]
                new_file = file[1]

                commit_files_size[new_file.path] = new_file.size
                programming_language = self.__get_programming_langunage(new_file.path)
                #get the timestamp from old filename
                old_timestamp = self.db_session.query(File).filter(File.name == str(old_file.path)).order_by(desc(File.timestamp)).one
                self.__create_new_file(db_session, str(new_file.path), commit_time, self.repository_id, programming_language, str(old_file.path), old_timestamp)

        files_with_lines_metric = self.__get_lines_metric(files_diff)
        for file in files_with_lines_metric:
            try:
                self.__create_new_version(db_session, file[0], commit_id, file[1], file[2], file[3],
                                          commit_files_size[file[0]])
            except KeyError:
                Log.log("f1: " + str(file[0]) + " f2: " + str(file[1]), Log.LEVEL_DEBUG)
                Log.log("Diff: " + str(files_diff), Log.LEVEL_DEBUG)

        db_session.close()

    def __get_programming_langunage(self, path):
        splitted_path = path.split('.')

        if len(splitted_path) > 1:
            for language in self.PROGRAMMING_LANGUAGES:
                if language[1] == splitted_path[1]:
                    return language[0]
        return "NOT_FOUND"

    def __get_lines_metric(self, files_diff):
        # diff string parsing copy pasta, spaghetti

        files_with_lines_metric = []

        # handle first commit very ugly
        if "***FIRSTCOMMIT***" in files_diff[0]:
            first_commit = True
        else:
            first_commit = False

        for diff_file in files_diff:

            # ugly string parsing
            # dooooge pfffui pfffuuuii

            added_lines = 0
            deleted_lines = 0

            # parse every line
            diff_lines = diff_file.split('\n')

            if len(diff_lines) <= 1:
                continue

            # added file
            if "--- /dev/null" in diff_lines[0]:
                filename = diff_lines[1][6:]

            # deleted file
            elif "+++ /dev/null" in diff_lines[1]:
                filename = diff_lines[0][6:]

            # skip binary file
            elif "Binary files" in diff_lines[0]:
                continue

            # renamed file 1
            elif diff_lines[0][6:] != diff_lines[1][6:]:
                filename = diff_lines[1][6:]

            # renamed file 2
            elif "similarity index 100%" in diff_lines[0]:
                filename = diff_lines[10][6:]

            # changed file
            else:
                filename = diff_lines[0][6:]

            for diff_line in diff_lines[2:]:
                if diff_line.startswith('+', 0, 1):
                    added_lines += 1
                if diff_line.startswith('-', 0, 1):
                    deleted_lines += 1

            # handle first commit
            if first_commit:
                if added_lines > 0:
                    continue
                added_lines = deleted_lines
                deleted_lines = 0

            changed_lines = added_lines + deleted_lines

            files_with_lines_metric.append((filename, changed_lines, added_lines, deleted_lines))

            # Log.log("File: " + filename + " changed lines " + str(changed_lines) + " added lines " + str(added_lines) + " deleted lines " + str(deleted_lines), Log.LEVEL_DEBUG)

        return files_with_lines_metric

    def __create_new_commit(self, db_session, commit_id, repository_id, message, timestamp):
        # Try to retrieve the commit record, if not found a new one is created.
        # TODO: Now that existing commits are skipped anyway, this query could be removed for performance
        self.commit_orm = db_session.query(Commit).filter(Commit.id == commit_id).one_or_none()
        if not self.commit_orm:
            self.commit_orm = Commit(
                id=commit_id,
                repository_id=repository_id,
                message=message,
                timestamp=timestamp
            )
            db_session.add(self.commit_orm)
            db_session.commit()

    def __create_new_file(self, db_session, file_id, timestamp, repository_id, language ,precursor_file_id=None, precursor_file_timestamp=None):
        # Try to retrieve the file record, if not found a new one is created.
        self.file_orm = db_session.query(File).filter(File.id == file_id, File.timestamp == timestamp).one_or_none()
        if not self.file_orm:
            self.file_orm = File(
                id=file_id,
                timestamp=timestamp,
                repository_id=repository_id,
                precursor_file_id=precursor_file_id,
                precursor_file_timestamp=precursor_file_timestamp,
                language=language
            )
            db_session.add(self.file_orm)
            db_session.commit()

    def __create_new_version(self, db_session, file_id, commit_id, lines_changed, lines_added, lines_deleted,
                             file_size):
        self.version_orm = Version(
            file_id=file_id,
            commit_id=commit_id,
            lines_changed=lines_changed,
            lines_added=lines_added,
            lines_deleted=lines_deleted,
            file_size=file_size
        )
        db_session.add(self.version_orm)
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
        renamed_files = []
        files_diff = []

        """ do the diff for previous_commit
            otherwise diff shows added code as deleted code
        """
        if previous_commit:
            diff_with_patch = previous_commit.diff(commit, create_patch=True)
            diff = previous_commit.diff(commit)
        else:
            diff_with_patch = commit.diff(None, staged=False, create_patch=True)
            diff = commit.diff(None)

        for item in diff:
            if item.a_blob is None:
                added_files.append(item.b_blob)
            if item.b_blob is None:
                deleted_files.append(item.a_blob)
            if (item.a_blob is not None) and (item.b_blob is not None) and (not item.renamed):
                changed_files.append(item.a_blob)
            if item.renamed:
                renamed_files.append((item.a_blob, item.b_blob))

        for item in diff_with_patch:
            # mark first commit for later handeling
            if previous_commit is None:
                files_diff.append("***FIRSTCOMMIT***")

            # TODO here we lose file size I guess. Compare it to original file
            files_diff.append(item.diff.decode("utf-8", "ignore"))

        """ handle first commit"""
        if previous_commit is None:
            added_files = deleted_files
            deleted_files = []

        return added_files, deleted_files, changed_files, renamed_files, files_diff

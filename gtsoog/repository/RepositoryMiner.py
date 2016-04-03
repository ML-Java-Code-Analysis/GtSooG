# coding=utf-8
import os
import threading
import datetime
import time
from uuid import uuid4 as uuid

from git import Repo

from model import DB
from model.objects.Line import Line, MAX_LINE_LENGTH, TYPE_ADDED, TYPE_DELETED
from model.objects.Repository import Repository, MAX_URL_LENGTH
from model.objects.Commit import Commit, MAX_MESSAGE_LENGTH, MAX_AUTHOR_LENGTH
from model.objects.File import File, MAX_PATH_LENGTH
from model.objects.Version import Version
from utils import Log
from sqlalchemy import desc
from utils import Config


# TODO Performance Optimierung mit Threads

class RepositoryMiner(object):
    def __init__(self, repository_path, name=None, db_session=None, branch='master'):
        """ Initialize the Repository Miner

        Args:
            repository_path: The url to the repository
            name: Optional. The unique name of this repository. Defaults to the last part of the path.
            branch: Optional. The branch to mine. Defaults to the master branch.
        """

        self.repository = Repo(repository_path)
        self.branch = branch

        self.PROGRAMMING_LANGUAGES = Config.programming_languages
        self.NUMBER_OF_THREADS = Config.number_of_threads
        self.NUMBER_OF_DBSESSIONS = Config.number_of_database_sessions
        self.EMPTY_TREE_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

        self.thread_db_sessions = {}
        self.init_db_sessions(db_session)

        self.existing_commit_ids = set()
        self.repository_id = self.__create_new_repository(self.db_session, name, repository_path)

        Log.info("Start mining the repository with path: " + repository_path)
        commits = self.__get_commits()
        self.iterate_commits(commits)

        # Leave open for the moment
        # self.close_all_db_sessions()

    def init_db_sessions(self, db_session):
        if db_session == None:
            self.db_session = DB.create_session()
        else:
            self.db_session = db_session
            for i in range(self.NUMBER_OF_DBSESSIONS):
                self.thread_db_sessions[i] = (False, DB.create_session())

    def get_db_session(self):
        return self.db_session

    def close_all_db_sessions(self):
        self.db_session.close()
        for i in self.thread_db_sessions.keys():
            self.thread_db_sessions[i][1].close()

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
        log_interval = 1
        if len(commits) > 1000:
            log_interval = 100

        for i, commit in enumerate(commits):
            if i % log_interval == 0:
                prc = i / len(commits) * 100
                Log.info("{0:0.2f}% - processed commits: {1}".format(prc, i))

            if commit.parents:
                previous_commit = commit.parents[0]
            else:
                previous_commit = self.EMPTY_TREE_SHA

            if len(commit.parents) <= 1 or self.commit_exists(str(commit)):
                if threading.active_count() < self.NUMBER_OF_THREADS:
                    t = threading.Thread(target=self.__process_commit, args=(commit, previous_commit))
                    threads.append(t)
                    t.start()
                else:
                    self.__process_commit(commit, previous_commit, db_session=self.db_session)
                    self.db_session.commit()

    def __get_db_session(self):
        for i in range(self.NUMBER_OF_DBSESSIONS):
            session_tuple = self.thread_db_sessions[i]
            if not session_tuple[0]:
                return session_tuple[1]

    def __process_commit(self, commit, previous_commit, db_session=None, manipulated_files=None):
        """

        Args:
            commit:
            previous_commit:

        Returns:

        """
        db_session_local = None
        if not db_session:
            db_session_local = True
            db_session = DB.create_session()

        added_files_thread = None
        changed_files_thread = None
        deleted_files_thread = None

        commit_processing_successful = True

        if not manipulated_files:
            manipulated_files = self.__get_changed_files(commit, previous_commit)

        added_files = manipulated_files['added_files']
        deleted_files = manipulated_files['deleted_files']
        changed_files = manipulated_files['changed_files']
        renamed_files = manipulated_files['renamed_files']
        files_diff = manipulated_files['files_diff']

        # no files were changed at all
        if (not added_files) and (not deleted_files) and (not changed_files) and (not renamed_files) and (
                not renamed_files):
            return

        commit_time = datetime.datetime.utcfromtimestamp(commit.committed_date)
        timestamp = commit_time
        commit_id = str(commit)

        self.__create_new_commit(db_session, commit_id, self.repository_id, commit.message, commit.author.name, commit_time)

        if added_files:
            # added_files_thread = threading.Thread(target=self.__thread_helper_added_file, args=(commit_id, added_files, files_diff, timestamp))
            # added_files_thread.start()
            self.__thread_helper_added_file(commit_id, added_files, files_diff, timestamp, db_session=db_session)

        if deleted_files:
            # deleted_files_thread = threading.Thread(target=self.__thread_helper_deleted_or_changed_file, args=(commit_id, deleted_files, files_diff, timestamp))
            # deleted_files_thread.start()
            self.__thread_helper_deleted_or_changed_file(commit_id, deleted_files, files_diff, timestamp,
                                                         db_session=db_session)

        if changed_files:
            # changed_files_thread = threading.Thread(target=self.__thread_helper_deleted_or_changed_file, args=(commit_id, changed_files, files_diff, timestamp))
            # changed_files_thread.start()
            self.__thread_helper_deleted_or_changed_file(commit_id, changed_files, files_diff, timestamp,
                                                         db_session=db_session)

        # for renamed files just create a new one and link to the old one
        if renamed_files:
            for file in renamed_files:
                old_file = file['old_file']
                new_file = file['new_file']

                programming_language = self.__get_programming_langunage(new_file.path)

                model_file = db_session.query(File).filter(File.path == str(old_file.path)).order_by(
                    desc(File.timestamp)).first()

                if not model_file:
                    commit_processing_successful = False
                    continue

                created_file = self.__create_new_file(db_session, str(new_file.path), timestamp, self.repository_id,
                                                      programming_language, model_file.id)
                db_session.commit()

        if not commit_processing_successful and self.NUMBER_OF_THREADS:
            Log.warning("Could not process commit " + str(commit_id) + ". Files added: " + str(
                manipulated_files['added_files']) + " files deleted: " + str(
                manipulated_files['deleted_files']) + " files changed: " + str(
                manipulated_files['changed_files']) + " files renamed: " + str(manipulated_files['renamed_files']))

        db_session.commit()

        if added_files_thread:
            added_files_thread.join()
        if changed_files_thread:
            changed_files_thread.join()
        if deleted_files_thread:
            deleted_files_thread.join()

        if db_session_local:
            db_session.close()

    def __thread_helper_added_file(self, commit_id, files, files_diff, timestamp, db_session=None):
        db_session_local = False
        if not db_session:
            db_session_local = True
            db_session = DB.create_session()
        for file in files:
            programming_language = self.__get_programming_langunage(file.path)

            created_file = self.__create_new_file(db_session, str(file.path), timestamp, self.repository_id,
                                                  programming_language)
            db_session.commit()
            try:
                created_version = self.__create_new_version(db_session, created_file.id, commit_id, 0, 0, file.size)
            except ValueError:
                Log.error("GityPython could not determine file size. Affected file: " + created_file.path + " Commit: " + commit_id)
                created_version = self.__create_new_version(db_session, created_file.id, commit_id, 0, 0, None)

            # skip this file because language is not interessting for us
            if not programming_language:
                continue
            self.__process_file_diff(db_session, file, files_diff, created_version)

        if db_session_local:
            db_session.close()

    def __thread_helper_deleted_or_changed_file(self, commit_id, files, files_diff, timestamp,
                                                db_session=None):
        db_session_local = False
        if not db_session:
            db_session_local = True
            db_session = DB.create_session()
        for file in files:
            commit_processing_successful = self.__process_deleted_or_changed_file(db_session, commit_id, file,
                                                                                  files_diff, timestamp)
            if not commit_processing_successful:
                Log.warning("Could not process commit " + str(commit_id) + ". Files affected: " + str(files))
                return

        if db_session_local:
            db_session.close()

    def __process_deleted_or_changed_file(self, db_session, commit_id, file, files_diff, timestamp):
        programming_language = self.__get_programming_langunage(file.path)

        created_version = self.__update_file_timestamp_and_create_version(db_session, commit_id, file, timestamp)

        # File is not yet in database
        if not created_version:
            return False

        # skip this file because language is not interessting for us
        if not programming_language:
            return True
        self.__process_file_diff(db_session, file, files_diff, created_version)
        return True

    def __update_file_timestamp_and_create_version(self, db_session, commit_id, file, timestamp):
        model_file = db_session.query(File).filter(File.path == str(file.path)).order_by(
            desc(File.timestamp)).first()

        # File is not yet in database
        if not model_file:
            return None

        model_file.timestamp = timestamp
        db_session.commit()
        try:
            created_version = self.__create_new_version(db_session, model_file.id, commit_id, 0, 0, file.size)
        except ValueError:
            Log.error("GityPython could not determine file size. Affected file: " + file.path + " Commit: " + commit_id)
            created_version = self.__create_new_version(db_session, model_file.id, commit_id, 0, 0, None)
        return created_version

    def __process_file_diff(self, db_session, file, files_diff, created_version):
        if Config.write_lines_in_database:
            # File could not be found in diff. hmmmmm
            file_diff = self.__get_diff_for_file(files_diff, str(file.path))
            if not file_diff:
                return
            self.__process_code_lines(db_session, file_diff['code'], created_version)

    def __get_commits(self):
        """
        Get all commits of a repository
        Returns: commits in reversed order --> first commit is first element in list
        """
        commits = list(self.repository.iter_commits(self.branch))
        commits.reverse()
        return commits

    def __get_changed_files(self, commit, previous_commit):
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

        diff_with_patch = commit.diff(previous_commit, create_patch=True)
        diff = commit.diff(previous_commit)

        for item in diff:
            if item.a_blob is None:
                deleted_files.append(item.b_blob)
            if item.b_blob is None:
                added_files.append(item.a_blob)
            if (item.a_blob is not None) and (item.b_blob is not None) and (not item.renamed):
                changed_files.append(item.a_blob)
            if item.renamed:
                renamed_files.append({'old_file': item.b_blob, 'new_file': item.a_blob})

        for item in diff_with_patch:
            # TODO here we lose file size I guess. Compare it to original file
            files_diff.append(item.diff.decode("utf-8", "ignore"))

        return {'added_files': added_files, 'deleted_files': deleted_files, 'changed_files': changed_files,
                'renamed_files': renamed_files, 'files_diff': files_diff}

    def __get_diff_for_file(self, files_diff, search_filename):

        # search the files_diff output for the right filename and return None if not found
        # if found return a dictrionary file,changed_line,code
        for diff_file in files_diff:
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

            # renamed file 2. Not realy recognized as rename by git. Don't know what to do with that...
            elif "similarity index 100%" in diff_lines[0]:
                filename = diff_lines[1][12:]

            # changed file
            else:
                filename = diff_lines[0][6:]

            if filename == search_filename:
                # lines_changed = diff_lines[3]
                code = diff_lines[2:]
                return {'filename': filename, 'code': code}

        return None

    def __process_code_lines(self, db_session, code, version):

        # because we compare commit with previous commit: Added and deleted lines are inverted

        added_lines_counter = 0
        added_lines = 0
        deleted_lines_counter = 0
        deleted_lines = 0

        for diff_line in code:
            # get information about line number
            if diff_line.startswith('@@', 0, 2):
                offset = 1
                try:
                    if ',' in diff_line.split('+')[0]:
                        added_lines_counter = int(diff_line[4:].split(',')[0])
                    else:
                        added_lines_counter = int(diff_line[4:].split(' ')[0])

                    if ',' in diff_line.split('+')[1]:
                        deleted_lines_counter = int(diff_line.split('+')[1].split(',')[0])
                    else:
                        deleted_lines_counter = int(diff_line.split('+')[1].split(' ')[0])

                    added_lines_counter -= offset
                    deleted_lines_counter -= offset

                except:
                    Log.error("Could no get diff information level strating with @@")
                    raise "Diff Parse Error"

            if diff_line.startswith('+', 0, 1):
                self.__create_new_line(db_session, diff_line, deleted_lines_counter, TYPE_DELETED, version.id)
                deleted_lines += 1
                added_lines_counter -= 1

            if diff_line.startswith('-', 0, 1):
                self.__create_new_line(db_session, diff_line, added_lines_counter,
                                       TYPE_ADDED, version.id)
                added_lines += 1
                deleted_lines_counter -= 1

            added_lines_counter += 1
            deleted_lines_counter += 1

        version.lines_added = added_lines
        version.lines_deleted = deleted_lines

    def __get_programming_langunage(self, path):
        splitted_path = path.split('.')

        if len(splitted_path) > 1:
            for language in self.PROGRAMMING_LANGUAGES:
                if language[1] == splitted_path[len(splitted_path) - 1]:
                    return language[0]
        return None

    def __create_new_repository(self, db_session, name, repository_url):
        # Try to retrieve the repository record, if not found a new one is created.
        if name is None:
            name = os.path.split(repository_url)[1]

        self.repository_orm = db_session.query(Repository).filter(Repository.name == name).one_or_none()
        if not self.repository_orm:
            # create new repository
            self.repository_orm = Repository(
                name=name,
                url=repository_url[0:MAX_URL_LENGTH]
            )
            db_session.add(self.repository_orm)
            db_session.flush()
            db_session.commit()
        else:
            # read existing commit ids into memory
            self.__read_existings_commit_ids(self.repository_orm.id)

        return self.repository_orm.id

    def __create_new_commit(self, db_session, commit_id, repository_id, message, author, timestamp):
        # Try to retrieve the commit record, if not found a new one is created.
        # TODO: Now that existing commits are skipped anyway, this query could be removed for performance
        commit_orm = db_session.query(Commit).filter(Commit.id == commit_id).one_or_none()
        if not commit_orm:
            commit_orm = Commit(
                id=commit_id,
                repository_id=repository_id,
                author=author[0:MAX_AUTHOR_LENGTH],
                message=message[0:MAX_MESSAGE_LENGTH],
                timestamp=timestamp
            )
            db_session.add(commit_orm)

    def __create_new_file(self, db_session, file_path, timestamp, repository_id, language, precursor_file_id=None):
        # Try to retrieve the file record, if not found a new one is created.
        file_orm = db_session.query(File).filter(File.path == file_path, File.timestamp == timestamp).one_or_none()
        if not file_orm:
            file_orm = File(
                id=uuid().hex,
                path=file_path[0:MAX_PATH_LENGTH],
                timestamp=timestamp,
                repository_id=repository_id,
                precursor_file_id=precursor_file_id,
                language=language
            )
            db_session.add(file_orm)
        return file_orm

    def __create_new_version(self, db_session, file_id, commit_id, lines_added,
                             lines_deleted,
                             file_size):
        version_orm = Version(
            id=uuid().hex,
            file_id=file_id,
            commit_id=commit_id,
            lines_added=lines_added,
            lines_deleted=lines_deleted,
            file_size=file_size
        )
        db_session.add(version_orm)
        return version_orm

    def __create_new_line(self, db_session, line, line_number, change_type, version_id):
        line_orm = Line(
            line=line[0:MAX_LINE_LENGTH],
            line_number=line_number,
            type=change_type,
            version_id=version_id
        )
        db_session.add(line_orm)

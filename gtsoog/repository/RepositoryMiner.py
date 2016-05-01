# coding=utf-8
import os
import threading
import datetime
from uuid import uuid4 as uuid

from git import Repo

from model import DB
from model.objects.Line import Line, MAX_LINE_LENGTH, TYPE_ADDED, TYPE_DELETED
from model.objects.Repository import Repository, MAX_URL_LENGTH
from model.objects.Commit import Commit, MAX_MESSAGE_LENGTH, MAX_AUTHOR_LENGTH
from model.objects.File import File
from model.objects.Version import Version, MAX_PATH_LENGTH
from utils import Log
from sqlalchemy import desc
from utils import Config


class RepositoryMiner(object):
    def __init__(self, repository_path, name=None, db_session=None, branch='master'):
        """ Initialize the Repository Miner

        Args:
            repository_path: The url to the repository
            name: Optional. The unique name of this repository. Defaults to the last part of the path.
            db_session: Optional if not specified it will create a new one
            branch: Optional. The branch to mine. Defaults to the master branch.
        """

        self.repository = Repo(repository_path)
        self.branch = branch

        self.PROGRAMMING_LANGUAGES = Config.programming_languages
        self.EMPTY_TREE_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

        # Size of the return character for calculating file size
        self.RETURN_SIGN_SIZE = 2

        self.init_db_sessions(db_session=db_session)

        self.existing_commit_ids = set()
        self.repository_id = self.__create_new_repository(self.db_session, name, repository_path)

        Log.info("Start mining the repository with path: " + repository_path)
        commits = self.__get_commits()
        self.iterate_commits(commits)

    def init_db_sessions(self, db_session=None):
        """ Init DB session. When treahding is activated it creates one db session per thread

        Args:
            db_session: Optional if not specified it will create a new one
        """
        if db_session == None:
            self.db_session = DB.create_session()
        else:
            self.db_session = db_session

    def close_all_db_sessions(self):
        """ Close DB session for every thread. And also main session.

        """
        self.db_session.close()

    def __read_existings_commit_ids(self, repository_id):
        """Read existing commits from database and skip does which already exists

        Args:
            repository_id:
        """
        self.existing_commit_ids = set(
            [t[0] for t in self.db_session.query(Commit.id).filter(Commit.repository_id == repository_id,
                                                                   Commit.complete == 1).all()])

    def __commit_exists(self, commit_id):
        return commit_id in self.existing_commit_ids

    def __get_project_file_count(self, repository_id):
        """Reads project file count of lastest commit in database

        Args:
            repository_id:
        Returns: project file count of the lastest commit in database
        """
        try:
            commit_orm = self.db_session.query(Commit).filter(Commit.repository_id == repository_id).order_by(
                desc(Commit.timestamp)).first()
            return commit_orm.project_file_count
        except Exception:
            return 0

    def __get_project_size(self, repository_id):
        """Reads project size (only of interested code files) of lastest commit in database

        Args:
            repository_id:
        Returns: project size (only of interested code files) of the lastest commit in database
        """
        try:
            commit_orm = self.db_session.query(Commit).filter(Commit.repository_id == repository_id).order_by(
                desc(Commit.timestamp)).first()
            return commit_orm.project_size
        except Exception:
            return 0

    def iterate_commits(self, commits):
        """Iterate all commits and do the work
        Args:
            commits:
        """
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

            if (len(commit.parents) <= 1) and (not self.__commit_exists(str(commit))):
                project_file_count = self.__get_project_file_count(self.repository_id)
                project_size = self.__get_project_size(self.repository_id)
                commit_orm = self.__process_commit(commit, previous_commit, project_size, project_file_count,
                                                   db_session=self.db_session)
                self.db_session.commit()

                # To prevent that half commits are in database (when gtsoog dies)
                commit_orm.complete = True
                self.db_session.commit()

    def __process_commit(self, commit, previous_commit, project_size, project_file_count, db_session=None):
        """Process a single commit.

        Args:
            commit: Actual commit
            previous_commit: Previous commit for creating differences
            project_size: Actual size of the project
            project_file_count: Acutal filecount of the project
            db_session: db session...
        Returns: commit_orm object

        """
        db_session_local = None
        if not db_session:
            db_session_local = True
            db_session = DB.create_session()

        added_files_thread = None
        changed_files_thread = None
        deleted_files_thread = None

        manipulated_files = self.__get_changed_files(commit, previous_commit)

        added_files = manipulated_files['added_files']
        added_files_count = len(added_files)
        deleted_files = manipulated_files['deleted_files']
        deleted_files_count = len(deleted_files)
        changed_files = manipulated_files['changed_files']
        changed_files_count = len(changed_files)
        renamed_files = manipulated_files['renamed_files']
        renamed_files_count = len(renamed_files)
        files_diff = manipulated_files['files_diff']

        new_project_file_count = project_file_count + added_files_count - deleted_files_count

        commit_time = datetime.datetime.utcfromtimestamp(commit.committed_date)
        commit_id = str(commit)

        commit_orm = self.__create_new_commit(db_session, commit_id, self.repository_id, commit.message,
                                              commit.author.email,
                                              commit_time, 0, 0, 0, 0, project_size, new_project_file_count)

        # no files were changed at all / very unlikley
        if (not added_files) and (not deleted_files) and (not changed_files) and (not renamed_files) and (
                not renamed_files):
            return commit_orm

        if added_files:
            for file in added_files:
                programming_language = self.__get_programming_langunage(file.path)

                file_orm = self.__create_new_file(db_session, self.repository_id,
                                                  programming_language)

                created_version = self.__create_new_version(db_session, file_orm.id, commit_id, 0, 0, 0, file.path)

                # skip this file because language is not interessting for us
                if not programming_language:
                    added_files_count -= 1
                    continue

                self.__process_file_diff(db_session, commit_id, file, files_diff, created_version)

        if deleted_files:
            for file in deleted_files:
                programming_language = self.__get_programming_langunage(file.path)
                if not programming_language:
                    deleted_files_count -= 1

                try:
                    version_orm = self.__process_deleted_or_changed_file(db_session, commit_id, file,
                                                                         programming_language,
                                                                         files_diff)
                    version_orm.deleted = True
                    version_orm.file_size = 0
                except ValueError as e:
                    Log.warning("Warning processing commit: " + str(commit_id) + ". File affected: " + str(
                        file.path) + " Reason: " + str(e))

        if changed_files:
            for file in changed_files:
                programming_language = self.__get_programming_langunage(file.path)
                if not programming_language:
                    changed_files_count -= 1

                try:
                    self.__process_deleted_or_changed_file(db_session, commit_id, file, programming_language,
                                                           files_diff)
                except ValueError as e:
                    Log.warning("Warning processing commit: " + str(commit_id) + ". File affected: " + str(
                        file.path) + " Reason: " + str(e))

        # for renamed files just create a new one and link to the old one
        if renamed_files:
            for file in renamed_files:
                old_file = file['old_file']
                new_file = file['new_file']

                old_version_orm = db_session.query(Commit, Version).filter(Commit.id == Version.commit_id,
                                                                           Version.path == str(old_file.path), Commit.repository_id == str(self.repository_id)).order_by(
                    desc(Commit.timestamp)).first()

                if not old_version_orm:
                    Log.warning("Could not process commit " + str(
                        commit_id) + ". Could not process rename because old file was not found. Old file: " + str(
                        old_file.path) + " new file: " + str(new_file.path))
                    continue

                version_orm = self.__create_new_version(db_session, old_version_orm.Version.file_id, commit_id, 0, 0, 0,
                                                        new_file.path)

                # skip this file because language is not interessting for us
                programming_language = self.__get_programming_langunage(new_file.path)
                if not programming_language:
                    renamed_files_count -= 1
                    continue

                version_orm.file_size = old_version_orm.Version.file_size
                self.__process_file_diff(db_session, commit_id, new_file, files_diff, version_orm)

        commit_orm.added_files_count = added_files_count
        commit_orm.deleted_files_count = deleted_files_count
        commit_orm.changed_files_count = changed_files_count
        commit_orm.renamed_files_count = renamed_files_count

        if added_files_thread:
            added_files_thread.join()
        if changed_files_thread:
            changed_files_thread.join()
        if deleted_files_thread:
            deleted_files_thread.join()

        if db_session_local:
            db_session.close()

        return commit_orm

    def __process_deleted_or_changed_file(self, db_session, commit_id, file, programming_language, files_diff):
        """Process single changed or deleted file. Creates new file version in database

        Args:
            db_session:
            commit_id:
            file:
            files_diff: diff of changed or deleted file
            timestamp: commit timestamp

        Returns: created_version

        """

        old_version_orm = db_session.query(Commit, Version).filter(Commit.id == Version.commit_id,
                                                                   Version.path == str(file.path), Commit.repository_id == str(self.repository_id)).order_by(
            desc(Commit.timestamp)).first()

        # file is probably a .orig file from a git merge ignore it
        if not old_version_orm:
            raise ValueError('file reference not yet in database, probably a .orig file from a merge')

        version_orm = self.__create_new_version(db_session, old_version_orm.Version.file_id, commit_id, 0, 0, 0,
                                                file.path)

        # File is not yet in database
        if not version_orm:
            raise ValueError('file reference not yet in database')

        # skip this file because language is not interessting for us
        if not programming_language:
            return version_orm

        self.__process_file_diff(db_session, commit_id, file, files_diff, version_orm)
        return version_orm

    def __process_file_diff(self, db_session, commit_id, file, files_diff, version_orm):
        """ get diff of the affected file for further code line processing

        Args:
            db_session:
            commit_id:
            file: affected file
            files_diff: diff of all files
            created_version: file version which diff belongs to

        Returns: Nothing

        """
        if Config.write_lines_in_database:
            file_diff = self.__get_diff_for_file(files_diff, str(file.path))

            # File could not be found in diff
            if not file_diff:
                return

            self.__process_code_lines(db_session, commit_id, file, file_diff['code'], version_orm)

    def __get_commits(self):
        """Get all commits of a repository

        Returns: commits in reversed order --> first commit is first element in list

        """
        commits = list(self.repository.iter_commits(self.branch))
        commits.reverse()
        return commits

    def __get_changed_files(self, commit, previous_commit):
        """process a commit and get the changed files and diff of them

        Args:
            commit:
            previous_commit:

        Returns: tuple of lists of added files, deleted files, changed files, renamed files and diff (of all files)

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
            files_diff.append(item.diff.decode("utf-8", "ignore"))

        return {'added_files': added_files, 'deleted_files': deleted_files, 'changed_files': changed_files,
                'renamed_files': renamed_files, 'files_diff': files_diff}

    def __get_diff_for_file(self, files_diff, search_filename):
        """String parsing of diff output. search for the filename in the files diff.

        Args:
            files_diff: diff of all files
            search_filename: file to search in diff

        Returns: tuple of filename and changed code (diff) which belongs to that file

        """
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
                filename = diff_lines[0][6:]

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

    def __process_code_lines(self, db_session, commit_id, file, code, version_orm):
        """Process code lines in diff and add it to the database
        because we compare commit with previous commit: Added and deleted lines are inverted
        Args:
            db_session:
            commit_id:
            code: code changes (diff)
            version_orm: file version
        """
        added_lines_counter = 0
        added_lines = 0
        changed_line_size = 0
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
                    Log.error("Could no get diff information level starting with @@")
                    raise "Diff Parse Error"

            # case deleted line (inverse because we compare current commit with previous)
            elif diff_line.startswith('+', 0, 1):
                self.__create_new_line(db_session, diff_line[1:], deleted_lines_counter, TYPE_DELETED, version_orm.id)
                deleted_lines += 1
                added_lines_counter -= 1
                changed_line_size -= (len(diff_line[1:]) + self.RETURN_SIGN_SIZE)
            # case added line (inverse because we compare current commit with previous)
            elif diff_line.startswith('-', 0, 1):
                self.__create_new_line(db_session, diff_line[1:], added_lines_counter,
                                       TYPE_ADDED, version_orm.id)
                added_lines += 1
                deleted_lines_counter -= 1
                changed_line_size += (len(diff_line[1:]) + self.RETURN_SIGN_SIZE)

            added_lines_counter += 1
            deleted_lines_counter += 1

        version_orm.lines_added = added_lines
        version_orm.lines_deleted = deleted_lines

        version_orm.file_size = file.size

        # set project size
        commit_orm = self.db_session.query(Commit).filter(Commit.id == commit_id, Commit.repository_id == str(self.repository_id)).one_or_none()
        commit_orm.project_size += version_orm.file_size

    def __get_programming_langunage(self, path):
        """Get programming language by file extension

        Args:
            path: file path including file extension

        Returns: programming language

        """
        splitted_path = path.split('.')

        if len(splitted_path) > 1:
            for language in self.PROGRAMMING_LANGUAGES:
                if language[1] == splitted_path[len(splitted_path) - 1]:
                    return language[0]
        return None

    def __create_new_repository(self, db_session, name, repository_url):
        """Create new repository record in database if not exists

        Args:
            db_session:
            name:
            repository_url:

        Returns: repository record

        """
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
            Log.info("Repository " + str(self.repository_orm.name) + " already in database.")
            self.__read_existings_commit_ids(self.repository_orm.id)

        return self.repository_orm.id

    def __create_new_commit(self, db_session, commit_id, repository_id, message, author, timestamp, added_files_count,
                            deleted_files_count, changed_files_count, renamed_files_count, project_size,
                            project_file_count):
        """Create new commit record in database if not exists

        Args:
            db_session:
            commit_id:
            repository_id:
            message:
            author:
            timestamp:
            added_files_count:
            deleted_files_count:
            changed_files_count:
            renamed_files_count:
            project_size: Actual size of all fiels in the project
            project_file_count: Actual amount of files in the project
        """
        # Try to retrieve the commit record, if not found a new one is created.
        # TODO: Now that existing commits are skipped anyway, this query could be removed for performance
        commit_orm = db_session.query(Commit).filter(Commit.id == commit_id, Commit.repository_id == str(self.repository_id)).one_or_none()
        if not commit_orm:
            commit_orm = Commit(
                id=commit_id,
                repository_id=repository_id,
                author=author[0:MAX_AUTHOR_LENGTH],
                message=message[0:MAX_MESSAGE_LENGTH],
                timestamp=timestamp,
                added_files_count=added_files_count,
                deleted_files_count=deleted_files_count,
                changed_files_count=changed_files_count,
                renamed_files_count=renamed_files_count,
                project_size=project_size,
                project_file_count=project_file_count,
                complete=False
            )
            db_session.add(commit_orm)
        return commit_orm

    def __create_new_file(self, db_session, repository_id, language):
        """Create new file record in database if not exists

        Args:
            db_session:
^^
            repository_id:
            language:

        Returns: created file

        """
        file_orm = File(
            id=uuid().hex,
            repository_id=repository_id,
            language=language
        )
        db_session.add(file_orm)
        return file_orm

    def __create_new_version(self, db_session, file_id, commit_id, lines_added,
                             lines_deleted,
                             file_size, file_path):
        """Create new version record in database

        Args:
            db_session:
            file_id:
            commit_id:
            lines_added:
            lines_deleted:
            file_size:
            file_path: Actual path of the file

        Returns: created version

        """
        version_orm = Version(
            id=uuid().hex,
            file_id=file_id,
            commit_id=commit_id,
            lines_added=lines_added,
            lines_deleted=lines_deleted,
            file_size=file_size,
            path=file_path[0:MAX_PATH_LENGTH],
            deleted=False
        )
        db_session.add(version_orm)
        return version_orm

    def __create_new_line(self, db_session, line, line_number, change_type, version_id):
        """Create new line record in database

        Args:
            db_session:
            line:
            line_number:
            change_type:
            version_id:
        """
        line_orm = Line(
            line=line[0:MAX_LINE_LENGTH],
            line_number=line_number,
            type=change_type,
            version_id=version_id
        )
        db_session.add(line_orm)

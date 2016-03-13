from git import Repo
from gtsoog import Log
import threading

class RepositoryMiner(object):

    def __init__(self, repository_url, branch='master'):
        self.repository = Repo(repository_url)
        self.branch = branch

        self.NUMBER_OF_THREADS = 0
        self.interesting_file_extensions = [".md",".py",".java"]

        commits = self.get_commits()
        self.iterate_commits(commits)


    def iterate_commits(self, commits):

        """

        Args:
            commits:
        """
        previous_commit = None

        threads = []
        commit_counter=0

        for commit in commits:
            commit_counter+=1
            if commit_counter % 1000 == 0:
                Log.log("Commit counter: " + str(commit_counter),Log.LEVEL_DEBUG)

            if commit.parents:
                previous_commit = commit.parents[0]

            if len(commit.parents) <= 1:
                if threading.active_count() < self.NUMBER_OF_THREADS:
                    t = threading.Thread(target=self.process_commit, args=(commit,previous_commit,))
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

        Log.log("------------",Log.LEVEL_DEBUG)
        Log.log("Commit: " + commit.message,Log.LEVEL_DEBUG)
        Log.log("Added: " + str([file.path for file in added_files]),Log.LEVEL_DEBUG)
        Log.log("Deleted: " + str([file.path for file in deleted_files]),Log.LEVEL_DEBUG)
        Log.log("Changed: " + str([file.path for file in changed_files]),Log.LEVEL_DEBUG)

        Log.log("Diff: " + str(files_diff),Log.LEVEL_DEBUG)


        return
        """ old stuff for getting file content """
        #Log.log("Added: " + str([file.path for file in added_files]),Log.LEVEL_DEBUG)
        # if added_files:
        #      for file in added_files:
        #          Log.log("File: " + str(file.path),Log.LEVEL_DEBUG)
        #
        #          if (any(file.path.rsplit(".")[-1] in s for s in self.interesting_file_extensions)) and (file.data_stream.read()):
        #              Log.log(str( file.data_stream.read().decode('utf8',"ignore") ),Log.LEVEL_DEBUG)
        #
        #  Log.log("Deleted: " + str([file.path for file in deleted_files]),Log.LEVEL_DEBUG)
        #
        #  if deleted_files:
        #      for file in deleted_files:
        #          Log.log("File: " + str(file.path),Log.LEVEL_DEBUG)
        #
        #          if (any(file.path.rsplit(".")[-1] in s for s in self.interesting_file_extensions)) and (file.data_stream.read()):
        #              Log.log(str( file.data_stream.read().decode('utf8',"ignore") ),Log.LEVEL_DEBUG)
        #
        #  Log.log("Changed: " + str([file.path for file in changed_files]),Log.LEVEL_DEBUG)
        #
        #
        #  if changed_files:
        #      for file in changed_files:
        #          Log.log("File: " + str(file.path),Log.LEVEL_DEBUG)
        #
        #          if (any(file.path.rsplit(".")[-1] in s for s in self.interesting_file_extensions)) and (file.data_stream.read()):
        #              Log.log(str( file.data_stream.read().decode('utf8',"ignore") ),Log.LEVEL_DEBUG)

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

        #for diff_added in diff_with_patch.iter_change_type('A'):
            #print(diff_added)

        """ handle first commit"""
        if previous_commit is None:
            added_files = deleted_files
            deleted_files = []

        return added_files,deleted_files,changed_files,files_diff

    def stats(repository_path, branch='master'):
        print("mine mine\n")
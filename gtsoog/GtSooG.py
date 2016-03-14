from model import DB
from repository.RepositoryMiner import RepositoryMiner


def main():
    DB.create_db()
    repository_url = r"P:\Studium\FS2016\BA\GitHubProjects\LED-Cube-Prototyper"

    RepositoryMiner(repository_url)


main()
